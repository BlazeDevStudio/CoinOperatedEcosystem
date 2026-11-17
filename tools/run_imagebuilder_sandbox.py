#!/usr/bin/env python3
"""Run one generated ImageBuilder wrapper with a read-only host root."""
from __future__ import annotations

import argparse
import json
import os
import select
import shutil
import stat
import subprocess
import sys


def blocked(message: str, detail: str = "") -> int:
    print(f"RELEASE-BLOCKED: {message}", file=sys.stderr)
    if detail:
        print(detail[-4000:], file=sys.stderr)
    return 125


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--builder", required=True)
    parser.add_argument("--wrapper", required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        return blocked("sandbox runner must be invoked through sudo")
    try:
        caller_uid = int(os.environ["SUDO_UID"])
        caller_gid = int(os.environ["SUDO_GID"])
    except (KeyError, ValueError):
        return blocked("sudo caller UID/GID are unavailable")
    if caller_uid <= 0 or caller_gid <= 0:
        return blocked("refusing to map a root or invalid caller identity")

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
    newuidmap = shutil.which("newuidmap")
    newgidmap = shutil.which("newgidmap")
    if not bwrap or not newuidmap or not newgidmap:
        return blocked("bubblewrap and uidmap helpers are required")

    probe_name = f".phx-bwrap-owner-probe-{os.getpid()}"
    probe_path = os.path.join(builder, probe_name)
    if os.path.lexists(probe_path):
        return blocked("refusing to overwrite an existing ownership probe")

    info_read, info_write = os.pipe()
    userns_block_read, userns_block_write = os.pipe()
    os.set_inheritable(info_write, True)
    os.set_inheritable(userns_block_read, True)
    sandbox_script = (
        'printf "owner-probe\\n" > "$OPENWRT_IMAGEBUILDER_DIR/$PHX_BWRAP_OWNER_PROBE"; '
        'exec sh "$1"'
    )
    command = [
        bwrap,
        "--unshare-all",
        "--share-net",  # Hosted runner cannot configure loopback; network isolation is not claimed.
        "--unshare-user",
        "--userns-block-fd", str(userns_block_read),
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
        "--uid", "0",
        "--gid", "0",
        "--",
        "sh", "-eu", "-c", sandbox_script, "phx-bwrap", wrapper,
    ]
    process = None
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env={"PATH": "/usr/bin:/bin", "LANG": "C"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            pass_fds=(info_write, userns_block_read),
        )
        os.close(info_write)
        info_write = -1
        os.close(userns_block_read)
        userns_block_read = -1

        ready, _, _ = select.select([info_read], [], [], 30)
        if not ready:
            process.terminate()
            _, stderr = process.communicate()
            return blocked("timed out waiting for bubblewrap user namespace", stderr)
        info_payload = os.read(info_read, 65536)
        if not info_payload:
            _, stderr = process.communicate()
            return blocked("bubblewrap exited before reporting its user namespace", stderr)
        try:
            namespace_info = json.loads(info_payload.decode("utf-8"))
            child_pid = str(namespace_info["child-pid"])
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            process.terminate()
            _, stderr = process.communicate()
            return blocked(f"invalid bubblewrap namespace information: {exc}", stderr)

        uid_result = subprocess.run(
            [newuidmap, child_pid, "0", str(caller_uid), "1"],
            capture_output=True, text=True, check=False,
        )
        gid_result = subprocess.run(
            [newgidmap, child_pid, "0", str(caller_gid), "1"],
            capture_output=True, text=True, check=False,
        )
        if uid_result.returncode != 0 or gid_result.returncode != 0:
            process.terminate()
            _, stderr = process.communicate()
            return blocked(
                "could not map sandbox root to the invoking runner UID/GID",
                f"newuidmap: {uid_result.stderr}\\nnewgidmap: {gid_result.stderr}\\nsandbox: {stderr}",
            )

        os.write(userns_block_write, b"1")
        os.close(userns_block_write)
        userns_block_write = -1
        stdout, stderr = process.communicate()
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
        if process is not None and process.poll() is None:
            process.terminate()
            process.communicate()
        return blocked(f"sandbox setup failed: {exc}")
    finally:
        for fd in (info_read, info_write, userns_block_read, userns_block_write):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if process is not None and process.poll() is None:
            process.terminate()
            process.communicate()
        if os.path.lexists(probe_path):
            try:
                os.unlink(probe_path)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
