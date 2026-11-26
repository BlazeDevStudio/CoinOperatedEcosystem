#!/usr/bin/env python3
"""Release-owned firmware artifact manifest and checksum regressions."""
from __future__ import annotations

import hashlib
import json
from contextlib import redirect_stdout
from io import StringIO
import os
import re
import stat
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import write_firmware_artifact_manifest as manifest_writer

from write_firmware_artifact_manifest import (
    CHECKSUMS_FILENAME,
    MANIFEST_FILENAME,
    ManifestError,
    build_artifact_manifest_payloads,
    main,
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

    def test_writer_durably_rolls_back_manifest_after_checksum_creation_failure(self):
        manifest_path = self.artifact_dir / MANIFEST_FILENAME
        checksums_path = self.artifact_dir / CHECKSUMS_FILENAME
        original_write = manifest_writer._write_new_file
        original_fsync = os.fsync
        directory_sync_states = []

        def fail_checksum_write(directory, filename, content, *args, **kwargs):
            if filename == CHECKSUMS_FILENAME:
                raise FileExistsError("injected checksum creation failure")
            return original_write(directory, filename, content, *args, **kwargs)

        def observe_directory_fsync(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_sync_states.append((manifest_path.exists(), checksums_path.exists()))
            return original_fsync(descriptor)

        with mock.patch.object(
            manifest_writer, "_write_new_file", side_effect=fail_checksum_write
        ):
            with mock.patch.object(
                manifest_writer.os, "fsync", side_effect=observe_directory_fsync
            ):
                with self.assertRaisesRegex(
                    FileExistsError, "injected checksum creation failure"
                ):
                    write_artifact_manifest(**self.kwargs())

        self.assertFalse(manifest_path.exists())
        self.assertFalse(checksums_path.exists())
        self.assertEqual(directory_sync_states, [(False, False)])

    def test_write_new_file_removes_partial_output_after_keyboard_interrupt(self):
        output_path = self.artifact_dir / "interrupted.bin"
        directory_descriptor = os.open(
            self.artifact_dir,
            os.O_RDONLY | os.O_DIRECTORY,
        )
        self.addCleanup(os.close, directory_descriptor)
        original_fsync = os.fsync
        fsync_calls = 0

        def interrupt_first_sync(descriptor):
            nonlocal fsync_calls
            fsync_calls += 1
            if fsync_calls == 1:
                raise KeyboardInterrupt("simulated partial-output interruption")
            return original_fsync(descriptor)

        with mock.patch.object(
            manifest_writer.os, "fsync", side_effect=interrupt_first_sync
        ):
            with self.assertRaisesRegex(
                KeyboardInterrupt, "simulated partial-output interruption"
            ):
                manifest_writer._write_new_file(
                    str(self.artifact_dir),
                    output_path.name,
                    b"partial artifact bytes",
                    directory_descriptor=directory_descriptor,
                )

        self.assertFalse(output_path.exists())
        self.assertEqual(fsync_calls, 2, "partial-file removal must be directory-synced")

    def test_writer_rolls_back_manifest_pair_after_keyboard_interrupt(self):
        manifest_path = self.artifact_dir / MANIFEST_FILENAME
        checksums_path = self.artifact_dir / CHECKSUMS_FILENAME
        original_write = manifest_writer._write_new_file
        original_fsync = os.fsync
        directory_sync_states = []

        def interrupt_checksum_write(directory, filename, content, *args, **kwargs):
            if filename == CHECKSUMS_FILENAME:
                self.assertTrue(
                    manifest_path.exists(),
                    "the first manifest must exist before checksum publication is interrupted",
                )
                raise KeyboardInterrupt("simulated checksum publication interruption")
            return original_write(directory, filename, content, *args, **kwargs)

        def observe_directory_fsync(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_sync_states.append((manifest_path.exists(), checksums_path.exists()))
            return original_fsync(descriptor)

        with mock.patch.object(
            manifest_writer, "_write_new_file", side_effect=interrupt_checksum_write
        ):
            with mock.patch.object(
                manifest_writer.os, "fsync", side_effect=observe_directory_fsync
            ):
                with self.assertRaisesRegex(
                    KeyboardInterrupt, "simulated checksum publication interruption"
                ):
                    write_artifact_manifest(**self.kwargs())

        self.assertFalse(manifest_path.exists())
        self.assertFalse(checksums_path.exists())
        self.assertEqual(
            directory_sync_states,
            [(False, False)],
            "the rollback must directory-sync the removed manifest",
        )

    def test_writer_durably_rolls_back_pair_after_directory_fsync_failure(self):
        manifest_path = self.artifact_dir / MANIFEST_FILENAME
        checksums_path = self.artifact_dir / CHECKSUMS_FILENAME
        original_fsync = os.fsync
        directory_sync_states = []

        def fail_first_directory_fsync(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_sync_states.append((manifest_path.exists(), checksums_path.exists()))
                if len(directory_sync_states) == 1:
                    raise OSError("injected directory fsync failure")
            return original_fsync(descriptor)

        with mock.patch.object(
            manifest_writer.os, "fsync", side_effect=fail_first_directory_fsync
        ):
            with self.assertRaisesRegex(OSError, "injected directory fsync failure"):
                write_artifact_manifest(**self.kwargs())

        self.assertFalse(manifest_path.exists())
        self.assertFalse(checksums_path.exists())
        self.assertEqual(
            directory_sync_states,
            [(True, True), (False, False)],
            "rollback must be directory-synced after both published names are removed",
        )

    def test_writer_reports_unconfirmed_rollback_when_output_removal_fails(self):
        manifest_path = self.artifact_dir / MANIFEST_FILENAME
        original_write = manifest_writer._write_new_file
        original_unlink = os.unlink

        def fail_checksum_write(directory, filename, content, *args, **kwargs):
            if filename == CHECKSUMS_FILENAME:
                raise FileExistsError("injected checksum creation failure")
            return original_write(directory, filename, content, *args, **kwargs)

        def fail_manifest_unlink(path, *args, **kwargs):
            if (
                os.fspath(path) == MANIFEST_FILENAME
                and kwargs.get("dir_fd") is not None
            ):
                raise PermissionError("injected rollback unlink denial")
            return original_unlink(path, *args, **kwargs)

        with mock.patch.object(
            manifest_writer, "_write_new_file", side_effect=fail_checksum_write
        ):
            with mock.patch.object(
                manifest_writer.os, "unlink", side_effect=fail_manifest_unlink
            ):
                with self.assertRaisesRegex(ManifestError, "rollback could not be confirmed"):
                    write_artifact_manifest(**self.kwargs())

        self.assertTrue(manifest_path.exists())

    def test_write_new_file_reports_interrupted_partial_output_rollback(self):
        output_path = self.artifact_dir / "interrupted-rollback.bin"
        directory_descriptor = os.open(
            self.artifact_dir,
            os.O_RDONLY | os.O_DIRECTORY,
        )
        self.addCleanup(os.close, directory_descriptor)
        original_fsync = os.fsync
        original_unlink = os.unlink
        file_sync_calls = 0
        directory_sync_states = []

        def interrupt_file_sync(descriptor):
            nonlocal file_sync_calls
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_sync_states.append(output_path.exists())
                return original_fsync(descriptor)
            file_sync_calls += 1
            if file_sync_calls == 1:
                raise KeyboardInterrupt("injected partial-output write interruption")
            return original_fsync(descriptor)

        def interrupt_output_unlink(path, *args, **kwargs):
            if (
                os.fspath(path) == output_path.name
                and kwargs.get("dir_fd") == directory_descriptor
            ):
                raise KeyboardInterrupt("injected partial-output rollback interruption")
            return original_unlink(path, *args, **kwargs)

        with mock.patch.object(
            manifest_writer.os, "fsync", side_effect=interrupt_file_sync
        ):
            with mock.patch.object(
                manifest_writer.os, "unlink", side_effect=interrupt_output_unlink
            ):
                with self.assertRaisesRegex(
                    ManifestError,
                    "partial artifact output rollback could not be confirmed",
                ):
                    manifest_writer._write_new_file(
                        str(self.artifact_dir),
                        output_path.name,
                        b"partial output",
                        directory_descriptor=directory_descriptor,
                    )

        self.assertTrue(output_path.exists())
        self.assertEqual(
            directory_sync_states,
            [True],
            "the failed unlink must still be followed by a directory sync attempt",
        )

    def test_writer_continues_manifest_pair_rollback_after_keyboard_interrupt(self):
        manifest_path = self.artifact_dir / MANIFEST_FILENAME
        checksums_path = self.artifact_dir / CHECKSUMS_FILENAME
        original_fsync = os.fsync
        original_unlink = os.unlink
        directory_fsync_calls = 0
        directory_sync_states = []
        unlink_names = []

        def fail_publication_sync_then_observe_rollback(descriptor):
            nonlocal directory_fsync_calls
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_fsync_calls += 1
                if directory_fsync_calls == 1:
                    raise OSError("injected publication directory fsync failure")
                directory_sync_states.append(
                    (manifest_path.exists(), checksums_path.exists())
                )
            return original_fsync(descriptor)

        def interrupt_first_pair_unlink(path, *args, **kwargs):
            name = os.fspath(path)
            if kwargs.get("dir_fd") is not None and name in (
                MANIFEST_FILENAME,
                CHECKSUMS_FILENAME,
            ):
                unlink_names.append(name)
                if len(unlink_names) == 1:
                    raise KeyboardInterrupt("injected pair rollback interruption")
            return original_unlink(path, *args, **kwargs)

        with mock.patch.object(
            manifest_writer.os,
            "fsync",
            side_effect=fail_publication_sync_then_observe_rollback,
        ):
            with mock.patch.object(
                manifest_writer.os, "unlink", side_effect=interrupt_first_pair_unlink
            ):
                with self.assertRaisesRegex(
                    ManifestError, "rollback could not be confirmed"
                ):
                    write_artifact_manifest(**self.kwargs())

        self.assertEqual(
            unlink_names,
            [CHECKSUMS_FILENAME, MANIFEST_FILENAME],
            "rollback must continue to the remaining output after an interruption",
        )
        self.assertFalse(manifest_path.exists())
        self.assertTrue(
            checksums_path.exists(),
            "the interrupted unlink must be reported as an unconfirmed leftover",
        )
        self.assertEqual(
            directory_sync_states,
            [(False, True)],
            "directory sync must still be attempted after the interrupted unlink",
        )

    def test_rejects_directory_entry_added_after_descriptor_listing_snapshot(self):
        original_listdir = os.listdir
        added = False

        def add_entry_after_snapshot(directory_descriptor):
            nonlocal added
            names = original_listdir(directory_descriptor)
            if not added:
                (self.artifact_dir / "late.bin").write_bytes(b"late firmware payload")
                added = True
            return names

        with mock.patch.object(
            manifest_writer.os, "listdir", side_effect=add_entry_after_snapshot
        ):
            with self.assertRaisesRegex(
                ManifestError, "artifact directory changed while scanning"
            ):
                build_artifact_manifest_payloads(**self.kwargs())

        self.assertTrue(added, "the deterministic post-listing mutation must execute")
        self.assertTrue((self.artifact_dir / "late.bin").is_file())

    def test_writer_rejects_artifact_directory_replaced_after_scan(self):
        original_directory = self.artifact_dir
        displaced_directory = Path(self.temp.name) / "artifact-original"
        replacement_directory = Path(self.temp.name) / "replacement"
        replacement_directory.mkdir()

        original_builder = manifest_writer.build_artifact_manifest_payloads

        def scan_then_replace(**kwargs):
            payloads = original_builder(**kwargs)
            original_directory.rename(displaced_directory)
            replacement_directory.rename(original_directory)
            return payloads

        with mock.patch.object(
            manifest_writer,
            "build_artifact_manifest_payloads",
            side_effect=scan_then_replace,
        ):
            with self.assertRaisesRegex(
                ManifestError,
                "artifact directory changed during manifest scan",
            ):
                write_artifact_manifest(**self.kwargs())

        self.assertFalse(
            (original_directory / MANIFEST_FILENAME).exists(),
            "replacement directory must not receive a manifest for another directory's payloads",
        )
        self.assertFalse((original_directory / CHECKSUMS_FILENAME).exists())
        self.assertFalse((displaced_directory / MANIFEST_FILENAME).exists())
        self.assertTrue((displaced_directory / "firmware.bin").is_file())

    def test_writer_rejects_nested_directory_replaced_with_symlink_before_file_open(self):
        nested_dir = self.artifact_dir / "nested"
        nested_dir.mkdir()
        nested_payload = nested_dir / "extra.bin"
        nested_payload.write_bytes(b"nested-firmware-payload")
        displaced_dir = Path(self.temp.name) / "displaced-nested"
        original_open = os.open
        replaced = False

        def replace_parent_before_open(path, flags, *args, **kwargs):
            nonlocal replaced
            candidate = os.fspath(path)
            is_target = (
                candidate == str(nested_payload)
                or (
                    candidate == nested_payload.name
                    and kwargs.get("dir_fd") is not None
                )
            )
            if is_target and not replaced:
                nested_dir.rename(displaced_dir)
                nested_dir.symlink_to(displaced_dir, target_is_directory=True)
                replaced = True
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(
            manifest_writer.os, "open", side_effect=replace_parent_before_open
        ):
            with self.assertRaisesRegex(
                ManifestError,
                "artifact directory changed during scan|artifact directory changed while scanning|symlink",
            ):
                build_artifact_manifest_payloads(**self.kwargs())

        self.assertTrue(replaced, "the deterministic parent-directory race must execute")
        self.assertTrue(nested_dir.is_symlink())
        self.assertTrue((displaced_dir / "extra.bin").is_file())

    def test_rejects_empty_firmware_binary(self):
        (self.artifact_dir / "firmware.bin").write_bytes(b"")
        with self.assertRaisesRegex(ManifestError, "non-empty .bin firmware payload"):
            build_artifact_manifest_payloads(**self.kwargs())

    def test_rejects_artifact_directory_without_firmware_binary(self):
        (self.artifact_dir / "firmware.bin").unlink()
        with self.assertRaisesRegex(ManifestError, "at least one non-empty .bin"):
            build_artifact_manifest_payloads(**self.kwargs())

    def test_rejects_unreadable_directory_during_descriptor_scan(self):
        def fail_listdir(directory_descriptor):
            self.assertIsInstance(directory_descriptor, int)
            raise PermissionError("permission denied")

        with mock.patch.object(
            manifest_writer.os, "listdir", side_effect=fail_listdir
        ):
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

    def test_cli_publishes_manifest_and_checksums_with_exact_provenance(self):
        output = StringIO()
        kwargs = self.kwargs()
        arguments = [
            "--artifact-dir", kwargs["artifact_dir"],
            "--repository", kwargs["repository"],
            "--source-sha", kwargs["source_sha"],
            "--event-sha", kwargs["event_sha"],
            "--pr-head-sha", kwargs["pr_head_sha"],
            "--pr-base-sha", kwargs["pr_base_sha"],
            "--product", kwargs["product"],
            "--board", kwargs["board"],
            "--fqbn", kwargs["fqbn"],
            "--arduino-cli-version", kwargs["arduino_cli_version"],
            "--core-id", kwargs["core_id"],
            "--core-version", kwargs["core_version"],
        ]
        with redirect_stdout(output):
            result = main(arguments)

        self.assertEqual(result, 0)
        self.assertIn("FIRMWARE-ARTIFACT-MANIFEST-PASS", output.getvalue())
        self.assertIn("FIRMWARE-SHA256SUMS-PASS", output.getvalue())
        self.assertTrue((self.artifact_dir / MANIFEST_FILENAME).is_file())
        self.assertTrue((self.artifact_dir / CHECKSUMS_FILENAME).is_file())

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


    def test_rejects_payload_mutated_in_place_while_hashing(self):
        payload_path = self.artifact_dir / "firmware.bin"
        chunk_size = 1024 * 1024
        payload_path.write_bytes(b"A" * (chunk_size + 64))
        manifest_path = self.artifact_dir / MANIFEST_FILENAME
        checksums_path = self.artifact_dir / CHECKSUMS_FILENAME
        original_read = os.read
        read_calls = 0

        def mutate_after_first_chunk(descriptor, size):
            nonlocal read_calls
            chunk = original_read(descriptor, size)
            if read_calls == 0:
                # Preserve inode and length while changing bytes already read.
                with open(payload_path, "r+b") as payload:
                    payload.write(b"B" * chunk_size)
                    payload.flush()
                    os.fsync(payload.fileno())
            read_calls += 1
            return chunk

        with mock.patch.object(
            manifest_writer.os, "read", side_effect=mutate_after_first_chunk
        ):
            with self.assertRaisesRegex(ManifestError, "changed while hashing"):
                write_artifact_manifest(**self.kwargs())

        self.assertGreaterEqual(read_calls, 2)
        self.assertFalse(manifest_path.exists())
        self.assertFalse(checksums_path.exists())



    def test_scanner_preserves_primary_error_when_root_descriptor_close_fails(self):
        original_open = os.open
        original_close = os.close
        root_descriptor = None

        def capture_root_descriptor(path, flags, *args, **kwargs):
            nonlocal root_descriptor
            descriptor = original_open(path, flags, *args, **kwargs)
            if (
                os.fspath(path) == os.path.abspath(str(self.artifact_dir))
                and flags & os.O_DIRECTORY
            ):
                root_descriptor = descriptor
            return descriptor

        def close_then_fail(descriptor):
            if descriptor == root_descriptor:
                original_close(descriptor)
                raise OSError("injected root descriptor close failure")
            return original_close(descriptor)

        def fail_scan(*args, **kwargs):
            raise ManifestError("primary artifact scan failure")

        with mock.patch.object(
            manifest_writer.os, "open", side_effect=capture_root_descriptor
        ), mock.patch.object(
            manifest_writer.os, "close", side_effect=close_then_fail
        ), mock.patch.object(
            manifest_writer, "_scan_artifact_directory_fd", side_effect=fail_scan
        ):
            with self.assertRaisesRegex(
                ManifestError, "primary artifact scan failure"
            ) as raised:
                manifest_writer._scan_artifact_files(str(self.artifact_dir))

        self.assertIsNotNone(root_descriptor)
        notes = getattr(raised.exception, "__notes__", [])
        self.assertTrue(
            any(
                "artifact root directory" in note
                and "injected root descriptor close failure" in note
                for note in notes
            ),
            f"expected close failure to be attached to primary exception, got {notes!r}",
        )


    def test_write_new_file_preserves_write_error_when_close_also_fails(self):
        output_path = self.artifact_dir / "write-and-close-failure.bin"
        original_fdopen = os.fdopen

        class CloseFailingOutput:
            def __init__(self, descriptor, mode):
                self.stream = original_fdopen(descriptor, mode)

            @property
            def closed(self):
                return self.stream.closed

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                self.close()
                return False

            def write(self, content):
                raise OSError("primary output write failure")

            def flush(self):
                return self.stream.flush()

            def fileno(self):
                return self.stream.fileno()

            def close(self):
                self.stream.close()
                raise OSError("secondary output close failure")

        with mock.patch.object(
            manifest_writer.os, "fdopen", side_effect=CloseFailingOutput
        ):
            with self.assertRaisesRegex(
                OSError, "primary output write failure"
            ) as raised:
                manifest_writer._write_new_file(
                    str(self.artifact_dir),
                    output_path.name,
                    b"artifact bytes",
                )

        self.assertFalse(output_path.exists(), "failed output must be removed")
        notes = getattr(raised.exception, "__notes__", [])
        self.assertTrue(
            any("secondary output close failure" in note for note in notes),
            f"expected close failure to be attached to primary error, got {notes!r}",
        )


    def test_write_new_file_preserves_write_error_when_close_is_interrupted(self):
        original_fdopen = os.fdopen

        for interruption_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(interruption=interruption_type.__name__):
                output_path = self.artifact_dir / (
                    f"write-and-close-{interruption_type.__name__.lower()}.bin"
                )

                class CloseInterruptingOutput:
                    def __init__(self, descriptor, mode):
                        self.stream = original_fdopen(descriptor, mode)

                    @property
                    def closed(self):
                        return self.stream.closed

                    def write(self, content):
                        raise OSError("primary output write failure")

                    def flush(self):
                        return self.stream.flush()

                    def fileno(self):
                        return self.stream.fileno()

                    def close(self):
                        self.stream.close()
                        raise interruption_type("secondary output close interruption")

                with mock.patch.object(
                    manifest_writer.os, "fdopen", side_effect=CloseInterruptingOutput
                ):
                    with self.assertRaisesRegex(
                        OSError, "primary output write failure"
                    ) as raised:
                        manifest_writer._write_new_file(
                            str(self.artifact_dir),
                            output_path.name,
                            b"artifact bytes",
                        )

                self.assertFalse(
                    output_path.exists(),
                    "failed output must be removed after close interruption",
                )
                notes = getattr(raised.exception, "__notes__", [])
                self.assertTrue(
                    any(
                        interruption_type.__name__ in note
                        and "secondary output close interruption" in note
                        for note in notes
                    ),
                    f"expected {interruption_type.__name__} diagnostic on primary error, got {notes!r}",
                )


    def test_write_new_file_retries_close_interrupted_before_underlying_close(self):
        original_fdopen = os.fdopen

        for interruption_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(interruption=interruption_type.__name__):
                output_path = self.artifact_dir / (
                    f"close-before-underlying-{interruption_type.__name__.lower()}.bin"
                )
                descriptors = []
                outputs = []

                class InterruptBeforeCloseOutput:
                    def __init__(self, descriptor, mode):
                        self.stream = original_fdopen(descriptor, mode)
                        self.close_calls = 0
                        descriptors.append(self.stream.fileno())
                        outputs.append(self)

                    @property
                    def closed(self):
                        return self.stream.closed

                    def write(self, content):
                        return self.stream.write(content)

                    def flush(self):
                        return self.stream.flush()

                    def fileno(self):
                        return self.stream.fileno()

                    def close(self):
                        self.close_calls += 1
                        if self.close_calls == 1:
                            raise interruption_type(
                                "injected close interruption before underlying close"
                            )
                        return self.stream.close()

                with mock.patch.object(
                    manifest_writer.os,
                    "fdopen",
                    side_effect=InterruptBeforeCloseOutput,
                ):
                    with self.assertRaises(interruption_type):
                        manifest_writer._write_new_file(
                            str(self.artifact_dir),
                            output_path.name,
                            b"artifact bytes",
                        )

                self.assertFalse(
                    output_path.exists(),
                    "output must be removed after an interrupted close",
                )
                self.assertEqual(
                    outputs[0].close_calls,
                    2,
                    "rollback must retry close when the first interruption occurs before the stream closes",
                )
                self.assertTrue(outputs[0].closed, "rollback must close the output stream")
                descriptor = descriptors[0]
                try:
                    with self.assertRaises(OSError):
                        os.fstat(descriptor)
                finally:
                    if not outputs[0].closed:
                        outputs[0].stream.close()

    def test_write_new_file_retries_interrupted_close_after_primary_write_error(self):
        original_fdopen = os.fdopen
        output_path = self.artifact_dir / "write-error-close-before-underlying.bin"
        descriptors = []
        outputs = []

        class InterruptBeforeCloseOutput:
            def __init__(self, descriptor, mode):
                self.stream = original_fdopen(descriptor, mode)
                self.close_calls = 0
                descriptors.append(self.stream.fileno())
                outputs.append(self)

            @property
            def closed(self):
                return self.stream.closed

            def write(self, content):
                raise OSError("primary output write failure")

            def flush(self):
                return self.stream.flush()

            def fileno(self):
                return self.stream.fileno()

            def close(self):
                self.close_calls += 1
                if self.close_calls == 1:
                    raise KeyboardInterrupt(
                        "secondary close interruption before underlying close"
                    )
                return self.stream.close()

        with mock.patch.object(
            manifest_writer.os,
            "fdopen",
            side_effect=InterruptBeforeCloseOutput,
        ):
            with self.assertRaisesRegex(
                OSError, "primary output write failure"
            ) as raised:
                manifest_writer._write_new_file(
                    str(self.artifact_dir),
                    output_path.name,
                    b"artifact bytes",
                )

        self.assertFalse(
            output_path.exists(),
            "failed output must be removed after the interrupted close",
        )
        notes = getattr(raised.exception, "__notes__", [])
        self.assertTrue(
            any("secondary close interruption before underlying close" in note for note in notes),
            f"expected interrupted close diagnostic on primary error, got {notes!r}",
        )
        self.assertEqual(
            outputs[0].close_calls,
            2,
            "rollback must retry close after the primary write error",
        )
        self.assertTrue(outputs[0].closed, "rollback must close the output stream")
        descriptor = descriptors[0]
        try:
            with self.assertRaises(OSError):
                os.fstat(descriptor)
        finally:
            if not outputs[0].closed:
                outputs[0].stream.close()


    def test_writer_rolls_back_outputs_when_interrupted_after_helper_returns(self):
        original_write = manifest_writer._write_new_file

        for interrupted_filename in (MANIFEST_FILENAME, CHECKSUMS_FILENAME):
            with self.subTest(filename=interrupted_filename):
                with tempfile.TemporaryDirectory(
                    prefix="phx-manifest-pair-return-interruption-"
                ) as temporary:
                    artifact_dir = Path(temporary)
                    (artifact_dir / "firmware.bin").write_bytes(b"synthetic firmware")
                    (artifact_dir / "sketch.ino").write_bytes(b"// synthetic source\\n")
                    kwargs = self.kwargs()
                    kwargs["artifact_dir"] = str(artifact_dir)

                    def interrupt_after_creation(directory, filename, content, *args, **kwargs):
                        output_path = original_write(
                            directory, filename, content, *args, **kwargs
                        )
                        if filename == interrupted_filename:
                            raise KeyboardInterrupt(
                                f"simulated interruption after {filename} creation"
                            )
                        return output_path

                    with mock.patch.object(
                        manifest_writer,
                        "_write_new_file",
                        side_effect=interrupt_after_creation,
                    ):
                        with self.assertRaises(KeyboardInterrupt) as raised:
                            write_artifact_manifest(**kwargs)

                    self.assertIn(interrupted_filename, str(raised.exception))
                    self.assertFalse(
                        (artifact_dir / MANIFEST_FILENAME).exists(),
                        "manifest-pair rollback left a partially published manifest",
                    )
                    self.assertFalse(
                        (artifact_dir / CHECKSUMS_FILENAME).exists(),
                        "manifest-pair rollback left a partially published checksum file",
                    )


    def test_scanner_preserves_primary_error_when_root_descriptor_close_is_interrupted(self):
        original_open = os.open
        original_close = os.close

        for interruption_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(interruption=interruption_type.__name__):
                root_descriptor = None

                def capture_root_descriptor(path, flags, *args, **kwargs):
                    nonlocal root_descriptor
                    descriptor = original_open(path, flags, *args, **kwargs)
                    if (
                        os.fspath(path) == os.path.abspath(str(self.artifact_dir))
                        and flags & os.O_DIRECTORY
                    ):
                        root_descriptor = descriptor
                    return descriptor

                def close_then_interrupt(descriptor):
                    if descriptor == root_descriptor:
                        original_close(descriptor)
                        raise interruption_type("injected descriptor-close interruption")
                    return original_close(descriptor)

                def fail_scan(*args, **kwargs):
                    raise ManifestError("primary artifact scan failure")

                with mock.patch.object(
                    manifest_writer.os, "open", side_effect=capture_root_descriptor
                ), mock.patch.object(
                    manifest_writer.os, "close", side_effect=close_then_interrupt
                ), mock.patch.object(
                    manifest_writer, "_scan_artifact_directory_fd", side_effect=fail_scan
                ):
                    with self.assertRaisesRegex(
                        ManifestError, "primary artifact scan failure"
                    ) as raised:
                        manifest_writer._scan_artifact_files(str(self.artifact_dir))

                self.assertIsNotNone(root_descriptor)
                notes = getattr(raised.exception, "__notes__", [])
                self.assertTrue(
                    any(
                        "artifact root directory" in note
                        and interruption_type.__name__ in note
                        for note in notes
                    ),
                    f"expected close interruption to be attached to primary error, got {notes!r}",
                )

    def test_descriptor_close_interrupt_propagates_without_primary_error(self):
        original_close = os.close

        for interruption_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(interruption=interruption_type.__name__):
                descriptor = os.open(
                    self.artifact_dir,
                    os.O_RDONLY | os.O_DIRECTORY,
                )

                def close_then_interrupt(candidate):
                    if candidate == descriptor:
                        original_close(candidate)
                        raise interruption_type("injected standalone close interruption")
                    return original_close(candidate)

                with mock.patch.object(
                    manifest_writer.os, "close", side_effect=close_then_interrupt
                ):
                    with self.assertRaises(interruption_type):
                        manifest_writer._close_descriptor_preserving_primary(
                            descriptor, "test artifact descriptor"
                        )

    def test_write_new_file_preserves_replacement_path_during_rollback(self):
        output_path = self.artifact_dir / "rollback-replacement.bin"
        displaced_path = self.artifact_dir / "rollback-original.bin"
        directory_descriptor = os.open(
            self.artifact_dir,
            os.O_RDONLY | os.O_DIRECTORY,
        )
        self.addCleanup(os.close, directory_descriptor)
        original_fsync = os.fsync
        replaced = False

        def replace_then_fail_output_sync(descriptor):
            nonlocal replaced
            if stat.S_ISREG(os.fstat(descriptor).st_mode) and not replaced:
                output_path.rename(displaced_path)
                output_path.write_bytes(b"operator-owned replacement")
                replaced = True
                raise OSError("injected output fsync failure")
            return original_fsync(descriptor)

        with mock.patch.object(
            manifest_writer.os, "fsync", side_effect=replace_then_fail_output_sync
        ):
            with self.assertRaisesRegex(
                ManifestError, "rollback could not be confirmed"
            ) as raised:
                manifest_writer._write_new_file(
                    str(self.artifact_dir),
                    output_path.name,
                    b"artifact bytes",
                    directory_descriptor=directory_descriptor,
                )

        self.assertTrue(replaced, "the deterministic replacement race must execute")
        self.assertEqual(output_path.read_bytes(), b"operator-owned replacement")
        self.assertEqual(displaced_path.read_bytes(), b"artifact bytes")
        self.assertIsInstance(raised.exception.__cause__, OSError)
        self.assertIn("injected output fsync failure", str(raised.exception.__cause__))

    def test_manifest_pair_rollback_preserves_replacement_of_first_output(self):
        manifest_path = self.artifact_dir / MANIFEST_FILENAME
        displaced_path = self.artifact_dir / "artifact-manifest.original"
        checksums_path = self.artifact_dir / CHECKSUMS_FILENAME
        original_write = manifest_writer._write_new_file
        replaced = False

        def replace_manifest_then_fail_checksums(directory, filename, content, *args, **kwargs):
            nonlocal replaced
            if filename == CHECKSUMS_FILENAME:
                raise OSError("injected checksum creation failure")
            result = original_write(directory, filename, content, *args, **kwargs)
            if filename == MANIFEST_FILENAME:
                manifest_path.rename(displaced_path)
                manifest_path.write_bytes(b"operator-owned manifest replacement")
                replaced = True
            return result

        with mock.patch.object(
            manifest_writer,
            "_write_new_file",
            side_effect=replace_manifest_then_fail_checksums,
        ):
            with self.assertRaisesRegex(
                ManifestError, "rollback could not be confirmed"
            ) as raised:
                write_artifact_manifest(**self.kwargs())

        self.assertTrue(replaced, "the deterministic manifest replacement must execute")
        self.assertEqual(
            manifest_path.read_bytes(),
            b"operator-owned manifest replacement",
        )
        self.assertTrue(displaced_path.is_file())
        self.assertFalse(checksums_path.exists())
        self.assertIsInstance(raised.exception.__cause__, OSError)
        self.assertIn(
            "injected checksum creation failure",
            str(raised.exception.__cause__),
        )



    def test_writer_rejects_group_or_world_writable_artifact_directory_before_publication(self):
        original_mode = stat.S_IMODE(self.artifact_dir.stat().st_mode)
        os.chmod(self.artifact_dir, original_mode | stat.S_IWGRP | stat.S_IWOTH)
        self.addCleanup(os.chmod, self.artifact_dir, original_mode)

        with self.assertRaisesRegex(ManifestError, "group- or world-writable"):
            write_artifact_manifest(**self.kwargs())

        self.assertFalse((self.artifact_dir / MANIFEST_FILENAME).exists())
        self.assertFalse((self.artifact_dir / CHECKSUMS_FILENAME).exists())

    def test_writer_rejects_artifact_directory_not_owned_by_effective_user(self):
        effective_uid = os.geteuid()
        with mock.patch.object(
            manifest_writer.os, "geteuid", return_value=effective_uid + 1
        ):
            with self.assertRaisesRegex(ManifestError, "current effective user"):
                write_artifact_manifest(**self.kwargs())

        self.assertFalse((self.artifact_dir / MANIFEST_FILENAME).exists())
        self.assertFalse((self.artifact_dir / CHECKSUMS_FILENAME).exists())


    def test_writer_refuses_manifest_when_artifact_changes_during_publication(self):
        manifest_path = self.artifact_dir / MANIFEST_FILENAME
        checksums_path = self.artifact_dir / CHECKSUMS_FILENAME
        original_write = manifest_writer._write_new_file
        changed_payload = b"operator replacement after initial artifact scan"

        def mutate_artifact_before_manifest(directory, filename, content, *args, **kwargs):
            if filename == MANIFEST_FILENAME:
                (self.artifact_dir / "firmware.bin").write_bytes(changed_payload)
            return original_write(directory, filename, content, *args, **kwargs)

        with mock.patch.object(
            manifest_writer,
            "_write_new_file",
            side_effect=mutate_artifact_before_manifest,
        ):
            with self.assertRaisesRegex(
                ManifestError,
                "artifact files changed while manifest was being published",
            ):
                write_artifact_manifest(**self.kwargs())

        self.assertEqual(
            (self.artifact_dir / "firmware.bin").read_bytes(),
            changed_payload,
            "rollback must preserve the artifact changed by the concurrent writer",
        )
        self.assertFalse(manifest_path.exists())
        self.assertFalse(checksums_path.exists())


    def _assert_writer_rejects_published_output_mutation(self, filename):
        target = self.artifact_dir / filename
        original_scan = manifest_writer._scan_artifact_files
        scan_calls = 0

        def mutate_after_final_scan(
            artifact_dir,
            directory_descriptor=None,
            *,
            excluded_root_outputs=None,
        ):
            nonlocal scan_calls
            records = original_scan(
                artifact_dir,
                directory_descriptor=directory_descriptor,
                excluded_root_outputs=excluded_root_outputs,
            )
            scan_calls += 1
            if scan_calls == 2:
                target.write_bytes(b"operator changed published output")
            return records

        with mock.patch.object(
            manifest_writer,
            "_scan_artifact_files",
            side_effect=mutate_after_final_scan,
        ):
            with self.assertRaisesRegex(
                ManifestError,
                f"published manifest output changed during publication: {filename}",
            ):
                write_artifact_manifest(**self.kwargs())

        self.assertEqual(scan_calls, 2, "the mutation must occur after publication revalidation")
        self.assertFalse((self.artifact_dir / MANIFEST_FILENAME).exists())
        self.assertFalse((self.artifact_dir / CHECKSUMS_FILENAME).exists())

    def test_writer_rejects_manifest_content_mutated_during_publication(self):
        self._assert_writer_rejects_published_output_mutation(MANIFEST_FILENAME)

    def test_writer_rejects_checksums_content_mutated_during_publication(self):
        self._assert_writer_rejects_published_output_mutation(CHECKSUMS_FILENAME)


    def test_writer_rejects_published_output_mutated_during_final_directory_fsync(self):
        target = self.artifact_dir / CHECKSUMS_FILENAME
        original_fsync = manifest_writer.os.fsync
        directory_syncs = 0
        mutated = False

        def mutate_during_directory_sync(descriptor):
            nonlocal directory_syncs, mutated
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_syncs += 1
                if not mutated:
                    target.write_bytes(b"operator changed checksums during directory fsync")
                    mutated = True
            return original_fsync(descriptor)

        with mock.patch.object(
            manifest_writer.os,
            "fsync",
            side_effect=mutate_during_directory_sync,
        ):
            with self.assertRaisesRegex(
                ManifestError,
                f"published manifest output changed during publication: {CHECKSUMS_FILENAME}",
            ):
                write_artifact_manifest(**self.kwargs())

        self.assertTrue(mutated, "the final directory fsync must exercise the mutation window")
        self.assertGreaterEqual(directory_syncs, 2, "failed publication must sync the rollback")
        self.assertFalse((self.artifact_dir / MANIFEST_FILENAME).exists())
        self.assertFalse((self.artifact_dir / CHECKSUMS_FILENAME).exists())


    def test_rejects_group_or_world_writable_nested_directory(self):
        nested = self.artifact_dir / "nested"
        nested.mkdir()
        (nested / "nested-firmware.bin").write_bytes(b"nested firmware payload")
        os.chmod(nested, 0o777)

        with self.assertRaisesRegex(ManifestError, "group- or world-writable"):
            write_artifact_manifest(**self.kwargs())

        self.assertFalse((self.artifact_dir / MANIFEST_FILENAME).exists())
        self.assertFalse((self.artifact_dir / CHECKSUMS_FILENAME).exists())

    def test_rejects_group_or_world_writable_payload_file(self):
        payload = self.artifact_dir / "firmware.bin"
        os.chmod(payload, 0o666)

        with self.assertRaisesRegex(ManifestError, "group- or world-writable"):
            write_artifact_manifest(**self.kwargs())

        self.assertFalse((self.artifact_dir / MANIFEST_FILENAME).exists())
        self.assertFalse((self.artifact_dir / CHECKSUMS_FILENAME).exists())


    def test_verify_published_output_opens_nonblocking_before_rejecting_fifo(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fifo_path = Path(temporary_directory) / MANIFEST_FILENAME
            os.mkfifo(fifo_path)
            fifo_stat = os.lstat(fifo_path)
            directory_descriptor = os.open(
                temporary_directory,
                os.O_RDONLY | os.O_DIRECTORY,
            )
            self.addCleanup(os.close, directory_descriptor)

            original_open = manifest_writer.os.open
            opened_descriptors = []

            def require_nonblocking(path, flags, *args, **kwargs):
                if path == MANIFEST_FILENAME:
                    self.assertTrue(
                        flags & os.O_NONBLOCK,
                        "published-output verification must not block on a FIFO replacement",
                    )
                descriptor = original_open(path, flags, *args, **kwargs)
                if path == MANIFEST_FILENAME:
                    opened_descriptors.append(descriptor)
                return descriptor

            with mock.patch.object(
                manifest_writer.os, "open", side_effect=require_nonblocking
            ):
                with self.assertRaisesRegex(
                    ManifestError,
                    "published manifest output changed during publication",
                ):
                    manifest_writer._verify_published_output(
                        directory_descriptor=directory_descriptor,
                        filename=MANIFEST_FILENAME,
                        expected_identity=(fifo_stat.st_dev, fifo_stat.st_ino),
                        expected_content=b"",
                    )

            self.assertEqual(len(opened_descriptors), 1)
            with self.assertRaises(OSError):
                os.fstat(opened_descriptors[0])


if __name__ == "__main__":
    unittest.main()
