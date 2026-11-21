#!/usr/bin/env python3
"""Create deterministic provenance and SHA-256 files for one firmware CI artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys

SCHEMA = "phoenix/firmware-artifact/v1"
MANIFEST_FILENAME = "artifact-manifest.json"
CHECKSUMS_FILENAME = "SHA256SUMS"
_GIT_SHA = re.compile(r"[0-9a-f]{40}")
_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
_SAFE_TOKEN = re.compile(r"[A-Za-z0-9._-]+")
_SAFE_FQBN = re.compile(r"[A-Za-z0-9:._-]+")
_SAFE_CORE_ID = re.compile(r"[a-z0-9_.-]+:[a-z0-9_.-]+")


class ManifestError(ValueError):
    """Raised when an artifact directory cannot be admitted for provenance."""


def _require_match(value: str, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ManifestError(f"{label} has an invalid format")
    return value


def _validate_metadata(
    *,
    repository: str,
    source_sha: str,
    event_sha: str,
    pr_head_sha: str,
    pr_base_sha: str,
    product: str,
    board: str,
    fqbn: str,
    arduino_cli_version: str,
    core_id: str,
    core_version: str,
) -> dict:
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ManifestError("repository must use owner/name form")
    _require_match(source_sha, _GIT_SHA, "checked-out source SHA (expected a 40-character Git SHA)")
    _require_match(event_sha, _GIT_SHA, "GitHub event SHA (expected a 40-character Git SHA)")
    if source_sha != event_sha:
        raise ManifestError("GitHub event SHA does not match the checked-out source SHA")

    if bool(pr_head_sha) != bool(pr_base_sha):
        raise ManifestError("pull-request head and base SHAs must both be set or both be empty")
    if pr_head_sha:
        _require_match(pr_head_sha, _GIT_SHA, "pull-request head SHA")
        _require_match(pr_base_sha, _GIT_SHA, "pull-request base SHA")

    _require_match(product, _SAFE_TOKEN, "product")
    if board not in ("esp8266", "esp32"):
        raise ManifestError("board must be esp8266 or esp32")
    _require_match(fqbn, _SAFE_FQBN, "FQBN")
    _require_match(arduino_cli_version, _VERSION, "Arduino CLI version")
    _require_match(core_id, _SAFE_CORE_ID, "board core ID")
    _require_match(core_version, _VERSION, "board core version")

    return {
        "schema": SCHEMA,
        "source": {
            "repository": repository,
            "checked_out_sha": source_sha,
            "event_sha": event_sha,
            "pull_request_head_sha": pr_head_sha or None,
            "pull_request_base_sha": pr_base_sha or None,
        },
        "target": {
            "product": product,
            "board": board,
            "fqbn": fqbn,
        },
        "toolchain": {
            "arduino_cli_version": arduino_cli_version,
            "core_id": core_id,
            "core_version": core_version,
        },
    }


def _raise_walk_error(error: OSError) -> None:
    """Do not publish a partial manifest when directory enumeration is incomplete."""
    raise ManifestError(f"could not enumerate artifact directory: {error}") from error


def _scan_artifact_files(artifact_dir: str) -> list[dict]:
    root = os.path.abspath(os.fspath(artifact_dir))
    try:
        root_stat = os.lstat(root)
    except OSError as exc:
        raise ManifestError(f"artifact directory is unavailable: {exc}") from exc
    if not stat.S_ISDIR(root_stat.st_mode) or os.path.realpath(root) != root:
        raise ManifestError("artifact root must be a real directory, not a symlink")

    if not hasattr(os, "O_NOFOLLOW"):
        raise ManifestError("safe artifact hashing requires O_NOFOLLOW support")

    records: list[dict] = []
    for current, directories, filenames in os.walk(
        root,
        topdown=True,
        onerror=_raise_walk_error,
        followlinks=False,
    ):
        directories.sort()
        filenames.sort()

        for directory in directories:
            directory_path = os.path.join(current, directory)
            try:
                directory_stat = os.lstat(directory_path)
            except OSError as exc:
                raise ManifestError(f"artifact directory changed during scan: {directory_path}: {exc}") from exc
            if not stat.S_ISDIR(directory_stat.st_mode):
                raise ManifestError(f"refusing symlink or non-directory artifact path: {directory_path}")

        for filename in filenames:
            if filename in (MANIFEST_FILENAME, CHECKSUMS_FILENAME):
                raise ManifestError(f"refusing pre-existing manifest output: {filename}")
            path = os.path.join(current, filename)
            try:
                before = os.lstat(path)
            except OSError as exc:
                raise ManifestError(f"artifact file changed during scan: {path}: {exc}") from exc
            if not stat.S_ISREG(before.st_mode):
                raise ManifestError(f"refusing symlink or non-regular artifact file: {path}")
            if before.st_nlink != 1:
                raise ManifestError(f"refusing hard-linked artifact file: {path}")

            relative = os.path.relpath(path, root).replace(os.sep, "/")
            parts = relative.split("/")
            if (
                relative.startswith("/")
                or any(part in ("", ".", "..") for part in parts)
                or not re.fullmatch(r"[A-Za-z0-9._/-]+", relative)
            ):
                raise ManifestError(f"artifact path cannot be represented safely in SHA256SUMS: {relative!r}")

            descriptor = -1
            try:
                descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                after = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(after.st_mode)
                    or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                    or after.st_nlink != 1
                ):
                    raise ManifestError(f"artifact identity changed while opening: {relative}")

                digest = hashlib.sha256()
                total = 0
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    total += len(chunk)
                if total != after.st_size:
                    raise ManifestError(f"artifact size changed while hashing: {relative}")
            except OSError as exc:
                raise ManifestError(f"could not safely hash artifact {relative}: {exc}") from exc
            finally:
                if descriptor >= 0:
                    os.close(descriptor)

            records.append(
                {
                    "path": relative,
                    "size": total,
                    "sha256": digest.hexdigest(),
                }
            )

    records.sort(key=lambda item: item["path"])
    if not records:
        raise ManifestError("artifact directory contains no regular files")
    if not any(item["path"].lower().endswith(".bin") and item["size"] > 0 for item in records):
        raise ManifestError("artifact directory must contain at least one non-empty .bin firmware payload")
    return records


def build_artifact_manifest_payloads(
    *,
    artifact_dir: str,
    repository: str,
    source_sha: str,
    event_sha: str,
    pr_head_sha: str = "",
    pr_base_sha: str = "",
    product: str,
    board: str,
    fqbn: str,
    arduino_cli_version: str,
    core_id: str,
    core_version: str,
) -> tuple[bytes, bytes]:
    """Return deterministic manifest and checksums bytes without writing files."""
    metadata = _validate_metadata(
        repository=repository,
        source_sha=source_sha,
        event_sha=event_sha,
        pr_head_sha=pr_head_sha,
        pr_base_sha=pr_base_sha,
        product=product,
        board=board,
        fqbn=fqbn,
        arduino_cli_version=arduino_cli_version,
        core_id=core_id,
        core_version=core_version,
    )
    records = _scan_artifact_files(artifact_dir)
    manifest = {**metadata, "files": records}
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")

    checksum_records = [
        (item["path"], item["sha256"])
        for item in records
    ]
    checksum_records.append((MANIFEST_FILENAME, hashlib.sha256(manifest_bytes).hexdigest()))
    checksum_records.sort(key=lambda item: item[0])
    checksums_bytes = (
        "".join(f"{digest}  {path}\n" for path, digest in checksum_records)
    ).encode("ascii")
    return manifest_bytes, checksums_bytes


def _write_new_file(directory: str, filename: str, content: bytes) -> str:
    path = os.path.join(directory, filename)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return path


def write_artifact_manifest(**kwargs) -> tuple[str, str]:
    """Publish manifest and SHA256SUMS without overwriting existing files."""
    artifact_dir = os.path.abspath(os.fspath(kwargs["artifact_dir"]))
    manifest_bytes, checksums_bytes = build_artifact_manifest_payloads(**kwargs)
    created: list[str] = []
    directory_descriptor = -1
    try:
        created.append(_write_new_file(artifact_dir, MANIFEST_FILENAME, manifest_bytes))
        created.append(_write_new_file(artifact_dir, CHECKSUMS_FILENAME, checksums_bytes))
        if not hasattr(os, "O_DIRECTORY"):
            raise ManifestError("durable artifact publication requires O_DIRECTORY support")
        directory_descriptor = os.open(artifact_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        os.fsync(directory_descriptor)
    except Exception:
        for path in reversed(created):
            try:
                os.unlink(path)
            except OSError:
                pass
        raise
    finally:
        if directory_descriptor >= 0:
            os.close(directory_descriptor)

    return (
        os.path.join(artifact_dir, MANIFEST_FILENAME),
        os.path.join(artifact_dir, CHECKSUMS_FILENAME),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--event-sha", required=True)
    parser.add_argument("--pr-head-sha", default="")
    parser.add_argument("--pr-base-sha", default="")
    parser.add_argument("--product", required=True)
    parser.add_argument("--board", choices=("esp8266", "esp32"), required=True)
    parser.add_argument("--fqbn", required=True)
    parser.add_argument("--arduino-cli-version", required=True)
    parser.add_argument("--core-id", required=True)
    parser.add_argument("--core-version", required=True)
    args = parser.parse_args(argv)

    try:
        manifest_path, checksums_path = write_artifact_manifest(**vars(args))
    except (ManifestError, OSError, ValueError) as exc:
        print(f"RELEASE-BLOCKED: firmware artifact manifest creation failed: {exc}", file=sys.stderr)
        return 2

    print(f"FIRMWARE-ARTIFACT-MANIFEST-PASS: {manifest_path}")
    print(f"FIRMWARE-SHA256SUMS-PASS: {checksums_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
