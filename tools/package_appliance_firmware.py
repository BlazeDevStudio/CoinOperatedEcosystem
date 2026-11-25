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
import hashlib
import ipaddress
import json
import os
import shutil
import shlex
import stat
import sys
import re
import secrets

from run_imagebuilder_sandbox import DEFAULT_BUILD_TIMEOUT_SECONDS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_PROFILES_DIR = os.path.join(BASE_DIR, "Shared", "contracts", "router-profile", "profiles")
TRUSTED_SYSTEM_PATH = "/usr/bin:/bin"
DEFAULT_ROOTFS = os.path.join(BASE_DIR, "Pisowifi", "openwrt", "rootfs")
DEFAULT_RENTAL_DIR = os.path.join(BASE_DIR, "Rental", "openwrt")

# Bound untrusted/custom router profile input before JSON parsing.
MAX_PROFILE_BYTES = 1024 * 1024

# Intentionally unset until PHX-CORE/COE select a durable site-prefix authority
# and MASTER approves the provisioning contract. Never use a vendor or per-device fallback.
APPROVED_SITE_ULA_PREFIX = None

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


def _reject_duplicate_json_object_keys(pairs):
    """Reject ambiguous JSON objects instead of silently keeping the last duplicate key."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def load_profile(profile_id_or_path: str) -> dict:
    """Load a profile through no-follow descriptors; profile paths must be regular files."""
    try:
        requested_path = os.fspath(profile_id_or_path)
    except TypeError as exc:
        raise ValueError("Router profile must be a profile ID or filesystem path") from exc
    if not isinstance(requested_path, str) or not requested_path:
        raise ValueError("Router profile must be a non-empty profile ID or filesystem path")

    # Preserve the CLI's profile-ID or custom-JSON-path behavior. lexists()
    # deliberately recognizes a final symlink so the descriptor open below
    # rejects it instead of treating it as a profile ID.
    is_explicit_path = (
        os.path.lexists(requested_path)
        or bool(os.path.dirname(requested_path))
        or requested_path.lower().endswith(".json")
    )
    if is_explicit_path:
        path = os.path.abspath(requested_path)
    else:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", requested_path):
            raise ValueError(f"Invalid router profile ID: {requested_path!r}")
        path = os.path.join(SHARED_PROFILES_DIR, f"{requested_path}.json")

    profile_fd = -1
    try:
        profile_fd = _open_file_without_symlink_parents(
            path,
            os.O_RDONLY | getattr(os, "O_NONBLOCK", 0),
            0,
            "Router profile",
            "Safe profile loading requires POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support",
            "Invalid router profile path",
        )
        profile_stat = os.fstat(profile_fd)
        if not stat.S_ISREG(profile_stat.st_mode):
            raise ValueError(f"Router profile is not a regular file: {path}")
        if profile_stat.st_size > MAX_PROFILE_BYTES:
            raise ValueError(
                f"Router profile exceeds maximum allowed size ({MAX_PROFILE_BYTES} bytes): {path}"
            )

        with os.fdopen(profile_fd, "rb") as profile_file:
            profile_fd = -1
            content = profile_file.read(MAX_PROFILE_BYTES + 1)
            if len(content) > MAX_PROFILE_BYTES:
                raise ValueError(
                    f"Router profile exceeds maximum allowed size ({MAX_PROFILE_BYTES} bytes): {path}"
                )
            after_read_stat = os.fstat(profile_file.fileno())
            before_read_identity = (
                profile_stat.st_dev,
                profile_stat.st_ino,
                profile_stat.st_mode,
                profile_stat.st_nlink,
                profile_stat.st_size,
                profile_stat.st_mtime_ns,
                profile_stat.st_ctime_ns,
            )
            after_read_identity = (
                after_read_stat.st_dev,
                after_read_stat.st_ino,
                after_read_stat.st_mode,
                after_read_stat.st_nlink,
                after_read_stat.st_size,
                after_read_stat.st_mtime_ns,
                after_read_stat.st_ctime_ns,
            )
            if (
                after_read_identity != before_read_identity
                or len(content) != profile_stat.st_size
            ):
                raise ValueError(f"Router profile changed while reading: {path}")
            return json.loads(
                content.decode("utf-8"),
                object_pairs_hook=_reject_duplicate_json_object_keys,
            )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Router profile not found: {path}") from exc
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise ValueError(
                f"Refusing symlinked or non-directory router profile path: {path}"
            ) from exc
        raise
    finally:
        if profile_fd >= 0:
            _close_overlay_descriptors_preserving_primary(
                [("router profile", profile_fd)]
            )


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


def _validate_site_ula_prefix(value) -> str:
    """Require an explicitly approved site-scoped RFC 4193 ULA /48."""
    error = (
        "An approved site-scoped RFC 4193 ULA /48 is required; "
        "release packaging is blocked until the site-prefix authority is defined"
    )
    if not isinstance(value, str) or not value.strip():
        raise ValueError(error)
    try:
        network = ipaddress.IPv6Network(value, strict=True)
    except ValueError as exc:
        raise ValueError(error) from exc

    ula_space = ipaddress.IPv6Network("fd00::/8")
    address = network.network_address
    if (
        network.prefixlen != 48
        or not network.subnet_of(ula_space)
        or address.is_multicast
        or address.is_link_local
        or address.is_global
        or address.is_unspecified
    ):
        raise ValueError(error)
    return network.with_prefixlen


def generate_network_uci(profile: dict) -> str:
    """Generate OpenWrt /etc/config/network with DSA/bridge VLAN isolation."""
    ula_prefix = _validate_site_ula_prefix(APPROVED_SITE_ULA_PREFIX)
    net = profile["networking"]
    vlan_ids = net.get("default_vlan_ids")
    if not isinstance(vlan_ids, dict):
        raise ValueError("Invalid default VLAN ID mapping")

    lan_vlan = _validate_uci_vlan_id(vlan_ids.get("lan"), "lan")
    guest_vlan = _validate_uci_vlan_id(vlan_ids.get("guest"), "guest")
    vendo_vlan = _validate_uci_vlan_id(vlan_ids.get("vendo"), "vendo")
    if len({lan_vlan, guest_vlan, vendo_vlan}) != 3:
        raise ValueError("LAN, guest, and vendo VLAN IDs must be distinct")
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
        f"\toption ula_prefix '{ula_prefix}'",
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


def _close_overlay_descriptors_preserving_primary(descriptors):
    """Attempt every owned descriptor close without masking an active primary error."""
    primary_error = sys.exc_info()[1]
    close_errors = []
    cleanup_interruptions = []

    for label, descriptor in descriptors:
        try:
            os.close(descriptor)
        except OSError as exc:
            if exc.errno != errno.EBADF:
                close_errors.append((label, exc))
        except BaseException as exc:
            cleanup_interruptions.append((label, exc))

    if cleanup_interruptions:
        details = "; ".join(
            f"{label}: {type(exc).__name__}: {exc}"
            for label, exc in cleanup_interruptions
        )
        if close_errors:
            details += "; " + "; ".join(
                f"{label}: {type(exc).__name__}: {exc}"
                for label, exc in close_errors
            )

        if primary_error is not None:
            note = "Owned descriptor cleanup was interrupted: " + details
            if hasattr(primary_error, "add_note"):
                primary_error.add_note(note)
            else:
                try:
                    sys.stderr.write(note + "\\n")
                except OSError:
                    pass
            return

        interruption = cleanup_interruptions[0][1]
        if hasattr(interruption, "add_note"):
            interruption.add_note(
                "Additional owned descriptor cleanup failures: " + details
            )
        raise interruption

    if not close_errors:
        return

    details = "; ".join(
        f"{label}: {type(exc).__name__}: {exc}"
        for label, exc in close_errors
    )
    note = "Owned descriptor cleanup encountered close errors: " + details
    if primary_error is not None:
        if hasattr(primary_error, "add_note"):
            primary_error.add_note(note)
        else:
            try:
                sys.stderr.write(note + "\n")
            except OSError:
                pass
        return

    first_error = close_errors[0][1]
    if hasattr(first_error, "add_note") and len(close_errors) > 1:
        first_error.add_note(
            "Additional owned descriptor cleanup failures: "
            + "; ".join(
                f"{label}: {type(exc).__name__}: {exc}"
                for label, exc in close_errors[1:]
            )
        )
    raise first_error


def calculate_overlay_size(staging_dir: str) -> int:
    """Calculate overlay size through pinned no-follow directory/entry descriptors.

    Each directory stays pinned until its descendants are scanned. At exit,
    compare its entry names and the identities of every observed entry so an
    addition, removal, or replacement cannot silently change the size result.
    The staging-root name is revalidated through its pinned parent as well.
    """
    if (
        os.name != "posix"
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_PATH")
        or os.open not in getattr(os, "supports_dir_fd", set())
        or os.stat not in getattr(os, "supports_dir_fd", set())
        or os.stat not in getattr(os, "supports_follow_symlinks", set())
    ):
        raise OSError(
            "Safe overlay size calculation requires Linux O_PATH and POSIX "
            "dir_fd, O_DIRECTORY and O_NOFOLLOW support"
        )

    def directory_snapshot(metadata):
        return (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
        )

    def entry_snapshot(metadata):
        return (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_nlink,
            metadata.st_uid,
            metadata.st_gid,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )

    staging_root = os.path.abspath(staging_dir)
    parent_fd = -1
    root_fd = -1
    directory_stack = []
    total_bytes = 0
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    entry_flags = os.O_PATH | os.O_NOFOLLOW

    def check_root_name(opened_root):
        try:
            current_root = os.stat(
                root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise ValueError(
                f"Staging root changed during overlay size walk: {staging_root}"
            ) from exc
        if (
            not stat.S_ISDIR(current_root.st_mode)
            or (current_root.st_dev, current_root.st_ino)
            != (opened_root.st_dev, opened_root.st_ino)
        ):
            raise ValueError(
                f"Staging root changed during overlay size walk: {staging_root}"
            )

    def push_directory(directory_fd, relative_directory):
        try:
            opened_directory = os.fstat(directory_fd)
            if not stat.S_ISDIR(opened_directory.st_mode):
                raise ValueError(
                    "Staged entry is not a real directory during overlay size walk: "
                    f"{relative_directory}"
                )
            names = os.listdir(directory_fd)
            directory_stack.append({
                "fd": directory_fd,
                "relative": relative_directory,
                "snapshot": directory_snapshot(opened_directory),
                "names": names,
                "entries": {},
                "index": 0,
            })
        except BaseException:
            _close_overlay_descriptors_preserving_primary(
                [("staged directory", directory_fd)]
            )
            raise

    try:
        parent_fd, root_name = _open_parent_directory_without_symlink_parents(
            staging_root,
            "Staging root for overlay size",
            "Safe overlay size calculation requires POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support",
            "Invalid staging root directory name",
        )
        try:
            root_entry = os.stat(
                root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Staging directory not found: {staging_root}"
            ) from exc
        if not stat.S_ISDIR(root_entry.st_mode):
            raise ValueError(
                f"Staging root is not a real directory: {staging_root}"
            )

        try:
            root_fd = os.open(root_name, directory_flags, dir_fd=parent_fd)
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOENT, errno.ENOTDIR):
                raise ValueError(
                    f"Staging root changed or became a symlink while opening: {staging_root}"
                ) from exc
            raise

        opened_root = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(opened_root.st_mode)
            or (root_entry.st_dev, root_entry.st_ino)
            != (opened_root.st_dev, opened_root.st_ino)
        ):
            raise ValueError(
                f"Staging root changed while opening: {staging_root}"
            )

        root_to_push = root_fd
        root_fd = -1
        push_directory(root_to_push, ".")

        while directory_stack:
            frame = directory_stack[-1]
            directory_fd = frame["fd"]
            relative_directory = frame["relative"]

            if frame["index"] >= len(frame["names"]):
                if relative_directory == ".":
                    check_root_name(opened_root)

                final_directory = os.fstat(directory_fd)
                if directory_snapshot(final_directory) != frame["snapshot"]:
                    raise ValueError(
                        "Staged directory identity or mode changed during overlay "
                        f"size walk: {relative_directory}"
                    )

                try:
                    current_names = os.listdir(directory_fd)
                except OSError as exc:
                    raise ValueError(
                        "Staged directory could not be rechecked during overlay "
                        f"size walk: {relative_directory}"
                    ) from exc
                if set(current_names) != set(frame["names"]):
                    raise ValueError(
                        "Staged directory changed during overlay size walk: "
                        f"{relative_directory}"
                    )

                for entry_name, expected_entry in frame["entries"].items():
                    try:
                        current_entry = os.stat(
                            entry_name,
                            dir_fd=directory_fd,
                            follow_symlinks=False,
                        )
                    except OSError as exc:
                        raise ValueError(
                            "Staged entry changed during overlay size walk: "
                            f"{relative_directory}/{entry_name}"
                        ) from exc
                    if entry_snapshot(current_entry) != expected_entry:
                        raise ValueError(
                            "Staged entry changed during overlay size walk: "
                            f"{relative_directory}/{entry_name}"
                        )

                completed_frame = directory_stack.pop()
                _close_overlay_descriptors_preserving_primary(
                    [("staged directory", completed_frame["fd"])]
                )
                continue

            entry_name = frame["names"][frame["index"]]
            frame["index"] += 1
            relative_entry = (
                entry_name
                if relative_directory == "."
                else f"{relative_directory}/{entry_name}"
            )
            try:
                entry_fd = os.open(
                    entry_name,
                    entry_flags,
                    dir_fd=directory_fd,
                )
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOENT, errno.ENOTDIR):
                    raise ValueError(
                        "Staged entry changed while opening during overlay "
                        f"size walk: {relative_entry}"
                    ) from exc
                raise

            try:
                opened_entry = os.fstat(entry_fd)
                try:
                    current_entry = os.stat(
                        entry_name,
                        dir_fd=directory_fd,
                        follow_symlinks=False,
                    )
                except FileNotFoundError as exc:
                    raise ValueError(
                        "Staged entry changed during overlay size walk: "
                        f"{relative_entry}"
                    ) from exc
                if (
                    (current_entry.st_dev, current_entry.st_ino)
                    != (opened_entry.st_dev, opened_entry.st_ino)
                ):
                    raise ValueError(
                        "Staged entry changed while opening during overlay "
                        f"size walk: {relative_entry}"
                    )
                frame["entries"][entry_name] = entry_snapshot(current_entry)

                # Rootfs symlinks are intentional and excluded from the byte
                # budget, but O_PATH pins the link itself so a symlink-to-file
                # replacement cannot be silently skipped.
                if stat.S_ISLNK(opened_entry.st_mode):
                    continue

                if stat.S_ISDIR(opened_entry.st_mode):
                    try:
                        child_fd = os.open(
                            entry_name,
                            directory_flags,
                            dir_fd=directory_fd,
                        )
                    except OSError as exc:
                        if exc.errno in (errno.ELOOP, errno.ENOENT, errno.ENOTDIR):
                            raise ValueError(
                                "Staged directory changed or became a symlink "
                                f"during overlay size walk: {relative_entry}"
                            ) from exc
                        raise

                    # The child descriptor is not yet owned by directory_stack.
                    # Keep ownership local until verification succeeds and push_directory
                    # accepts it; otherwise an interruption here would leak the descriptor.
                    try:
                        opened_child = os.fstat(child_fd)
                        if (
                            not stat.S_ISDIR(opened_child.st_mode)
                            or (opened_entry.st_dev, opened_entry.st_ino)
                            != (opened_child.st_dev, opened_child.st_ino)
                        ):
                            raise ValueError(
                                "Staged directory changed while opening during "
                                f"overlay size walk: {relative_entry}"
                            )
                    except BaseException:
                        _close_overlay_descriptors_preserving_primary(
                            [("in-flight staged directory", child_fd)]
                        )
                        raise
                    push_directory(child_fd, relative_entry)
                    continue

                # O_PATH gives a stable metadata handle without requiring file
                # read permission or opening a FIFO/device.
                total_bytes += opened_entry.st_size
            finally:
                _close_overlay_descriptors_preserving_primary(
                    [("staged entry", entry_fd)]
                )

        check_root_name(opened_root)
        return (total_bytes + 1023) // 1024
    finally:
        pending_descriptors = []
        while directory_stack:
            frame = directory_stack.pop()
            pending_descriptors.append(("staged directory", frame["fd"]))
        if root_fd >= 0:
            pending_descriptors.append(("staging root", root_fd))
            root_fd = -1
        if parent_fd >= 0:
            pending_descriptors.append(("staging parent", parent_fd))
            parent_fd = -1
        _close_overlay_descriptors_preserving_primary(pending_descriptors)

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
    """Create staging directories through pinned descriptors without following links."""
    components = relative_path.split("/")
    for component in components:
        if component in ("", ".", ".."):
            raise ValueError(f"Invalid staged directory component: {component!r}")

    if (
        os.mkdir not in getattr(os, "supports_dir_fd", set())
        or os.stat not in getattr(os, "supports_dir_fd", set())
        or os.stat not in getattr(os, "supports_follow_symlinks", set())
    ):
        raise OSError(
            "Safe staged directory creation requires POSIX dir_fd mkdir/stat support"
        )

    staging_root = os.path.abspath(staging_dir)
    root_parent_fd = -1
    current_fd = -1
    current_label = "staging root"
    owned_descriptors = []
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        root_parent_fd, root_name = _open_parent_directory_without_symlink_parents(
            staging_root,
            "Staging root",
            "Safe staged directory creation requires POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support",
            "Invalid staging root directory name",
        )
        owned_descriptors.append(("staging root parent", root_parent_fd))
        try:
            current_fd = os.open(root_name, directory_flags, dir_fd=root_parent_fd)
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise ValueError(
                    f"Staging root path contains a symlink or non-directory: {staging_root}"
                ) from exc
            raise
        owned_descriptors.append((current_label, current_fd))

        root_entry = os.stat(root_name, dir_fd=root_parent_fd, follow_symlinks=False)
        root_opened = os.fstat(current_fd)
        if not stat.S_ISDIR(root_entry.st_mode) or (
            root_entry.st_dev,
            root_entry.st_ino,
        ) != (root_opened.st_dev, root_opened.st_ino):
            raise ValueError(f"Staging root path changed while opening: {staging_root}")

        # Keep every live descriptor in the cleanup ledger until close succeeds.
        # If close raises after closing the fd, final cleanup ignores EBADF; if
        # it raises before closing, final cleanup makes one more safe attempt.
        os.close(root_parent_fd)
        owned_descriptors.remove(("staging root parent", root_parent_fd))
        root_parent_fd = -1
        current_path = staging_root

        for component in components:
            try:
                os.mkdir(component, 0o755, dir_fd=current_fd)
            except FileExistsError:
                pass

            try:
                next_fd = os.open(component, directory_flags, dir_fd=current_fd)
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise ValueError(
                        "Refusing symlink or non-directory in staged configuration path: "
                        f"{os.path.join(current_path, component)}"
                    ) from exc
                raise

            next_label = f"staged directory {component}"
            owned_descriptors.append((next_label, next_fd))
            entry_stat = os.stat(
                component,
                dir_fd=current_fd,
                follow_symlinks=False,
            )
            opened_stat = os.fstat(next_fd)
            if not stat.S_ISDIR(entry_stat.st_mode) or (
                entry_stat.st_dev,
                entry_stat.st_ino,
            ) != (opened_stat.st_dev, opened_stat.st_ino):
                raise ValueError(
                    "Staging directory path changed while opening: "
                    f"{os.path.join(current_path, component)}"
                )

            previous_fd = current_fd
            previous_label = current_label
            os.close(previous_fd)
            owned_descriptors.remove((previous_label, previous_fd))
            current_fd = next_fd
            current_label = next_label
            current_path = os.path.join(current_path, component)

        return current_path
    finally:
        _close_overlay_descriptors_preserving_primary(owned_descriptors)

def _write_staging_bytes(directory: str, filename: str, content: bytes, mode: int = 0o644) -> None:
    """Atomically replace one staged file without following links or writing through hardlinks."""
    path = os.path.join(directory, filename)
    try:
        existing_mode = os.lstat(path).st_mode
    except FileNotFoundError:
        existing_mode = None
    if existing_mode is not None and not stat.S_ISREG(existing_mode):
        raise ValueError(
            f"Refusing symlink or non-regular staged file destination: {path}"
        )

    if (
        os.stat not in getattr(os, "supports_dir_fd", set())
        or os.stat not in getattr(os, "supports_follow_symlinks", set())
        or os.rename not in getattr(os, "supports_dir_fd", set())
        or os.unlink not in getattr(os, "supports_dir_fd", set())
    ):
        raise OSError(
            "Safe staged file replacement requires dir_fd stat, rename and unlink support"
        )

    directory_fd = -1
    temporary_name = None
    file_fd = -1
    try:
        directory_fd, destination_name = _open_parent_directory_without_symlink_parents(
            path,
            "Staged file destination",
            "Safe staged file writes require POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support",
            "Invalid staged file destination filename",
        )

        try:
            current_stat = os.stat(
                destination_name,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            current_stat = None
        if current_stat is not None and not stat.S_ISREG(current_stat.st_mode):
            raise ValueError(
                f"Refusing symlink or non-regular staged file destination: {path}"
            )

        # Never truncate the destination inode: it may be a hardlink to an
        # operator-owned file. Write a fresh inode in the same directory and
        # atomically replace the directory entry only after the full write.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        for _ in range(16):
            temporary_name = f".phx-staging-{os.getpid()}-{secrets.token_hex(8)}"
            try:
                file_fd = os.open(
                    temporary_name,
                    flags,
                    0o600,
                    dir_fd=directory_fd,
                )
                break
            except FileExistsError:
                temporary_name = None
        else:
            raise FileExistsError(
                "Unable to allocate a unique staged-file temporary name"
            )

        try:
            with os.fdopen(file_fd, "wb") as staged_file:
                file_fd = -1
                staged_file.write(content)
                staged_file.flush()
                # Set the final mode on the private temporary inode before
                # publishing it; never chmod a destination that may be a hardlink.
                os.fchmod(staged_file.fileno(), mode)
                os.fsync(staged_file.fileno())

            os.rename(
                temporary_name,
                destination_name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            temporary_name = None
            os.fsync(directory_fd)
        finally:
            if file_fd >= 0:
                _close_overlay_descriptors_preserving_primary(
                    [("staged temporary file", file_fd)]
                )
    finally:
        primary_error = sys.exc_info()[1]
        unlink_error = None
        if temporary_name is not None and directory_fd >= 0:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except BaseException as exc:
                unlink_error = exc

        if unlink_error is not None and primary_error is not None:
            if hasattr(primary_error, "add_note"):
                primary_error.add_note(
                    "Staged temporary-file cleanup failed: "
                    f"{type(unlink_error).__name__}: {unlink_error}"
                )
            if directory_fd >= 0:
                _close_overlay_descriptors_preserving_primary(
                    [("staged file destination", directory_fd)]
                )
        elif unlink_error is not None:
            try:
                raise unlink_error
            finally:
                if directory_fd >= 0:
                    _close_overlay_descriptors_preserving_primary(
                        [("staged file destination", directory_fd)]
                    )
        elif directory_fd >= 0:
            _close_overlay_descriptors_preserving_primary(
                [("staged file destination", directory_fd)]
            )



def _normalize_staging_directory_mode(path: str, mode: int) -> bool:
    """Set a staged directory mode through a pinned no-follow descriptor."""
    if (
        os.stat not in getattr(os, "supports_dir_fd", set())
        or os.stat not in getattr(os, "supports_follow_symlinks", set())
        or not hasattr(os, "fchmod")
    ):
        raise OSError(
            "Safe staged directory permissions require dir_fd stat and fchmod support"
        )

    parent_fd = -1
    directory_fd = -1
    try:
        parent_fd, name = _open_parent_directory_without_symlink_parents(
            path,
            "Staged directory permission target",
            "Safe staged directory permissions require POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support",
            "Invalid staged directory permission target",
        )
        try:
            entry_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError as exc:
            raise ValueError(f"Staged directory disappeared before permission normalization: {path}") from exc

        if stat.S_ISLNK(entry_stat.st_mode):
            return False
        if not stat.S_ISDIR(entry_stat.st_mode):
            raise ValueError(f"Refusing non-directory staged permission target: {path}")

        try:
            directory_fd = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=parent_fd,
            )
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise ValueError(
                    f"Staged directory changed to a symlink or non-directory: {path}"
                ) from exc
            raise

        opened_stat = os.fstat(directory_fd)
        if not stat.S_ISDIR(opened_stat.st_mode) or (
            entry_stat.st_dev,
            entry_stat.st_ino,
        ) != (opened_stat.st_dev, opened_stat.st_ino):
            raise ValueError(f"Staged directory changed while opening: {path}")

        if stat.S_IMODE(opened_stat.st_mode) != mode:
            os.fchmod(directory_fd, mode)
        return True
    finally:
        _close_overlay_descriptors_preserving_primary(
            [
                (label, descriptor)
                for label, descriptor in (
                    ("staged directory", directory_fd),
                    ("staged directory parent", parent_fd),
                )
                if descriptor >= 0
            ]
        )


def _normalize_staging_file_mode(path: str, mode: int) -> bool:
    """Normalize one regular staged file without chmodding a symlink or hardlink target."""
    if (
        os.stat not in getattr(os, "supports_dir_fd", set())
        or os.stat not in getattr(os, "supports_follow_symlinks", set())
    ):
        raise OSError(
            "Safe staged file permissions require dir_fd stat and no-follow support"
        )

    parent_fd = -1
    file_fd = -1
    content = None
    absolute_path = os.path.abspath(path)
    try:
        parent_fd, name = _open_parent_directory_without_symlink_parents(
            absolute_path,
            "Staged file permission target",
            "Safe staged file permissions require POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support",
            "Invalid staged file permission target",
        )
        try:
            entry_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError as exc:
            raise ValueError(f"Staged file disappeared before permission normalization: {path}") from exc

        if stat.S_ISLNK(entry_stat.st_mode):
            return False
        if not stat.S_ISREG(entry_stat.st_mode):
            raise ValueError(f"Refusing non-regular staged permission target: {path}")

        try:
            file_fd = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
                dir_fd=parent_fd,
            )
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise ValueError(
                    f"Staged file changed to a symlink or non-regular entry: {path}"
                ) from exc
            raise

        opened_stat = os.fstat(file_fd)
        if not stat.S_ISREG(opened_stat.st_mode) or (
            entry_stat.st_dev,
            entry_stat.st_ino,
        ) != (opened_stat.st_dev, opened_stat.st_ino):
            raise ValueError(f"Staged file changed while opening: {path}")

        if stat.S_IMODE(opened_stat.st_mode) == mode:
            return True

        # A hardlink can expose the same inode outside staging. Read the
        # pinned source, then atomically replace the staging entry with a new
        # private inode whose final mode is set before publication.
        with os.fdopen(file_fd, "rb") as staged_file:
            file_fd = -1
            content = staged_file.read()
    finally:
        _close_overlay_descriptors_preserving_primary(
            [
                (label, descriptor)
                for label, descriptor in (
                    ("staged file", file_fd),
                    ("staged file parent", parent_fd),
                )
                if descriptor >= 0
            ]
        )

    _write_staging_bytes(
        os.path.dirname(absolute_path),
        os.path.basename(absolute_path),
        content,
        mode=mode,
    )
    return True


def _write_staging_file(directory: str, filename: str, content: str) -> None:
    """Write UTF-8 staged configuration without following copied symlinks."""
    _write_staging_bytes(directory, filename, content.encode("utf-8"))



def _copy_staging_file(source_path: str, directory: str, filename: str) -> None:
    """Copy one regular rental source file without following symlinked path components."""
    source_stat = os.lstat(source_path)
    if not stat.S_ISREG(source_stat.st_mode):
        raise ValueError(f"Refusing symlink or non-regular rental source file: {source_path}")

    source_fd = -1
    try:
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
        try:
            source_fd = _open_file_without_symlink_parents(
                source_path,
                flags,
                0,
                "Rental source file",
                "Safe rental source copying requires POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support",
                "Invalid rental source file filename",
            )
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOENT, errno.ENOTDIR):
                raise ValueError(
                    f"Refusing symlinked or unavailable rental source file: {source_path}"
                ) from exc
            raise

        opened_stat = os.fstat(source_fd)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise ValueError(
                f"Refusing non-regular rental source file after open: {source_path}"
            )
        if (opened_stat.st_dev, opened_stat.st_ino) != (
            source_stat.st_dev,
            source_stat.st_ino,
        ):
            raise ValueError(
                f"Rental source file changed while opening: {source_path}"
            )

        with os.fdopen(source_fd, "rb") as source_file:
            source_fd = -1
            content = source_file.read()
            after_read_stat = os.fstat(source_file.fileno())
            before_read_identity = (
                opened_stat.st_dev,
                opened_stat.st_ino,
                opened_stat.st_mode,
                opened_stat.st_nlink,
                opened_stat.st_size,
                opened_stat.st_mtime_ns,
                opened_stat.st_ctime_ns,
            )
            after_read_identity = (
                after_read_stat.st_dev,
                after_read_stat.st_ino,
                after_read_stat.st_mode,
                after_read_stat.st_nlink,
                after_read_stat.st_size,
                after_read_stat.st_mtime_ns,
                after_read_stat.st_ctime_ns,
            )
            if (
                after_read_identity != before_read_identity
                or len(content) != opened_stat.st_size
            ):
                raise ValueError(
                    f"Rental source file changed while reading: {source_path}"
                )
    finally:
        if source_fd >= 0:
            os.close(source_fd)

    _write_staging_bytes(directory, filename, content)

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
    requested_parent_dir = os.path.dirname(requested_staging_dir)
    if os.path.realpath(requested_parent_dir) != requested_parent_dir:
        raise ValueError(
            "Staging destination parent path contains a symlink: "
            f"{requested_parent_dir}"
        )
    # Keep the validated operator path. Resolving the destination itself would
    # silently redirect a new staging tree through a symlinked parent.
    staging_dir = requested_staging_dir
    try:
        shared_path = os.path.commonpath((source_rootfs, staging_dir))
    except ValueError:
        shared_path = None
    if shared_path in (source_rootfs, staging_dir):
        raise ValueError(
            "Staging destination must be separate from and outside the source rootfs"
        )
    _copy_rootfs_to_new_staging_directory(source_rootfs, staging_dir)

    # Inject generated configuration only through real directories and regular files.
    # copytree preserves symlinks; following one here could overwrite data outside staging.
    etc_config = _ensure_staging_directory(staging_dir, "etc/config")
    _write_staging_file(etc_config, "network", generate_network_uci(profile))

    # Save target profile specification into appliance metadata
    etc_blaze = _ensure_staging_directory(staging_dir, "etc/blazepwifi")
    _write_staging_file(etc_blaze, "appliance_profile.json", json.dumps(profile, indent=2))

    rental_etc = None
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

    # Normalize through pinned descriptors. A path-based islink()+chmod()
    # sequence can follow a symlink inserted between the check and chmod.
    # os.walk() ignores traversal errors unless onerror is supplied; silently
    # skipping a subtree would leave permissions unnormalized while reporting
    # a successful staging result. Treat every scan failure as a hard failure.
    def raise_walk_error(error: OSError) -> None:
        raise error

    for root, dirs, files in os.walk(staging_dir, onerror=raise_walk_error):
        for d in dirs:
            directory_path = os.path.join(root, d)
            # Keep the optional Rental configuration directory private.
            # Apply this mode during final normalization so the general
            # directory mode pass cannot overwrite the intended 0700.
            directory_mode = (
                0o700
                if rental_etc is not None
                and os.path.abspath(directory_path) == os.path.abspath(rental_etc)
                else 0o755
            )
            _normalize_staging_directory_mode(directory_path, directory_mode)
        for f in files:
            fp = os.path.join(root, f)
            # Classify executable paths inside the overlay, never by the
            # operator-selected absolute staging directory.
            relative_path = os.path.relpath(fp, staging_dir).replace(os.sep, "/")
            relative_path_with_root = f"/{relative_path}/"
            if (
                "/cgi-bin/" in relative_path_with_root
                or "/init.d/" in relative_path_with_root
                or "/usr/sbin/" in relative_path_with_root
                or relative_path.endswith(".sh")
            ):
                file_mode = 0o755
            else:
                file_mode = 0o644
            _normalize_staging_file_mode(fp, file_mode)

    return {
        "profile_id": profile["profile_id"],
        "target_architecture": profile["target_architecture"],
        "overlay_size_kb": size_kb,
        "flash_kb": flash_kb,
        "include_rental": include_rental,
        "staging_dir": staging_dir,
        "imagebuilder_command": build_imagebuilder_cmd(profile, os.path.abspath(staging_dir), include_rental=include_rental)
    }




def _open_parent_directory_without_symlink_parents(
    path: str,
    purpose: str,
    unsupported_message: str,
    invalid_filename_message: str,
) -> tuple[int, str]:
    """Open a file's parent directory through a no-symlink descriptor walk."""
    if (
        os.name != "posix"
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or os.open not in getattr(os, "supports_dir_fd", set())
    ):
        raise OSError(unsupported_message)

    absolute_path = os.path.abspath(path)
    parent_path, filename = os.path.split(absolute_path)
    if filename in ("", ".", ".."):
        raise ValueError(invalid_filename_message)

    directory_fd = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY)
    owned_descriptors = [directory_fd]
    try:
        # Keep the newly opened component owned before closing its predecessor.
        # If that close fails or is interrupted, cleanup still knows about the
        # new descriptor and can attempt every remaining close exactly once.
        for component in parent_path.split(os.sep):
            if not component:
                continue
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=owned_descriptors[-1],
                )
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise ValueError(
                        f"{purpose} parent path contains a symlink or non-directory: {parent_path}"
                    ) from exc
                raise
            owned_descriptors.append(next_fd)
            previous_fd = owned_descriptors.pop(-2)
            os.close(previous_fd)
        return owned_descriptors.pop(), filename
    except BaseException:
        _close_overlay_descriptors_preserving_primary(
            [
                ("directory path walk", descriptor)
                for descriptor in reversed(owned_descriptors)
            ]
        )
        raise
