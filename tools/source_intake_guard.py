#!/usr/bin/env python3
"""Fail-closed, OFFLINE source-intake gate for CoinOperatedEcosystem.

This checks *declared* commit/blob identities and any locally staged bytes.
It cannot authenticate a remote repository or authorize financial admission.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ORIGIN = "BlazeDevStudio/BlazingSystems-Experiments"
ROOTS = {
    "core": ("core/", "experiment/openwrt/BlazePwifi/openwrt/"),
    "rental": ("rental/", "experiment/openwrt/BlazePwifi/android/"),
    "pisonet": ("pisonet/", "experiment/windows/BlazePisonet-SoftTimer/"),
    "esp8266": ("controllers/esp8266/", "experiment/openwrt/BlazePwifi/esp8266/"),
    "esp32": ("controllers/esp32/", "experiment/openwrt/BlazePwifi/esp32/"),
}
MODULES = frozenset(ROOTS)
SOURCE_SUFFIXES = frozenset({
    ".sh", ".py", ".c", ".h", ".cpp", ".hpp", ".ino", ".cs", ".java", ".kt",
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".html", ".xml", ".json",
    ".gradle", ".kts", ".ps1", ".bat", ".cmd", ".yml", ".yaml", ".exe", ".dll",
    ".apk", ".bin",
})
BASE_FIELDS = frozenset({
    "module", "source_repo", "source_pr", "source_commit",
    "source_path", "source_blob_sha", "state",
})
STAGED_FIELDS = frozenset({"destination_path", "content_sha256"})
REFACTORED_FIELDS = frozenset({"source_content_sha256", "review_note"})
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PORTABLE = re.compile(r"^[A-Za-z0-9_.\/-]+$")


class IntakeError(ValueError):
    pass


def no_duplicate_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise IntakeError("duplicate JSON key: " + key)
        result[key] = value
    return result


def safe_path(text):
    if not isinstance(text, str) or not PORTABLE.fullmatch(text):
        raise IntakeError("invalid or nonportable relative path")
    if (text.startswith("/") or "//" in text or
            any(segment in (".", "..", "") for segment in text.split("/"))):
        raise IntakeError("unsafe source/destination path")
    return text


def hex_sha(value, length):
    if not isinstance(value, str) or not (HEX40 if length == 40 else HEX64).fullmatch(value):
        raise IntakeError("missing or invalid lowercase full SHA")
    return value


def stage_file(root, relative, sha256, blob_sha=None):
    path = root / relative
    current = root
    for component in relative.split("/"):
        current = current / component
        if current.is_symlink():
            raise IntakeError("symlink in staged destination")
    if not path.is_file():
        raise IntakeError("staged source is missing")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != sha256:
        raise IntakeError("staged source SHA-256 mismatch")
    git_blob = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()
    if blob_sha is not None and git_blob != blob_sha:
        raise IntakeError("staged source Git blob mismatch")


def audit(root, manifest):
    root = Path(root).resolve()
    manifest = Path(manifest)
    if manifest.is_symlink() or not manifest.is_file():
        raise IntakeError("manifest must be a real file")
    try:
        document = json.loads(
            manifest.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_json_keys
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise IntakeError("unreadable JSON manifest") from error
    if not isinstance(document, dict) or set(document) != {
        "schema_version", "project", "production_authorized", "entries"
    }:
        raise IntakeError("manifest fields differ from schema v1")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise IntakeError("unsupported manifest schema version")
    if document["project"] != "CoinOperatedEcosystem":
        raise IntakeError("wrong project identity")
    if document["production_authorized"] is not False:
        raise IntakeError("source intake must never authorize production")
    entries = document["entries"]
    if not isinstance(entries, list) or not entries:
        raise IntakeError("source intake needs pinned source entries")

    seen = set()
    staged = set()
    modules = set()
    for entry in entries:
        if not isinstance(entry, dict) or not BASE_FIELDS.issubset(entry):
            raise IntakeError("missing intake fields")
        state = entry["state"]
        if state not in ("candidate", "staged", "refactored"):
            raise IntakeError("unknown or prematurely promoted intake state")
        expected = BASE_FIELDS
        if state in ("staged", "refactored"):
            expected |= STAGED_FIELDS
        if state == "refactored":
            expected |= REFACTORED_FIELDS
        if set(entry) != expected:
            raise IntakeError("intake fields inconsistent for declared state")
        module = entry["module"]
        if not isinstance(module, str) or module not in ROOTS:
            raise IntakeError("unknown ecosystem module")
        dest_prefix, source_prefix = ROOTS[module]
        if entry["source_repo"] != ORIGIN:
            raise IntakeError("third-party import requires separate license intake")
        if type(entry["source_pr"]) is not int or entry["source_pr"] < 1:
            raise IntakeError("source PR must be an explicit positive integer")
        hex_sha(entry["source_commit"], 40)
        hex_sha(entry["source_blob_sha"], 40)
        origin_path = safe_path(entry["source_path"])
        if not origin_path.startswith(source_prefix):
            raise IntakeError("source path outside module's original ownership")
        identity = (module, origin_path)
        if identity in seen:
            raise IntakeError("duplicate source intake identity")
        seen.add(identity)
        modules.add(module)
        if state in ("staged", "refactored"):
            destination = safe_path(entry["destination_path"])
            if not destination.startswith(dest_prefix) or destination in staged:
                raise IntakeError("duplicate or cross-module destination")
            sha256 = hex_sha(entry["content_sha256"], 64)
            if state == "refactored":
                original_sha = hex_sha(entry["source_content_sha256"], 64)
                if original_sha == sha256:
                    raise IntakeError("refactored content must differ from exact upstream copy")
                note = safe_path(entry["review_note"])
                if not note.startswith("docs/decisions/"):
                    raise IntakeError("review note must live under docs/decisions")
                review_file = root / note
                if review_file.is_symlink() or not review_file.is_file():
                    raise IntakeError("review note is missing or unsafe")
                # Original blob and SHA are independently rechecked against
                # pinned GitHub upstream in a separate CI job.
                stage_file(root, destination, sha256)
            else:
                stage_file(root, destination, sha256, entry["source_blob_sha"])
            staged.add(destination)

    if modules != MODULES:
        raise IntakeError("missing mandatory module provenance")
    # A source file with no exact intake record is never silently adopted.
    # Documentation-only README scaffolds and branded assets are not runtime source.
    for prefix in ("core", "rental", "pisonet", "controllers"):
        directory = root / prefix
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise IntakeError("unexpected symlink in a component directory")
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            # Extensionless scripts remain runnable by a shell even without
            # an executable bit. Runtime command/init directories must never
            # permit unregistered files of any suffix or POSIX mode.
            runtime = any(
                f"/{name}/" in f"/{relative}"
                for name in ("usr/sbin", "usr/bin", "etc/init.d")
            )
            if (path.suffix.lower() not in SOURCE_SUFFIXES and
                    not (path.stat().st_mode & 0o111) and not runtime):
                continue
            if relative not in staged:
                raise IntakeError("unrecorded runtime source: " + relative)
    return len(entries), len(staged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, default=Path("inventory/source-intake.json"))
    args = parser.parse_args()
    try:
        count, staged = audit(args.root, args.manifest)
    except (IntakeError, OSError) as error:
        print("SOURCE_INTAKE_DENIED:", error, file=sys.stderr)
        return 1
    print(f"SOURCE_INTAKE_PASS: {count} pinned candidate/file records; "
          f"{staged} locally staged source files; production NO-GO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
