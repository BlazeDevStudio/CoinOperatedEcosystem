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


def _require_descriptor_scan_support() -> None:
    """Require the POSIX descriptor-relative operations used by the safe scanner."""
    if (
        os.name != "posix"
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
    ):
        raise ManifestError(
            "safe artifact traversal requires POSIX descriptor-relative directory operations"
        )


def _close_descriptor_preserving_primary(descriptor: int, label: str) -> None:
    """Close a descriptor without masking an active artifact-integrity failure."""
    primary_error = sys.exc_info()[1]
    try:
        os.close(descriptor)
    except BaseException as close_error:
        detail = (
            f"could not close {label}: "
            f"{type(close_error).__name__}: {close_error}"
        )
        if primary_error is not None:
            try:
                if hasattr(primary_error, "add_note"):
                    primary_error.add_note(detail)
                else:
                    print(detail, file=sys.stderr)
            except BaseException:
                # Cleanup diagnostics must never replace the active primary error.
                pass
            return
        if isinstance(close_error, OSError):
            raise ManifestError(detail) from close_error
        # With no primary error, preserve process-level interruptions rather
        # than swallowing KeyboardInterrupt or SystemExit.
        raise


def _directory_scan_snapshot(info: os.stat_result) -> tuple[int, ...]:
    """Capture directory metadata that changes when its entry set is modified."""
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _scan_artifact_directory_fd(
    directory_descriptor: int,
    relative_prefix: str,
    records: list[dict],
) -> None:
    """Hash one directory using pinned descriptors, never path-based parent traversal."""
    try:
        directory_before = os.fstat(directory_descriptor)
        if not stat.S_ISDIR(directory_before.st_mode):
            raise ManifestError("artifact descriptor is not a directory")
        names = os.listdir(directory_descriptor)
    except (OSError, TypeError, NotImplementedError) as exc:
        raise ManifestError(f"could not enumerate artifact directory: {exc}") from exc

    names.sort()
    for name in names:
        if not name or name in (".", "..") or "/" in name:
            raise ManifestError("artifact directory returned an unsafe entry name")

        relative = f"{relative_prefix}/{name}" if relative_prefix else name
        parts = relative.split("/")
        if (
            relative.startswith("/")
            or any(part in ("", ".", "..") for part in parts)
            or not re.fullmatch(r"[A-Za-z0-9._/-]+", relative)
        ):
            raise ManifestError(
                f"artifact path cannot be represented safely in SHA256SUMS: {relative!r}"
            )
        if name in (MANIFEST_FILENAME, CHECKSUMS_FILENAME):
            raise ManifestError(f"refusing pre-existing manifest output: {name}")

        try:
            before = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
        except OSError as exc:
            raise ManifestError(
                f"artifact entry changed during scan: {relative}: {exc}"
            ) from exc

        if stat.S_ISLNK(before.st_mode):
            raise ManifestError(
                "refusing symlink or non-regular artifact file; "
                f"refusing symlink or non-directory artifact path: {relative}"
            )

        if stat.S_ISDIR(before.st_mode):
            try:
                child_descriptor = os.open(
                    name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_descriptor,
                )
            except (OSError, TypeError, NotImplementedError) as exc:
                raise ManifestError(
                    f"artifact directory changed during scan: {relative}: {exc}"
                ) from exc

            try:
                opened = os.fstat(child_descriptor)
                if (
                    not stat.S_ISDIR(opened.st_mode)
                    or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
                ):
                    raise ManifestError(
                        f"artifact directory changed while opening: {relative}"
                    )

                _scan_artifact_directory_fd(child_descriptor, relative, records)

                try:
                    current = os.stat(
                        name,
                        dir_fd=directory_descriptor,
                        follow_symlinks=False,
                    )
                except (OSError, TypeError, NotImplementedError) as exc:
                    raise ManifestError(
                        f"artifact directory changed during scan: {relative}: {exc}"
                    ) from exc
                if (
                    not stat.S_ISDIR(current.st_mode)
                    or _directory_scan_snapshot(opened) != _directory_scan_snapshot(current)
                ):
                    raise ManifestError(
                        f"artifact directory changed during scan: {relative}"
                    )
            finally:
                _close_descriptor_preserving_primary(
                    child_descriptor, f"artifact child directory {relative}"
                )
            continue

        if not stat.S_ISREG(before.st_mode):
            raise ManifestError(
                f"refusing symlink or non-regular artifact file: {relative}"
            )
        if before.st_nlink != 1:
            raise ManifestError(f"refusing hard-linked artifact file: {relative}")

        descriptor = -1
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW,
                dir_fd=directory_descriptor,
            )
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

            # The pathname and inode can remain stable while another process
            # rewrites bytes in place. Compare a second descriptor snapshot
            # after the final read so a mixed/stale digest is never admitted.
            finished = os.fstat(descriptor)
            if (
                not stat.S_ISREG(finished.st_mode)
                or (after.st_dev, after.st_ino) != (finished.st_dev, finished.st_ino)
                or after.st_mode != finished.st_mode
                or after.st_nlink != finished.st_nlink
                or after.st_size != finished.st_size
                or after.st_mtime_ns != finished.st_mtime_ns
                or after.st_ctime_ns != finished.st_ctime_ns
            ):
                raise ManifestError(f"artifact file changed while hashing: {relative}")

            try:
                current = os.stat(
                    name,
                    dir_fd=directory_descriptor,
                    follow_symlinks=False,
                )
            except (OSError, TypeError, NotImplementedError) as exc:
                raise ManifestError(
                    f"artifact file changed while hashing: {relative}: {exc}"
                ) from exc
            if (
                not stat.S_ISREG(current.st_mode)
                or (finished.st_dev, finished.st_ino) != (current.st_dev, current.st_ino)
                or finished.st_mode != current.st_mode
                or finished.st_nlink != current.st_nlink
                or finished.st_size != current.st_size
                or finished.st_mtime_ns != current.st_mtime_ns
                or finished.st_ctime_ns != current.st_ctime_ns
            ):
                raise ManifestError(f"artifact file changed while hashing: {relative}")
        except (OSError, TypeError, NotImplementedError) as exc:
            raise ManifestError(f"could not safely hash artifact {relative}: {exc}") from exc
        finally:
            if descriptor >= 0:
                _close_descriptor_preserving_primary(
                    descriptor, f"artifact file {relative}"
                )

        records.append(
            {
                "path": relative,
                "size": total,
                "sha256": digest.hexdigest(),
            }
        )

    try:
        directory_after = os.fstat(directory_descriptor)
    except (OSError, TypeError, NotImplementedError) as exc:
        raise ManifestError(f"could not verify artifact directory after scan: {exc}") from exc
    if _directory_scan_snapshot(directory_before) != _directory_scan_snapshot(directory_after):
        raise ManifestError(
            "artifact directory changed while scanning: "
            f"{relative_prefix or '.'}"
        )


