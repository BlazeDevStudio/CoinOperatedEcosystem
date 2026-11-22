#!/usr/bin/env python3
"""Run ImageBuilder with masked host-data paths and one writable build tree."""
from __future__ import annotations

import argparse
import json
import os
import re
import select
import shutil
import signal
import stat
import subprocess
import sys
import time

import imagebuilder_bwrap_trust
from imagebuilder_bwrap_trust import PRIVATE_HOST_PATHS, private_host_mount_args as _private_host_mount_args


USERNS_INFO_TIMEOUT_SECONDS = 30
PROCESS_TERMINATION_GRACE_SECONDS = 2.0
DEFAULT_BUILD_TIMEOUT_SECONDS = 3600
MAX_BUILD_TIMEOUT_SECONDS = 14400
TRUSTED_BWRAP_PATH = "/usr/bin:/bin"
SANDBOX_PATH = "/usr/sbin:/usr/bin:/sbin:/bin"
def blocked(message: str, detail: str = "") -> int:
    print(f"RELEASE-BLOCKED: {message}", file=sys.stderr)
    if detail:
        print(detail[-4000:], file=sys.stderr)
    return 125


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _recover_available_namespace_child_pgid(info_fd: int) -> tuple[int | None, str]:
    """Best-effort nonblocking recovery of Bubblewrap's detached child PGID."""
    if info_fd < 0:
        return None, "namespace info pipe is already closed"
    try:
        os.set_blocking(info_fd, False)
        payload = os.read(info_fd, 65536)
    except BlockingIOError:
        return None, "namespace info pipe had no available child-pid during interruption"
    except OSError as exc:
        return None, f"could not read namespace info pipe during interruption: {exc}"
    if not payload:
        return None, "namespace info pipe closed before child-pid recovery"

    try:
        namespace_info = json.loads(payload.decode("utf-8"))
        child_pid = int(namespace_info["child-pid"])
        if child_pid <= 0:
            raise ValueError("child-pid must be a positive integer")
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return None, f"could not recover Bubblewrap child-pid during interruption: {exc}"
    return child_pid, ""

def _invoking_unprivileged_identity() -> tuple[int, int]:
    """Return the single host UID/GID allowed to own sandbox output."""
    uid = os.getuid()
    gid = os.getgid()
    if uid <= 0 or gid <= 0:
        raise PermissionError("sandbox runner must be invoked by a non-root user")
    if os.geteuid() != uid or os.getegid() != gid:
        raise PermissionError("sandbox runner must not use elevated or mismatched effective UID/GID")
    return uid, gid


def _wait_for_process_groups_exit(groups: list[int], timeout_seconds: float) -> list[str]:
    """Wait until every sandbox process group is gone, or fail closed."""
    pending = set(groups)
    if not pending:
        return []

    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while pending:
        for pgid in tuple(pending):
            try:
                os.killpg(pgid, 0)
            except ProcessLookupError:
                pending.discard(pgid)
            except OSError as exc:
                return [
                    f"RELEASE-BLOCKED: could not confirm sandbox process group {pgid} exit: {exc}"
                ]

        if not pending:
            break

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            survivors = ", ".join(str(pgid) for pgid in sorted(pending))
            return [
                "RELEASE-BLOCKED: sandbox process group(s) did not exit after SIGKILL: "
                + survivors
            ]
        time.sleep(min(0.05, remaining))

    return []


