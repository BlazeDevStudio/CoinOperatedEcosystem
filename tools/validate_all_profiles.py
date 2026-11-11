#!/usr/bin/env python3
"""End-to-End Appliance Profile and Firmware Staging Validator.

Validates that all target hardware profiles in Shared/contracts/router-profile/profiles/
can be successfully packaged with and without the BlazeRental module, produce valid
network topologies, satisfy flash bounds, and emit executable ImageBuilder build scripts.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(BASE_DIR, "Shared", "contracts", "router-profile", "profiles")
ROOTFS_DIR = os.path.join(BASE_DIR, "Pisowifi", "openwrt", "rootfs")
RENTAL_DIR = os.path.join(BASE_DIR, "Rental", "openwrt")
DIAG_SCRIPT = os.path.join(ROOTFS_DIR, "usr", "sbin", "blaze-appliance-diag")

# Import packaging primitives
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))
from package_appliance_firmware import load_profile, stage_overlay, generate_build_script


def validate_profile(profile_path: str, temp_base: str) -> dict:
    profile = load_profile(profile_path)
    pid = profile["profile_id"]
    arch = profile["target_architecture"]
    flash_kb = profile["hardware"]["flash_kb"]
    min_overlay_kb = profile["hardware"]["min_free_overlay_kb"]

    # 1. Stage without rental
    stage_no_rental = os.path.join(temp_base, f"stage_{pid}_standalone")
    manifest_standalone = stage_overlay(profile, ROOTFS_DIR, stage_no_rental, include_rental=False)

    size_standalone = manifest_standalone["overlay_size_kb"]
    if size_standalone > (flash_kb - min_overlay_kb):
        raise ValueError(f"Standalone overlay size {size_standalone} KB exceeds flash budget for {pid}")

    # Verify staged files
    staged_profile = os.path.join(stage_no_rental, "etc", "blazepwifi", "appliance_profile.json")
    if not os.path.isfile(staged_profile):
        raise FileNotFoundError(f"Missing staged appliance profile in {staged_profile}")

    network_uci = os.path.join(stage_no_rental, "etc", "config", "network")
    with open(network_uci, "r", encoding="utf-8") as f:
        net_content = f.read()
    if "config device 'br_lan'" not in net_content:
        raise ValueError(f"Staged network UCI missing br_lan bridge for {pid}")

    # Verify build script emission
    script_standalone = os.path.join(temp_base, f"build_{pid}.sh")
    generate_build_script(manifest_standalone, script_standalone)
    if not os.path.isfile(script_standalone):
        raise FileNotFoundError(f"Build script not created for {pid}")
    if not bool(os.stat(script_standalone).st_mode & stat.S_IXUSR):
        raise PermissionError(f"Build script not executable for {pid}")
    with open(script_standalone, "r", encoding="utf-8") as f:
        script_content = f.read()
    if f"PROFILE={pid}" not in script_content:
        raise ValueError(f"Build script missing PROFILE={pid}")

    # 2. Stage with rental
    stage_rental = os.path.join(temp_base, f"stage_{pid}_rental")
    manifest_rental = stage_overlay(profile, ROOTFS_DIR, stage_rental, include_rental=True, rental_source_dir=RENTAL_DIR)

    size_rental = manifest_rental["overlay_size_kb"]
    if size_rental > (flash_kb - min_overlay_kb):
        raise ValueError(f"Rental bundle overlay size {size_rental} KB exceeds flash budget for {pid}")

    # Verify rental components
    for path, is_exec in [
        (os.path.join(stage_rental, "usr", "lib", "blazerental", "core.sh"), False),
        (os.path.join(stage_rental, "usr", "sbin", "blazerentalctl"), True),
        (os.path.join(stage_rental, "www", "cgi-bin", "blazerental"), True)
    ]:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Missing rental component: {path}")
        if is_exec and not bool(os.stat(path).st_mode & stat.S_IXUSR):
            raise PermissionError(f"Rental binary not executable: {path}")

    # 3. Test runtime diagnostics mock run on staged overlay
    env = os.environ.copy()
    env["BLAZE_ROOT"] = stage_rental
    env["SYSINFO_MODEL"] = profile["name"]
    env["SYSINFO_BOARD"] = pid
    res = subprocess.run(
        ["sh", DIAG_SCRIPT, "--json"],
        capture_output=True,
        text=True,
        env=env
    )
    if res.returncode != 0:
        raise RuntimeError(f"blaze-appliance-diag failed for {pid}: {res.stderr}\n{res.stdout}")

    diag_data = json.loads(res.stdout)
    if diag_data["profile"]["profile_id"] != pid:
        raise ValueError(f"Diag profile mismatch: expected {pid}, got {diag_data['profile']['profile_id']}")

    return {
        "profile_id": pid,
        "name": profile["name"],
        "architecture": arch,
        "flash_kb": flash_kb,
        "standalone_kb": size_standalone,
        "rental_bundle_kb": size_rental,
        "diag_status": diag_data["profile"]["status"]
    }


def main():
    if not os.path.isdir(PROFILES_DIR):
        print(f"ERROR: Profiles directory not found: {PROFILES_DIR}", file=sys.stderr)
        sys.exit(1)

    profile_files = sorted([f for f in os.listdir(PROFILES_DIR) if f.endswith(".json")])
    if not profile_files:
        print("ERROR: No profile files found", file=sys.stderr)
        sys.exit(1)

    temp_base = tempfile.mkdtemp(prefix="appliance_validation_")
    results = []
    failed = False

    print(f"=== Validating {len(profile_files)} Hardware Appliance Profiles ===")
    try:
        for pf in profile_files:
            profile_path = os.path.join(PROFILES_DIR, pf)
            try:
                res = validate_profile(profile_path, temp_base)
                results.append(res)
                print(f"  [PASS] {res['profile_id']:<24} {res['architecture']:<18} "
                      f"Standalone: {res['standalone_kb']}KB | Rental: {res['rental_bundle_kb']}KB | Diag: {res['diag_status']}")
            except Exception as e:
                failed = True
                print(f"  [FAIL] {pf}: {e}", file=sys.stderr)
    finally:
        shutil.rmtree(temp_base, ignore_errors=True)

    print("\n=== Appliance Packaging & Diagnostics Summary ===")
    print(f"Total Profiles Tested: {len(profile_files)}")
    print(f"Successful Validations: {len(results)}")
    print(f"Failures: {len(profile_files) - len(results)}")

    if failed:
        sys.exit(1)
    print("ALL HARDWARE APPLIANCE PROFILES VALIDATED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
