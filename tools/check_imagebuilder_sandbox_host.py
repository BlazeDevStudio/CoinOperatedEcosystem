#!/usr/bin/env python3
"""Fail-fast capability probe for the release-owned ImageBuilder sandbox host."""
import os
import shutil
import stat

import imagebuilder_bwrap_trust
import subprocess
import sys

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
PRIVATE_HOST_PATHS = ("/home", "/root", "/run", "/mnt", "/media", "/srv")


def _private_host_mount_args() -> list[str]:
    """Mirror the runner's masked host-data mount list."""
    return [argument for path in PRIVATE_HOST_PATHS for argument in ("--tmpfs", path)]


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

    try:
        result = subprocess.run(
            build_probe_command(executable),
            cwd="/",
            env={"PATH": SANDBOX_PATH, "LANG": "C"},
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        detail = (_as_text(exc.stderr) or _as_text(exc.stdout)).strip()
        message = f"bubblewrap namespace probe timed out after {timeout_seconds:g} seconds"
        return False, f"{message}: {detail}" if detail else message
    except OSError as exc:
        return False, f"could not execute bubblewrap namespace probe: {exc}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        message = f"bubblewrap namespace probe exited with status {result.returncode}"
        return False, f"{message}: {detail}" if detail else message

    return True, "unprivileged user namespace, masked host-data paths and tmpfs write probe passed"


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