def _open_or_create_directory_without_symlink_parents(
    path: str,
    purpose: str,
    unsupported_message: str,
) -> int:
    """Open or create a directory path one no-follow component at a time."""
    if (
        os.name != "posix"
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or os.open not in getattr(os, "supports_dir_fd", set())
        or os.mkdir not in getattr(os, "supports_dir_fd", set())
    ):
        raise OSError(unsupported_message)

    absolute_path = os.path.abspath(path)
    directory_fd = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY)
    owned_descriptors = [directory_fd]
    try:
        for component in absolute_path.split(os.sep):
            if not component:
                continue
            parent_fd = owned_descriptors[-1]
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=parent_fd,
                )
            except FileNotFoundError:
                try:
                    os.mkdir(component, 0o755, dir_fd=parent_fd)
                except FileExistsError:
                    pass
                try:
                    next_fd = os.open(
                        component,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=parent_fd,
                    )
                except OSError as exc:
                    if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                        raise ValueError(
                            f"{purpose} path contains a symlink or non-directory: {absolute_path}"
                        ) from exc
                    raise
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise ValueError(
                        f"{purpose} path contains a symlink or non-directory: {absolute_path}"
                    ) from exc
                raise

            # Transfer ownership of the new descriptor before closing its
            # predecessor. If close is interrupted, cleanup still knows about
            # the new descriptor and can attempt every remaining owned close.
            owned_descriptors.append(next_fd)
            previous_fd = owned_descriptors.pop(-2)
            os.close(previous_fd)

        return owned_descriptors.pop()
    except BaseException:
        _close_overlay_descriptors_preserving_primary(
            [
                ("directory creation path walk", descriptor)
                for descriptor in reversed(owned_descriptors)
            ]
        )
        raise


