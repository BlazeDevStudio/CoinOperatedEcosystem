#!/usr/bin/env python3
"""Run one generated ImageBuilder wrapper with a read-only host root and one writable build tree."""
from __future__ import annotations

import argparse
import json
import os
import select
import shutil
import signal
import stat
import subprocess
import sys


USERNS_INFO_TIMEOUT_SECONDS = 30
PROCESS_TERMINATION_GRACE_SECONDS = 2.0
DEFAULT_BUILD_TIMEOUT_SECONDS = 3600
MAX_BUILD_TIMEOUT_SECONDS = 14400


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

def _invoking_unprivileged_identity() -> tuple[int, int]:
    """Return the single host UID/GID allowed to own sandbox output."""
    uid = os.getuid()
    gid = os.getgid()
    if uid <= 0 or gid <= 0:
        raise PermissionError("sandbox runner must be invoked by a non-root user")
    if os.geteuid() != uid or os.getegid() != gid:
        raise PermissionError("sandbox runner must not use elevated or mismatched effective UID/GID")
    return uid, gid


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
                errors.append(f"could not signal process group {pgid}: {exc}")

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

    if errors:
        stderr = "\n".join(part for part in (_as_text(stderr), *errors) if part)
    return _as_text(stdout), _as_text(stderr)


def _communicate_with_timeout(
    process: subprocess.Popen,
    timeout_seconds: int,
    child_pgid: int | None = None,
) -> tuple[tuple[str, str], bool]:
    try:
        return process.communicate(timeout=timeout_seconds), False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = _terminate_process_groups(process, child_pgid)
        stdout = stdout or _as_text(exc.output or exc.stdout)
        stderr = stderr or _as_text(exc.stderr)
        return (stdout, stderr), True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--builder", required=True)
    parser.add_argument("--wrapper", required=True)
    parser.add_argument(
        "--timeout-seconds", type=int, default=DEFAULT_BUILD_TIMEOUT_SECONDS,
        help=f"maximum ImageBuilder runtime in seconds (1-{MAX_BUILD_TIMEOUT_SECONDS})",
    )
    args = parser.parse_args()

    if not 1 <= args.timeout_seconds <= MAX_BUILD_TIMEOUT_SECONDS:
        return blocked(f"build timeout must be between 1 and {MAX_BUILD_TIMEOUT_SECONDS} seconds")

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

    bwrap = shutil.which("bwrap")
    if not bwrap:
        return blocked("bubblewrap is required")

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
        "--dev", "/dev",
        "--proc", "/proc",
        "--tmpfs", "/tmp",
        "--bind", builder, builder,
        "--chdir", cwd,
        "--clearenv",
        "--setenv", "PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
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
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env={"PATH": "/usr/bin:/bin", "LANG": "C"},
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
            return blocked("timed out waiting for bubblewrap user namespace", stderr)
        info_payload = os.read(info_read, 65536)
        if not info_payload:
            _, stderr = _terminate_process_groups(process)
            return blocked("bubblewrap exited before reporting its user namespace", stderr)
        try:
            namespace_info = json.loads(info_payload.decode("utf-8"))
            child_pid = int(namespace_info["child-pid"])
            if child_pid <= 0:
                raise ValueError("child-pid must be a positive integer")
            sandbox_child_pgid = child_pid
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            _, stderr = _terminate_process_groups(process)
            return blocked(f"invalid bubblewrap namespace information: {exc}", stderr)

        # Bubblewrap's unprivileged user namespace maps only this invoking
        # host UID/GID to namespace root; no external mapping helper is used.
        (stdout, stderr), timed_out = _communicate_with_timeout(
            process, args.timeout_seconds, sandbox_child_pgid
        )
        if timed_out:
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
    except (OSError, subprocess.SubprocessError) as exc:
        detail = ""
        if process is not None:
            cleanup_stdout, cleanup_stderr = _terminate_process_groups(
                process, sandbox_child_pgid
            )
            detail = f"{cleanup_stdout}\n{cleanup_stderr}".strip()
        return blocked(f"sandbox setup failed: {exc}", detail)
    finally:
        for fd in (info_read, info_write):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if process is not None and process.poll() is None:
            _terminate_process_groups(process, sandbox_child_pgid)
        if os.path.lexists(probe_path):
            try:
                os.unlink(probe_path)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