def _terminate_process_groups(
    process: subprocess.Popen,
    child_pgid: int | None = None,
    grace_seconds: float = PROCESS_TERMINATION_GRACE_SECONDS,
) -> tuple[str, str]:
    """Stop both the outer bwrap group and its --new-session child group."""
    groups: list[int] = []
    for raw_pgid in (process.pid, child_pgid):
        if raw_pgid is None:
            continue
        try:
            pgid = int(raw_pgid)
        except (TypeError, ValueError):
            continue
        if pgid > 0 and pgid not in groups:
            groups.append(pgid)

    errors: list[str] = []

    def signal_groups(signum: int) -> None:
        for pgid in groups:
            try:
                os.killpg(pgid, signum)
            except ProcessLookupError:
                pass
            except OSError as exc:
                if signum == signal.SIGKILL:
                    errors.append(
                        f"RELEASE-BLOCKED: could not signal sandbox process group {pgid} with SIGKILL: {exc}"
                    )

    signal_groups(signal.SIGTERM)
    try:
        stdout, stderr = process.communicate(timeout=grace_seconds)
    except subprocess.TimeoutExpired as first_timeout:
        stdout = _as_text(first_timeout.output or first_timeout.stdout)
        stderr = _as_text(first_timeout.stderr)
        signal_groups(signal.SIGKILL)
        try:
            stdout, stderr = process.communicate(timeout=grace_seconds)
        except subprocess.TimeoutExpired as final_timeout:
            stdout = _as_text(final_timeout.output or final_timeout.stdout) or stdout
            stderr = _as_text(final_timeout.stderr) or stderr
            try:
                process.kill()
            except OSError as exc:
                errors.append(f"could not kill bubblewrap process: {exc}")
            try:
                process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                errors.append("bubblewrap process did not exit after SIGKILL")
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
    else:
        # The command leader may exit while a detached descendant remains in
        # the sandbox session. The process group belongs only to this runner.
        signal_groups(signal.SIGKILL)

    errors.extend(_wait_for_process_groups_exit(groups, grace_seconds))

    if errors:
        stderr = "\n".join(part for part in (_as_text(stderr), *errors) if part)
    return _as_text(stdout), _as_text(stderr)


def _communicate_with_timeout(
    process: subprocess.Popen,
    timeout_seconds: int,
    child_pgid: int | None = None,
) -> tuple[tuple[str, str], bool]:
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = _terminate_process_groups(process, child_pgid)
        stdout = stdout or _as_text(exc.output or exc.stdout)
        stderr = "\n".join(part for part in (_as_text(stderr), _as_text(exc.stderr)) if part)
        return (stdout, stderr), True

    # A successful shell leader can still leave detached descendants behind.
    # Reap the entire per-invocation sandbox session before accepting success.
    cleanup_stdout, cleanup_stderr = _terminate_process_groups(process, child_pgid)
    stdout = stdout or cleanup_stdout
    if cleanup_stderr:
        stderr = "\n".join(part for part in (_as_text(stderr), _as_text(cleanup_stderr)) if part)
    # A wrapped build may intentionally print RELEASE-BLOCKED for an ordinary
    # nonzero result. Only diagnostics emitted by process-group cleanup make
    # this a sandbox timeout/cleanup failure.
    cleanup_error_markers = (
        "RELEASE-BLOCKED: sandbox process group(s) did not exit after SIGKILL:",
        "RELEASE-BLOCKED: could not signal sandbox process group",
        "could not kill bubblewrap process:",
        "bubblewrap process did not exit after SIGKILL",
    )
    cleanup_failed = any(marker in cleanup_stderr for marker in cleanup_error_markers)
    return (stdout, stderr), cleanup_failed


def _is_trusted_system_directory(path: str) -> bool:
    return imagebuilder_bwrap_trust.is_trusted_system_directory(path)


def _is_within_trusted_system_directories(path: str) -> bool:
    return imagebuilder_bwrap_trust.is_trusted_executable(path)


def _has_single_id_mapping(path: str) -> bool:
    try:
        with open(path, "r", encoding="ascii") as mapping_file:
            rows = [line.split() for line in mapping_file if line.strip()]
    except OSError:
        return False
    if len(rows) != 1 or len(rows[0]) != 3:
        return False
    try:
        namespace_id, host_id, length = (int(value, 10) for value in rows[0])
    except ValueError:
        return False
    return namespace_id == 0 and host_id > 0 and length == 1


def _decode_mountinfo_path(value: str) -> str:
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)


