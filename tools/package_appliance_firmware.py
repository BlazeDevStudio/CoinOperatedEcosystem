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


def build_imagebuilder_cmd(profile: dict, files_dir: str) -> str:
    """Construct exact OpenWrt ImageBuilder command."""
    arch = profile["target_architecture"]
    profile_id = profile["profile_id"]
    all_packages = RECOMMENDED_PACKAGES + EXCLUDED_PACKAGES
    pkg_str = " ".join(all_packages)
    return f"make image PROFILE={profile_id} PACKAGES=\"{pkg_str}\" FILES=\"{files_dir}\""


def stage_overlay(profile: dict, source_rootfs: str, staging_dir: str) -> dict:
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
                # Executable for scripts, cgi-bin, init.d
                if "/cgi-bin/" in fp or "/init.d/" in fp or "/usr/sbin/" in fp or fp.endswith(".sh"):
                    os.chmod(fp, 0o755)
                else:
                    os.chmod(fp, 0o644)

    return {
        "profile_id": profile["profile_id"],
        "target_architecture": profile["target_architecture"],
        "overlay_size_kb": size_kb,
        "flash_kb": flash_kb,
        "staging_dir": staging_dir,
        "imagebuilder_command": build_imagebuilder_cmd(profile, staging_dir)
    }


def main():
    parser = argparse.ArgumentParser(description="Package OpenWrt appliance firmware overlay.")
    parser.add_argument("--profile", required=True, help="Profile ID (e.g., ew1200g-pro, r281, orangepi-r1-plus-lts, x86_64) or JSON path")
    parser.add_argument("--rootfs", default=DEFAULT_ROOTFS, help="Source rootfs directory")
    parser.add_argument("--output", required=True, help="Destination staging directory")
    args = parser.parse_args()

    try:
        profile = load_profile(args.profile)
        manifest = stage_overlay(profile, args.rootfs, args.output)
        print(f"Appliance firmware staged successfully for '{manifest['profile_id']}':")
        print(f"  Target Arch:    {manifest['target_architecture']}")
        print(f"  Overlay Size:   {manifest['overlay_size_kb']} KB / {manifest['flash_kb']} KB")
        print(f"  Staging Dir:    {manifest['staging_dir']}")
        print(f"  ImageBuilder:   {manifest['imagebuilder_command']}")
    except Exception as e:
        print(f"Error packaging appliance firmware: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
