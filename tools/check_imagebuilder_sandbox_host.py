#!/usr/bin/env python3
"""Fail-fast capability probe for the release-owned ImageBuilder sandbox host."""
import os
import shutil
import subprocess
import sys

import imagebuilder_bwrap_trust
from run_imagebuilder_sandbox import _terminate_process_groups
from imagebuilder_bwrap_trust import PRIVATE_HOST_PATHS, private_host_mount_args as _private_host_mount_args

PROBE_TIMEOUT_SECONDS = 10
PROBE_SCRIPT = (
    'test "$(id -u)" = "0" && '
    'test "$(id -g)" = "0" && '
    'printf "ready\\\\n" > /tmp/.phx-userns-preflight && '
    'test -s /tmp/.phx-userns-preflight && '
    'rm -f /tmp/.phx-userns-preflight'
)
TRUSTED_BWRAP_PATH = "/usr/bin:/bin"
SANDBOX_PATH = "/usr/sbin:/usr/bin:/sbin:/bin"
def _is_trusted_system_directory(path: str) -> bool:
    return imagebuilder_bwrap_trust.is_trusted_system_directory(path)


def _find_trusted_bwrap() -> str | None:
    candidate = shutil.which("bwrap", path=TRUSTED_BWRAP_PATH)
    if not candidate:
        return None
    resolved = os.path.abspath(candidate)
    if not imagebuilder_bwrap_trust.is_trusted_executable(resolved):
        return None
    return resolved


def build_probe_command(bwrap_path: str) -> list[str]:
    """Mirror the runner's unprivileged namespace and minimal mount setup."""
    return [
        bwrap_path,
        "--unshare-all",
        "--share-net",
        "--unshare-user",
        "--die-with-parent",
        "--new-session",
        "--ro-bind", "/", "/",
        *_private_host_mount_args(),
        "--dev", "/dev",
        "--proc", "/proc",
        "--tmpfs", "/tmp",
        "--chdir", "/tmp",
        "--clearenv",
        "--setenv", "PATH", SANDBOX_PATH,
        "--setenv", "HOME", "/tmp",
        "--setenv", "TMPDIR", "/tmp",
        "--setenv", "LC_ALL", "C",
        "--uid", "0",
        "--gid", "0",
        "--",
        "sh", "-eu", "-c", PROBE_SCRIPT,
    ]


def _as_text(value) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value or ""