def _copy_rootfs_to_new_staging_directory(source_rootfs: str, staging_dir: str) -> None:
    """Copy the rootfs into a pinned new staging directory, never a replaced parent path."""
    absolute_staging = os.path.abspath(staging_dir)
    parent_path, staging_name = os.path.split(absolute_staging)
    if staging_name in ("", ".", ".."):
        raise ValueError(f"Invalid staging destination filename: {absolute_staging}")

    unsupported = (
        "Safe rootfs staging requires POSIX dir_fd, O_DIRECTORY, O_NOFOLLOW "
        "and /proc/self/fd support"
    )
    parent_fd = _open_or_create_directory_without_symlink_parents(
        parent_path,
        "Staging destination parent",
        unsupported,
    )
    staging_fd = -1
    staging_created = False
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        try:
            os.mkdir(staging_name, 0o755, dir_fd=parent_fd)
        except FileExistsError:
            raise FileExistsError(
                f"Staging destination already exists; refusing to overwrite or delete: {absolute_staging}"
            ) from None
        staging_created = True

        try:
            staging_fd = os.open(staging_name, directory_flags, dir_fd=parent_fd)
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise ValueError(
                    f"Staging destination changed while opening: {absolute_staging}"
                ) from exc
            raise

        entry_stat = os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)
        opened_stat = os.fstat(staging_fd)
        if not stat.S_ISDIR(entry_stat.st_mode) or (
            entry_stat.st_dev,
            entry_stat.st_ino,
        ) != (opened_stat.st_dev, opened_stat.st_ino):
            raise ValueError(
                f"Staging destination changed while opening: {absolute_staging}"
            )

        pinned_staging_path = f"/proc/self/fd/{staging_fd}"
        if not os.path.isdir(pinned_staging_path):
            raise OSError(unsupported)

        # copytree follows only the pinned descriptor path. Replacing the
        # operator-visible parent with a symlink cannot redirect these writes.
        shutil.copytree(
            source_rootfs,
            pinned_staging_path,
            symlinks=True,
            dirs_exist_ok=True,
        )

        try:
            current_parent_fd, current_name = _open_parent_directory_without_symlink_parents(
                absolute_staging,
                "Staging destination",
                unsupported,
                "Invalid staging destination filename",
            )
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"Staging destination parent path changed during rootfs copy: {parent_path}"
            ) from exc
        try:
            original_parent_stat = os.fstat(parent_fd)
            current_parent_stat = os.fstat(current_parent_fd)
            if current_name != staging_name or (
                original_parent_stat.st_dev,
                original_parent_stat.st_ino,
            ) != (current_parent_stat.st_dev, current_parent_stat.st_ino):
                raise ValueError(
                    f"Staging destination parent path changed during rootfs copy: {parent_path}"
                )
        finally:
            os.close(current_parent_fd)

        final_entry = os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)
        final_opened = os.fstat(staging_fd)
        if not stat.S_ISDIR(final_entry.st_mode) or (
            final_entry.st_dev,
            final_entry.st_ino,
        ) != (final_opened.st_dev, final_opened.st_ino):
            raise ValueError(
                f"Staging destination changed during rootfs copy: {absolute_staging}"
            )
    except BaseException as copy_error:
        # Remove only the directory still pinned by our descriptor. Never
        # follow or delete a replacement symlink or another directory entry.
        cleanup_error = None
        if staging_created:
            if staging_fd < 0:
                cleanup_error = RuntimeError(
                    "staging directory was created but could not be pinned; "
                    "refusing path-based rollback"
                )
            else:
                try:
                    current_entry = os.stat(
                        staging_name,
                        dir_fd=parent_fd,
                        follow_symlinks=False,
                    )
                    opened_entry = os.fstat(staging_fd)
                    if not stat.S_ISDIR(current_entry.st_mode) or (
                        current_entry.st_dev,
                        current_entry.st_ino,
                    ) != (opened_entry.st_dev, opened_entry.st_ino):
                        raise RuntimeError(
                            "staging destination no longer names the pinned partial directory; "
                            "replacement was left untouched"
                        )
                    shutil.rmtree(
                        os.path.join(f"/proc/self/fd/{parent_fd}", staging_name)
                    )
                except BaseException as exc:
                    cleanup_error = exc

        if cleanup_error is not None:
            raise OSError(
                "Rootfs staging rollback could not be confirmed after "
                f"{type(copy_error).__name__}: "
                f"{type(cleanup_error).__name__}: {cleanup_error}"
            ) from copy_error
        raise
    finally:
        owned_descriptors = []
        if staging_fd >= 0:
            owned_descriptors.append(("staging directory", staging_fd))
        owned_descriptors.append(("staging parent directory", parent_fd))
        _close_overlay_descriptors_preserving_primary(owned_descriptors)


