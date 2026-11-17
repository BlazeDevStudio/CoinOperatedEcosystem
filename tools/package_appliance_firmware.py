#!/usr/bin/env python3
"""Appliance Firmware Packager and ImageBuilder Configurator for Coin-Operated Ecosystem.

Generates validated OpenWrt rootfs overlays and ImageBuilder profiles for turnkey hardware bundles:
- Ruijie RG-EW1200G Pro v1.1 (MediaTek MT7621 DSA switch)
- Notion R281 (MediaTek MT7621)
- Orange Pi R1 Plus LTS (Rockchip RK3328 arm64)
- Generic x86_64 Mini PC
"""
import argparse
import errno
import json
import os
import shutil
import shlex
import stat
import sys
import re

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


def _validate_uci_interface(value, field_name: str) -> str:
    """Accept only Linux interface-name characters before writing UCI syntax."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", value):
        raise ValueError(f"Invalid network interface for {field_name}: {value!r}")
    return value


def _validate_uci_vlan_id(value, field_name: str) -> int:
    """Require a real 802.1Q VLAN ID before interpolating it into a device name."""
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 4094:
        raise ValueError(f"Invalid VLAN ID for {field_name}: {value!r}")
    return value


def generate_network_uci(profile: dict) -> str:
    """Generate OpenWrt /etc/config/network with DSA/bridge VLAN isolation."""
    net = profile["networking"]
    vlan_ids = net.get("default_vlan_ids")
    if not isinstance(vlan_ids, dict):
        raise ValueError("Invalid default VLAN ID mapping")

    lan_vlan = _validate_uci_vlan_id(vlan_ids.get("lan"), "lan")
    guest_vlan = _validate_uci_vlan_id(vlan_ids.get("guest"), "guest")
    vendo_vlan = _validate_uci_vlan_id(vlan_ids.get("vendo"), "vendo")
    wan_interface = _validate_uci_interface(net.get("wan_interface"), "wan_interface")

    raw_ports = net.get("ports")
    if not isinstance(raw_ports, list):
        raise ValueError("Invalid network ports list")
    ports = []
    for index, port in enumerate(raw_ports):
        if not isinstance(port, dict):
            raise ValueError(f"Invalid network port entry at index {index}")
        interface = _validate_uci_interface(
            port.get("interface"), f"ports[{index}].interface"
        )
        if interface != wan_interface:
            ports.append(interface)

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
        f"\toption device '{wan_interface}'",
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
    return "make image PROFILE={} PACKAGES={} FILES={}".format(
        shlex.quote(profile_id),
        shlex.quote(pkg_str),
        shlex.quote(os.path.abspath(files_dir)),
    )


def _ensure_staging_directory(staging_dir: str, relative_path: str) -> str:
    """Create a real directory chain beneath staging without traversing copied symlinks."""
    current = staging_dir
    for component in relative_path.split("/"):
        if component in ("", ".", ".."):
            raise ValueError(f"Invalid staged directory component: {component!r}")
        current = os.path.join(current, component)
        try:
            os.mkdir(current)
        except FileExistsError:
            pass
        mode = os.lstat(current).st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ValueError(
                f"Refusing symlink or non-directory in staged configuration path: {current}"
            )
    return current


def _write_staging_bytes(directory: str, filename: str, content: bytes) -> None:
    """Write a staged file without following a copied final-component symlink."""
    path = os.path.join(directory, filename)
    try:
        existing_mode = os.lstat(path).st_mode
    except FileNotFoundError:
        existing_mode = None
    if existing_mode is not None and not stat.S_ISREG(existing_mode):
        raise ValueError(
            f"Refusing symlink or non-regular staged file destination: {path}"
        )

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    flags |= getattr(os, "O_NOFOLLOW", 0)
    file_fd = os.open(path, flags, 0o644)
    with os.fdopen(file_fd, "wb") as staged_file:
        staged_file.write(content)


def _write_staging_file(directory: str, filename: str, content: str) -> None:
    """Write UTF-8 staged configuration without following copied symlinks."""
    _write_staging_bytes(directory, filename, content.encode("utf-8"))


def _copy_staging_file(source_path: str, directory: str, filename: str) -> None:
    """Copy a regular source file into a verified staging directory safely."""
    source_mode = os.lstat(source_path).st_mode
    if not stat.S_ISREG(source_mode):
        raise ValueError(f"Refusing symlink or non-regular rental source file: {source_path}")
    with open(source_path, "rb") as source_file:
        _write_staging_bytes(directory, filename, source_file.read())


def stage_overlay(profile: dict, source_rootfs: str, staging_dir: str, include_rental: bool = False, rental_source_dir: str = DEFAULT_RENTAL_DIR) -> dict:
    """Stage the rootfs into a fresh, isolated destination without deleting existing data."""
    source_rootfs = os.path.realpath(os.path.abspath(source_rootfs))
    requested_staging_dir = os.path.abspath(staging_dir)
    if not os.path.isdir(source_rootfs):
        raise FileNotFoundError(f"Source rootfs directory not found: {source_rootfs}")
    # lexists catches dangling symlinks too; never remove or follow an operator path.
    if os.path.lexists(requested_staging_dir):
        raise FileExistsError(
            f"Staging destination already exists; refusing to overwrite or delete: {requested_staging_dir}"
        )
    staging_dir = os.path.realpath(requested_staging_dir)
    if os.path.lexists(staging_dir):
        raise FileExistsError(
            f"Resolved staging destination already exists; refusing to overwrite or delete: {staging_dir}"
        )
    try:
        shared_path = os.path.commonpath((source_rootfs, staging_dir))
    except ValueError:
        shared_path = None
    if shared_path in (source_rootfs, staging_dir):
        raise ValueError(
            "Staging destination must be separate from and outside the source rootfs"
        )
    shutil.copytree(source_rootfs, staging_dir, symlinks=True)

    # Inject generated configuration only through real directories and regular files.
    # copytree preserves symlinks; following one here could overwrite data outside staging.
    etc_config = _ensure_staging_directory(staging_dir, "etc/config")
    _write_staging_file(etc_config, "network", generate_network_uci(profile))

    # Save target profile specification into appliance metadata
    etc_blaze = _ensure_staging_directory(staging_dir, "etc/blazepwifi")
    _write_staging_file(etc_blaze, "appliance_profile.json", json.dumps(profile, indent=2))

    # Optionally bundle BlazeRental module for unified appliance bundles
    if include_rental:
        if not os.path.isdir(rental_source_dir):
            raise FileNotFoundError(f"Rental source directory not found: {rental_source_dir}")

        # usr/lib/blazerental/core.sh
        rental_lib = _ensure_staging_directory(staging_dir, "usr/lib/blazerental")
        _copy_staging_file(
            os.path.join(rental_source_dir, "lib", "core.sh"), rental_lib, "core.sh"
        )

        # usr/sbin/blazerentalctl
        rental_sbin = _ensure_staging_directory(staging_dir, "usr/sbin")
        _copy_staging_file(
            os.path.join(rental_source_dir, "bin", "blazerentalctl"),
            rental_sbin,
            "blazerentalctl",
        )

        # www/cgi-bin/blazerental
        rental_cgi = _ensure_staging_directory(staging_dir, "www/cgi-bin")
        _copy_staging_file(
            os.path.join(rental_source_dir, "cgi-bin", "blazerental"),
            rental_cgi,
            "blazerental",
        )

        # etc/blazerental
        rental_etc = _ensure_staging_directory(staging_dir, "etc/blazerental")
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
            directory_path = os.path.join(root, d)
            # os.walk lists directory symlinks in dirs even when it will not
            # recurse into them. chmod follows symlinks by default, so skip
            # them to avoid changing permissions outside the staging tree.
            if not os.path.islink(directory_path):
                os.chmod(directory_path, 0o755)
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
        "imagebuilder_command": build_imagebuilder_cmd(profile, os.path.abspath(staging_dir), include_rental=include_rental)
    }



def _open_new_file_without_symlink_parents(path: str, flags: int, mode: int) -> int:
    """Create a new file through a descriptor chain that never follows parent symlinks."""
    if (
        os.name != "posix"
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or os.open not in getattr(os, "supports_dir_fd", set())
    ):
        raise OSError(
            "Safe build-script creation requires POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support"
        )

    absolute_path = os.path.abspath(path)
    parent_path, filename = os.path.split(absolute_path)
    if filename in ("", ".", ".."):
        raise ValueError("Invalid build-script output filename")

    directory_fd = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # Walk from the filesystem root one component at a time. O_NOFOLLOW
        # protects every parent component, not only the final output filename.
        for component in parent_path.split(os.sep):
            if not component:
                continue
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise ValueError(
                        f"Build script parent path contains a symlink or non-directory: {parent_path}"
                    ) from exc
                raise
            os.close(directory_fd)
            directory_fd = next_fd

        return os.open(
            filename,
            flags | os.O_NOFOLLOW,
            mode,
            dir_fd=directory_fd,
        )
    finally:
        os.close(directory_fd)


def generate_build_script(manifest: dict, script_path: str) -> None:
    """Emit an executable shell script to run ImageBuilder and generate SHA-256 release checksums."""
    profile_id = manifest["profile_id"]
    target_arch = manifest["target_architecture"]
    cmd = manifest["imagebuilder_command"]
    staging_dir = os.path.abspath(manifest["staging_dir"])
    # Do not interpolate an untrusted/custom JSON profile into shell syntax.
    if not re.fullmatch(r"[A-Za-z0-9._-]+", profile_id):
        raise ValueError("Invalid ImageBuilder profile ID")
    if not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", target_arch):
        raise ValueError("Invalid ImageBuilder target/subtarget")
    # This absolute path remains valid after the wrapper changes into ImageBuilder.
    stage_arg = shlex.quote(staging_dir)

    content = f"""#!/bin/sh
