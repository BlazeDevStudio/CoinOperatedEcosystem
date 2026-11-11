#!/usr/bin/env python3
"""Fail if a Git tree contains paths that differ only by letter case.

Such trees cannot be checked out on case-insensitive filesystems (Windows,
default macOS): one spelling silently overwrites the other. In pull-request CI
the checked-out commit is the *merge result*, so checking HEAD catches
collisions between two branches that are each individually fine.

Usage: check_case_collisions.py [treeish]   (default: HEAD)
Exit 0 = clean, 1 = collision(s) found, 2 = git error.
"""
import subprocess
import sys


def tree_paths(treeish):
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", "-r", "-z", "--name-only", treeish],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr.decode(errors="replace"))
        sys.exit(2)
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def find_collisions(paths):
    """Return {lowercased prefix: sorted spellings} for every ambiguous prefix."""
    seen = {}
    for path in paths:
        parts = path.split("/")
        for i in range(1, len(parts) + 1):
            prefix = "/".join(parts[:i])
            seen.setdefault(prefix.lower(), set()).add(prefix)
    return {k: sorted(v) for k, v in seen.items() if len(v) > 1}


def main(argv):
    treeish = argv[1] if len(argv) > 1 else "HEAD"
    collisions = find_collisions(tree_paths(treeish))
    if not collisions:
        print(f"OK: no case-insensitive path collisions in {treeish}")
        return 0
    print(f"FAIL: case-insensitive path collisions in {treeish}:")
    for spellings in sorted(collisions.values()):
        print("  " + "  <->  ".join(spellings))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