def verify_sandbox_context(
    builder: str,
    probe_name: str,
    proc_root: str = "/proc",
) -> bool:
    """Verify the wrapper is inside the expected single-ID, read-only-root sandbox."""
    if os.environ.get("PHX_IMAGEBUILDER_SANDBOX_ACTIVE") != "1":
        return False
    if os.environ.get("PHX_BWRAP_OWNER_PROBE") != probe_name:
        return False
    if not re.fullmatch(r"\.phx-bwrap-owner-probe-[0-9]+|\.phx-test-owner-probe", probe_name or ""):
        return False
    if (os.getuid(), os.geteuid(), os.getgid(), os.getegid()) != (0, 0, 0, 0):
        return False

    builder_path = os.path.abspath(builder)
    if os.path.realpath(builder_path) != builder_path or not os.path.isdir(builder_path):
        return False

    probe_path = os.path.join(builder_path, probe_name)
    try:
        probe_stat = os.lstat(probe_path)
    except OSError:
        return False
    if not stat.S_ISREG(probe_stat.st_mode):
        return False

    if not _has_single_id_mapping(os.path.join(proc_root, "self", "uid_map")):
        return False
    if not _has_single_id_mapping(os.path.join(proc_root, "self", "gid_map")):
        return False

    mountinfo_path = os.path.join(proc_root, "self", "mountinfo")
    try:
        with open(mountinfo_path, "r", encoding="utf-8") as mountinfo_file:
            mountinfo_lines = mountinfo_file.readlines()
    except OSError:
        return False

    mounts: dict[str, tuple[str, set[str]]] = {}
    for line in mountinfo_lines:
        left, separator, right = line.partition(" - ")
        if not separator:
            return False
        left_fields = left.split()
        right_fields = right.split()
        if len(left_fields) < 6 or len(right_fields) < 3:
            return False
        mountpoint = os.path.normpath(_decode_mountinfo_path(left_fields[4]))
        if mountpoint in mounts:
            return False
        mounts[mountpoint] = (right_fields[0], set(left_fields[5].split(",")))

    root_mount = mounts.get("/")
    tmp_mount = mounts.get("/tmp")
    proc_mount = mounts.get("/proc")
    dev_mount = mounts.get("/dev")
    builder_mount = mounts.get(builder_path)
    if not root_mount or "ro" not in root_mount[1] or "rw" in root_mount[1]:
        return False
    if not tmp_mount or tmp_mount[0] != "tmpfs" or "rw" not in tmp_mount[1]:
        return False
    if not proc_mount or proc_mount[0] != "proc" or "rw" not in proc_mount[1]:
        return False
    if not dev_mount or dev_mount[0] != "tmpfs" or "rw" not in dev_mount[1]:
        return False
    if not builder_mount or "rw" not in builder_mount[1]:
        return False
    for private_path in PRIVATE_HOST_PATHS:
        private_mount = mounts.get(private_path)
        if not private_mount or private_mount[0] != "tmpfs" or "rw" not in private_mount[1]:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd")
    parser.add_argument("--builder", required=True)
    parser.add_argument("--wrapper")
    parser.add_argument("--probe")
    parser.add_argument("--verify-context", action="store_true")
    parser.add_argument(
        "--timeout-seconds", type=int, default=DEFAULT_BUILD_TIMEOUT_SECONDS,
        help=f"maximum ImageBuilder runtime in seconds (1-{MAX_BUILD_TIMEOUT_SECONDS})",
    )
    args = parser.parse_args()

    if not 1 <= args.timeout_seconds <= MAX_BUILD_TIMEOUT_SECONDS:
        return blocked(f"build timeout must be between 1 and {MAX_BUILD_TIMEOUT_SECONDS} seconds")

    if args.verify_context:
        probe_name = args.probe or os.environ.get("PHX_BWRAP_OWNER_PROBE", "")
        if verify_sandbox_context(args.builder, probe_name):
            return 0
        return blocked("current process does not satisfy the required single-ID read-only-root ImageBuilder sandbox")

    if not args.cwd or not args.wrapper:
        return blocked("normal sandbox invocation requires --cwd and --wrapper")

    try:
        caller_uid, caller_gid = _invoking_unprivileged_identity()
    except PermissionError as exc:
        return blocked(str(exc))

    cwd = os.path.realpath(os.path.abspath(args.cwd))
    builder = os.path.abspath(args.builder)
    wrapper = os.path.abspath(args.wrapper)
    if os.path.realpath(builder) != builder or not os.path.isdir(builder):
        return blocked("ImageBuilder path is not a real directory")
    if os.path.realpath(wrapper) != wrapper or not os.path.isfile(wrapper):
        return blocked("generated wrapper is not a regular file")
    try:
        if os.path.commonpath((cwd, builder)) != cwd or builder == cwd:
            return blocked("writable ImageBuilder path escapes the disposable test workspace")
        if os.path.commonpath((cwd, wrapper)) != cwd:
            return blocked("generated wrapper escapes the disposable test workspace")
    except ValueError:
        return blocked("sandbox paths are not on one filesystem root")

    bwrap_candidate = shutil.which("bwrap", path=TRUSTED_BWRAP_PATH)
    if not bwrap_candidate:
        return blocked("bubblewrap is required in trusted system directories")
    bwrap = os.path.abspath(bwrap_candidate)
    if not _is_within_trusted_system_directories(bwrap):
        return blocked("bubblewrap resolved outside trusted system directories")

    probe_name = f".phx-bwrap-owner-probe-{os.getpid()}"
    probe_path = os.path.join(builder, probe_name)
    if os.path.lexists(probe_path):
        return blocked("refusing to overwrite an existing ownership probe")

    info_read, info_write = os.pipe()
    os.set_inheritable(info_write, True)
    sandbox_script = (
        'printf "owner-probe\\n" > "$OPENWRT_IMAGEBUILDER_DIR/$PHX_BWRAP_OWNER_PROBE"; '
        'exec sh "$1"'
    )
    command = [
        bwrap,
        "--unshare-all",
        "--share-net",  # Hosted runner cannot configure loopback; network isolation is not claimed.
        "--unshare-user",
        "--info-fd", str(info_write),
        "--die-with-parent",
        "--new-session",
        "--ro-bind", "/", "/",
        *_private_host_mount_args(),
        "--dev", "/dev",
        "--proc", "/proc",
        "--tmpfs", "/tmp",
        "--bind", builder, builder,
        "--chdir", cwd,
        "--clearenv",
        "--setenv", "PATH", SANDBOX_PATH,
        "--setenv", "HOME", "/tmp",
        "--setenv", "TMPDIR", "/tmp",
        "--setenv", "LC_ALL", "C",
        "--setenv", "OPENWRT_IMAGEBUILDER_DIR", builder,
        "--setenv", "PHX_BWRAP_OWNER_PROBE", probe_name,
        "--setenv", "PHX_IMAGEBUILDER_SANDBOX_ACTIVE", "1",
        "--uid", "0",
        "--gid", "0",
        "--",
        "sh", "-eu", "-c", sandbox_script, "phx-bwrap", wrapper,
    ]
    process = None
    sandbox_child_pgid = None
    process_groups_cleanup_complete = False
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env={"PATH": TRUSTED_BWRAP_PATH, "LANG": "C"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            pass_fds=(info_write,),
            start_new_session=True,
        )
        os.close(info_write)
        info_write = -1
        ready, _, _ = select.select(
            [info_read], [], [], USERNS_INFO_TIMEOUT_SECONDS
        )
        if not ready:
            _, stderr = _terminate_process_groups(process)
            process_groups_cleanup_complete = True
            return blocked("timed out waiting for bubblewrap user namespace", stderr)
        info_payload = os.read(info_read, 65536)
        if not info_payload:
            _, stderr = _terminate_process_groups(process)
            process_groups_cleanup_complete = True
            return blocked("bubblewrap exited before reporting its user namespace", stderr)
        try:
            namespace_info = json.loads(info_payload.decode("utf-8"))
            child_pid = int(namespace_info["child-pid"])
            if child_pid <= 0:
                raise ValueError("child-pid must be a positive integer")
            sandbox_child_pgid = child_pid
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            _, stderr = _terminate_process_groups(process)
            process_groups_cleanup_complete = True
            return blocked(f"invalid bubblewrap namespace information: {exc}", stderr)

        # Bubblewrap's unprivileged user namespace maps only this invoking
        # host UID/GID to namespace root; no external mapping helper is used.
        (stdout, stderr), timed_out = _communicate_with_timeout(
            process, args.timeout_seconds, sandbox_child_pgid
        )
        process_groups_cleanup_complete = True
        if timed_out:
            if "sandbox process group" in stderr.lower():
                return blocked(
                    "sandbox descendant process group did not terminate cleanly",
                    f"stdout:\n{stdout}\nstderr:\n{stderr}",
                )
            return blocked(
                f"ImageBuilder build exceeded its {args.timeout_seconds}s timeout",
                f"stdout:\n{stdout}\nstderr:\n{stderr}",
            )
        if stdout:
            sys.stdout.write(stdout)
        if stderr:
            sys.stderr.write(stderr)

        try:
            probe_stat = os.lstat(probe_path)
        except FileNotFoundError:
            return blocked("sandbox did not create its ownership probe", stderr)
        try:
            if not stat.S_ISREG(probe_stat.st_mode):
                return blocked("sandbox ownership probe is not a regular file", stderr)
            if probe_stat.st_uid != caller_uid or probe_stat.st_gid != caller_gid:
                return blocked(
                    "sandbox output ownership does not match the invoking runner",
                    f"expected {caller_uid}:{caller_gid}, got {probe_stat.st_uid}:{probe_stat.st_gid}",
                )
        finally:
            os.unlink(probe_path)
        return process.returncode
    except (KeyboardInterrupt, SystemExit) as interruption:
        cleanup_parts: list[str] = []
        if process is not None and not process_groups_cleanup_complete:
            if sandbox_child_pgid is None:
                sandbox_child_pgid, recovery_detail = (
                    _recover_available_namespace_child_pgid(info_read)
                )
                if recovery_detail:
                    cleanup_parts.append(recovery_detail)
            try:
                cleanup_stdout, cleanup_stderr = _terminate_process_groups(
                    process, sandbox_child_pgid
                )
                cleanup_parts.extend(
                    part
                    for part in (_as_text(cleanup_stdout), _as_text(cleanup_stderr))
                    if part
                )
                process_groups_cleanup_complete = True
            except Exception as cleanup_error:
                cleanup_parts.append(
                    "process-group cleanup raised "
                    f"{type(cleanup_error).__name__}: {cleanup_error}"
                )

        if cleanup_parts:
            note = "ImageBuilder runner process-group cleanup: " + "\n".join(cleanup_parts)
            if hasattr(interruption, "add_note"):
                interruption.add_note(note)
            else:
                print(note, file=sys.stderr)
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        detail = ""
        if process is not None:
            cleanup_stdout, cleanup_stderr = _terminate_process_groups(
                process, sandbox_child_pgid
            )
            process_groups_cleanup_complete = True
            detail = f"{cleanup_stdout}\n{cleanup_stderr}".strip()
        return blocked(f"sandbox setup failed: {exc}", detail)
    finally:
        if process is not None and not process_groups_cleanup_complete:
            cleanup_parts: list[str] = []
            if sandbox_child_pgid is None:
                sandbox_child_pgid, recovery_detail = (
                    _recover_available_namespace_child_pgid(info_read)
                )
                if recovery_detail:
                    cleanup_parts.append(recovery_detail)
            try:
                cleanup_stdout, cleanup_stderr = _terminate_process_groups(
                    process, sandbox_child_pgid
                )
                cleanup_parts.extend(
                    part
                    for part in (_as_text(cleanup_stdout), _as_text(cleanup_stderr))
                    if part
                )
                process_groups_cleanup_complete = True
            except Exception as cleanup_error:
                cleanup_parts.append(
                    "process-group cleanup raised "
                    f"{type(cleanup_error).__name__}: {cleanup_error}"
                )

            if cleanup_parts:
                note = "ImageBuilder runner finalizer cleanup: " + "\n".join(cleanup_parts)
                active_exception = sys.exc_info()[1]
                if active_exception is not None:
                    if hasattr(active_exception, "add_note"):
                        active_exception.add_note(note)
                    else:
                        print(note, file=sys.stderr)
                else:
                    raise RuntimeError(note)

        for fd in (info_read, info_write):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if os.path.lexists(probe_path):
            try:
                os.unlink(probe_path)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
