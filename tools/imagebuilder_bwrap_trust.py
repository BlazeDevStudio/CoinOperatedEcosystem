#!/usr/bin/env python3
"""Shared trusted-system executable checks for the release ImageBuilder sandbox."""
import os
import stat


def is_trusted_system_directory(path: str) -> bool:
    """Require every canonical directory component to be root-owned and non-writable."""
    if path not in ("/usr/bin", "/bin"):
        return False

    current = os.sep
    for component in path.strip(os.sep).split(os.sep):
        if not component:
            continue
        current = os.path.join(current, component)
        try:
            entry = os.lstat(current)
        except OSError:
            return False
        if (
            not stat.S_ISDIR(entry.st_mode)
            or entry.st_uid != 0
            or entry.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            return False
    return True


def is_trusted_executable(path: str) -> bool:
    """Require a root-owned regular executable below a trusted canonical parent."""
    candidate = os.path.abspath(path)
    # Resolve the parent, not the final component: /bin -> /usr/bin is a
    # supported merged-usr alias, but a redirect outside trusted system paths is not.
    trusted_parent = os.path.realpath(os.path.dirname(candidate))
    if not is_trusted_system_directory(trusted_parent):
        return False
    try:
        entry = os.lstat(candidate)
    except OSError:
        return False

    # The runner uses only the unprivileged single-ID user-namespace model.
    forbidden_mode_bits = stat.S_ISUID | stat.S_ISGID | stat.S_IWGRP | stat.S_IWOTH
    return (
        stat.S_ISREG(entry.st_mode)
        and entry.st_uid == 0
        and not (entry.st_mode & forbidden_mode_bits)
        and os.access(candidate, os.X_OK)
    )
