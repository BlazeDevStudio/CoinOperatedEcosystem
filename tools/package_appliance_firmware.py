#!/usr/bin/env python3
"""Appliance Firmware Packager and ImageBuilder Configurator for Coin-Operated Ecosystem.

Generates validated OpenWrt rootfs overlays and ImageBuilder profiles for turnkey hardware bundles:
- Ruijie RG-EW1200G Pro v1.1 (MediaTek MT7621 DSA switch)
- Notion R281 (MediaTek MT7621)
- Orange Pi R1 Plus LTS (Rockchip RK3328 arm64)
- Generic x86_64 Mini PC
"""
import argparse
import json
import os
import shutil
import stat
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_PROFILES_DIR = os.path.join(BASE_DIR, "Shared", "contracts", "router-profile", "profiles")
DEFAULT_ROOTFS = os.path.join(BASE_DIR, "Pisowifi", "openwrt", "rootfs")
DEFAULT_RENTAL_DIR = os.path.join(BASE_DIR, "Rental", "openwrt")

RENTAL_PACKAGES = [
    "openssl-util",
    "coreutils-date"
]

RECOMMENDED_PACKAGES = [
    "nftables",
    "kmod-nft-core",
    "kmod-nft-nat",
    "kmod-nft-offload",
    "firewall4",
    "uhttpd",
    "uhttpd-mod-ubus",
    "curl",
    "jq",
    "coreutils-sha256sum",
    "ca-bundle",
    "libustream-mbedtls"
]

EXCLUDED_PACKAGES = [
    "-iptables",
    "-ip6tables",
    "-firewall",
    "-dnsmasq",
    "dnsmasq-full"
]


def load_profile(profile_id_or_path: str) -> dict:
    if os.path.isfile(profile_id_or_path):
        path = profile_id_or_path
    else:
        path = os.path.join(SHARED_PROFILES_DIR, f"{profile_id_or_path}.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Router profile not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_network_uci(profile: dict) -> str:
    """Generate OpenWrt /etc/config/network with DSA/bridge VLAN isolation."""
    net = profile["networking"]
    lan_vlan = net["default_vlan_ids"]["lan"]
    guest_vlan = net["default_vlan_ids"]["guest"]
    vendo_vlan = net["default_vlan_ids"]["vendo"]

    out = [
        "config interface 'loopback'",
        "\toption device 'lo'",
        "\toption proto 'static'",
        "\toption ipaddr '127.0.0.1'",
        "\toption netmask '255.0.0.0'",
        "",
        "config globals 'globals'",
        "\toption ula_prefix 'fd00:db8:blaze::/48'",
        "",
        "config device 'br_lan'",
        "\toption name 'br-lan'",
        "\toption type 'bridge'",
    ]

    # Handle DSA vs generic switch bridge ports
    ports = [p["interface"] for p in net["ports"] if p["interface"] != net["wan_interface"]]
    if ports:
        out.append(f"\tlist ports '{' '.join(ports)}'")

    if net.get("vlan_supported", False):
        out.append("\toption vlan_filtering '1'")

    out.extend([
        "",
        "config interface 'lan'",
        "\toption device 'br-lan'",
        "\toption proto 'static'",
        "\toption ipaddr '10.0.0.1'",
        "\toption netmask '255.255.255.0'",
        "",
        "config interface 'guest'",
        f"\toption device 'br-lan.{guest_vlan}'",
        "\toption proto 'static'",
        "\toption ipaddr '10.10.0.1'",
        "\toption netmask '255.255.255.0'",
        "",
        "config interface 'vendo'",
        f"\toption device 'br-lan.{vendo_vlan}'",
        "\toption proto 'static'",
        "\toption ipaddr '10.20.0.1'",
        "\toption netmask '255.255.255.0'",
        "",
        "config interface 'wan'",
        f"\toption device '{net['wan_interface']}'",
        "\toption proto 'dhcp'",
        "",
    ])

    return "\n".join(out)


def calculate_overlay_size(staging_dir: str) -> int:
    """Calculate total size of overlay in kilobytes."""
    total_bytes = 0
    for root, _, files in os.walk(staging_dir):
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp):
                total_bytes += os.path.getsize(fp)
    return (total_bytes + 1023) // 1024


