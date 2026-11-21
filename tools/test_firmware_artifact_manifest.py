#!/usr/bin/env python3
"""Release-owned firmware artifact manifest and checksum regressions."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from write_firmware_artifact_manifest import (
    CHECKSUMS_FILENAME,
    MANIFEST_FILENAME,
    ManifestError,
    build_artifact_manifest_payloads,
    write_artifact_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "hardware-ci.yml"
SOURCE_SHA = "a" * 40
PR_HEAD_SHA = "b" * 40
PR_BASE_SHA = "c" * 40


class FirmwareArtifactManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.artifact_dir = Path(self.temp.name) / "artifact"
        self.artifact_dir.mkdir()
        (self.artifact_dir / "firmware.bin").write_bytes(b"firmware-payload")
        (self.artifact_dir / "sketch.ino").write_bytes(b"// source sketch\n")

    def kwargs(self):
        return {
            "artifact_dir": str(self.artifact_dir),
            "repository": "BlazeDevStudio/CoinOperatedEcosystem",
            "source_sha": SOURCE_SHA,
            "event_sha": SOURCE_SHA,
            "pr_head_sha": PR_HEAD_SHA,
            "pr_base_sha": PR_BASE_SHA,
            "product": "BlazePwifiVendo",
            "board": "esp8266",
            "fqbn": "esp8266:esp8266:nodemcuv2",
            "arduino_cli_version": "1.6.0",
            "core_id": "esp8266:esp8266",
            "core_version": "3.1.2",
        }

    def test_manifest_and_checksums_are_deterministic_and_bind_exact_sources(self):
        first_manifest, first_checksums = build_artifact_manifest_payloads(**self.kwargs())
        second_manifest, second_checksums = build_artifact_manifest_payloads(**self.kwargs())
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(first_checksums, second_checksums)

        manifest = json.loads(first_manifest)
        self.assertEqual(manifest["schema"], "phoenix/firmware-artifact/v1")
        self.assertEqual(
            manifest["source"],
            {
                "repository": "BlazeDevStudio/CoinOperatedEcosystem",
                "checked_out_sha": SOURCE_SHA,
                "event_sha": SOURCE_SHA,
                "pull_request_head_sha": PR_HEAD_SHA,
                "pull_request_base_sha": PR_BASE_SHA,
            },
        )
        self.assertEqual(
            manifest["target"],
            {
                "product": "BlazePwifiVendo",
                "board": "esp8266",
                "fqbn": "esp8266:esp8266:nodemcuv2",
            },
        )
        self.assertEqual(
            manifest["toolchain"],
            {
                "arduino_cli_version": "1.6.0",
                "core_id": "esp8266:esp8266",
                "core_version": "3.1.2",
            },
        )
        self.assertEqual(
            [item["path"] for item in manifest["files"]],
            ["firmware.bin", "sketch.ino"],
        )
        binary = next(item for item in manifest["files"] if item["path"] == "firmware.bin")
        self.assertEqual(binary["size"], len(b"firmware-payload"))
        self.assertEqual(binary["sha256"], hashlib.sha256(b"firmware-payload").hexdigest())

        checksum_lines = first_checksums.decode("ascii").splitlines()
        self.assertEqual(len(checksum_lines), 3)
        self.assertTrue(any(line.endswith("  firmware.bin") for line in checksum_lines))
        self.assertTrue(any(line.endswith("  sketch.ino") for line in checksum_lines))
        self.assertTrue(
            any(
                line == f"{hashlib.sha256(first_manifest).hexdigest()}  {MANIFEST_FILENAME}"
                for line in checksum_lines
            )
        )
        self.assertFalse(any(line.endswith(f"  {CHECKSUMS_FILENAME}") for line in checksum_lines))

    def test_writer_publishes_both_files_and_refuses_overwrite(self):
        manifest_path, checksums_path = write_artifact_manifest(**self.kwargs())
        manifest = Path(manifest_path)
        checksums = Path(checksums_path)
        self.assertTrue(manifest.is_file())
        self.assertTrue(checksums.is_file())
        original_manifest = manifest.read_bytes()
        original_checksums = checksums.read_bytes()

        with self.assertRaises(ManifestError):
            write_artifact_manifest(**self.kwargs())

        self.assertEqual(manifest.read_bytes(), original_manifest)
        self.assertEqual(checksums.read_bytes(), original_checksums)

    def test_rejects_empty_firmware_binary(self):
        (self.artifact_dir / "firmware.bin").write_bytes(b"")
        with self.assertRaisesRegex(ManifestError, "non-empty .bin firmware payload"):
            build_artifact_manifest_payloads(**self.kwargs())

    def test_rejects_artifact_directory_without_firmware_binary(self):
        (self.artifact_dir / "firmware.bin").unlink()
        with self.assertRaisesRegex(ManifestError, "at least one non-empty .bin"):
            build_artifact_manifest_payloads(**self.kwargs())

    def test_rejects_unreadable_directory_during_artifact_walk(self):
        def fail_walk(_path, **kwargs):
            self.assertIn("onerror", kwargs)
            kwargs["onerror"](PermissionError("permission denied"))
            return iter(())

        with mock.patch("write_firmware_artifact_manifest.os.walk", side_effect=fail_walk):
            with self.assertRaisesRegex(ManifestError, "could not enumerate artifact directory"):
                build_artifact_manifest_payloads(**self.kwargs())

    def test_rejects_symlinked_artifact_file(self):
        target = Path(self.temp.name) / "outside.bin"
        target.write_bytes(b"outside")
        link = self.artifact_dir / "linked.bin"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this runner")
        with self.assertRaisesRegex(ManifestError, "symlink or non-regular"):
            build_artifact_manifest_payloads(**self.kwargs())

    def test_rejects_symlinked_artifact_directory(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "hidden.bin").write_bytes(b"outside")
        link = self.artifact_dir / "nested"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this runner")
        with self.assertRaisesRegex(ManifestError, "symlink or non-directory"):
            build_artifact_manifest_payloads(**self.kwargs())

    def test_rejects_mismatched_checked_out_and_event_sha(self):
        kwargs = self.kwargs()
        kwargs["event_sha"] = "d" * 40
        with self.assertRaisesRegex(ManifestError, "does not match the checked-out source SHA"):
            build_artifact_manifest_payloads(**kwargs)

    def test_rejects_malformed_source_sha(self):
        kwargs = self.kwargs()
        kwargs["source_sha"] = "not-a-git-sha"
        with self.assertRaisesRegex(ManifestError, "40-character Git SHA"):
            build_artifact_manifest_payloads(**kwargs)

    def test_workflow_writes_board_manifests_before_artifact_upload(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for board, fqbn, core_id, core_version in (
            ("ESP8266", "esp8266:esp8266:nodemcuv2", "esp8266:esp8266", "3.1.2"),
            ("ESP32", "esp32:esp32:esp32", "esp32:esp32", "3.3.13"),
        ):
            write_name = f"Write {board} firmware artifact manifest and SHA256SUMS"
            upload_name = f"Upload {board} Firmware Artifact"
            write_marker = f"      - name: {write_name}\n"
            upload_marker = f"      - name: {upload_name}\n"
            self.assertIn(write_marker, workflow)
            self.assertIn(upload_marker, workflow)
            write_start = workflow.index(write_marker)
            upload_start = workflow.index(upload_marker)
            self.assertLess(write_start, upload_start)
            next_step = re.search(r"(?m)^      - name:", workflow[write_start + len(write_marker):])
            self.assertIsNotNone(next_step)
            block_end = write_start + len(write_marker) + next_step.start()
            block = workflow[write_start:block_end]
            self.assertIn("python3 tools/write_firmware_artifact_manifest.py", block)
            self.assertIn('source_sha="$(git rev-parse HEAD)"', block)
            self.assertIn('--source-sha "$source_sha"', block)
            self.assertIn('--event-sha "$GITHUB_SHA"', block)
            self.assertIn(f"--board {board.lower()}", block)
            self.assertIn(f"--fqbn {fqbn}", block)
            self.assertIn(f"--core-id {core_id}", block)
            self.assertIn(f"--core-version {core_version}", block)


if __name__ == "__main__":
    unittest.main()