def check_host(bwrap_path: str | None = None, timeout_seconds: float = PROBE_TIMEOUT_SECONDS) -> tuple[bool, str]:
    """Return readiness and an actionable reason without any privileged fallback."""
    executable = bwrap_path if bwrap_path is not None else _find_trusted_bwrap()
    if not executable:
        return False, "bubblewrap executable not found"
    if timeout_seconds <= 0:
        return False, "bubblewrap preflight timeout must be positive"

    process = None
    try:
        process = subprocess.Popen(
            build_probe_command(executable),
            cwd="/",
            env={"PATH": SANDBOX_PATH, "LANG": "C"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            cleanup_stdout, cleanup_stderr = _terminate_process_groups(
                process, grace_seconds=0.25
            )
            detail = "\\n".join(
                part
                for part in (
                    _as_text(cleanup_stdout),
                    _as_text(cleanup_stderr),
                    _as_text(exc.stdout),
                    _as_text(exc.stderr),
                )
                if part
            ).strip()
            message = f"bubblewrap namespace probe timed out after {timeout_seconds:g} seconds"
            return False, f"{message}: {detail}" if detail else message

        cleanup_stdout, cleanup_stderr = _terminate_process_groups(
            process, grace_seconds=0.25
        )
        stdout = stdout or cleanup_stdout
        stderr = stderr or cleanup_stderr
        cleanup_error_markers = (
            "RELEASE-BLOCKED: sandbox process group(s) did not exit after SIGKILL:",
            "RELEASE-BLOCKED: could not signal sandbox process group",
            "could not kill bubblewrap process:",
            "bubblewrap process did not exit after SIGKILL",
        )
        if any(marker in cleanup_stderr for marker in cleanup_error_markers):
            detail = cleanup_stderr.strip()
            return False, f"bubblewrap namespace probe cleanup failed: {detail}"

        if process.returncode != 0:
            detail = (stderr or stdout).strip()
            message = f"bubblewrap namespace probe exited with status {process.returncode}"
            return False, f"{message}: {detail}" if detail else message

        return True, "unprivileged user namespace, masked host-data paths and tmpfs write probe passed"
    except OSError as exc:
        cleanup_detail = ""
        if process is not None:
            try:
                cleanup_stdout, cleanup_stderr = _terminate_process_groups(
                    process, grace_seconds=0.25
                )
                cleanup_detail = "\n".join(
                    part
                    for part in (_as_text(cleanup_stdout), _as_text(cleanup_stderr))
                    if part
                ).strip()
            except Exception as cleanup_error:
                cleanup_detail = (
                    "process-group cleanup raised "
                    f"{type(cleanup_error).__name__}: {cleanup_error}"
                )
            except BaseException as cleanup_interruption:
                retry_detail = "process-group cleanup retry completed"
                try:
                    retry_stdout, retry_stderr = _terminate_process_groups(
                        process, grace_seconds=0.25
                    )
                    retry_output = "\n".join(
                        part
                        for part in (_as_text(retry_stdout), _as_text(retry_stderr))
                        if part
                    ).strip()
                    if retry_output:
                        retry_detail = f"{retry_detail}: {retry_output}"
                except Exception as retry_error:
                    retry_detail = (
                        "process-group cleanup retry raised "
                        f"{type(retry_error).__name__}: {retry_error}"
                    )
                except BaseException as retry_interruption:
                    retry_detail = (
                        "process-group cleanup retry was interrupted by "
                        f"{type(retry_interruption).__name__}: {retry_interruption}"
                    )

                note = (
                    f"Original preflight OSError: {exc}; "
                    "first process-group cleanup was interrupted by "
                    f"{type(cleanup_interruption).__name__}: {cleanup_interruption}; "
                    f"{retry_detail}"
                )
                if hasattr(cleanup_interruption, "add_note"):
                    cleanup_interruption.add_note(note)
                else:
                    print(note, file=sys.stderr)
                raise
        message = f"could not execute bubblewrap namespace probe: {exc}"
        if cleanup_detail:
            message = f"{message}; cleanup: {cleanup_detail}"
        return False, message
    except BaseException as interruption:
        # KeyboardInterrupt/SystemExit can arrive while communicate() is
        # waiting. Terminate the whole session even if the leader has already
        # exited: descendants may still be alive in its process group.
        if process is not None:
            try:
                cleanup_stdout, cleanup_stderr = _terminate_process_groups(
                    process, grace_seconds=0.25
                )
                cleanup_detail = "\\n".join(
                    part
                    for part in (
                        _as_text(cleanup_stdout),
                        _as_text(cleanup_stderr),
                    )
                    if part
                ).strip()
            except Exception as cleanup_error:
                cleanup_detail = (
                    "process-group cleanup raised "
                    f"{type(cleanup_error).__name__}: {cleanup_error}"
                )
            except BaseException as cleanup_interruption:
                retry_detail = "process-group cleanup retry completed"
                try:
                    retry_stdout, retry_stderr = _terminate_process_groups(
                        process, grace_seconds=0.25
                    )
                    retry_output = "\\n".join(
                        part
                        for part in (
                            _as_text(retry_stdout),
                            _as_text(retry_stderr),
                        )
                        if part
                    ).strip()
                    if retry_output:
                        retry_detail = f"{retry_detail}: {retry_output}"
                except Exception as retry_error:
                    retry_detail = (
                        "process-group cleanup retry raised "
                        f"{type(retry_error).__name__}: {retry_error}"
                    )
                except BaseException as retry_interruption:
                    retry_detail = (
                        "process-group cleanup retry was interrupted by "
                        f"{type(retry_interruption).__name__}: {retry_interruption}"
                    )

                cleanup_detail = (
                    "Original preflight interruption: "
                    f"{type(interruption).__name__}: {interruption}; "
                    "first process-group cleanup was interrupted by "
                    f"{type(cleanup_interruption).__name__}: {cleanup_interruption}; "
                    f"{retry_detail}"
                )

            if cleanup_detail:
                note = (
                    "ImageBuilder host preflight process-group cleanup: "
                    + cleanup_detail
                )
                if hasattr(interruption, "add_note"):
                    interruption.add_note(note)
                else:
                    print(note, file=sys.stderr)
        raise


def main() -> int:
    ready, detail = check_host()
    if not ready:
        print(
            "RELEASE-BLOCKED: required unprivileged bubblewrap user namespace is unavailable; "
            "refusing to run sandbox-dependent packaging regressions without the approved boundary.",
            file=sys.stderr,
        )
        print(detail, file=sys.stderr)
        return 125

    print(f"SANDBOX-HOST-READY: {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