# Auto-generated nonproduction ImageBuilder wrapper for {profile_id} ({target_arch})
# A checksum is not hardware or financial release acceptance.
set -eu
# Refuse shell redirections to paths created after the preflight checks.
# This protects both checksum-manifest paths from symlink substitution by the builder.
set -C

BUILD_DIR="${{OPENWRT_IMAGEBUILDER_DIR:-$PWD}}"
# Normalize relative workspace overrides before deriving paths or changing directories.
case "$BUILD_DIR" in
    /*) ;;
    *) BUILD_DIR="$(pwd -P)/$BUILD_DIR" ;;
esac
STAGING_DIR={stage_arg}
if [ ! -f "$BUILD_DIR/Makefile" ]; then
    echo "RELEASE-BLOCKED: ImageBuilder Makefile not found in $BUILD_DIR" >&2
    exit 1
fi
if [ ! -d "$STAGING_DIR" ]; then
    echo "RELEASE-BLOCKED: staged rootfs not found: $STAGING_DIR" >&2
    exit 1
fi

# A reused ImageBuilder may report success without writing a new binary.
# Never certify files or a checksum manifest left by an earlier invocation.
# Refuse stale data without deleting or modifying an operator's files.
BIN_DIR="$BUILD_DIR/bin/targets/{target_arch}"
OUT_MANIFEST="$BUILD_DIR/RELEASE_MANIFEST.sha256"
TMP_MANIFEST="$BUILD_DIR/RELEASE_MANIFEST.sha256.tmp"

# ImageBuilder writes directly below bin/targets. Never let an existing
# symlinked target path redirect build output outside this workspace.
IMAGE_PATH="$BUILD_DIR"
for IMAGE_COMPONENT in bin targets {target_arch.replace("/", " ")}; do
    IMAGE_PATH="$IMAGE_PATH/$IMAGE_COMPONENT"
    if [ -L "$IMAGE_PATH" ]; then
        echo "RELEASE-BLOCKED: symlinked ImageBuilder output directory: $IMAGE_PATH" >&2
        exit 1
    fi
done
if [ -e "$TMP_MANIFEST" ] || [ -L "$TMP_MANIFEST" ]; then
    echo "RELEASE-BLOCKED: previous temporary release manifest exists: $TMP_MANIFEST; use a clean ImageBuilder workspace" >&2
    exit 1
fi
if [ -e "$OUT_MANIFEST" ] || [ -L "$OUT_MANIFEST" ]; then
    echo "RELEASE-BLOCKED: previous release manifest exists: $OUT_MANIFEST; use a clean ImageBuilder workspace" >&2
    exit 1
fi
if [ -d "$BIN_DIR" ]; then
    PRIOR_SYMLINK_IMAGE=$(find "$BIN_DIR" -type l \\( -name "*.bin" -o -name "*.img.gz" \\) -print -quit)
    if [ -n "$PRIOR_SYMLINK_IMAGE" ]; then
        echo "RELEASE-BLOCKED: stale symlinked firmware images exist: $PRIOR_SYMLINK_IMAGE; use a clean ImageBuilder workspace" >&2
        exit 1
    fi
    # Reject every pre-existing symlink in the target tree before invoking
    # ImageBuilder. A nested link with an arbitrary name can redirect Makefile
    # writes outside this workspace before the post-build scan runs.
    PRIOR_SYMLINK_ENTRY=$(find "$BIN_DIR" -type l -print -quit)
    if [ -n "$PRIOR_SYMLINK_ENTRY" ]; then
        echo "RELEASE-BLOCKED: pre-existing symlink entry in ImageBuilder output tree: $PRIOR_SYMLINK_ENTRY" >&2
        exit 1
    fi
    PRIOR_IMAGE=$(find "$BIN_DIR" -type f \\( -name "*.bin" -o -name "*.img.gz" \\) -print -quit)
    if [ -n "$PRIOR_IMAGE" ]; then
        echo "RELEASE-BLOCKED: stale firmware images exist: $PRIOR_IMAGE; use a clean ImageBuilder workspace" >&2
        exit 1
    fi
fi

echo "=== Building Appliance Firmware for {profile_id} ==="
cd "$BUILD_DIR"
{cmd}

echo "=== Verifying Built Firmware Binaries & Generating Manifest ==="
IMAGE_REL_DIR="bin/targets/{target_arch}"
if [ ! -d "$IMAGE_REL_DIR" ]; then
    echo "RELEASE-BLOCKED: target/subtarget image directory missing: $BUILD_DIR/$IMAGE_REL_DIR" >&2
    exit 1
fi

# Reject every symlink in the output tree. find does not descend symlinked
# directories, so checking only firmware-named links can hide nested images
# from the checksum manifest while leaving them in the output tree.
SYMLINK_ENTRY=$(find "$IMAGE_REL_DIR" -type l -print -quit)
if [ -n "$SYMLINK_ENTRY" ]; then
    echo "RELEASE-BLOCKED: symlinked entry in firmware output tree: $SYMLINK_ENTRY" >&2
    exit 1
fi

EMPTY_IMAGE=$(find "$IMAGE_REL_DIR" -type f \\( -name "*.bin" -o -name "*.img.gz" \\) -size 0 -print -quit)\nif [ -n "$EMPTY_IMAGE" ]; then\n    echo "RELEASE-BLOCKED: empty firmware image: $EMPTY_IMAGE" >&2\n    exit 1\nfi\nfind "$IMAGE_REL_DIR" -type f \\( -name "*.bin" -o -name "*.img.gz" \\) -exec sha256sum {{}} + > "$TMP_MANIFEST"
if [ ! -s "$TMP_MANIFEST" ]; then
    rm -f "$TMP_MANIFEST"
    echo "RELEASE-BLOCKED: no firmware images found for {target_arch}" >&2
    exit 1
fi
LC_ALL=C sort "$TMP_MANIFEST" > "$BUILD_DIR/RELEASE_MANIFEST.sha256"
rm -f "$TMP_MANIFEST"
echo "Release manifest written to $BUILD_DIR/RELEASE_MANIFEST.sha256 (PREVIEW ONLY)"
cat "$BUILD_DIR/RELEASE_MANIFEST.sha256"
echo "Appliance PREVIEW build completed; physical/signing gates still NO-GO."
"""

    # Create exclusively: never truncate an operator-owned file or follow a
    # final-component symlink when the requested output path already exists.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        script_fd = _open_new_file_without_symlink_parents(script_path, flags, 0o755)
    except FileExistsError:
        raise FileExistsError(
            f"Build script destination already exists; refusing to overwrite: {script_path}"
        ) from None

    with os.fdopen(script_fd, "w", encoding="utf-8") as f:
        if hasattr(os, "fchmod"):
            os.fchmod(f.fileno(), 0o755)
        f.write(content)
    if not hasattr(os, "fchmod"):
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