def _scan_artifact_files(
    artifact_dir: str,
    directory_descriptor: int | None = None,
) -> list[dict]:
    """Hash the artifact tree through pinned directory descriptors."""
    root = os.path.abspath(os.fspath(artifact_dir))
    _require_descriptor_scan_support()

    owns_descriptor = directory_descriptor is None
    if owns_descriptor:
        try:
            directory_descriptor = os.open(
                root,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
        except OSError as exc:
            raise ManifestError(f"artifact directory is unavailable: {exc}") from exc

    try:
        _require_artifact_directory_identity(root, directory_descriptor)
        records: list[dict] = []
        _scan_artifact_directory_fd(directory_descriptor, "", records)
        _require_artifact_directory_identity(root, directory_descriptor)
    finally:
        if owns_descriptor:
            _close_descriptor_preserving_primary(
                directory_descriptor, "artifact root directory"
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
    artifact_directory_descriptor: int | None = None,
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
    records = _scan_artifact_files(artifact_dir, directory_descriptor=artifact_directory_descriptor)
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


def _require_artifact_directory_identity(
    artifact_dir: str,
    directory_descriptor: int,
) -> None:
    """Ensure the scanned path still names the directory pinned for publication."""
    try:
        path_stat = os.lstat(artifact_dir)
        descriptor_stat = os.fstat(directory_descriptor)
    except OSError as exc:
        raise ManifestError(
            f"artifact directory changed during manifest scan/publication: {exc}"
        ) from exc

    if (
        not stat.S_ISDIR(path_stat.st_mode)
        or not stat.S_ISDIR(descriptor_stat.st_mode)
        or (path_stat.st_dev, path_stat.st_ino)
        != (descriptor_stat.st_dev, descriptor_stat.st_ino)
        or os.path.realpath(artifact_dir) != artifact_dir
    ):
        raise ManifestError(
            "artifact directory changed during manifest scan/publication"
        )

    effective_uid = os.geteuid()
    if path_stat.st_uid != effective_uid or descriptor_stat.st_uid != effective_uid:
        raise ManifestError(
            "artifact directory must be owned by the current effective user"
        )
    if stat.S_IMODE(path_stat.st_mode) != stat.S_IMODE(descriptor_stat.st_mode):
        raise ManifestError(
            "artifact directory permissions changed during manifest scan/publication"
        )
    if (path_stat.st_mode | descriptor_stat.st_mode) & 0o022:
        raise ManifestError(
            "artifact directory must not be group- or world-writable"
        )



def _unlink_created_output_if_unchanged(
    *,
    path: str,
    filename: str,
    directory_descriptor: int | None,
    expected_identity: tuple[int, int] | None,
) -> None:
    """Remove only the regular file still named by this invocation's created inode."""
    if expected_identity is None:
        raise ManifestError(
            f"refusing to remove output without a verified creation identity: {filename}"
        )

    try:
        if directory_descriptor is None:
            current = os.stat(path, follow_symlinks=False)
        else:
            current = os.stat(
                filename,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
    except FileNotFoundError:
        return

    if (
        not stat.S_ISREG(current.st_mode)
        or (current.st_dev, current.st_ino) != expected_identity
    ):
        raise ManifestError(
            f"refusing to remove output replaced after creation: {filename}"
        )

    try:
        if directory_descriptor is None:
            os.unlink(path)
        else:
            os.unlink(filename, dir_fd=directory_descriptor)
    except FileNotFoundError:
        # Another actor already removed the exact entry after the identity check.
        return


def _write_new_file(
    directory: str,
    filename: str,
    content: bytes,
    *,
    directory_descriptor: int | None = None,
    created_paths: list[tuple[str, tuple[int, int]]] | None = None,
) -> str:
    """Create and sync one new output, durably removing it if writing fails or is interrupted."""
    path = os.path.join(directory, filename)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    descriptor = -1
    output = None
    created_identity: tuple[int, int] | None = None

    def add_cleanup_note(
        primary_error: BaseException,
        close_error: BaseException,
    ) -> None:
        detail = (
            "output close also failed: "
            f"{type(close_error).__name__}: {close_error}"
        )
        try:
            if hasattr(primary_error, "add_note"):
                primary_error.add_note(detail)
            else:
                sys.stderr.write(detail + "\n")
        except BaseException:
            # Diagnostics must never replace the original write/flush failure.
            pass

    def rollback(primary_error: BaseException) -> None:
        rollback_errors: list[str] = []
        if output is not None and not output.closed:
            try:
                # A Python-level interruption can occur before the underlying
                # file object has closed its descriptor. Retry while the stream
                # still reports itself open; if close already completed before
                # raising, do not issue a second close against a possibly reused fd.
                output.close()
            except BaseException as exc:
                rollback_errors.append(
                    f"close partial output stream: {type(exc).__name__}: {exc}"
                )
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except BaseException as exc:
                rollback_errors.append(
                    f"close partial output: {type(exc).__name__}: {exc}"
                )
        try:
            _unlink_created_output_if_unchanged(
                path=path,
                filename=filename,
                directory_descriptor=directory_descriptor,
                expected_identity=created_identity,
            )
        except BaseException as exc:
            rollback_errors.append(
                f"remove partial output: {type(exc).__name__}: {exc}"
            )
        if directory_descriptor is not None:
            try:
                os.fsync(directory_descriptor)
            except BaseException as exc:
                rollback_errors.append(
                    f"sync partial-output rollback: {type(exc).__name__}: {exc}"
                )
        if rollback_errors:
            details = "; ".join(rollback_errors)
            raise ManifestError(
                f"partial artifact output rollback could not be confirmed for {filename}: {details}"
            ) from primary_error

    # Register ownership inside this helper, before returning to the pair
    # publisher. If the caller is interrupted after this helper completes but
    # before its next bookkeeping bytecode, the outer rollback still knows
    # which output name this invocation created.
    try:
        if directory_descriptor is None:
            descriptor = os.open(path, flags, 0o644)
        else:
            descriptor = os.open(
                filename,
                flags,
                0o644,
                dir_fd=directory_descriptor,
            )
        created_stat = os.fstat(descriptor)
        if not stat.S_ISREG(created_stat.st_mode):
            raise ManifestError("new artifact output descriptor is not a regular file")
        created_identity = (created_stat.st_dev, created_stat.st_ino)
        if created_paths is not None:
            created_paths.append((path, created_identity))
    except BaseException as creation_error:
        if descriptor >= 0:
            rollback(creation_error)
        raise

    try:
        output = os.fdopen(descriptor, "wb")
    except BaseException as open_error:
        rollback(open_error)
        raise
    descriptor = -1

    try:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    except BaseException as write_error:
        try:
            output.close()
        except BaseException as close_error:
            # A close-time interruption is secondary to the write/flush/fsync
            # failure already being handled. Record it, roll back the partial
            # output, and preserve the original publication failure.
            add_cleanup_note(write_error, close_error)

        rollback(write_error)
        raise

    try:
        output.close()
    except BaseException as close_error:
        rollback(close_error)
        raise

    return path


def write_artifact_manifest(**kwargs) -> tuple[str, str]:
    """Publish the manifest pair, rolling back on failures and Python-level interruptions."""
    artifact_dir = os.path.abspath(os.fspath(kwargs["artifact_dir"]))
    _require_descriptor_scan_support()
    try:
        directory_descriptor = os.open(
            artifact_dir,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
    except (OSError, TypeError, NotImplementedError) as exc:
        raise ManifestError(f"artifact directory cannot be opened for durable publication: {exc}") from exc

    try:
        # Establish exclusive directory ownership before scanning untrusted
        # artifact entries or publishing files. Recheck after the scan and
        # after publication to detect permission/identity changes.
        _require_artifact_directory_identity(artifact_dir, directory_descriptor)
        payload_kwargs = dict(kwargs)
        payload_kwargs["artifact_directory_descriptor"] = directory_descriptor
        manifest_bytes, checksums_bytes = build_artifact_manifest_payloads(**payload_kwargs)
        _require_artifact_directory_identity(artifact_dir, directory_descriptor)

        created: list[tuple[str, tuple[int, int]]] = []
        try:
            _write_new_file(
                artifact_dir,
                MANIFEST_FILENAME,
                manifest_bytes,
                directory_descriptor=directory_descriptor,
                created_paths=created,
            )
            _write_new_file(
                artifact_dir,
                CHECKSUMS_FILENAME,
                checksums_bytes,
                directory_descriptor=directory_descriptor,
                created_paths=created,
            )
            os.fsync(directory_descriptor)
            _require_artifact_directory_identity(artifact_dir, directory_descriptor)
        except BaseException as publication_error:
            rollback_errors: list[str] = []
            for path, created_identity in reversed(created):
                filename = os.path.basename(path)
                try:
                    _unlink_created_output_if_unchanged(
                        path=path,
                        filename=filename,
                        directory_descriptor=directory_descriptor,
                        expected_identity=created_identity,
                    )
                except BaseException as exc:
                    rollback_errors.append(
                        f"remove {filename}: {type(exc).__name__}: {exc}"
                    )
            if created:
                try:
                    os.fsync(directory_descriptor)
                except BaseException as exc:
                    rollback_errors.append(
                        f"sync artifact-pair rollback: {type(exc).__name__}: {exc}"
                    )
            if rollback_errors:
                details = "; ".join(rollback_errors)
                raise ManifestError(
                    f"artifact publication failed; rollback could not be confirmed: {details}"
                ) from publication_error
            raise
    finally:
        _close_descriptor_preserving_primary(
            directory_descriptor, "artifact publication directory"
        )

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