def build_imagebuilder_cmd(profile: dict, files_dir: str, include_rental: bool = False) -> str:
    """Construct exact OpenWrt ImageBuilder command."""
    arch = profile["target_architecture"]
    profile_id = profile["profile_id"]
    packages = list(RECOMMENDED_PACKAGES)
    if include_rental:
        packages.extend(RENTAL_PACKAGES)
    all_packages = packages + EXCLUDED_PACKAGES
    pkg_str = " ".join(all_packages)
    return f"make image PROFILE={profile_id} PACKAGES=\"{pkg_str}\" FILES=\"{files_dir}\""


def stage_overlay(profile: dict, source_rootfs: str, staging_dir: str, include_rental: bool = False, rental_source_dir: str = DEFAULT_RENTAL_DIR) -> dict:
    """Stage and customize the rootfs overlay for the target profile."""
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    shutil.copytree(source_rootfs, staging_dir, symlinks=True)

    # Inject profile-tailored network configuration
    etc_config = os.path.join(staging_dir, "etc", "config")
    os.makedirs(etc_config, exist_ok=True)
    with open(os.path.join(etc_config, "network"), "w", encoding="utf-8") as f:
        f.write(generate_network_uci(profile))

    # Save target profile specification into appliance metadata
    etc_blaze = os.path.join(staging_dir, "etc", "blazepwifi")
    os.makedirs(etc_blaze, exist_ok=True)
    with open(os.path.join(etc_blaze, "appliance_profile.json"), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    # Optionally bundle BlazeRental module for unified appliance bundles
    if include_rental:
        if not os.path.isdir(rental_source_dir):
            raise FileNotFoundError(f"Rental source directory not found: {rental_source_dir}")

        # usr/lib/blazerental/core.sh
        rental_lib = os.path.join(staging_dir, "usr", "lib", "blazerental")
        os.makedirs(rental_lib, exist_ok=True)
        shutil.copy2(os.path.join(rental_source_dir, "lib", "core.sh"), os.path.join(rental_lib, "core.sh"))

        # usr/sbin/blazerentalctl
        rental_sbin = os.path.join(staging_dir, "usr", "sbin")
        os.makedirs(rental_sbin, exist_ok=True)
        shutil.copy2(os.path.join(rental_source_dir, "bin", "blazerentalctl"), os.path.join(rental_sbin, "blazerentalctl"))

        # www/cgi-bin/blazerental
        rental_cgi = os.path.join(staging_dir, "www", "cgi-bin")
        os.makedirs(rental_cgi, exist_ok=True)
        shutil.copy2(os.path.join(rental_source_dir, "cgi-bin", "blazerental"), os.path.join(rental_cgi, "blazerental"))

        # etc/blazerental
        rental_etc = os.path.join(staging_dir, "etc", "blazerental")
        os.makedirs(rental_etc, exist_ok=True)
        os.chmod(rental_etc, 0o700)

    # Calculate overlay size and verify flash constraints
    size_kb = calculate_overlay_size(staging_dir)
    flash_kb = profile["hardware"]["flash_kb"]
    min_overlay_kb = profile["hardware"]["min_free_overlay_kb"]
    max_overlay_budget_kb = flash_kb - min_overlay_kb

    if size_kb > max_overlay_budget_kb:
        raise ValueError(
            f"Overlay size ({size_kb} KB) exceeds flash budget ({max_overlay_budget_kb} KB) "
            f"for profile '{profile['profile_id']}'"
        )

    # Set strict filesystem permissions
    for root, dirs, files in os.walk(staging_dir):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp):
                # Executable for scripts, cgi-bin, sbin, init.d
                if "/cgi-bin/" in fp or "/init.d/" in fp or "/usr/sbin/" in fp or fp.endswith(".sh"):
                    os.chmod(fp, 0o755)
                else:
                    os.chmod(fp, 0o644)

    return {
        "profile_id": profile["profile_id"],
        "target_architecture": profile["target_architecture"],
        "overlay_size_kb": size_kb,
        "flash_kb": flash_kb,
        "include_rental": include_rental,
        "staging_dir": staging_dir,
        "imagebuilder_command": build_imagebuilder_cmd(profile, staging_dir, include_rental=include_rental)
    }