def _open_file_without_symlink_parents(
    path: str,
    flags: int,
    mode: int,
    purpose: str,
    unsupported_message: str,
    invalid_filename_message: str,
) -> int:
    """Open a file through directory descriptors without following any symlink component."""
    directory_fd, filename = _open_parent_directory_without_symlink_parents(
        path,
        purpose,
        unsupported_message,
        invalid_filename_message,
    )
    try:
        file_descriptor = os.open(
            filename,
            flags | os.O_NOFOLLOW,
            mode,
            dir_fd=directory_fd,
        )
    except BaseException:
        # Keep the original open failure authoritative if closing the parent
        # descriptor is itself interrupted or reports an error.
        _close_overlay_descriptors_preserving_primary(
            [("router profile parent directory", directory_fd)]
        )
        raise

    try:
        _close_overlay_descriptors_preserving_primary(
            [("router profile parent directory", directory_fd)]
        )
    except BaseException:
        # The new file descriptor is still owned by this helper until it is
        # returned. If parent cleanup fails, close it rather than leaking a
        # descriptor that the caller never receives.
        _close_overlay_descriptors_preserving_primary(
            [("opened router profile", file_descriptor)]
        )
        raise

    return file_descriptor


def _open_new_file_without_symlink_parents(path: str, flags: int, mode: int) -> tuple[int, int]:
    """Create a build script and retain its parent descriptor for durable publication."""
    directory_fd, filename = _open_parent_directory_without_symlink_parents(
        path,
        "Build script",
        "Safe build-script creation requires POSIX dir_fd, O_DIRECTORY and O_NOFOLLOW support",
        "Invalid build-script output filename",
    )
    try:
        file_fd = os.open(
            filename,
            flags | os.O_NOFOLLOW,
            mode,
            dir_fd=directory_fd,
        )
        return file_fd, directory_fd
    except BaseException:
        # Keep the original exclusive-create failure authoritative if parent
        # descriptor cleanup also fails or is interrupted.
        _close_overlay_descriptors_preserving_primary(
            [("build-script parent directory", directory_fd)]
        )
        raise

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
    # Resolve only after preserving the candidate path: realpath() alone erases
    # whether the repository-owned runner was reached through a symlink.
    runner_candidate = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_imagebuilder_sandbox.py")
    )
    if os.path.realpath(runner_candidate) != runner_candidate:
        raise FileNotFoundError(
            f"Required ImageBuilder sandbox runner path contains a symlink: {runner_candidate}"
        )
    if not hasattr(os, "O_NOFOLLOW"):
        raise OSError("Safe ImageBuilder runner verification requires O_NOFOLLOW support")

    try:
        runner_fd = os.open(runner_candidate, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOENT, errno.ENOTDIR):
            raise FileNotFoundError(
                "Required ImageBuilder sandbox runner is missing, symlinked, or not a regular file: "
                f"{runner_candidate}"
            ) from exc
        raise
    try:
        if not stat.S_ISREG(os.fstat(runner_fd).st_mode):
            raise FileNotFoundError(
                f"Required ImageBuilder sandbox runner is not a regular file: {runner_candidate}"
            )
        with os.fdopen(runner_fd, "rb") as runner_file:
            runner_fd = -1
            runner_sha256 = hashlib.sha256(runner_file.read()).hexdigest()
    finally:
        if runner_fd >= 0:
            os.close(runner_fd)

    runner_path = runner_candidate

    # Pin the interpreter that generated this host-specific wrapper. Never
    # resolve python3 from an operator-controlled PATH at execution time.
    python_path = os.path.realpath(sys.executable)
    if (
        not os.path.isabs(python_path)
        or os.path.islink(python_path)
        or not os.path.isfile(python_path)
        or not os.access(python_path, os.X_OK)
        or not stat.S_ISREG(os.stat(python_path).st_mode)
    ):
        raise OSError("Safe ImageBuilder wrapper requires a stable executable Python interpreter")
    with open(python_path, "rb") as python_file:
        python_sha256 = hashlib.sha256(python_file.read()).hexdigest()

    sha256sum_candidate = shutil.which("sha256sum", path=TRUSTED_SYSTEM_PATH)
    if not sha256sum_candidate:
        raise OSError("Safe ImageBuilder wrapper requires sha256sum in trusted system directories")
    # Preserve the trusted system PATH entry: some distributions expose
    # sha256sum through a system-managed symlink outside the directory itself.
    # Pin the bytes reached through that entry and re-check them before use.
    sha256sum_path = os.path.abspath(sha256sum_candidate)
    if (
        os.path.dirname(sha256sum_path) not in ("/usr/bin", "/bin")
        or not os.path.isfile(sha256sum_path)
        or not os.access(sha256sum_path, os.X_OK)
    ):
        raise OSError("Safe ImageBuilder wrapper requires a regular trusted-system sha256sum executable")
    sha256sum_fd = -1
    try:
        sha256sum_fd = os.open(sha256sum_path, os.O_RDONLY)
        sha256sum_stat = os.fstat(sha256sum_fd)
        sha256sum_parent_stat = os.stat(os.path.dirname(sha256sum_path))
        if (
            not stat.S_ISREG(sha256sum_stat.st_mode)
            or not sha256sum_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            or sha256sum_stat.st_uid != 0
            or sha256sum_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
            or not stat.S_ISDIR(sha256sum_parent_stat.st_mode)
            or sha256sum_parent_stat.st_uid != 0
            or sha256sum_parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            raise OSError(
                "Safe ImageBuilder wrapper requires a root-owned, non-writable system sha256sum executable"
            )
        with os.fdopen(sha256sum_fd, "rb") as sha256sum_file:
            sha256sum_fd = -1
            sha256sum_sha256 = hashlib.sha256(sha256sum_file.read()).hexdigest()
    finally:
        if sha256sum_fd >= 0:
            os.close(sha256sum_fd)

    # This absolute path remains valid after the wrapper changes into ImageBuilder.
    stage_arg = shlex.quote(staging_dir)
    runner_arg = shlex.quote(runner_path)
    python_arg = shlex.quote(python_path)
    sha256sum_arg = shlex.quote(sha256sum_path)

    content = f"""#!/bin/sh
# Auto-generated nonproduction ImageBuilder wrapper for {profile_id} ({target_arch})
# A checksum is not hardware or financial release acceptance.
# Host root is read-only and only ImageBuilder is writable; network is shared, not isolated.
set -eu

PYTHON_PATH={python_arg}
PYTHON_SHA256={python_sha256}
SHA256SUM_PATH={sha256sum_arg}
SHA256SUM_BOOTSTRAP_PATH={sha256sum_arg}
SHA256SUM_SHA256={sha256sum_sha256}
RUNNER_PATH={runner_arg}
RUNNER_SHA256={runner_sha256}

if [ ! -f "$SHA256SUM_PATH" ] || [ ! -x "$SHA256SUM_PATH" ]; then
    echo "RELEASE-BLOCKED: pinned sha256sum executable is missing or unsafe" >&2
    exit 1
fi
if [ ! -f "$SHA256SUM_BOOTSTRAP_PATH" ] || [ ! -x "$SHA256SUM_BOOTSTRAP_PATH" ]; then
    echo "RELEASE-BLOCKED: bootstrap sha256sum executable is missing or unsafe" >&2
    exit 1
fi
if [ ! -f "$PYTHON_PATH" ] || [ -L "$PYTHON_PATH" ] || [ ! -x "$PYTHON_PATH" ]; then
    echo "RELEASE-BLOCKED: pinned Python interpreter is missing or unsafe" >&2
    exit 1
fi

# The absolute root-owned system sha256sum is the bootstrap trust root. Verify
# Python before executing it; Python then verifies the pinned checksum utility.
PYTHON_DIGEST_LINE="$("$SHA256SUM_BOOTSTRAP_PATH" "$PYTHON_PATH")"
ACTUAL_PYTHON_SHA256="${{PYTHON_DIGEST_LINE%% *}}"
if [ "$ACTUAL_PYTHON_SHA256" != "$PYTHON_SHA256" ]; then
    echo "RELEASE-BLOCKED: pinned Python interpreter SHA-256 differs from the generated wrapper" >&2
    exit 1
fi

"$PYTHON_PATH" - "$SHA256SUM_PATH" "$SHA256SUM_SHA256" <<'PHX_SHA256SUM_VERIFY'
import hashlib
import os
import stat
import sys

path, expected = sys.argv[1:]
fd = -1
try:
    fd = os.open(path, os.O_RDONLY)
    metadata = os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode) or not (
        metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    ):
        raise OSError("checksum utility is not a regular executable file")
    with os.fdopen(fd, "rb") as source:
        fd = -1
        actual = hashlib.sha256(source.read()).hexdigest()
except OSError as exc:
    raise SystemExit(
        "RELEASE-BLOCKED: pinned sha256sum executable could not be verified: " + str(exc)
    )
finally:
    if fd >= 0:
        os.close(fd)

if actual != expected:
    raise SystemExit(
        "RELEASE-BLOCKED: pinned sha256sum executable SHA-256 differs from the generated wrapper"
    )
PHX_SHA256SUM_VERIFY
# Resolve remaining shell utilities and ImageBuilder tools only from trusted system paths.
PATH="/usr/sbin:/usr/bin:/sbin:/bin"
export PATH

BUILD_DIR="${{OPENWRT_IMAGEBUILDER_DIR:-$PWD}}"
BUILD_DIR="$("$PYTHON_PATH" -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$BUILD_DIR")"
if [ ! -d "$BUILD_DIR" ]; then
    echo "RELEASE-BLOCKED: ImageBuilder directory not found: $BUILD_DIR" >&2
    exit 1
fi
BUILD_DIR_REAL="$(cd "$BUILD_DIR" && pwd -P)"
if [ "$BUILD_DIR_REAL" != "$BUILD_DIR" ]; then
    echo "RELEASE-BLOCKED: ImageBuilder path contains a symlink component: $BUILD_DIR" >&2
    exit 1
fi

SCRIPT_PATH="$("$PYTHON_PATH" -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$0")"
SCRIPT_REAL="$("$PYTHON_PATH" -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$SCRIPT_PATH")"
if [ "$SCRIPT_REAL" != "$SCRIPT_PATH" ]; then
    echo "RELEASE-BLOCKED: generated build script path contains a symlink: $SCRIPT_PATH" >&2
    exit 1
fi

RUNNER_REALPATH="$("$PYTHON_PATH" -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$RUNNER_PATH")"
if [ "$RUNNER_REALPATH" != "$RUNNER_PATH" ] || [ ! -f "$RUNNER_PATH" ] || [ -L "$RUNNER_PATH" ]; then
    echo "RELEASE-BLOCKED: sandbox runner path contains a symlink or changed target: $RUNNER_PATH" >&2
    exit 1
fi
RUNNER_DIGEST_LINE="$("$SHA256SUM_PATH" "$RUNNER_PATH")"
ACTUAL_RUNNER_SHA256="${{RUNNER_DIGEST_LINE%% *}}"
if [ "$ACTUAL_RUNNER_SHA256" != "$RUNNER_SHA256" ]; then
    echo "RELEASE-BLOCKED: sandbox runner SHA-256 differs from the generated wrapper" >&2
    exit 1
fi

# Environment markers and a writable probe are not proof of a namespace.
# Ask the pinned runner to verify the single-ID maps and mount boundaries before
# allowing Makefile execution. A direct operator invocation always enters bwrap.
if [ "${{PHX_IMAGEBUILDER_SANDBOX_ACTIVE:-}}" = "1" ] &&
   [ -n "${{PHX_BWRAP_OWNER_PROBE:-}}" ]; then
    echo "RELEASE-BOUNDARY: verifying active ImageBuilder sandbox context." >&2
    "$PYTHON_PATH" "$RUNNER_PATH" --verify-context --builder "$BUILD_DIR" --probe "$PHX_BWRAP_OWNER_PROBE"
else
    SANDBOX_ROOT="$("$PYTHON_PATH" - "$BUILD_DIR" "$SCRIPT_PATH" <<'PY'
import os, sys
try:
    print(os.path.commonpath((os.path.dirname(sys.argv[1]), sys.argv[2])))
except ValueError:
    raise SystemExit(1)
PY
)"
    if [ -z "$SANDBOX_ROOT" ]; then
        echo "RELEASE-BLOCKED: cannot determine a common read-only sandbox root" >&2
        exit 1
    fi
    echo "RELEASE-BOUNDARY: entering unprivileged bubblewrap; only the ImageBuilder directory is writable; network isolation is not claimed." >&2
    # Operators may bound this invocation without editing the generated wrapper.
    # The runner validates the value against its 1..14400 second limit.
    exec "$PYTHON_PATH" "$RUNNER_PATH" --cwd "$SANDBOX_ROOT" --builder "$BUILD_DIR" --wrapper "$SCRIPT_PATH" --timeout-seconds "${{PHX_IMAGEBUILDER_TIMEOUT_SECONDS:-{DEFAULT_BUILD_TIMEOUT_SECONDS}}}"
fi
# Refuse shell redirections to paths created after the preflight checks.
# This protects both checksum-manifest paths from symlink substitution by the builder.
set -C

STAGING_DIR={stage_arg}
if [ ! -f "$BUILD_DIR/Makefile" ]; then
    echo "RELEASE-BLOCKED: ImageBuilder Makefile not found in $BUILD_DIR" >&2
    exit 1
fi
if [ ! -d "$STAGING_DIR" ]; then
    echo "RELEASE-BLOCKED: staged rootfs not found: $STAGING_DIR" >&2
    exit 1
fi
STAGING_DIR_REAL="$("$PYTHON_PATH" -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$STAGING_DIR")"
if [ "$STAGING_DIR_REAL" != "$STAGING_DIR" ] || [ -L "$STAGING_DIR" ]; then
    echo "RELEASE-BLOCKED: staged rootfs path contains a symlink: $STAGING_DIR" >&2
    exit 1
fi

# A reused ImageBuilder may report success without writing a new binary.
# Never certify files or a checksum manifest left by an earlier invocation.
# Refuse stale data without deleting or modifying an operator's files.
BIN_DIR="$BUILD_DIR/bin/targets/{target_arch}"
OUT_MANIFEST="$BUILD_DIR/RELEASE_MANIFEST.sha256"
TMP_MANIFEST="$BUILD_DIR/RELEASE_MANIFEST.sha256.tmp"
SORTED_MANIFEST="$BUILD_DIR/RELEASE_MANIFEST.sha256.sorted.tmp"

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
if [ -e "$SORTED_MANIFEST" ] || [ -L "$SORTED_MANIFEST" ]; then
    echo "RELEASE-BLOCKED: previous sorted temporary manifest exists: $SORTED_MANIFEST; use a clean ImageBuilder workspace" >&2
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

# The pre-build check rejects existing symlinks, but Makefile execution can
# replace a previously absent output ancestor with a symlink. Revalidate
# every target/subtarget path component before the manifest scan.
IMAGE_PATH="$BUILD_DIR"
for IMAGE_COMPONENT in bin targets {target_arch.replace("/", " ")}; do
    IMAGE_PATH="$IMAGE_PATH/$IMAGE_COMPONENT"
    if [ -L "$IMAGE_PATH" ]; then
        echo "RELEASE-BLOCKED: symlinked ImageBuilder output directory after build: $IMAGE_PATH" >&2
        exit 1
    fi
done

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

# A regular file can still alias a cached payload elsewhere in the builder
# tree. Admit only independently materialized firmware files into the manifest.
HARDLINKED_IMAGE=$(find "$IMAGE_REL_DIR" -type f \\( -name "*.bin" -o -name "*.img.gz" \\) -links +1 -print -quit)
if [ -n "$HARDLINKED_IMAGE" ]; then
    echo "RELEASE-BLOCKED: hard-linked firmware image: $HARDLINKED_IMAGE" >&2
    exit 1
fi

EMPTY_IMAGE=$(find "$IMAGE_REL_DIR" -type f \\( -name "*.bin" -o -name "*.img.gz" \\) -size 0 -print -quit)
if [ -n "$EMPTY_IMAGE" ]; then
    echo "RELEASE-BLOCKED: empty firmware image: $EMPTY_IMAGE" >&2
    exit 1
fi
find "$IMAGE_REL_DIR" -type f \\( -name "*.bin" -o -name "*.img.gz" \\) -exec "$SHA256SUM_PATH" {{}} + > "$TMP_MANIFEST"
if [ ! -s "$TMP_MANIFEST" ]; then
    rm -f "$TMP_MANIFEST"
    echo "RELEASE-BLOCKED: no firmware images found for {target_arch}" >&2
    exit 1
fi
# Sort into a temporary file first. Publish the final manifest with an
# atomic no-overwrite hard link only after sort has completed successfully.
if ! LC_ALL=C sort "$TMP_MANIFEST" > "$SORTED_MANIFEST"; then
    echo "RELEASE-BLOCKED: checksum manifest sort failed; final manifest was not published" >&2
    exit 1
fi
if ! ln "$SORTED_MANIFEST" "$OUT_MANIFEST"; then
    echo "RELEASE-BLOCKED: final checksum manifest path became occupied; refusing to overwrite: $OUT_MANIFEST" >&2
    exit 1
fi
"$PYTHON_PATH" - "$BUILD_DIR" "RELEASE_MANIFEST.sha256" "RELEASE_MANIFEST.sha256.sorted.tmp" "RELEASE_MANIFEST.sha256.tmp" <<'PHX_MANIFEST_SYNC'
# PHX-MANIFEST-DURABILITY-BEGIN
import os
import stat
import sys

build_dir, final_name, sorted_name, temporary_name = sys.argv[1:]
directory_fd = -1
try:
    directory_fd = os.open(
        build_dir,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    final_fd = os.open(
        final_name,
        os.O_WRONLY | os.O_NOFOLLOW,
        dir_fd=directory_fd,
    )
    try:
        final_stat = os.fstat(final_fd)
        sorted_stat = os.stat(
            sorted_name,
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
        temporary_stat = os.stat(
            temporary_name,
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
        if not stat.S_ISREG(final_stat.st_mode):
            raise RuntimeError("final manifest is not a regular file")
        if not stat.S_ISREG(sorted_stat.st_mode):
            raise RuntimeError("sorted temporary manifest is not a regular file")
        if not stat.S_ISREG(temporary_stat.st_mode):
            raise RuntimeError("temporary checksum input is not a regular file")
        if (final_stat.st_dev, final_stat.st_ino) != (sorted_stat.st_dev, sorted_stat.st_ino):
            raise RuntimeError("final manifest is not the published sorted inode")
        if final_stat.st_nlink != 2:
            raise RuntimeError("published manifest has an unexpected hard-link count")
        if temporary_stat.st_nlink != 1 or (
            temporary_stat.st_dev,
            temporary_stat.st_ino,
        ) == (final_stat.st_dev, final_stat.st_ino):
            raise RuntimeError("temporary checksum input has an unexpected inode alias")
        os.fsync(final_fd)
    finally:
        os.close(final_fd)

    # Persist the final manifest inode and its published directory entry
    # before deleting either temporary name.
    os.fsync(directory_fd)

    os.unlink(sorted_name, dir_fd=directory_fd)
    os.unlink(temporary_name, dir_fd=directory_fd)

    # Persist temporary-name cleanup while retaining the final manifest link.
    os.fsync(directory_fd)
except (OSError, RuntimeError) as exc:
    raise SystemExit(
        "RELEASE-BLOCKED: checksum manifest durability finalization failed: " + str(exc)
    )
finally:
    if directory_fd >= 0:
        os.close(directory_fd)

print("PHX-MANIFEST-DURABILITY-PASS")
# PHX-MANIFEST-DURABILITY-END
PHX_MANIFEST_SYNC
echo "Release manifest written to $BUILD_DIR/RELEASE_MANIFEST.sha256 (PREVIEW ONLY)"
cat "$BUILD_DIR/RELEASE_MANIFEST.sha256"
echo "Appliance PREVIEW build completed; physical/signing gates still NO-GO."
"""

    # Create exclusively and non-executable. Publish execute permission only
    # after the complete script has been written and durably flushed through
    # the same descriptor, so a failed write leaves a fail-closed partial file.
    if not hasattr(os, "fchmod"):
        raise OSError("Safe build-script publication requires fchmod support")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        script_fd, parent_directory_fd = _open_new_file_without_symlink_parents(
            script_path,
            flags,
            0o600,
        )
    except FileExistsError:
        raise FileExistsError(
            f"Build script destination already exists; refusing to overwrite: {script_path}"
        ) from None

    try:
        try:
            script_file = os.fdopen(script_fd, "w", encoding="utf-8")
        except BaseException as fdopen_error:
            # fdopen owns the descriptor only when it returns a file object.
            # If stream construction fails first, close the raw descriptor
            # while the outer finally still releases the parent directory fd.
            try:
                os.close(script_fd)
            except OSError as close_error:
                if close_error.errno != errno.EBADF:
                    raise OSError(
                        "Build-script descriptor close failed after fdopen error: "
                        + str(close_error)
                    ) from fdopen_error
            raise
        with script_file as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
            # Persist the new directory entry while the file is still 0600.
            # If directory sync fails, the wrapper never becomes executable.
            os.fsync(parent_directory_fd)
            os.fchmod(f.fileno(), 0o755)
            # Persist the executable inode metadata after the mode change.
            # If that final sync fails, return the complete script to the
            # already-durable non-executable state before reporting failure.
            try:
                os.fsync(f.fileno())
            except OSError as publish_error:
                try:
                    os.fchmod(f.fileno(), 0o600)
                    os.fsync(f.fileno())
                except OSError as rollback_error:
                    raise OSError(
                        "Build-script executable-mode fsync failed and "
                        "non-executable rollback could not be confirmed: "
                        f"{rollback_error}"
                    ) from publish_error
                raise OSError(
                    "Build-script executable-mode fsync failed; "
                    "script reverted to non-executable mode"
                ) from publish_error
    finally:
        os.close(parent_directory_fd)


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