def generate_build_script(manifest: dict, script_path: str) -> None:
    """Emit an executable shell script to run ImageBuilder and generate SHA-256 release checksums."""
    profile_id = manifest["profile_id"]
    target_arch = manifest["target_architecture"]
    cmd = manifest["imagebuilder_command"]
    staging_dir = os.path.abspath(manifest["staging_dir"])
    target_prefix = target_arch.split("/")[0]

    content = f"""#!/bin/sh
# Auto-generated OpenWrt ImageBuilder wrapper for {profile_id} ({target_arch})
set -eu

BUILD_DIR="${{OPENWRT_IMAGEBUILDER_DIR:-$PWD}}"
if [ ! -f "$BUILD_DIR/Makefile" ]; then
    echo "ERROR: ImageBuilder Makefile not found in $BUILD_DIR" >&2
    echo "Set OPENWRT_IMAGEBUILDER_DIR to the extracted OpenWrt ImageBuilder root." >&2
    exit 1
fi

echo "=== Building Appliance Firmware for {profile_id} ==="
cd "$BUILD_DIR"
{cmd}

echo "=== Verifying Built Firmware Binaries & Generating Manifest ==="
BIN_DIR="$BUILD_DIR/bin/targets/{target_prefix}"
if [ -d "$BIN_DIR" ]; then
    find "$BIN_DIR" -type f \\( -name "*.bin" -o -name "*.img.gz" \\) -exec sha256sum {{}} + > "$BUILD_DIR/RELEASE_MANIFEST.sha256"
    echo "Release manifest written to $BUILD_DIR/RELEASE_MANIFEST.sha256"
    cat "$BUILD_DIR/RELEASE_MANIFEST.sha256"
fi
echo "Appliance build completed successfully."
"""
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(script_path, 0o755)


def main():
    parser = argparse.ArgumentParser(description="Package OpenWrt appliance firmware overlay.")
    parser.add_argument("--profile", required=True, help="Profile ID (e.g., ew1200g-pro, r281, orangepi-r1-plus-lts, orangepi-zero3, archer-c6-v3, gl-mt1300, raspberrypi-4b, x86_64) or JSON path")
    parser.add_argument("--rootfs", default=DEFAULT_ROOTFS, help="Source rootfs directory")
    parser.add_argument("--rental-dir", default=DEFAULT_RENTAL_DIR, help="Rental source root directory")
    parser.add_argument("--include-rental", action="store_true", help="Bundle BlazeRental module into overlay")
    parser.add_argument("--emit-build-script", help="Path to write ImageBuilder runner shell script")
    parser.add_argument("--output", required=True, help="Destination staging directory")
    args = parser.parse_args()

    try:
        profile = load_profile(args.profile)
        manifest = stage_overlay(profile, args.rootfs, args.output, include_rental=args.include_rental, rental_source_dir=args.rental_dir)
        print(f"Appliance firmware staged successfully for '{manifest['profile_id']}':")
        print(f"  Target Arch:    {manifest['target_architecture']}")
        print(f"  Overlay Size:   {manifest['overlay_size_kb']} KB / {manifest['flash_kb']} KB")
        print(f"  Include Rental: {manifest['include_rental']}")
        print(f"  Staging Dir:    {manifest['staging_dir']}")
        print(f"  ImageBuilder:   {manifest['imagebuilder_command']}")

        if args.emit_build_script:
            generate_build_script(manifest, args.emit_build_script)
            print(f"  Build Script:   {args.emit_build_script}")
    except Exception as e:
        print(f"Error packaging appliance firmware: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

