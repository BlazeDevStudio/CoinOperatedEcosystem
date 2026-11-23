#!/usr/bin/env python3
"""Automated tests for Appliance Firmware Packager and ImageBuilder Configurator."""
import hashlib
import json
import os
import shlex
import stat
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest import mock

import run_imagebuilder_sandbox
import check_imagebuilder_sandbox_host
import package_appliance_firmware as packager

# Synthetic test-only site prefix; never a production or deployment allocation.
TEST_ONLY_SITE_ULA_PREFIX = "fd12:3456:789a::/48"


def trusted_bwrap_metadata_patches(
    module,
    candidate,
    *,
    parent_path="/usr/bin",
    parent_mode=0o755,
    parent_uid=0,
    file_mode=0o755,
    file_uid=0,
):
    """Model trusted root-owned system directories and the Bubblewrap inode."""
    original_lstat = module.os.lstat

    def fake_lstat(path):
        value = os.fspath(path)
        if value == candidate:
            return SimpleNamespace(st_mode=stat.S_IFREG | file_mode, st_uid=file_uid)
        if value == "/":
            return SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0)
        if value == "/usr":
            return SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0)
        if value == parent_path:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | parent_mode,
                st_uid=parent_uid,
            )
        return original_lstat(path)

    stack = ExitStack()
    stack.enter_context(
        mock.patch.object(module.os.path, "realpath", return_value=parent_path)
    )
    stack.enter_context(
        mock.patch.object(module.os, "lstat", side_effect=fake_lstat)
    )
    return stack


from package_appliance_firmware import (
    load_profile,
    generate_network_uci,
    stage_overlay,
    build_imagebuilder_cmd,
    generate_build_script,
    DEFAULT_ROOTFS
)


class TestPackageApplianceFirmware(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_appliance_")
        self._site_ula_patch = mock.patch.object(
            packager,
            "APPROVED_SITE_ULA_PREFIX",
            TEST_ONLY_SITE_ULA_PREFIX,
            create=True,
        )
        self._site_ula_patch.start()
        self.profiles = [
            "ew1200g-pro",
            "r281",
            "orangepi-r1-plus-lts",
            "orangepi-zero3",
            "archer-c6-v3",
            "gl-mt1300",
            "raspberrypi-4b",
            "xiaomi-4a-gigabit",
            "nanopi-r2s",
            "x86_64"
        ]

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        finally:
            self._site_ula_patch.stop()

    def test_load_all_profiles(self):
        for pid in self.profiles:
            p = load_profile(pid)
            self.assertEqual(p["profile_id"], pid)
            self.assertIn("target_architecture", p)
            self.assertIn("hardware", p)
            self.assertIn("networking", p)

    def test_load_profile_rejects_symlinked_profile_file(self):
        external_dir = os.path.join(self.temp_dir, "external-profile")
        os.makedirs(external_dir)
        external_profile = os.path.join(external_dir, "profile.json")
        expected_profile = load_profile("ew1200g-pro")
        with open(external_profile, "w", encoding="utf-8") as fp:
            json.dump(expected_profile, fp)

        linked_profile = os.path.join(self.temp_dir, "profile-link.json")
        os.symlink(external_profile, linked_profile)

        with self.assertRaisesRegex(ValueError, "symlink|symbolic|no-follow"):
            load_profile(linked_profile)

        with open(external_profile, "r", encoding="utf-8") as fp:
            self.assertEqual(json.load(fp), expected_profile)

    def test_load_profile_rejects_symlinked_parent_directory(self):
        external_dir = os.path.join(self.temp_dir, "external-profile-parent")
        os.makedirs(external_dir)
        external_profile = os.path.join(external_dir, "profile.json")
        expected_profile = load_profile("ew1200g-pro")
        with open(external_profile, "w", encoding="utf-8") as fp:
            json.dump(expected_profile, fp)

        linked_parent = os.path.join(self.temp_dir, "linked-profile-parent")
        os.symlink(external_dir, linked_parent)

        with self.assertRaisesRegex(ValueError, "symlink|symbolic|parent path"):
            load_profile(os.path.join(linked_parent, "profile.json"))

        with open(external_profile, "r", encoding="utf-8") as fp:
            self.assertEqual(json.load(fp), expected_profile)

    def test_load_profile_accepts_regular_custom_json_path(self):
        custom_profile = os.path.join(self.temp_dir, "custom-profile.json")
        expected_profile = load_profile("ew1200g-pro")
        with open(custom_profile, "w", encoding="utf-8") as fp:
            json.dump(expected_profile, fp)

        self.assertEqual(load_profile(custom_profile), expected_profile)

    def test_load_profile_rejects_oversized_profile_before_opening_stream(self):
        max_profile_bytes = 1024 * 1024
        custom_profile = os.path.join(self.temp_dir, "oversized-profile.json")
        with open(custom_profile, "wb") as profile_file:
            profile_file.truncate(max_profile_bytes + 1)

        with mock.patch.object(
            packager.os, "fdopen", wraps=packager.os.fdopen
        ) as fdopen:
            with self.assertRaisesRegex(
                ValueError, "exceeds maximum allowed size"
            ):
                load_profile(custom_profile)

        fdopen.assert_not_called()

    def test_load_profile_bounds_read_when_profile_grows_after_initial_stat(self):
        max_profile_bytes = 1024 * 1024
        custom_profile = os.path.join(self.temp_dir, "profile-growth-race.json")
        initial_content = b'{"profile_id":"ew1200g-pro"}\\n'
        with open(custom_profile, "wb") as profile_file:
            profile_file.write(initial_content)

        original_fdopen = packager.os.fdopen
        observed = {"grown": False, "read_sizes": []}

        class TrackingReader:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                self.stream.__enter__()
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return self.stream.__exit__(exc_type, exc_value, traceback)

            def fileno(self):
                return self.stream.fileno()

            def read(self, size=-1):
                observed["read_sizes"].append(size)
                return self.stream.read(size)

        def grow_after_open(descriptor, mode, *args, **kwargs):
            stream = original_fdopen(descriptor, mode, *args, **kwargs)
            with open(custom_profile, "ab") as replacement:
                replacement.write(
                    b" " * (max_profile_bytes + 1 - len(initial_content))
                )
                replacement.flush()
                os.fsync(replacement.fileno())
            observed["grown"] = True
            return TrackingReader(stream)

        with mock.patch.object(
            packager.os, "fdopen", side_effect=grow_after_open
        ):
            with self.assertRaisesRegex(
                ValueError, "exceeds maximum allowed size"
            ):
                load_profile(custom_profile)

        self.assertTrue(observed["grown"])
        self.assertEqual(
            observed["read_sizes"],
            [max_profile_bytes + 1],
            "profile reads must be capped at the limit plus one detection byte",
        )

    def test_load_profile_rejects_profile_modified_during_read(self):
        custom_profile = os.path.join(self.temp_dir, "profile-read-race.json")
        original_content = b'{"profile_id":"ew1200g-pro"}\n'
        replacement_content = b'{"profile_id":"zzzzzzzzzzz"}\n'
        self.assertEqual(len(original_content), len(replacement_content))
        with open(custom_profile, "wb") as fp:
            fp.write(original_content)

        original_fdopen = packager.os.fdopen
        mutation = {"performed": False}

        def fdopen_after_profile_mutation(descriptor, mode, *args, **kwargs):
            profile_file = original_fdopen(descriptor, mode, *args, **kwargs)
            if mode == "rb" and not mutation["performed"]:
                with open(custom_profile, "r+b") as replacement:
                    replacement.seek(original_content.index(b"ew1200g-pro"))
                    replacement.write(b"zzzzzzzzzzz")
                    replacement.flush()
                    os.fsync(replacement.fileno())
                mutation["performed"] = True
            return profile_file

        with mock.patch.object(
            packager.os,
            "fdopen",
            side_effect=fdopen_after_profile_mutation,
        ):
            with self.assertRaisesRegex(ValueError, "changed while reading"):
                load_profile(custom_profile)

        self.assertTrue(mutation["performed"])
        with open(custom_profile, "rb") as fp:
            self.assertEqual(fp.read(), replacement_content)

    def test_load_profile_rejects_duplicate_json_object_keys(self):
        duplicate_documents = [
            (
                "top-level",
                '{"profile_id": "ew1200g-pro", "profile_id": "r281"}',
                "profile_id",
            ),
            (
                "nested",
                '{"profile_id": "ew1200g-pro", "networking": {"default_vlan_ids": {"lan": 10, "lan": 20}}}',
                "lan",
            ),
        ]
        for label, document, duplicate_key in duplicate_documents:
            with self.subTest(label=label):
                custom_profile = os.path.join(
                    self.temp_dir, f"duplicate-{label}.json"
                )
                with open(custom_profile, "w", encoding="utf-8") as fp:
                    fp.write(document)

                with self.assertRaisesRegex(
                    ValueError,
                    rf"Duplicate JSON object key: '{duplicate_key}'",
                ):
                    load_profile(custom_profile)

    def test_generate_network_uci_ew1200g_pro(self):
        p = load_profile("ew1200g-pro")
        uci = generate_network_uci(p)
        self.assertIn("option name 'br-lan'", uci)
        self.assertIn("option vlan_filtering '1'", uci)
        self.assertIn("list ports 'lan1 lan2 lan3'", uci)
        self.assertIn("option device 'br-lan.10'", uci)
        self.assertIn("option device 'br-lan.20'", uci)
        self.assertIn("option device 'wan'", uci)
        self.assertIn(
            f"option ula_prefix '{TEST_ONLY_SITE_ULA_PREFIX}'",
            uci,
        )

    def test_generate_network_uci_rejects_unapproved_or_invalid_site_ula_prefix(self):
        invalid_prefixes = [
            None,
            "fd00:db8:blaze::/48",
            "fd12:3456:789a::/64",
            "2001:db8::/48",
            "fe80::/48",
            "ff00::/48",
            "::/48",
            "fd00::/8",
            "fd12:3456:789a::1/48",
        ]
        for prefix in invalid_prefixes:
            with self.subTest(prefix=prefix):
                with mock.patch.object(
                    packager, "APPROVED_SITE_ULA_PREFIX", prefix, create=True
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        "approved site-scoped RFC 4193 ULA /48",
                    ):
                        generate_network_uci(load_profile("ew1200g-pro"))

    def test_production_default_site_ula_remains_unconfigured_and_fails_closed(self):
        # The class normally patches a synthetic test-only site prefix in setUp.
        # Remove that fixture temporarily to verify the actual production default.
        self._site_ula_patch.stop()
        try:
            self.assertIsNone(
                packager.APPROVED_SITE_ULA_PREFIX,
                "production ULA must remain unset until site-prefix authority is approved",
            )
            with self.assertRaisesRegex(
                ValueError,
                "approved site-scoped RFC 4193 ULA /48",
            ):
                generate_network_uci(load_profile("ew1200g-pro"))
        finally:
            self._site_ula_patch.start()

    def test_generate_network_uci_uses_real_newlines_and_tabs(self):
        profile = load_profile("ew1200g-pro")
        uci = generate_network_uci(profile)

        self.assertIn(
            "\n",
            uci,
            "Generated UCI must contain real newline characters between sections",
        )
        self.assertNotIn(
            "\\n",
            uci,
            "Generated UCI must not contain literal backslash-n sequences",
        )
        self.assertNotIn(
            "\\t",
            uci,
            "Generated UCI must not contain literal backslash-t sequences",
        )
        self.assertIn("\toption name 'br-lan'", uci)
        self.assertIn("\nconfig interface 'wan'\n", uci)
        self.assertGreater(len(uci.splitlines()), 10)

    def test_generate_network_uci_rejects_profile_uci_injection(self):
        mutations = [
            (
                "wan_interface",
                lambda profile: profile["networking"].__setitem__(
                    "wan_interface",
                    "wan'\\nconfig interface 'injected"
                ),
            ),
            (
                "port_interface",
                lambda profile: profile["networking"]["ports"][1].__setitem__(
                    "interface",
                    "lan1'\\nconfig interface 'injected"
                ),
            ),
            (
                "guest_vlan",
                lambda profile: profile["networking"]["default_vlan_ids"].__setitem__(
                    "guest",
                    "10'\\nconfig interface 'injected"
                ),
            ),
        ]
        for field, mutate in mutations:
            with self.subTest(field=field):
                profile = load_profile("ew1200g-pro")
                mutate(profile)
                with self.assertRaisesRegex(
                    ValueError, "Invalid (network interface|VLAN ID)"
                ):
                    generate_network_uci(profile)

    def test_generate_network_uci_rejects_duplicate_isolation_vlans(self):
        duplicate_pairs = [
            ("lan", "guest"),
            ("lan", "vendo"),
            ("guest", "vendo"),
        ]
        for first, second in duplicate_pairs:
            with self.subTest(first=first, second=second):
                profile = load_profile("ew1200g-pro")
                vlan_ids = profile["networking"]["default_vlan_ids"]
                vlan_ids[second] = vlan_ids[first]
                with self.assertRaisesRegex(
                    ValueError, "LAN, guest, and vendo VLAN IDs must be distinct"
                ):
                    generate_network_uci(profile)

    def test_generate_network_uci_orangepi(self):
        p = load_profile("orangepi-r1-plus-lts")
        uci = generate_network_uci(p)
        self.assertIn("option name 'br-lan'", uci)
        self.assertIn("list ports 'eth1'", uci)
        self.assertIn("option device 'eth0'", uci)

    def test_generate_network_uci_orangepi_zero3(self):
        p = load_profile("orangepi-zero3")
        uci = generate_network_uci(p)
        self.assertIn("option name 'br-lan'", uci)
        self.assertIn("list ports 'wlan0'", uci)
        self.assertIn("option device 'eth0'", uci)

    def test_build_imagebuilder_cmd(self):
        p = load_profile("ew1200g-pro")
        cmd = build_imagebuilder_cmd(p, "/tmp/staging", include_rental=False)
        self.assertTrue(cmd.startswith("make image PROFILE=ew1200g-pro"))
        self.assertIn("nftables", cmd)
        self.assertIn("firewall4", cmd)
        self.assertNotIn("openssl-util", cmd)
        self.assertIn("FILES=/tmp/staging", shlex.split(cmd))

        # Rental enabled
        cmd_rental = build_imagebuilder_cmd(p, "/tmp/staging", include_rental=True)
        self.assertIn("openssl-util", cmd_rental)

    def test_stage_overlay_execution(self):
        staging_dest = os.path.join(self.temp_dir, "staging_ew1200g")
        p = load_profile("ew1200g-pro")
        manifest = stage_overlay(p, DEFAULT_ROOTFS, staging_dest)

        self.assertEqual(manifest["profile_id"], "ew1200g-pro")
        self.assertGreater(manifest["overlay_size_kb"], 50)
        self.assertFalse(manifest["include_rental"])
        self.assertTrue(os.path.isfile(os.path.join(staging_dest, "etc", "config", "network")))
        self.assertTrue(os.path.isfile(os.path.join(staging_dest, "etc", "blazepwifi", "appliance_profile.json")))

        # Check executable permissions on cgi-bin
        api_path = os.path.join(staging_dest, "www", "blazepwifi", "cgi-bin", "api")
        self.assertTrue(os.path.isfile(api_path))
        mode = os.stat(api_path).st_mode
        self.assertTrue(bool(mode & 0o111), "cgi-bin/api should be executable (0755)")

    def test_stage_overlay_with_rental(self):
        staging_dest = os.path.join(self.temp_dir, "staging_rental")
        p = load_profile("orangepi-zero3")
        manifest = stage_overlay(p, DEFAULT_ROOTFS, staging_dest, include_rental=True)

        self.assertTrue(manifest["include_rental"])
        self.assertTrue(os.path.isfile(os.path.join(staging_dest, "usr", "lib", "blazerental", "core.sh")))
        self.assertTrue(os.path.isfile(os.path.join(staging_dest, "usr", "sbin", "blazerentalctl")))
        self.assertTrue(os.path.isfile(os.path.join(staging_dest, "www", "cgi-bin", "blazerental")))
        self.assertTrue(os.path.isdir(os.path.join(staging_dest, "etc", "blazerental")))
        rental_etc_path = os.path.join(staging_dest, "etc", "blazerental")
        rental_etc_mode = os.stat(rental_etc_path).st_mode & 0o777
        self.assertEqual(
            rental_etc_mode,
            0o700,
            "etc/blazerental must retain its private mode after permission normalization",
        )

        ctl_path = os.path.join(staging_dest, "usr", "sbin", "blazerentalctl")
        mode = os.stat(ctl_path).st_mode
        self.assertTrue(bool(mode & 0o111), "blazerentalctl must be executable (0755)")

        cgi_path = os.path.join(staging_dest, "www", "cgi-bin", "blazerental")
        mode = os.stat(cgi_path).st_mode
        self.assertTrue(bool(mode & 0o111), "cgi-bin/blazerental must be executable (0755)")

    def test_ensure_staging_directory_closes_child_fd_on_baseexception_during_identity_check(self):
        for exception_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(interruption=exception_type.__name__):
                staging_root = os.path.join(
                    self.temp_dir,
                    f"ensure-interrupt-{exception_type.__name__.lower()}",
                )
                os.makedirs(staging_root)

                child_fd = {"value": None}
                interrupted = {"value": False}
                original_open = os.open
                original_fstat = os.fstat

                def open_and_capture(path, flags, mode=0o777, *, dir_fd=None):
                    descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
                    if os.fspath(path) == "etc" and dir_fd is not None:
                        child_fd["value"] = descriptor
                    return descriptor

                def fstat_and_interrupt(descriptor):
                    if (
                        descriptor == child_fd["value"]
                        and not interrupted["value"]
                    ):
                        interrupted["value"] = True
                        raise exception_type("injected child identity interruption")
                    return original_fstat(descriptor)

                patched_open = mock.Mock(side_effect=open_and_capture)
                supported_dir_fd = set(os.supports_dir_fd)
                supported_dir_fd.add(patched_open)
                with mock.patch.object(
                    packager.os, "open", new=patched_open
                ), mock.patch.object(
                    packager.os, "fstat", side_effect=fstat_and_interrupt
                ), mock.patch.object(
                    packager.os, "supports_dir_fd", supported_dir_fd
                ):
                    with self.assertRaisesRegex(
                        exception_type, "injected child identity interruption"
                    ):
                        packager._ensure_staging_directory(staging_root, "etc")

                self.assertTrue(interrupted["value"])
                self.assertIsInstance(child_fd["value"], int)
                with self.assertRaises(OSError):
                    original_fstat(child_fd["value"])

    def test_ensure_staging_directory_rejects_parent_swapped_to_symlink_during_walk(self):
        staging_root = os.path.join(self.temp_dir, "ensure-staging-root")
        etc_path = os.path.join(staging_root, "etc")
        external_dir = os.path.join(self.temp_dir, "operator-owned-directory")
        os.makedirs(staging_root)
        os.makedirs(external_dir)

        sentinel_path = os.path.join(external_dir, "operator-owned.txt")
        with open(sentinel_path, "wb") as fp:
            fp.write(b"KEEP-OPERATOR-DIRECTORY")

        root_stat = os.stat(staging_root)
        swapped = {"value": False}
        original_lstat = os.lstat
        original_open = os.open
        original_fstat = os.fstat

        def swap_directory_entry():
            if swapped["value"]:
                return
            os.rmdir(etc_path)
            os.symlink(external_dir, etc_path, target_is_directory=True)
            swapped["value"] = True

        def lstat_then_swap(path, *args, **kwargs):
            result = original_lstat(path, *args, **kwargs)
            if os.fspath(path) == etc_path:
                # Reproduce the old mkdir/lstat gap: the returned stat still
                # describes a directory after its pathname has been replaced.
                swap_directory_entry()
            return result

        def open_then_swap(path, flags, mode=0o777, *, dir_fd=None):
            fd = original_open(path, flags, mode, dir_fd=dir_fd)
            if os.fspath(path) == "etc" and dir_fd is not None:
                parent_stat = original_fstat(dir_fd)
                if (parent_stat.st_dev, parent_stat.st_ino) == (
                    root_stat.st_dev,
                    root_stat.st_ino,
                ):
                    # The descriptor pins the opened directory while its
                    # pathname is replaced. A safe walker must detect that
                    # the directory entry no longer names the opened inode.
                    swap_directory_entry()
            return fd

        patched_open = mock.Mock(side_effect=open_then_swap)
        supported_dir_fd = set(os.supports_dir_fd)
        supported_dir_fd.add(patched_open)
        with mock.patch.object(
            packager.os, "lstat", side_effect=lstat_then_swap
        ), mock.patch.object(
            packager.os, "open", new=patched_open
        ), mock.patch.object(
            packager.os, "supports_dir_fd", supported_dir_fd
        ):
            with self.assertRaisesRegex(
                ValueError, "Staging directory path changed while opening"
            ):
                packager._ensure_staging_directory(staging_root, "etc/config")

        self.assertTrue(swapped["value"])
        self.assertTrue(os.path.islink(etc_path))
        self.assertFalse(os.path.lexists(os.path.join(external_dir, "config")))
        with open(sentinel_path, "rb") as fp:
            self.assertEqual(fp.read(), b"KEEP-OPERATOR-DIRECTORY")

    def test_write_staging_bytes_rejects_parent_replaced_with_symlink_after_lstat(self):
        staging_root = os.path.join(self.temp_dir, "write-race-staging")
        destination_dir = os.path.join(staging_root, "etc", "config")
        external_dir = os.path.join(self.temp_dir, "operator-owned-config")
        os.makedirs(destination_dir)
        os.makedirs(external_dir)

        sentinel_path = os.path.join(external_dir, "operator-owned.txt")
        with open(sentinel_path, "wb") as fp:
            fp.write(b"KEEP-OPERATOR-CONFIG")

        destination_path = os.path.join(destination_dir, "network")
        swapped = {"value": False}
        original_lstat = os.lstat

        def lstat_then_swap_parent(path, *args, **kwargs):
            try:
                result = original_lstat(path, *args, **kwargs)
            except FileNotFoundError:
                if os.fspath(path) == destination_path and not swapped["value"]:
                    os.rmdir(destination_dir)
                    os.symlink(external_dir, destination_dir, target_is_directory=True)
                    swapped["value"] = True
                raise
            return result

        # Replace the destination parent after the final-file lstat but before
        # open. Path-based O_NOFOLLOW on the final filename does not protect
        # this parent-directory race.
        with mock.patch.object(
            packager.os, "lstat", side_effect=lstat_then_swap_parent
        ):
            with self.assertRaisesRegex(
                ValueError, "Staged file destination parent path contains a symlink"
            ):
                packager._write_staging_bytes(
                    destination_dir, "network", b"config=operator-overwrite\\n"
                )

        self.assertTrue(swapped["value"])
        self.assertTrue(os.path.islink(destination_dir))
        self.assertFalse(os.path.lexists(os.path.join(external_dir, "network")))
        with open(sentinel_path, "rb") as fp:
            self.assertEqual(fp.read(), b"KEEP-OPERATOR-CONFIG")

    def test_write_staging_bytes_replaces_hardlink_without_modifying_external_target(self):
        staging_dir = os.path.join(self.temp_dir, "hardlink-write-staging")
        os.makedirs(staging_dir)

        external_path = os.path.join(self.temp_dir, "operator-owned-hardlink-target")
        destination_path = os.path.join(staging_dir, "network")
        with open(external_path, "wb") as fp:
            fp.write(b"KEEP-OPERATOR-OWNED-CONTENT")

        linked = {"value": False}
        original_lstat = os.lstat

        def lstat_then_insert_hardlink(path, *args, **kwargs):
            try:
                return original_lstat(path, *args, **kwargs)
            except FileNotFoundError:
                if os.fspath(path) == destination_path and not linked["value"]:
                    os.link(external_path, destination_path)
                    linked["value"] = True
                raise

        # A hardlink inserted after lstat is not a symlink: opening and
        # truncating it modifies the operator-owned inode outside staging.
        with mock.patch.object(
            packager.os, "lstat", side_effect=lstat_then_insert_hardlink
        ):
            packager._write_staging_bytes(
                staging_dir, "network", b"config generated by packager\\n"
            )

        self.assertTrue(linked["value"])
        with open(external_path, "rb") as fp:
            self.assertEqual(fp.read(), b"KEEP-OPERATOR-OWNED-CONTENT")
        with open(destination_path, "rb") as fp:
            self.assertEqual(fp.read(), b"config generated by packager\\n")
        external_stat = os.stat(external_path)
        destination_stat = os.stat(destination_path)
        self.assertNotEqual(
            (external_stat.st_dev, external_stat.st_ino),
            (destination_stat.st_dev, destination_stat.st_ino),
        )
        self.assertEqual(external_stat.st_nlink, 1)
        self.assertEqual(destination_stat.st_nlink, 1)

    def test_copy_staging_file_rejects_source_modified_during_read(self):
        source_dir = os.path.join(self.temp_dir, "rental-source-read-race")
        destination_dir = os.path.join(self.temp_dir, "rental-destination-read-race")
        os.makedirs(source_dir)
        os.makedirs(destination_dir)

        source_path = os.path.join(source_dir, "core.sh")
        destination_path = os.path.join(destination_dir, "core.sh")
        original_content = b"trusted rental source"
        replacement_content = b"mutated rental source"
        self.assertEqual(len(original_content), len(replacement_content))
        with open(source_path, "wb") as fp:
            fp.write(original_content)

        source_stat = os.stat(source_path, follow_symlinks=False)
        original_fdopen = os.fdopen
        mutation = {"performed": False}

        class MutatingReader:
            def __init__(self, wrapped):
                self.wrapped = wrapped

            def __enter__(self):
                self.wrapped.__enter__()
                return self

            def __exit__(self, exc_type, exc, traceback):
                return self.wrapped.__exit__(exc_type, exc, traceback)

            def fileno(self):
                return self.wrapped.fileno()

            def read(self, *args, **kwargs):
                data = self.wrapped.read(*args, **kwargs)
                if not mutation["performed"]:
                    with open(source_path, "r+b") as fp:
                        fp.seek(0)
                        fp.write(replacement_content)
                        fp.flush()
                        os.fsync(fp.fileno())
                    mutation["performed"] = True
                return data

        def fdopen_after_source_mutation(descriptor, mode="r", *args, **kwargs):
            opened_stat = os.fstat(descriptor)
            if (opened_stat.st_dev, opened_stat.st_ino) == (
                source_stat.st_dev,
                source_stat.st_ino,
            ):
                return MutatingReader(original_fdopen(descriptor, mode, *args, **kwargs))
            return original_fdopen(descriptor, mode, *args, **kwargs)

        # Change the already-read source bytes in place before the packager
        # accepts the read. The same inode and file size are deliberately kept.
        with mock.patch.object(
            packager.os, "fdopen", side_effect=fdopen_after_source_mutation
        ):
            with self.assertRaisesRegex(ValueError, "changed while reading"):
                packager._copy_staging_file(source_path, destination_dir, "core.sh")

        self.assertTrue(mutation["performed"])
        self.assertFalse(
            os.path.lexists(destination_path),
            "A source that changes during the read must never be copied into staging",
        )
        with open(source_path, "rb") as fp:
            self.assertEqual(fp.read(), replacement_content)

    def test_copy_staging_file_rejects_source_replaced_with_symlink_after_lstat(self):
        source_dir = os.path.join(self.temp_dir, "rental-source-race")
        destination_dir = os.path.join(self.temp_dir, "rental-destination-race")
        os.makedirs(source_dir)
        os.makedirs(destination_dir)

        source_path = os.path.join(source_dir, "core.sh")
        external_path = os.path.join(self.temp_dir, "operator-owned-core.sh")
        destination_path = os.path.join(destination_dir, "core.sh")
        with open(source_path, "wb") as fp:
            fp.write(b"trusted rental source")
        with open(external_path, "wb") as fp:
            fp.write(b"operator-owned sentinel")

        swapped = {"value": False}
        original_lstat = os.lstat

        def lstat_then_swap_source(path, *args, **kwargs):
            result = original_lstat(path, *args, **kwargs)
            if os.fspath(path) == source_path and not swapped["value"]:
                os.unlink(source_path)
                os.symlink(external_path, source_path)
                swapped["value"] = True
            return result

        # Simulate replacement in the gap between the regular-file lstat and open.
        with mock.patch.object(
            packager.os, "lstat", side_effect=lstat_then_swap_source
        ):
            with self.assertRaises(ValueError):
                packager._copy_staging_file(source_path, destination_dir, "core.sh")

        self.assertTrue(swapped["value"])
        self.assertTrue(os.path.islink(source_path))
        self.assertFalse(os.path.lexists(destination_path))
        with open(external_path, "rb") as fp:
            self.assertEqual(fp.read(), b"operator-owned sentinel")

    def test_copy_staging_file_rejects_symlinked_source_parent(self):
        external_source_dir = os.path.join(self.temp_dir, "operator-owned-rental")
        source_alias_dir = os.path.join(self.temp_dir, "rental-source-alias")
        destination_dir = os.path.join(self.temp_dir, "rental-destination-parent")
        os.makedirs(external_source_dir)
        os.makedirs(destination_dir)

        external_source = os.path.join(external_source_dir, "core.sh")
        destination_path = os.path.join(destination_dir, "core.sh")
        with open(external_source, "wb") as fp:
            fp.write(b"operator-owned source sentinel")
        os.symlink(external_source_dir, source_alias_dir, target_is_directory=True)
        source_path = os.path.join(source_alias_dir, "core.sh")

        # O_NOFOLLOW on the final filename is insufficient if an ancestor
        # directory is a symlink. Every parent component must be opened by
        # descriptor with O_DIRECTORY | O_NOFOLLOW.
        with self.assertRaisesRegex(
            ValueError, "Rental source file parent path contains a symlink"
        ):
            packager._copy_staging_file(source_path, destination_dir, "core.sh")

        self.assertTrue(os.path.islink(source_alias_dir))
        self.assertFalse(os.path.lexists(destination_path))
        with open(external_source, "rb") as fp:
            self.assertEqual(fp.read(), b"operator-owned source sentinel")

    def test_stage_overlay_file_modes_are_relative_to_staging_root(self):
        # The selected staging parent deliberately contains an executable-path
        # marker. Permission policy must classify paths relative to the overlay,
        # not by searching the absolute temporary destination.
        source_rootfs = os.path.join(self.temp_dir, "mode-source")
        utility_dir = os.path.join(source_rootfs, "usr", "sbin")
        os.makedirs(utility_dir)
        utility_source = os.path.join(utility_dir, "diagnostic")
        with open(utility_source, "w", encoding="utf-8") as fp:
            fp.write("#!/bin/sh\\nexit 0\\n")
        os.chmod(utility_source, 0o644)

        staging_parent = os.path.join(self.temp_dir, "usr", "sbin")
        os.makedirs(staging_parent)
        staging_dest = os.path.join(staging_parent, "staging")
        stage_overlay(load_profile("ew1200g-pro"), source_rootfs, staging_dest)

        network_path = os.path.join(staging_dest, "etc", "config", "network")
        profile_path = os.path.join(staging_dest, "etc", "blazepwifi", "appliance_profile.json")
        staged_utility = os.path.join(staging_dest, "usr", "sbin", "diagnostic")

        self.assertEqual(
            os.stat(network_path).st_mode & 0o777,
            0o644,
            "generated UCI config must remain non-executable when the staging root contains /usr/sbin/",
        )
        self.assertEqual(
            os.stat(profile_path).st_mode & 0o777,
            0o644,
            "generated profile metadata must remain non-executable when the staging root contains /usr/sbin/",
        )
        self.assertEqual(
            os.stat(staged_utility).st_mode & 0o777,
            0o755,
            "actual overlay usr/sbin utilities must remain executable",
        )

    def test_calculate_overlay_size_closes_child_descriptor_when_fstat_is_interrupted(self):
        for interruption_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(interruption=interruption_type.__name__):
                staging_dir = os.path.join(
                    self.temp_dir,
                    f"overlay-size-child-fstat-{interruption_type.__name__.lower()}",
                )
                os.makedirs(os.path.join(staging_dir, "nested"))
                captured = {"child_fd": None}
                original_open = os.open
                original_fstat = os.fstat

                def capture_child_directory(path, flags, mode=0o777, *, dir_fd=None):
                    descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
                    if (
                        os.fspath(path) == "nested"
                        and dir_fd is not None
                        and flags & os.O_DIRECTORY
                        and captured["child_fd"] is None
                    ):
                        captured["child_fd"] = descriptor
                    return descriptor

                def interrupt_child_fstat(descriptor):
                    if descriptor == captured["child_fd"]:
                        raise interruption_type(
                            "simulated child directory fstat interruption"
                        )
                    return original_fstat(descriptor)

                supported_dir_fd = set(os.supports_dir_fd)
                with mock.patch.object(
                    packager.os,
                    "open",
                    side_effect=capture_child_directory,
                ) as patched_open:
                    supported_dir_fd.add(patched_open)
                    with mock.patch.object(
                        packager.os,
                        "supports_dir_fd",
                        supported_dir_fd,
                    ):
                        with mock.patch.object(
                            packager.os,
                            "fstat",
                            side_effect=interrupt_child_fstat,
                        ):
                            with self.assertRaisesRegex(
                                interruption_type,
                                "simulated child directory fstat interruption",
                            ):
                                packager.calculate_overlay_size(staging_dir)

                self.assertIsNotNone(
                    captured["child_fd"],
                    "the child-directory open boundary was not reached",
                )
                try:
                    original_fstat(captured["child_fd"])
                except OSError:
                    descriptor_closed = True
                else:
                    os.close(captured["child_fd"])
                    descriptor_closed = False
                self.assertTrue(
                    descriptor_closed,
                    "the in-flight child directory descriptor must close when fstat is interrupted",
                )

    def test_calculate_overlay_size_does_not_follow_file_replaced_with_symlink_before_open(self):
        staging_dir = os.path.join(self.temp_dir, "overlay-size-race")
        os.makedirs(staging_dir)

        staged_file = os.path.join(staging_dir, "payload.bin")
        external_file = os.path.join(self.temp_dir, "operator-owned-payload.bin")
        with open(staged_file, "wb") as fp:
            fp.write(b"x")
        with open(external_file, "wb") as fp:
            fp.write(b"KEEP-OPERATOR-OWNED-CONTENT" * 256)

        swapped = {"value": False}
        held_fd = {"value": None}
        original_open = os.open

        def open_then_swap_final_file(path, flags, mode=0o777, *, dir_fd=None):
            if (
                os.fspath(path) == "payload.bin"
                and dir_fd is not None
                and not swapped["value"]
            ):
                # Keep the original inode alive so the filesystem cannot reuse
                # its number for the replacement symlink during this test.
                held_fd["value"] = original_open(
                    staged_file,
                    os.O_PATH | os.O_NOFOLLOW,
                )
                os.unlink(staged_file)
                os.symlink(external_file, staged_file)
                swapped["value"] = True
            return original_open(path, flags, mode, dir_fd=dir_fd)

        supported_dir_fd = set(os.supports_dir_fd)
        try:
            with mock.patch.object(
                packager.os, "open", side_effect=open_then_swap_final_file
            ) as patched_open:
                supported_dir_fd.add(patched_open)
                with mock.patch.object(packager.os, "supports_dir_fd", supported_dir_fd):
                    size_kib = packager.calculate_overlay_size(staging_dir)
        finally:
            if held_fd["value"] is not None:
                os.close(held_fd["value"])

        self.assertTrue(swapped["value"], "race fixture did not reach the file-open boundary")
        self.assertTrue(os.path.islink(staged_file))
        self.assertEqual(size_kib, 0, "external symlink target must not enter the overlay byte budget")
        with open(external_file, "rb") as fp:
            self.assertEqual(
                fp.read(),
                b"KEEP-OPERATOR-OWNED-CONTENT" * 256,
            )

    def test_calculate_overlay_size_counts_symlink_replaced_with_file_before_open(self):
        staging_dir = os.path.join(self.temp_dir, "overlay-size-reverse-race")
        os.makedirs(staging_dir)

        staged_file = os.path.join(staging_dir, "payload.bin")
        external_file = os.path.join(self.temp_dir, "operator-owned-target.bin")
        with open(external_file, "wb") as fp:
            fp.write(b"KEEP-OPERATOR-OWNED-CONTENT" * 256)
        os.symlink(external_file, staged_file)

        payload = b"new-staged-file" * 256
        swapped = {"value": False}
        held_fd = {"value": None}
        original_open = os.open

        def open_then_replace_symlink(path, flags, mode=0o777, *, dir_fd=None):
            if (
                os.fspath(path) == "payload.bin"
                and dir_fd is not None
                and not swapped["value"]
            ):
                held_fd["value"] = original_open(
                    staged_file,
                    os.O_PATH | os.O_NOFOLLOW,
                )
                os.unlink(staged_file)
                with open(staged_file, "wb") as fp:
                    fp.write(payload)
                swapped["value"] = True
            return original_open(path, flags, mode, dir_fd=dir_fd)

        supported_dir_fd = set(os.supports_dir_fd)
        try:
            with mock.patch.object(
                packager.os, "open", side_effect=open_then_replace_symlink
            ) as patched_open:
                supported_dir_fd.add(patched_open)
                with mock.patch.object(packager.os, "supports_dir_fd", supported_dir_fd):
                    size_kib = packager.calculate_overlay_size(staging_dir)
        finally:
            if held_fd["value"] is not None:
                os.close(held_fd["value"])

        self.assertTrue(swapped["value"], "race fixture did not reach the symlink-open boundary")
        self.assertFalse(os.path.islink(staged_file))
        self.assertEqual(size_kib, (len(payload) + 1023) // 1024)
        with open(external_file, "rb") as fp:
            self.assertEqual(
                fp.read(),
                b"KEEP-OPERATOR-OWNED-CONTENT" * 256,
            )

    def test_calculate_overlay_size_rejects_directory_entry_added_after_listing_snapshot(self):
        staging_dir = os.path.join(self.temp_dir, "overlay-size-entry-addition")
        os.makedirs(staging_dir)
        with open(os.path.join(staging_dir, "payload.bin"), "wb") as fp:
            fp.write(b"x")

        late_path = os.path.join(staging_dir, "late.bin")
        original_listdir = os.listdir
        added = {"value": False}

        def listdir_then_add_entry(directory_fd):
            names = original_listdir(directory_fd)
            if not added["value"]:
                with open(late_path, "wb") as fp:
                    fp.write(b"late-overlay-entry" * 1024)
                added["value"] = True
            return names

        with mock.patch.object(
            packager.os, "listdir", side_effect=listdir_then_add_entry
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Staged directory changed during overlay size walk",
            ):
                packager.calculate_overlay_size(staging_dir)

        self.assertTrue(added["value"], "the post-listing directory mutation must execute")
        self.assertTrue(os.path.isfile(late_path))

    def test_calculate_overlay_size_rejects_staging_root_replaced_after_scan(self):
        staging_dir = os.path.join(self.temp_dir, "overlay-size-root-replacement")
        displaced_dir = os.path.join(self.temp_dir, "overlay-size-root-displaced")
        replacement_dir = os.path.join(self.temp_dir, "overlay-size-root-replacement-new")
        os.makedirs(staging_dir)
        os.makedirs(replacement_dir)
        with open(os.path.join(staging_dir, "original.bin"), "wb") as fp:
            fp.write(b"original")
        with open(os.path.join(replacement_dir, "replacement.bin"), "wb") as fp:
            fp.write(b"replacement")

        original_listdir = os.listdir
        replaced = {"value": False}

        def listdir_then_replace_root(directory_fd):
            names = original_listdir(directory_fd)
            if not replaced["value"]:
                os.rename(staging_dir, displaced_dir)
                os.rename(replacement_dir, staging_dir)
                replaced["value"] = True
            return names

        with mock.patch.object(
            packager.os, "listdir", side_effect=listdir_then_replace_root
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Staging root changed during overlay size walk",
            ):
                packager.calculate_overlay_size(staging_dir)

        self.assertTrue(replaced["value"], "the staging-root replacement must execute")
        self.assertTrue(os.path.isfile(os.path.join(displaced_dir, "original.bin")))
        self.assertTrue(os.path.isfile(os.path.join(staging_dir, "replacement.bin")))

    def test_flash_overflow_guard(self):
        staging_dest = os.path.join(self.temp_dir, "staging_overflow")
        p = load_profile("ew1200g-pro")
        # Artificially constrain flash budget
        p["hardware"]["flash_kb"] = 100
        p["hardware"]["min_free_overlay_kb"] = 50
        with self.assertRaises(ValueError) as ctx:
            stage_overlay(p, DEFAULT_ROOTFS, staging_dest)
        self.assertIn("exceeds flash budget", str(ctx.exception))

    def test_generate_network_uci_archer_c6(self):
        p = load_profile("archer-c6-v3")
        uci = generate_network_uci(p)
        self.assertIn("option name 'br-lan'", uci)
        self.assertIn("option vlan_filtering '1'", uci)
        self.assertIn("list ports 'lan1 lan2 lan3 lan4'", uci)
        self.assertIn("option device 'wan'", uci)

    def test_generate_build_script(self):
        p = load_profile("gl-mt1300")
        manifest = stage_overlay(p, DEFAULT_ROOTFS, os.path.join(self.temp_dir, "staging_gl"))
        script_path = os.path.join(self.temp_dir, "build_gl.sh")
        generate_build_script(manifest, script_path)

        self.assertTrue(os.path.isfile(script_path))
        mode = os.stat(script_path).st_mode
        self.assertTrue(bool(mode & 0o111), "Build script must be executable (0755)")

        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("make image PROFILE=gl-mt1300", content)
        self.assertIn("RELEASE_MANIFEST.sha256", content)
        self.assertIn(
            '--timeout-seconds "${PHX_IMAGEBUILDER_TIMEOUT_SECONDS:-3600}"',
            content,
            "Generated wrapper must forward the operator's bounded per-invocation timeout",
        )

    def test_generated_wrapper_rejects_replaced_staging_directory_symlink(self):
        profile = load_profile("gl-mt1300")
        staging_dir = os.path.join(self.temp_dir, "staging-replaced-by-link")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging_dir)
        wrapper = os.path.join(self.temp_dir, "staging-symlink-build.sh")
        generate_build_script(manifest, wrapper)

        # Simulate an operator path being replaced after staging and wrapper
        # generation. The external directory is deliberately not a rootfs.
        real_staging = os.path.join(self.temp_dir, "staging-original")
        os.rename(staging_dir, real_staging)
        external_staging = os.path.join(self.temp_dir, "operator-owned-staging")
        os.makedirs(external_staging)
        sentinel_path = os.path.join(external_staging, "operator-owned.txt")
        with open(sentinel_path, "w", encoding="utf-8") as fp:
            fp.write("KEEP-OPERATOR-STAGING\n")
        os.symlink(external_staging, staging_dir, target_is_directory=True)

        builder = os.path.join(self.temp_dir, "staging-symlink-builder")
        os.makedirs(builder)
        make_marker = os.path.join(self.temp_dir, "make-must-not-run")
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write("image:\n\t@printf 'MAKE-RAN' > " + shlex.quote(make_marker) + "\n")

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("staged rootfs path contains a symlink", result.stderr)
        self.assertFalse(
            os.path.exists(make_marker),
            "ImageBuilder must not run when the staged rootfs path is replaced by a symlink",
        )
        self.assertTrue(os.path.islink(staging_dir))
        self.assertTrue(os.path.isdir(real_staging))
        with open(sentinel_path, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "KEEP-OPERATOR-STAGING\n")

    def test_generated_build_script_passes_posix_shell_syntax_check(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile,
            DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "staging_shell_syntax")
        )
        script_path = os.path.join(self.temp_dir, "shell-syntax-build.sh")
        generate_build_script(manifest, script_path)

        result = subprocess.run(
            ["sh", "-n", script_path],
            capture_output=True,
            text=True
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"Generated ImageBuilder wrapper is not valid POSIX shell: {result.stderr}"
        )

    def test_generate_build_script_fsyncs_parent_directory_before_publish(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "durable-directory-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        script_path = os.path.join(self.temp_dir, "durable-directory-build.sh")

        events = []
        original_fsync = os.fsync
        original_fchmod = os.fchmod

        def record_fsync(file_descriptor):
            mode = os.fstat(file_descriptor).st_mode
            events.append(("fsync", "directory" if stat.S_ISDIR(mode) else "file"))
            return original_fsync(file_descriptor)

        def record_fchmod(file_descriptor, mode):
            events.append(("fchmod", mode))
            return original_fchmod(file_descriptor, mode)

        with mock.patch.object(packager.os, "fsync", side_effect=record_fsync):
            with mock.patch.object(packager.os, "fchmod", side_effect=record_fchmod):
                generate_build_script(manifest, script_path)

        self.assertEqual(
            events,
            [
                ("fsync", "file"),
                ("fsync", "directory"),
                ("fchmod", 0o755),
                ("fsync", "file"),
            ],
            "The directory entry must be durable while the new script is still non-executable; "
            "only then may the executable mode be published and synced",
        )
        self.assertEqual(os.stat(script_path).st_mode & 0o777, 0o755)

    def test_generate_build_script_fsyncs_executable_mode_after_chmod(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "durable-mode-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        script_path = os.path.join(self.temp_dir, "durable-mode-build.sh")

        events = []
        original_fsync = os.fsync
        original_fchmod = os.fchmod

        def record_fsync(file_descriptor):
            if not stat.S_ISDIR(os.fstat(file_descriptor).st_mode):
                events.append("fsync")
            return original_fsync(file_descriptor)

        def record_fchmod(file_descriptor, mode):
            events.append("fchmod")
            return original_fchmod(file_descriptor, mode)

        with mock.patch.object(packager.os, "fsync", side_effect=record_fsync):
            with mock.patch.object(packager.os, "fchmod", side_effect=record_fchmod):
                generate_build_script(manifest, script_path)

        self.assertEqual(
            events,
            ["fsync", "fchmod", "fsync"],
            "The executable mode must be fsynced after fchmod, not only the script bytes before it",
        )
        self.assertEqual(os.stat(script_path).st_mode & 0o777, 0o755)

    def test_generate_build_script_final_mode_fsync_failure_reverts_to_non_executable(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "mode-fsync-failure-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        script_path = os.path.join(self.temp_dir, "mode-fsync-failure-build.sh")

        file_syncs = 0
        fsync_events = []
        chmod_modes = []
        original_fsync = os.fsync
        original_fchmod = os.fchmod

        def fail_final_file_sync(file_descriptor):
            nonlocal file_syncs
            if stat.S_ISDIR(os.fstat(file_descriptor).st_mode):
                fsync_events.append("directory")
                return original_fsync(file_descriptor)
            file_syncs += 1
            fsync_events.append("file")
            if file_syncs == 2:
                raise OSError("simulated executable-mode fsync failure")
            return original_fsync(file_descriptor)

        def record_fchmod(file_descriptor, mode):
            chmod_modes.append(mode)
            return original_fchmod(file_descriptor, mode)

        with mock.patch.object(
            packager.os, "fsync", side_effect=fail_final_file_sync
        ):
            with mock.patch.object(
                packager.os, "fchmod", side_effect=record_fchmod
            ):
                with self.assertRaisesRegex(OSError, "executable-mode fsync"):
                    generate_build_script(manifest, script_path)

        self.assertEqual(
            fsync_events,
            ["file", "directory", "file", "file"],
            "A failed executable-mode sync must be followed by a synced non-executable rollback",
        )
        self.assertEqual(chmod_modes, [0o755, 0o600])
        self.assertTrue(os.path.isfile(script_path))
        self.assertEqual(os.stat(script_path).st_mode & 0o777, 0o600)
        with open(script_path, "r", encoding="utf-8") as fp:
            self.assertIn("Appliance PREVIEW build completed", fp.read())

    def test_generate_build_script_failed_write_never_publishes_executable_partial_file(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "partial-write-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        script_path = os.path.join(self.temp_dir, "partial-build.sh")
        original_fdopen = os.fdopen

        class FailingTextWriter:
            def __init__(self, wrapped):
                self.wrapped = wrapped

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                self.wrapped.close()
                return False

            def fileno(self):
                return self.wrapped.fileno()

            def write(self, value):
                self.wrapped.write(value[:32])
                self.wrapped.flush()
                os.fsync(self.wrapped.fileno())
                raise OSError("simulated generated-script write failure")

        def fail_only_script_write(file_fd, mode="r", *args, **kwargs):
            opened = original_fdopen(file_fd, mode, *args, **kwargs)
            if mode == "w":
                return FailingTextWriter(opened)
            return opened

        with mock.patch.object(
            packager.os, "fdopen", side_effect=fail_only_script_write
        ):
            with self.assertRaisesRegex(
                OSError, "simulated generated-script write failure"
            ):
                generate_build_script(manifest, script_path)

        self.assertTrue(os.path.isfile(script_path))
        self.assertNotEqual(os.path.getsize(script_path), 0)
        self.assertEqual(
            os.stat(script_path).st_mode & 0o111,
            0,
            "A partial generated script must never be published executable",
        )

    def test_generate_build_script_closes_raw_descriptor_when_fdopen_fails(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile,
            DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "fdopen-failure-staging"),
        )
        script_path = os.path.join(self.temp_dir, "fdopen-failure-build.sh")
        original_open_new = packager._open_new_file_without_symlink_parents
        original_fdopen = os.fdopen
        captured = {}

        def capture_script_open(path, flags, mode):
            descriptors = original_open_new(path, flags, mode)
            if os.path.abspath(path) == os.path.abspath(script_path):
                captured["script_fd"], captured["parent_fd"] = descriptors
            return descriptors

        def fail_script_fdopen(file_descriptor, mode="r", *args, **kwargs):
            if mode == "w" and file_descriptor == captured.get("script_fd"):
                raise OSError("simulated generated-script fdopen failure")
            return original_fdopen(file_descriptor, mode, *args, **kwargs)

        with mock.patch.object(
            packager, "_open_new_file_without_symlink_parents",
            side_effect=capture_script_open,
        ):
            with mock.patch.object(
                packager.os, "fdopen", side_effect=fail_script_fdopen
            ):
                with self.assertRaisesRegex(
                    OSError, "simulated generated-script fdopen failure"
                ):
                    generate_build_script(manifest, script_path)

        self.assertIn("script_fd", captured)
        self.assertIn("parent_fd", captured)
        for descriptor_name in ("script_fd", "parent_fd"):
            with self.subTest(descriptor=descriptor_name):
                with self.assertRaises(OSError):
                    os.fstat(captured[descriptor_name])

        self.assertTrue(os.path.isfile(script_path))
        self.assertEqual(
            os.stat(script_path).st_mode & 0o777,
            0o600,
            "A failed stream construction must leave the script non-executable",
        )

    def test_generate_build_script_closes_parent_descriptor_when_open_is_interrupted(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile,
            DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "open-interrupted-staging"),
        )
        original_open = packager.os.open
        original_parent_open = packager._open_parent_directory_without_symlink_parents

        for interruption_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(interruption=interruption_type.__name__):
                script_path = os.path.join(
                    self.temp_dir,
                    f"{interruption_type.__name__.lower()}-open-interrupted-build.sh",
                )
                captured = {}
                open_patcher = None

                def capture_parent_then_interrupt(*args, **kwargs):
                    nonlocal open_patcher
                    directory_fd, filename = original_parent_open(*args, **kwargs)
                    captured["parent_fd"] = directory_fd

                    def interrupt_final_open(path, flags, mode=0o777, *, dir_fd=None):
                        if dir_fd == directory_fd and path == filename:
                            raise interruption_type(
                                "simulated build-script open interruption"
                            )
                        return original_open(path, flags, mode, dir_fd=dir_fd)

                    open_patcher = mock.patch.object(
                        packager.os, "open", side_effect=interrupt_final_open
                    )
                    open_patcher.start()
                    return directory_fd, filename

                try:
                    with mock.patch.object(
                        packager,
                        "_open_parent_directory_without_symlink_parents",
                        side_effect=capture_parent_then_interrupt,
                    ):
                        with self.assertRaisesRegex(
                            interruption_type,
                            "simulated build-script open interruption",
                        ):
                            generate_build_script(manifest, script_path)
                finally:
                    if open_patcher is not None:
                        open_patcher.stop()

                self.assertIn("parent_fd", captured)
                try:
                    os.fstat(captured["parent_fd"])
                except OSError:
                    parent_closed = True
                else:
                    parent_closed = False
                    os.close(captured["parent_fd"])
                self.assertTrue(
                    parent_closed,
                    "the parent directory descriptor must close when exclusive script creation is interrupted",
                )
                self.assertFalse(
                    os.path.lexists(script_path),
                    "an interrupted open before file creation must not leave a generated script",
                )

    def test_generate_build_script_refuses_existing_file_without_overwriting(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile, DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "staging_existing_build_script")
        )
        script_path = os.path.join(self.temp_dir, "operator-owned-build.sh")
        sentinel = "# operator-owned build instructions\\n"
        with open(script_path, "w", encoding="utf-8") as fp:
            fp.write(sentinel)

        with self.assertRaises(FileExistsError):
            generate_build_script(manifest, script_path)

        with open(script_path, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)

    def test_generate_build_script_refuses_symlink_without_overwriting_target(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile, DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "staging_symlink_build_script")
        )
        target_path = os.path.join(self.temp_dir, "operator-owned-target.sh")
        script_path = os.path.join(self.temp_dir, "generated-build-link.sh")
        sentinel = "# external operator-owned target\\n"
        with open(target_path, "w", encoding="utf-8") as fp:
            fp.write(sentinel)
        os.symlink(target_path, script_path)

        with self.assertRaises(FileExistsError):
            generate_build_script(manifest, script_path)

        self.assertTrue(os.path.islink(script_path))
        with open(target_path, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)

    def test_generate_build_script_rejects_symlinked_runner_paths(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile, DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "staging_symlinked_runner")
        )
        sentinel = b"#!/usr/bin/env python3\\n# operator-owned runner\\n"

        for case in ("final-component", "parent-directory"):
            with self.subTest(case=case):
                visible_tools_dir = os.path.join(self.temp_dir, f"visible-tools-{case}")
                target_path = os.path.join(self.temp_dir, f"operator-owned-runner-{case}.py")

                if case == "final-component":
                    os.makedirs(visible_tools_dir)
                    with open(target_path, "wb") as fp:
                        fp.write(sentinel)
                    runner_candidate = os.path.join(
                        visible_tools_dir, "run_imagebuilder_sandbox.py"
                    )
                    os.symlink(target_path, runner_candidate)
                else:
                    real_tools_dir = os.path.join(self.temp_dir, "real-tools-parent")
                    os.makedirs(real_tools_dir)
                    target_path = os.path.join(real_tools_dir, "run_imagebuilder_sandbox.py")
                    with open(target_path, "wb") as fp:
                        fp.write(sentinel)
                    os.symlink(real_tools_dir, visible_tools_dir, target_is_directory=True)
                    runner_candidate = os.path.join(
                        visible_tools_dir, "run_imagebuilder_sandbox.py"
                    )

                module_path = os.path.join(
                    visible_tools_dir, "package_appliance_firmware.py"
                )
                script_path = os.path.join(self.temp_dir, f"generated-{case}.sh")
                with mock.patch.object(packager, "__file__", module_path):
                    with self.assertRaisesRegex(FileNotFoundError, "symlink"):
                        generate_build_script(manifest, script_path)

                self.assertFalse(os.path.lexists(script_path))
                self.assertEqual(os.path.realpath(runner_candidate), target_path)
                with open(target_path, "rb") as fp:
                    self.assertEqual(fp.read(), sentinel)

    def test_generated_wrapper_rejects_runner_parent_symlink_at_runtime(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile, DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "staging_runtime_runner_symlink")
        )
        tools_dir = os.path.join(self.temp_dir, "runner-tools")
        os.makedirs(tools_dir)
        marker_path = os.path.join(self.temp_dir, "runner-was-invoked")
        fake_runner = os.path.join(tools_dir, "run_imagebuilder_sandbox.py")
        with open(fake_runner, "w", encoding="utf-8") as fp:
            fp.write(
                "#!/usr/bin/env python3\\n"
                "import pathlib, sys\\n"
                + f"pathlib.Path({marker_path!r}).write_text('invoked')\\n"
                + "raise SystemExit(73)\\n"
            )
        module_path = os.path.join(tools_dir, "package_appliance_firmware.py")
        wrapper = os.path.join(self.temp_dir, "runtime-runner-symlink-build.sh")
        with mock.patch.object(packager, "__file__", module_path):
            generate_build_script(manifest, wrapper)

        moved_tools_dir = os.path.join(self.temp_dir, "runner-tools-real")
        os.rename(tools_dir, moved_tools_dir)
        os.symlink(moved_tools_dir, tools_dir, target_is_directory=True)

        builder = os.path.join(self.temp_dir, "runtime-runner-symlink-builder")
        os.makedirs(builder)
        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = subprocess.run(
            ["sh", wrapper],
            cwd=self.temp_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("runner path contains a symlink", result.stderr)
        self.assertFalse(
            os.path.exists(marker_path),
            "A runner reached through a symlinked parent must never execute",
        )
        self.assertFalse(
            os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256"))
        )

    def _run_generated_wrapper(self, wrapper, cwd, env, timeout_seconds=60):
        """Run a generated wrapper with a test-only runner stub unless real bwrap is mandatory."""
        cwd_path = os.path.realpath(os.path.abspath(cwd))
        wrapper_path = os.path.abspath(
            wrapper if os.path.isabs(wrapper) else os.path.join(cwd_path, wrapper)
        )
        if os.path.realpath(wrapper_path) != wrapper_path or not os.path.isfile(wrapper_path):
            raise RuntimeError("Generated wrapper must be a regular file inside the test workspace")
        try:
            if os.path.commonpath((cwd_path, wrapper_path)) != cwd_path:
                raise RuntimeError("Generated wrapper is outside the test workspace")
        except ValueError as exc:
            raise RuntimeError("Generated wrapper is outside the test workspace") from exc

        if os.environ.get("PHX_REQUIRE_BWRAP") != "1":
            # Shared CI emulates only the verified-context branch with a
            # test-owned runner stub. The dedicated NO-GO workflow uses the
            # real runner and must pass the actual namespace/mount checks.
            raw_builder = env.get("OPENWRT_IMAGEBUILDER_DIR")
            if not raw_builder:
                raise RuntimeError("ImageBuilder workspace is required for wrapper tests")
            builder_path = os.path.abspath(
                raw_builder if os.path.isabs(raw_builder) else os.path.join(cwd_path, raw_builder)
            )
            probe_name = ".phx-test-owner-probe"
            probe_path = os.path.join(builder_path, probe_name)
            if os.path.lexists(probe_path):
                raise RuntimeError("Refusing to overwrite the test ownership probe")
            with open(probe_path, "w", encoding="utf-8") as fp:
                fp.write("test-only probe\n")

            fake_runner_path = os.path.join(cwd_path, ".phx-test-imagebuilder-runner.py")
            fake_runner_content = (
                "import sys\n"
                "if '--verify-context' in sys.argv:\n"
                "    raise SystemExit(0)\n"
                "raise SystemExit(125)\n"
            )
            with open(fake_runner_path, "w", encoding="utf-8") as fp:
                fp.write(fake_runner_content)
            with open(fake_runner_path, "rb") as fp:
                fake_runner_sha256 = hashlib.sha256(fp.read()).hexdigest()

            with open(wrapper_path, "r", encoding="utf-8") as fp:
                wrapper_lines = fp.read().splitlines()
            replaced_path = False
            replaced_digest = False
            for index, line in enumerate(wrapper_lines):
                if line.startswith("RUNNER_PATH="):
                    wrapper_lines[index] = f"RUNNER_PATH={shlex.quote(fake_runner_path)}"
                    replaced_path = True
                elif line.startswith("RUNNER_SHA256="):
                    wrapper_lines[index] = f"RUNNER_SHA256={fake_runner_sha256}"
                    replaced_digest = True
            if not replaced_path or not replaced_digest:
                raise RuntimeError("Generated wrapper did not expose the pinned runner fields")
            with open(wrapper_path, "w", encoding="utf-8") as fp:
                fp.write("\n".join(wrapper_lines) + "\n")

            test_env = env.copy()
            test_env["PHX_IMAGEBUILDER_SANDBOX_ACTIVE"] = "1"
            test_env["PHX_BWRAP_OWNER_PROBE"] = probe_name
            command = ["/bin/sh", wrapper_path]
            try:
                process = subprocess.Popen(
                    command,
                    cwd=cwd_path,
                    env=test_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                )
                (stdout, stderr), timed_out = run_imagebuilder_sandbox._communicate_with_timeout(
                    process, timeout_seconds
                )
                if timed_out:
                    timeout_message = (
                        f"RELEASE-BLOCKED: generated wrapper exceeded its "
                        f"{timeout_seconds}s test timeout"
                    )
                    stderr = "\n".join(part for part in (stderr, timeout_message) if part)
                    return subprocess.CompletedProcess(command, 124, stdout, stderr)
                return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
            finally:
                if os.path.lexists(probe_path):
                    os.unlink(probe_path)

        sandbox_runner = os.path.join(os.path.dirname(__file__), "run_imagebuilder_sandbox.py")
        if not os.path.isfile(sandbox_runner):
            raise RuntimeError("PHX_REQUIRE_BWRAP=1 requires the release sandbox runner")

        raw_builder = env.get("OPENWRT_IMAGEBUILDER_DIR")
        if not raw_builder:
            raise RuntimeError("ImageBuilder workspace is required for sandboxed execution")
        builder_path = os.path.abspath(
            raw_builder if os.path.isabs(raw_builder) else os.path.join(cwd_path, raw_builder)
        )
        if os.path.realpath(builder_path) != builder_path or not os.path.isdir(builder_path):
            raise RuntimeError("ImageBuilder workspace must be a real directory without symlink parents")
        try:
            if os.path.commonpath((cwd_path, builder_path)) != cwd_path or builder_path == cwd_path:
                raise RuntimeError("Writable ImageBuilder workspace must be a strict child of the test workspace")
        except ValueError as exc:
            raise RuntimeError("ImageBuilder workspace is outside the test workspace") from exc

        # Run as the invoking unprivileged account. Bubblewrap maps only this
        # single host UID/GID to namespace root; no sudo or subordinate-ID helper.
        command = [
            sys.executable,
            sandbox_runner,
            "--cwd", cwd_path,
            "--builder", builder_path,
            "--wrapper", wrapper_path,
            "--timeout-seconds", str(timeout_seconds),
        ]
        return subprocess.run(
            command,
            cwd=cwd_path,
            env={"PATH": "/usr/bin:/bin", "LANG": "C"},
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )

    def _run_mock_imagebuilder(self, image_subpath=None, mkdir_subtarget=False,
                               preexisting_image=False, preexisting_manifest=False,
                               manifest_symlink=False, temp_manifest_symlink=False,
                               image_symlink_subpath=None,
                               image_symlink_dir_subpath=None,
                               preexisting_image_symlink=False,
                               symlinked_output_dir=False,
                               timeout_seconds=60,
                               sleep_seconds=None,
                               timeout_marker=None,
                               hardlinked_image=False):
        """Execute a generated wrapper against a disposable local Makefile."""
        profile = load_profile("gl-mt1300")
        stage_absolute = os.path.join(self.temp_dir, "staging with spaces")
        stage_relative = os.path.relpath(stage_absolute, os.getcwd())
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, stage_relative)
        wrapper = os.path.join(self.temp_dir, "nonshipping-build.sh")
        generate_build_script(manifest, wrapper)

        fake_builder = os.path.join(self.temp_dir, "fake-imagebuilder")
        os.makedirs(fake_builder, exist_ok=True)
        if hardlinked_image:
            cache_dir = os.path.join(fake_builder, "cache")
            os.makedirs(cache_dir, exist_ok=True)
            with open(os.path.join(cache_dir, "prior-image.bin"), "wb") as fp:
                fp.write(b"STALE-CACHED-IMAGE-NOT-CURRENT")
        if preexisting_image_symlink:
            image_dir = os.path.join(fake_builder, "bin", "targets", "ramips", "mt7621")
            os.makedirs(image_dir, exist_ok=True)
            external_image = os.path.join(self.temp_dir, "operator-owned-prior-image.img.gz")
            with open(external_image, "wb") as fp:
                fp.write(b"KEEP-OPERATOR-IMAGE")
            os.symlink(external_image, os.path.join(image_dir, "linked.img.gz"))
        if symlinked_output_dir:
            image_parent = os.path.join(fake_builder, "bin", "targets", "ramips")
            os.makedirs(image_parent, exist_ok=True)
            external_dir = os.path.join(self.temp_dir, "operator-owned-image-output")
            os.makedirs(external_dir, exist_ok=True)
            with open(os.path.join(external_dir, "operator-owned.bin"), "wb") as fp:
                fp.write(b"KEEP-OPERATOR-DIRECTORY")
            os.symlink(external_dir, os.path.join(image_parent, "mt7621"))
        recipe = 'image:\n\t@test -d "$(FILES)"\n'
        if hardlinked_image:
            recipe += (
                '\t@mkdir -p bin/targets/ramips/mt7621\n'
                '\t@ln cache/prior-image.bin bin/targets/ramips/mt7621/hardlinked.bin\n'
            )
        if mkdir_subtarget:
            recipe += '\t@mkdir -p bin/targets/ramips/mt7621\n'
        if image_subpath is not None:
            # Fixture paths are hardcoded by these tests, never user input.
            recipe += '\t@mkdir -p "$(dir ' + image_subpath + ')"\n'
            recipe += '\t@printf "SYNTHETIC-NOT-FIRMWARE" > ' + image_subpath + '\n'
        if image_symlink_subpath is not None:
            # Keep the symlink target outside the target-image directory.
            external_image = os.path.join(self.temp_dir, "external-synthetic-image.bin")
            with open(external_image, "wb") as fp:
                fp.write(b"EXTERNAL-SYNTHETIC-NOT-FIRMWARE")
            recipe += '\t@mkdir -p "$(dir ' + image_symlink_subpath + ')"\n'
            recipe += '\t@ln -s ' + shlex.quote(external_image) + ' ' + image_symlink_subpath + '\n'
        if image_symlink_dir_subpath is not None:
            # Keep a firmware-looking file outside the target tree behind a
            # directory symlink that find(1) will not traverse by default.
            external_dir = os.path.join(self.temp_dir, "external-synthetic-image-directory")
            os.makedirs(external_dir, exist_ok=True)
            external_image = os.path.join(external_dir, "hidden.img.gz")
            with open(external_image, "wb") as fp:
                fp.write(b"EXTERNAL-SYNTHETIC-NOT-FIRMWARE")
            recipe += '\t@ln -s ' + shlex.quote(external_dir) + ' ' + image_symlink_dir_subpath + '\n'
        if sleep_seconds is not None:
            if isinstance(sleep_seconds, bool) or not isinstance(sleep_seconds, int) or sleep_seconds < 1:
                raise ValueError("sleep_seconds must be a positive integer")
            if not timeout_marker:
                raise ValueError("timeout_marker is required for the timeout fixture")
            recipe += (
                f'\t@sleep {sleep_seconds}; printf "late" > {shlex.quote(timeout_marker)}\n'
            )

        with open(os.path.join(fake_builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        if preexisting_image:
            stale_image = os.path.join(fake_builder, "bin", "targets", "ramips", "mt7621", "old.bin")
            os.makedirs(os.path.dirname(stale_image), exist_ok=True)
            with open(stale_image, "wb") as fp:
                fp.write(b"OLD-NOT-CURRENT-IMAGE")
        if preexisting_manifest or manifest_symlink:
            manifest_path = os.path.join(fake_builder, "RELEASE_MANIFEST.sha256")
            if manifest_symlink:
                outside = os.path.join(self.temp_dir, "outside-manifest.txt")
                with open(outside, "w", encoding="utf-8") as fp:
                    fp.write("DO-NOT-OVERWRITE\n")
                os.symlink(outside, manifest_path)
            else:
                with open(manifest_path, "w", encoding="utf-8") as fp:
                    fp.write("PRIOR-RUN-MANIFEST\n")

        if temp_manifest_symlink:
            outside = os.path.join(self.temp_dir, "outside-temp-manifest.txt")
            with open(outside, "w", encoding="utf-8") as fp:
                fp.write("DO-NOT-OVERWRITE-TEMP\n")
            os.symlink(outside, os.path.join(fake_builder, "RELEASE_MANIFEST.sha256.tmp"))

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = fake_builder
        result = self._run_generated_wrapper(
            wrapper, self.temp_dir, env, timeout_seconds=timeout_seconds
        )
        return result, fake_builder, wrapper, stage_absolute

    def test_generated_wrapper_routes_operator_invocation_through_unprivileged_runner(self):
        profile = load_profile("gl-mt1300")
        staging_dir = os.path.join(self.temp_dir, "operator staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging_dir)
        wrapper = os.path.join(self.temp_dir, "operator-build.sh")

        builder = os.path.join(self.temp_dir, "operator-imagebuilder")
        os.makedirs(builder, exist_ok=True)
        image_path = os.path.join(builder, "bin", "targets", "ramips", "mt7621", "operator.bin")
        recipe = (
            "image:\n"
            "\t@mkdir -p bin/targets/ramips/mt7621\n"
            "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/operator.bin\n"
        )
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        fake_bin = os.path.join(self.temp_dir, "fake-bin")
        os.makedirs(fake_bin, exist_ok=True)
        python3_path = os.path.join(fake_bin, "python3")
        sudo_path = os.path.join(fake_bin, "sudo")
        args_path = os.path.join(self.temp_dir, "python3-runner-args.txt")
        sudo_called_path = os.path.join(self.temp_dir, "sudo-was-called")
        with open(python3_path, "w", encoding="utf-8") as fp:
            fp.write(
                "#!/bin/sh\n"
                "case \"$1\" in\n"
                "  -c|-) exec \"$PHX_TEST_REAL_PYTHON3\" \"$@\" ;;\n"
                "esac\n"
                "printf '%s\n' \"$@\" > \"$PHX_TEST_PYTHON_ARGS\"\n"
                "exit 73\n"
            )
        with open(sudo_path, "w", encoding="utf-8") as fp:
            fp.write(
                "#!/bin/sh\n"
                "printf called > \"$PHX_TEST_SUDO_CALLED\"\n"
                "exit 91\n"
            )
        os.chmod(python3_path, 0o755)
        os.chmod(sudo_path, 0o755)

        # The generated wrapper must pin this explicit interpreter path rather
        # than trusting whichever python3 happens to lead the caller's PATH.
        with mock.patch.object(packager.sys, "executable", python3_path):
            generate_build_script(manifest, wrapper)

        env = os.environ.copy()
        env["PATH"] = fake_bin + os.pathsep + env.get("PATH", "")
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        env["PHX_TEST_REAL_PYTHON3"] = shutil.which("python3") or sys.executable
        env["PHX_TEST_PYTHON_ARGS"] = args_path
        env["PHX_TEST_SUDO_CALLED"] = sudo_called_path
        env.pop("PHX_IMAGEBUILDER_SANDBOX_ACTIVE", None)
        env.pop("PHX_BWRAP_OWNER_PROBE", None)
        result = subprocess.run(
            ["/bin/sh", wrapper],
            cwd=self.temp_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 73, result.stderr)
        with open(args_path, "r", encoding="utf-8") as fp:
            runner_args = [line.rstrip("\n") for line in fp]
        runner_path = os.path.join(os.path.dirname(__file__), "run_imagebuilder_sandbox.py")
        self.assertEqual(runner_args[0], runner_path)
        self.assertEqual(runner_args[runner_args.index("--cwd") + 1], self.temp_dir)
        self.assertEqual(runner_args[runner_args.index("--builder") + 1], builder)
        self.assertEqual(runner_args[runner_args.index("--wrapper") + 1], wrapper)
        self.assertFalse(os.path.exists(sudo_called_path), "operator entrypoint must never invoke sudo")
        self.assertFalse(os.path.exists(image_path), "operator Makefile must not run outside the sandbox")
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

    def test_generated_wrapper_ignores_path_shadowed_bootstrap_tools(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "staging_path_shadow")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "path-shadow-build.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "path-shadow-imagebuilder")
        os.makedirs(builder)
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write("image:\n\t@exit 42\n")

        fake_bin = os.path.join(self.temp_dir, "path-shadow-bin")
        os.makedirs(fake_bin)
        python_marker = os.path.join(self.temp_dir, "shadowed-python-called")
        sha_marker = os.path.join(self.temp_dir, "shadowed-sha256sum-called")
        bwrap_marker = os.path.join(self.temp_dir, "shadowed-bwrap-called")
        real_python = os.path.realpath(sys.executable)
        real_sha256sum = shutil.which("sha256sum", path="/usr/bin:/bin")
        self.assertIsNotNone(real_sha256sum, "system sha256sum is required by the release wrapper")

        fake_tools = {
            "python3": (
                f"#!/bin/sh\nprintf called > {shlex.quote(python_marker)}\n"
                f"exec {shlex.quote(real_python)} \"$@\"\n"
            ),
            "sha256sum": (
                f"#!/bin/sh\nprintf called > {shlex.quote(sha_marker)}\n"
                f"exec {shlex.quote(real_sha256sum)} \"$@\"\n"
            ),
            "bwrap": (
                f"#!/bin/sh\nprintf called > {shlex.quote(bwrap_marker)}\n"
                "exit 125\n"
            ),
        }
        for name, script in fake_tools.items():
            path = os.path.join(fake_bin, name)
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(script)
            os.chmod(path, 0o755)

        env = os.environ.copy()
        env["PATH"] = fake_bin + os.pathsep + "/usr/bin:/bin"
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        env.pop("PHX_IMAGEBUILDER_SANDBOX_ACTIVE", None)
        env.pop("PHX_BWRAP_OWNER_PROBE", None)
        result = subprocess.run(
            ["/bin/sh", wrapper],
            cwd=self.temp_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

        self.assertIn("RELEASE-BOUNDARY", result.stderr)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(os.path.exists(python_marker), "caller PATH must not choose the Python interpreter")
        self.assertFalse(os.path.exists(sha_marker), "caller PATH must not choose the runner hash utility")
        self.assertFalse(os.path.exists(bwrap_marker), "caller PATH must not choose the sandbox executable")
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

    def test_generated_wrapper_rejects_checksum_utility_changed_after_generation(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "staging_checksum_tool")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "checksum-tool-build.sh")
        generate_build_script(manifest, wrapper)

        with open(wrapper, "r", encoding="utf-8") as fp:
            content = fp.read()
        self.assertRegex(
            content,
            r"(?m)^SHA256SUM_SHA256=[0-9a-f]{64}$",
            "generated wrapper must pin the checksum utility bytes, not only its path",
        )

        tool_marker = os.path.join(self.temp_dir, "checksum-tool-executed")
        fake_tool = os.path.join(self.temp_dir, "pinned-sha256sum")
        original_tool = (
            "#!/bin/sh\n"
            f"printf trusted-tool-used > {shlex.quote(tool_marker)}\n"
            "exit 0\n"
        ).encode("utf-8")
        with open(fake_tool, "wb") as fp:
            fp.write(original_tool)
        os.chmod(fake_tool, 0o755)
        expected_tool_sha256 = hashlib.sha256(original_tool).hexdigest()

        wrapper_lines = content.splitlines()
        path_assignments = 0
        digest_assignments = 0
        for index, line in enumerate(wrapper_lines):
            if line.startswith("SHA256SUM_PATH="):
                wrapper_lines[index] = "SHA256SUM_PATH=" + shlex.quote(fake_tool)
                path_assignments += 1
            elif line.startswith("SHA256SUM_SHA256="):
                wrapper_lines[index] = "SHA256SUM_SHA256=" + expected_tool_sha256
                digest_assignments += 1
        self.assertEqual(path_assignments, 1)
        self.assertEqual(digest_assignments, 1)
        with open(wrapper, "w", encoding="utf-8") as fp:
            fp.write("\n".join(wrapper_lines) + "\n")
        os.chmod(wrapper, 0o755)

        # Simulate replacement after wrapper generation but before operator execution.
        with open(fake_tool, "wb") as fp:
            fp.write(
                (
                    "#!/bin/sh\n"
                    f"printf tampered-tool-used > {shlex.quote(tool_marker)}\n"
                    "exit 0\n"
                ).encode("utf-8")
            )
        os.chmod(fake_tool, 0o755)

        builder = os.path.join(self.temp_dir, "checksum-tool-imagebuilder")
        os.makedirs(builder)
        make_marker = os.path.join(self.temp_dir, "checksum-tool-make-ran")
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write("image:\n\t@printf 'MAKE-RAN' > " + shlex.quote(make_marker) + "\n")

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        env.pop("PHX_IMAGEBUILDER_SANDBOX_ACTIVE", None)
        env.pop("PHX_BWRAP_OWNER_PROBE", None)
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(
            "pinned sha256sum executable SHA-256 differs",
            result.stderr,
        )
        self.assertFalse(
            os.path.exists(tool_marker),
            "a replaced checksum utility must be rejected before it is executed",
        )
        self.assertFalse(
            os.path.exists(make_marker),
            "ImageBuilder Makefile must not run after checksum utility pin failure",
        )

    def test_generated_wrapper_rejects_python_interpreter_changed_after_generation(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "staging_python_interpreter")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "python-interpreter-build.sh")
        generate_build_script(manifest, wrapper)

        with open(wrapper, "r", encoding="utf-8") as fp:
            content = fp.read()

        real_python = os.path.realpath(sys.executable)
        python_marker = os.path.join(self.temp_dir, "pinned-python-executed")
        fake_python = os.path.join(self.temp_dir, "pinned-python")
        original_python = (
            "#!/bin/sh\n"
            f"printf trusted-python-used > {shlex.quote(python_marker)}\n"
            f"exec {shlex.quote(real_python)} \"$@\"\n"
        ).encode("utf-8")
        with open(fake_python, "wb") as fp:
            fp.write(original_python)
        os.chmod(fake_python, 0o755)
        expected_python_sha256 = hashlib.sha256(original_python).hexdigest()

        wrapper_lines = content.splitlines()
        path_assignments = 0
        digest_assignments = 0
        for index, line in enumerate(wrapper_lines):
            if line.startswith("PYTHON_PATH="):
                wrapper_lines[index] = "PYTHON_PATH=" + shlex.quote(fake_python)
                path_assignments += 1
            elif line.startswith("PYTHON_SHA256="):
                wrapper_lines[index] = "PYTHON_SHA256=" + expected_python_sha256
                digest_assignments += 1
        self.assertEqual(path_assignments, 1)
        self.assertEqual(digest_assignments, 1)
        with open(wrapper, "w", encoding="utf-8") as fp:
            fp.write("\n".join(wrapper_lines) + "\n")
        os.chmod(wrapper, 0o755)

        # Simulate replacement after wrapper generation but before first interpreter use.
        tampered_python = (
            "#!/bin/sh\n"
            f"printf tampered-python-executed > {shlex.quote(python_marker)}\n"
            f"exec {shlex.quote(real_python)} \"$@\"\n"
        ).encode("utf-8")
        with open(fake_python, "wb") as fp:
            fp.write(tampered_python)
        os.chmod(fake_python, 0o755)

        builder = os.path.join(self.temp_dir, "python-interpreter-imagebuilder")
        os.makedirs(builder)
        make_marker = os.path.join(self.temp_dir, "python-interpreter-make-ran")
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write("image:\n\t@printf 'MAKE-RAN' > " + shlex.quote(make_marker) + "\n")

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        env.pop("PHX_IMAGEBUILDER_SANDBOX_ACTIVE", None)
        env.pop("PHX_BWRAP_OWNER_PROBE", None)
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(
            "pinned Python interpreter SHA-256 differs",
            result.stderr,
        )
        self.assertFalse(
            os.path.exists(python_marker),
            "the pinned Python interpreter must be verified before it is executed",
        )
        self.assertFalse(
            os.path.exists(make_marker),
            "ImageBuilder Makefile must not run after Python interpreter pin failure",
        )

    def test_generated_wrapper_does_not_accept_forged_sandbox_environment(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "staging_forged_sandbox")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "forged-sandbox-build.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "forged-sandbox-imagebuilder")
        os.makedirs(builder)
        probe_name = ".phx-bwrap-owner-probe-12345"
        with open(os.path.join(builder, probe_name), "w", encoding="utf-8") as fp:
            fp.write("operator-forged-probe\n")
        external_marker = os.path.join(self.temp_dir, "operator-owned-sentinel")
        recipe = (
            "image:\n"
            "\t@printf 'UNSANDBOXED-WRITE' > ../operator-owned-sentinel\n"
            "\t@mkdir -p bin/targets/ramips/mt7621\n"
            "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/forged.bin\n"
        )
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        env = os.environ.copy()
        env["PATH"] = "/usr/bin:/bin"
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        env["PHX_IMAGEBUILDER_SANDBOX_ACTIVE"] = "1"
        env["PHX_BWRAP_OWNER_PROBE"] = probe_name
        result = subprocess.run(
            ["/bin/sh", wrapper],
            cwd=self.temp_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

        self.assertIn("RELEASE-BOUNDARY", result.stderr)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(
            os.path.exists(external_marker),
            "caller-forged environment and probe file must not bypass the sandbox runner",
        )
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

    def test_runner_verify_context_requires_single_id_maps_and_mount_boundaries(self):
        proc_root = os.path.join(self.temp_dir, "fake-proc")
        proc_self = os.path.join(proc_root, "self")
        os.makedirs(proc_self)
        builder = os.path.join(self.temp_dir, "verified-builder")
        os.makedirs(builder)
        probe_name = ".phx-bwrap-owner-probe-123"
        with open(os.path.join(builder, probe_name), "w", encoding="utf-8") as fp:
            fp.write("owner-probe\n")

        with open(os.path.join(proc_self, "uid_map"), "w", encoding="ascii") as fp:
            fp.write("0 1000 1\n")
        with open(os.path.join(proc_self, "gid_map"), "w", encoding="ascii") as fp:
            fp.write("0 1000 1\n")

        private_paths = ("/home", "/root", "/run", "/mnt", "/media", "/srv")

        def write_mountinfo(root_mode, hidden_paths=private_paths):
            rows = [
                f"1 0 8:1 / / {root_mode},relatime - ext4 /dev/root {root_mode},relatime",
                "2 1 0:2 / /tmp rw,nosuid,nodev - tmpfs tmpfs rw",
                "3 1 0:3 / /proc rw,nosuid,nodev,noexec - proc proc rw",
                "4 1 0:4 / /dev rw,nosuid,strictatime - tmpfs tmpfs rw",
                f"5 1 0:5 / {builder} rw,relatime - ext4 /dev/root rw,relatime",
            ]
            for mount_id, path in enumerate(hidden_paths, start=6):
                rows.append(
                    f"{mount_id} 1 0:{mount_id} / {path} rw,nosuid,nodev - tmpfs tmpfs rw,nosuid,nodev"
                )
            with open(os.path.join(proc_self, "mountinfo"), "w", encoding="ascii") as fp:
                fp.write("\n".join(rows) + "\n")

        write_mountinfo("ro")
        env = {
            "PHX_IMAGEBUILDER_SANDBOX_ACTIVE": "1",
            "PHX_BWRAP_OWNER_PROBE": probe_name,
        }
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(run_imagebuilder_sandbox.os, "getuid", return_value=0):
                with mock.patch.object(run_imagebuilder_sandbox.os, "geteuid", return_value=0):
                    with mock.patch.object(run_imagebuilder_sandbox.os, "getgid", return_value=0):
                        with mock.patch.object(run_imagebuilder_sandbox.os, "getegid", return_value=0):
                            self.assertTrue(
                                run_imagebuilder_sandbox.verify_sandbox_context(
                                    builder, probe_name, proc_root=proc_root
                                )
                            )
                            write_mountinfo("ro", hidden_paths=private_paths[1:])
                            self.assertFalse(
                                run_imagebuilder_sandbox.verify_sandbox_context(
                                    builder, probe_name, proc_root=proc_root
                                ),
                                "host credential and external-mount paths must be hidden by tmpfs",
                            )
                            write_mountinfo("rw")
                            self.assertFalse(
                                run_imagebuilder_sandbox.verify_sandbox_context(
                                    builder, probe_name, proc_root=proc_root
                                ),
                                "a forged marker in a read-write host root must not be trusted",
                            )

    def test_runner_private_host_mount_arguments_hide_credential_paths(self):
        expected = [
            argument
            for path in ("/home", "/root", "/run", "/mnt", "/media", "/srv")
            for argument in ("--tmpfs", path)
        ]
        self.assertEqual(run_imagebuilder_sandbox._private_host_mount_args(), expected)

    def test_preflight_and_runtime_share_private_host_mount_policy(self):
        self.assertIs(
            check_imagebuilder_sandbox_host._private_host_mount_args,
            run_imagebuilder_sandbox._private_host_mount_args,
            "host preflight and runtime must use the same private-host mask helper",
        )
        self.assertIs(
            check_imagebuilder_sandbox_host.PRIVATE_HOST_PATHS,
            run_imagebuilder_sandbox.PRIVATE_HOST_PATHS,
            "host preflight and runtime must share one immutable path list",
        )
        expected = [
            argument
            for path in ("/home", "/root", "/run", "/mnt", "/media", "/srv")
            for argument in ("--tmpfs", path)
        ]
        probe = check_imagebuilder_sandbox_host.build_probe_command("/usr/bin/bwrap")
        first_mask = probe.index("--tmpfs")
        self.assertEqual(probe[first_mask:first_mask + len(expected)], expected)

    def test_runner_resolves_bubblewrap_from_trusted_system_path_only(self):
        cwd = os.path.join(self.temp_dir, "runner-path-cwd")
        builder = os.path.join(cwd, "builder")
        wrapper = os.path.join(cwd, "build.sh")
        os.makedirs(builder)
        with open(wrapper, "w", encoding="utf-8") as fp:
            fp.write("#!/bin/sh\nexit 0\n")

        argv = [
            "run_imagebuilder_sandbox.py",
            "--cwd", cwd,
            "--builder", builder,
            "--wrapper", wrapper,
        ]
        with mock.patch.object(
            run_imagebuilder_sandbox, "_invoking_unprivileged_identity",
            return_value=(1000, 1000),
        ):
            with mock.patch.object(
                run_imagebuilder_sandbox.shutil, "which", return_value=None
            ) as which:
                with mock.patch.object(sys, "argv", argv):
                    result = run_imagebuilder_sandbox.main()

        self.assertEqual(result, 125)
        which.assert_called_once_with("bwrap", path="/usr/bin:/bin")

    def test_generated_wrapper_mock_execution_enforces_timeout_and_kills_child_group(self):
        marker_path = os.path.join(self.temp_dir, "late-make-completion")
        result, builder, _, _ = self._run_mock_imagebuilder(
            timeout_seconds=1,
            sleep_seconds=3,
            timeout_marker=marker_path,
        )

        self.assertEqual(result.returncode, 124, result.stderr + result.stdout)
        self.assertIn(
            "RELEASE-BLOCKED: generated wrapper exceeded its 1s test timeout",
            result.stderr,
        )
        self.assertFalse(
            os.path.exists(marker_path),
            "A timed-out Makefile child must not continue after the test returns",
        )
        self.assertFalse(
            os.path.lexists(os.path.join(builder, ".phx-test-owner-probe")),
            "The test ownership probe must be removed after timeout",
        )
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

    def test_generated_wrapper_denies_missing_target_images(self):
        result, builder, _, _ = self._run_mock_imagebuilder()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: target/subtarget image directory missing", result.stderr)
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

    def test_generated_wrapper_denies_empty_expected_subtarget(self):
        result, builder, _, _ = self._run_mock_imagebuilder(mkdir_subtarget=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: no firmware images found", result.stderr)
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

    def test_generated_wrapper_denies_wrong_subtarget_images(self):
        result, _, _, _ = self._run_mock_imagebuilder(
            image_subpath="bin/targets/ramips/mt7620/decoy.bin"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: target/subtarget image directory missing", result.stderr)

    def test_generated_wrapper_denies_hardlinked_firmware_output(self):
        result, builder, _, _ = self._run_mock_imagebuilder(hardlinked_image=True)
        cached_image = os.path.join(builder, "cache", "prior-image.bin")
        output_image = os.path.join(
            builder, "bin", "targets", "ramips", "mt7621", "hardlinked.bin"
        )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RELEASE-BLOCKED: hard-linked firmware image", result.stderr)
        self.assertFalse(
            os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")),
            "A hard-linked output must never be admitted into a release manifest",
        )
        self.assertEqual(os.stat(output_image).st_ino, os.stat(cached_image).st_ino)
        self.assertEqual(os.stat(output_image).st_nlink, 2)
        with open(cached_image, "rb") as fp:
            self.assertEqual(fp.read(), b"STALE-CACHED-IMAGE-NOT-CURRENT")

    def test_generated_wrapper_denies_stale_image_from_prior_build(self):
        # GNU Make reports success without generating a new image. Old
        # binaries must never be accepted as this run's deliverable.
        result, builder, _, _ = self._run_mock_imagebuilder(preexisting_image=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: stale firmware images", result.stderr)
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))
        self.assertTrue(os.path.isfile(
            os.path.join(builder, "bin", "targets", "ramips", "mt7621", "old.bin")
        ), "release guard must not delete prior operator data")

    def test_generated_wrapper_denies_preexisting_symlinked_firmware_candidate_before_make(self):
        result, builder, _, _ = self._run_mock_imagebuilder(
            image_subpath="bin/targets/ramips/mt7621/linked.img.gz",
            preexisting_image_symlink=True,
        )
        link_path = os.path.join(
            builder, "bin", "targets", "ramips", "mt7621", "linked.img.gz"
        )
        external_image = os.path.join(self.temp_dir, "operator-owned-prior-image.img.gz")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(os.path.islink(link_path))
        with open(external_image, "rb") as fp:
            self.assertEqual(fp.read(), b"KEEP-OPERATOR-IMAGE")
        self.assertIn("RELEASE-BLOCKED: stale symlinked firmware images", result.stderr)
        self.assertFalse(os.path.exists(
            os.path.join(builder, "RELEASE_MANIFEST.sha256")
        ))

    def test_generated_wrapper_denies_symlinked_target_output_directory_before_make(self):
        result, builder, _, _ = self._run_mock_imagebuilder(
            image_subpath="bin/targets/ramips/mt7621/synthetic.bin",
            symlinked_output_dir=True,
        )
        link_path = os.path.join(builder, "bin", "targets", "ramips", "mt7621")
        external_dir = os.path.join(self.temp_dir, "operator-owned-image-output")
        external_output = os.path.join(external_dir, "synthetic.bin")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(os.path.islink(link_path))
        self.assertFalse(os.path.exists(external_output))
        with open(os.path.join(external_dir, "operator-owned.bin"), "rb") as fp:
            self.assertEqual(fp.read(), b"KEEP-OPERATOR-DIRECTORY")
        self.assertIn("RELEASE-BLOCKED: symlinked ImageBuilder output directory", result.stderr)
        self.assertFalse(os.path.exists(
            os.path.join(builder, "RELEASE_MANIFEST.sha256")
        ))

    def test_generated_wrapper_rejects_output_ancestor_symlink_created_by_make(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "staging_make_output_symlink")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "make-output-symlink-build.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "make-output-symlink-imagebuilder")
        redirected_output = os.path.join(builder, "redirected-output")
        os.makedirs(builder)
        recipe = (
            "image:\n"
            "\t@mkdir -p redirected-output\n"
            "\t@ln -s redirected-output bin\n"
            "\t@mkdir -p bin/targets/ramips/mt7621\n"
            "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/redirected.bin\n"
        )
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(os.path.islink(os.path.join(builder, "bin")))
        self.assertTrue(
            os.path.isfile(
                os.path.join(
                    redirected_output, "targets", "ramips", "mt7621", "redirected.bin"
                )
            ),
            "The synthetic Makefile must reproduce output redirected through a new ancestor symlink",
        )
        self.assertIn(
            "RELEASE-BLOCKED: symlinked ImageBuilder output directory",
            result.stderr,
        )
        self.assertFalse(
            os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")),
            "A manifest must not admit images reached through a Makefile-created ancestor symlink",
        )

    def test_generated_wrapper_denies_previous_manifest_without_clobber(self):
        result, builder, _, _ = self._run_mock_imagebuilder(
            image_subpath="bin/targets/ramips/mt7621/synthetic.bin",
            preexisting_manifest=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: previous release manifest", result.stderr)
        with open(os.path.join(builder, "RELEASE_MANIFEST.sha256"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "PRIOR-RUN-MANIFEST\n")
        self.assertFalse(os.path.exists(
            os.path.join(builder, "bin", "targets", "ramips", "mt7621", "synthetic.bin")
        ), "the build must not execute after an existing manifest is detected")

    def test_generated_wrapper_denies_symlinked_manifest(self):
        result, builder, _, _ = self._run_mock_imagebuilder(manifest_symlink=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: previous release manifest", result.stderr)
        with open(os.path.join(self.temp_dir, "outside-manifest.txt"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "DO-NOT-OVERWRITE\n")
        self.assertTrue(os.path.islink(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

    def test_generated_wrapper_denies_symlinked_temporary_manifest_before_make(self):
        result, builder, _, _ = self._run_mock_imagebuilder(
            image_subpath="bin/targets/ramips/mt7621/synthetic.bin",
            temp_manifest_symlink=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: previous temporary release manifest", result.stderr)
        with open(os.path.join(self.temp_dir, "outside-temp-manifest.txt"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "DO-NOT-OVERWRITE-TEMP\n")
        self.assertTrue(os.path.islink(os.path.join(builder, "RELEASE_MANIFEST.sha256.tmp")))
        self.assertFalse(os.path.exists(os.path.join(builder, "bin", "targets", "ramips", "mt7621", "synthetic.bin")))

    def test_generated_wrapper_emits_empty_image_guard_as_real_shell_lines(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "guard-lines-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "guard-lines-build.sh")
        generate_build_script(manifest, wrapper)

        with open(wrapper, "r", encoding="utf-8") as fp:
            contents = fp.read()

        self.assertIn('EMPTY_IMAGE=$(find "$IMAGE_REL_DIR"', contents)
        self.assertIn(
            ' -size 0 -print -quit)\nif [ -n "$EMPTY_IMAGE" ]; then\n',
            contents,
            "The generated empty-image guard must be emitted as real shell lines",
        )
        self.assertNotIn(
            r' -size 0 -print -quit)\nif [ -n "$EMPTY_IMAGE" ]; then',
            contents,
            "Literal backslash-n text is not a shell command separator",
        )

    def test_generated_wrapper_denies_empty_firmware_payload(self):
        # Empty output is not a usable firmware binary, even with .bin suffix.
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "empty-build.sh")
        generate_build_script(manifest, wrapper)
        builder = os.path.join(self.temp_dir, "empty-imagebuilder")
        os.makedirs(builder)
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write("image:\n\t@mkdir -p bin/targets/ramips/mt7621\n"
                     "\t@: > bin/targets/ramips/mt7621/empty.bin\n")
        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: empty firmware image", result.stderr)
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

    def test_generated_wrapper_denies_symlinked_firmware_candidate(self):
        result, builder, _, _ = self._run_mock_imagebuilder(
            image_subpath="bin/targets/ramips/mt7621/regular.bin",
            image_symlink_subpath="bin/targets/ramips/mt7621/linked.img.gz",
        )
        linked_image = os.path.join(
            builder, "bin", "targets", "ramips", "mt7621", "linked.img.gz"
        )
        regular_image = os.path.join(
            builder, "bin", "targets", "ramips", "mt7621", "regular.bin"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: symlinked entry in firmware output tree", result.stderr)
        self.assertTrue(os.path.isfile(regular_image))
        self.assertTrue(os.path.islink(linked_image))
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))
        with open(os.path.join(self.temp_dir, "external-synthetic-image.bin"), "rb") as fp:
            self.assertEqual(fp.read(), b"EXTERNAL-SYNTHETIC-NOT-FIRMWARE")

    def test_generated_wrapper_denies_symlinked_directory_hiding_firmware_candidates(self):
        result, builder, _, _ = self._run_mock_imagebuilder(
            image_subpath="bin/targets/ramips/mt7621/regular.bin",
            image_symlink_dir_subpath="bin/targets/ramips/mt7621/linked-images",
        )
        linked_dir = os.path.join(
            builder, "bin", "targets", "ramips", "mt7621", "linked-images"
        )
        external_image = os.path.join(
            self.temp_dir, "external-synthetic-image-directory", "hidden.img.gz"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "RELEASE-BLOCKED: symlinked entry in firmware output tree",
            result.stderr,
        )
        self.assertTrue(os.path.islink(linked_dir))
        self.assertTrue(os.path.isfile(os.path.join(linked_dir, "hidden.img.gz")))
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))
        with open(external_image, "rb") as fp:
            self.assertEqual(fp.read(), b"EXTERNAL-SYNTHETIC-NOT-FIRMWARE")

    def test_generated_wrapper_rejects_preexisting_nested_symlink_before_make(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile,
            DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "staging_nested_symlink"),
        )
        wrapper = os.path.join(self.temp_dir, "nested-symlink-build.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "nested-symlink-imagebuilder")
        output_dir = os.path.join(builder, "bin", "targets", "ramips", "mt7621")
        os.makedirs(output_dir)
        external_dir = os.path.join(self.temp_dir, "operator-owned-nested-output")
        os.makedirs(external_dir)
        sentinel_path = os.path.join(external_dir, "operator-owned.txt")
        sentinel = "KEEP-OPERATOR-NESTED-OUTPUT"
        with open(sentinel_path, "w", encoding="utf-8") as fp:
            fp.write(sentinel)

        link_path = os.path.join(output_dir, "cache")
        os.symlink(external_dir, link_path)
        escaped_image = os.path.join(external_dir, "escaped.img.gz")
        recipe = (
            "image:\n"
            "\t@test -d \"$(FILES)\"\n"
            "\t@mkdir -p bin/targets/ramips/mt7621/cache\n"
            "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/cache/escaped.img.gz\n"
        )
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)

        self.assertNotEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse(
            os.path.exists(escaped_image),
            "ImageBuilder must not write through a pre-existing nested output symlink",
        )
        self.assertIn(
            "RELEASE-BLOCKED: pre-existing symlink entry in ImageBuilder output tree",
            result.stderr,
        )
        self.assertTrue(os.path.islink(link_path))
        with open(sentinel_path, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)
        self.assertFalse(
            os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256"))
        )

    def test_generated_wrapper_relative_stage_uses_absolute_path(self):
        result, builder, wrapper, stage_absolute = self._run_mock_imagebuilder(
            image_subpath="bin/targets/ramips/mt7621/synthetic.bin"
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Appliance PREVIEW build completed", result.stdout)
        manifest = os.path.join(builder, "RELEASE_MANIFEST.sha256")
        with open(manifest, "r", encoding="utf-8") as fp:
            lines = fp.read().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("synthetic.bin", lines[0])
        with open(wrapper, "r", encoding="utf-8") as fp:
            contents = fp.read()
        self.assertIn("FILES=" + shlex.quote(stage_absolute), contents)

    def test_generated_wrapper_relative_imagebuilder_dir_uses_absolute_path(self):
        # A relative environment override must be normalized before the
        # wrapper changes directory; otherwise BIN_DIR and manifest paths
        # are accidentally resolved relative to the builder twice.
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "relative-builder-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "relative-builder.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "relative-imagebuilder")
        os.makedirs(builder)
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write("image:\n\t@mkdir -p bin/targets/ramips/mt7621\n"
                     "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/synthetic.bin\n")

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = os.path.relpath(builder, self.temp_dir)
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Appliance PREVIEW build completed", result.stdout)
        manifest_path = os.path.join(builder, "RELEASE_MANIFEST.sha256")
        with open(manifest_path, "r", encoding="utf-8") as fp:
            lines = fp.read().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("synthetic.bin", lines[0])

    def test_generate_network_uci_xiaomi(self):
        p = load_profile("xiaomi-4a-gigabit")
        uci = generate_network_uci(p)
        self.assertIn("option name 'br-lan'", uci)
        self.assertIn("option vlan_filtering '1'", uci)
        self.assertIn("list ports 'lan1 lan2'", uci)
        self.assertIn("option device 'wan'", uci)

    def test_generate_network_uci_nanopi(self):
        p = load_profile("nanopi-r2s")
        uci = generate_network_uci(p)
        self.assertIn("option name 'br-lan'", uci)
        self.assertIn("list ports 'eth1'", uci)
        self.assertIn("option device 'eth0'", uci)


    def test_stage_overlay_creates_missing_parent_directories_safely(self):
        source_rootfs = os.path.join(self.temp_dir, "missing-parent-source")
        os.makedirs(source_rootfs)
        source_marker = os.path.join(source_rootfs, "source-marker.txt")
        with open(source_marker, "w", encoding="utf-8") as fp:
            fp.write("SOURCE-PRESERVED")

        missing_parent = os.path.join(
            self.temp_dir, "new-staging-parent", "nested", "output"
        )
        staging_dest = os.path.join(missing_parent, "generated-overlay")
        manifest = stage_overlay(
            load_profile("ew1200g-pro"),
            source_rootfs,
            staging_dest,
        )

        self.assertTrue(os.path.isdir(staging_dest))
        self.assertEqual(manifest["staging_dir"], staging_dest)
        with open(os.path.join(staging_dest, "source-marker.txt"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "SOURCE-PRESERVED")


    def test_stage_overlay_refuses_existing_output_without_deleting_contents(self):
        source_rootfs = os.path.join(self.temp_dir, "safe-source")
        os.makedirs(source_rootfs)
        source_marker = os.path.join(source_rootfs, "source-preserved.txt")
        with open(source_marker, "w", encoding="utf-8") as fp:
            fp.write("SOURCE-PRESERVED")

        staging_dest = os.path.join(self.temp_dir, "existing-staging")
        os.makedirs(staging_dest)
        operator_file = os.path.join(staging_dest, "operator-data.txt")
        with open(operator_file, "w", encoding="utf-8") as fp:
            fp.write("DO-NOT-DELETE")

        with self.assertRaises(FileExistsError):
            stage_overlay(load_profile("ew1200g-pro"), source_rootfs, staging_dest)

        with open(operator_file, encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "DO-NOT-DELETE")
        self.assertTrue(os.path.isfile(source_marker))

    def test_stage_overlay_refuses_source_rootfs_as_output(self):
        source_rootfs = os.path.join(self.temp_dir, "source-is-output")
        os.makedirs(source_rootfs)
        source_marker = os.path.join(source_rootfs, "owner-source.txt")
        with open(source_marker, "w", encoding="utf-8") as fp:
            fp.write("KEEP-SOURCE")

        with self.assertRaises(FileExistsError):
            stage_overlay(load_profile("ew1200g-pro"), source_rootfs, source_rootfs)

        with open(source_marker, encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "KEEP-SOURCE")

    def test_stage_overlay_refuses_new_output_nested_inside_source(self):
        source_rootfs = os.path.join(self.temp_dir, "nested-source")
        os.makedirs(source_rootfs)
        source_marker = os.path.join(source_rootfs, "owner-source.txt")
        with open(source_marker, "w", encoding="utf-8") as fp:
            fp.write("KEEP-SOURCE")
        staging_dest = os.path.join(source_rootfs, "generated-overlay")

        with self.assertRaises(ValueError):
            stage_overlay(load_profile("ew1200g-pro"), source_rootfs, staging_dest)

        self.assertTrue(os.path.isfile(source_marker))
        self.assertFalse(os.path.lexists(staging_dest))



    def test_stage_overlay_rejects_symlinked_output_parent_without_external_creation(self):
        source_rootfs = os.path.join(self.temp_dir, "symlink-parent-source")
        os.makedirs(source_rootfs)
        with open(os.path.join(source_rootfs, "source-marker.txt"), "w", encoding="utf-8") as fp:
            fp.write("SOURCE-PRESERVED")

        external_parent = os.path.join(self.temp_dir, "operator-owned-parent")
        os.makedirs(external_parent)
        sentinel = os.path.join(external_parent, "operator-data.txt")
        with open(sentinel, "w", encoding="utf-8") as fp:
            fp.write("KEEP-EXTERNAL-DATA")

        parent_link = os.path.join(self.temp_dir, "staging-parent-link")
        os.symlink(external_parent, parent_link, target_is_directory=True)
        requested_staging = os.path.join(parent_link, "generated-overlay")

        with self.assertRaisesRegex(ValueError, "Staging destination parent path contains a symlink"):
            stage_overlay(load_profile("ew1200g-pro"), source_rootfs, requested_staging)

        self.assertTrue(os.path.islink(parent_link))
        self.assertFalse(os.path.lexists(os.path.join(external_parent, "generated-overlay")))
        with open(sentinel, encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "KEEP-EXTERNAL-DATA")
        with open(os.path.join(source_rootfs, "source-marker.txt"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "SOURCE-PRESERVED")

    def test_stage_overlay_rejects_parent_swapped_to_symlink_during_copy(self):
        source_rootfs = os.path.join(self.temp_dir, "race-source")
        os.makedirs(source_rootfs)
        with open(os.path.join(source_rootfs, "source-marker.txt"), "w", encoding="utf-8") as fp:
            fp.write("SOURCE-PRESERVED")

        requested_parent = os.path.join(self.temp_dir, "race-staging-parent")
        detached_parent = os.path.join(self.temp_dir, "race-staging-parent-original")
        external_parent = os.path.join(self.temp_dir, "race-operator-parent")
        os.makedirs(requested_parent)
        os.makedirs(external_parent)
        sentinel = os.path.join(external_parent, "operator-data.txt")
        with open(sentinel, "w", encoding="utf-8") as fp:
            fp.write("KEEP-EXTERNAL-DATA")

        requested_staging = os.path.join(requested_parent, "generated-overlay")
        original_copytree = shutil.copytree
        swapped = {"value": False}

        def swap_parent_before_copy(src, dst, *args, **kwargs):
            if not swapped["value"]:
                os.rename(requested_parent, detached_parent)
                os.symlink(external_parent, requested_parent, target_is_directory=True)
                swapped["value"] = True
            return original_copytree(src, dst, *args, **kwargs)

        with mock.patch.object(
            packager.shutil, "copytree", side_effect=swap_parent_before_copy
        ):
            with self.assertRaises(ValueError):
                stage_overlay(
                    load_profile("ew1200g-pro"),
                    source_rootfs,
                    requested_staging,
                )

        self.assertTrue(swapped["value"])
        self.assertTrue(os.path.islink(requested_parent))
        self.assertFalse(
            os.path.lexists(os.path.join(external_parent, "generated-overlay")),
            "a parent replaced after preflight must not redirect the initial rootfs copy",
        )
        self.assertFalse(
            os.path.lexists(os.path.join(detached_parent, "generated-overlay")),
            "failed staging must clean up its pinned partial destination",
        )
        with open(sentinel, encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "KEEP-EXTERNAL-DATA")
        with open(os.path.join(source_rootfs, "source-marker.txt"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "SOURCE-PRESERVED")


    def test_rootfs_copy_rolls_back_partial_staging_on_process_interruption(self):
        source_rootfs = os.path.join(self.temp_dir, "interrupted-copy-source")
        os.makedirs(source_rootfs)
        with open(os.path.join(source_rootfs, "source-marker.txt"), "w", encoding="utf-8") as fp:
            fp.write("SOURCE-PRESERVED")

        for interruption_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(interruption=interruption_type.__name__):
                staging_dest = os.path.join(
                    self.temp_dir,
                    f"interrupted-copy-{interruption_type.__name__.lower()}",
                )

                def interrupt_after_partial_copy(source, destination, *args, **kwargs):
                    partial_directory = os.path.join(destination, "etc")
                    os.makedirs(partial_directory, exist_ok=True)
                    with open(
                        os.path.join(partial_directory, "partial.bin"),
                        "wb",
                    ) as partial_file:
                        partial_file.write(b"partial rootfs bytes")
                    raise interruption_type("simulated rootfs copy interruption")

                with mock.patch.object(
                    packager.shutil,
                    "copytree",
                    side_effect=interrupt_after_partial_copy,
                ):
                    with self.assertRaisesRegex(
                        interruption_type,
                        "simulated rootfs copy interruption",
                    ):
                        packager._copy_rootfs_to_new_staging_directory(
                            source_rootfs,
                            staging_dest,
                        )

                self.assertFalse(
                    os.path.lexists(staging_dest),
                    "interrupted rootfs copy must remove only its own partial staging directory",
                )
                with open(
                    os.path.join(source_rootfs, "source-marker.txt"),
                    "r",
                    encoding="utf-8",
                ) as source_file:
                    self.assertEqual(source_file.read(), "SOURCE-PRESERVED")

    def test_stage_overlay_does_not_chmod_external_directory_symlink_target(self):
        # copytree preserves directory symlinks. Permission normalization must
        # not follow one and mutate an operator-owned directory outside staging.
        source_rootfs = os.path.join(self.temp_dir, "symlink-source")
        external_target = os.path.join(self.temp_dir, "operator-owned")
        os.makedirs(source_rootfs)
        os.makedirs(external_target)
        os.chmod(external_target, 0o700)
        with open(os.path.join(external_target, "operator-data.txt"), "w", encoding="utf-8") as fp:
            fp.write("KEEP-EXTERNAL-DATA")

        source_link = os.path.join(source_rootfs, "external-assets")
        os.symlink(external_target, source_link)
        staging_dest = os.path.join(self.temp_dir, "symlink-staging")
        expected_mode = os.stat(external_target).st_mode & 0o777

        stage_overlay(load_profile("ew1200g-pro"), source_rootfs, staging_dest)

        staged_link = os.path.join(staging_dest, "external-assets")
        self.assertTrue(os.path.islink(staged_link))
        self.assertEqual(os.readlink(staged_link), external_target)
        self.assertEqual(
            os.stat(external_target).st_mode & 0o777,
            expected_mode,
            "staging permission normalization must not chmod a directory symlink target",
        )
        with open(os.path.join(external_target, "operator-data.txt"), encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "KEEP-EXTERNAL-DATA")

    def test_stage_overlay_permission_normalization_does_not_follow_file_symlink_race(self):
        source_rootfs = os.path.join(self.temp_dir, "chmod-file-race-source")
        os.makedirs(source_rootfs)
        external_target = os.path.join(self.temp_dir, "operator-owned-file")
        with open(external_target, "w", encoding="utf-8") as fp:
            fp.write("KEEP-EXTERNAL-FILE")
        os.chmod(external_target, 0o600)

        staging_dest = os.path.join(self.temp_dir, "chmod-file-race-staging")
        staged_target = os.path.join(staging_dest, "etc", "config", "network")
        normalization = {"started": False}
        swapped = {"value": False}
        original_calculate = packager.calculate_overlay_size
        original_chmod = packager.os.chmod

        def calculate_then_enable_normalization(path):
            result = original_calculate(path)
            normalization["started"] = True
            return result

        def chmod_then_swap_file(path, mode, *args, **kwargs):
            if (
                normalization["started"]
                and os.path.abspath(os.fspath(path)) == staged_target
                and not swapped["value"]
            ):
                os.unlink(staged_target)
                os.symlink(external_target, staged_target)
                swapped["value"] = True
            return original_chmod(path, mode, *args, **kwargs)

        with mock.patch.object(
            packager, "calculate_overlay_size",
            side_effect=calculate_then_enable_normalization,
        ), mock.patch.object(
            packager.os, "chmod", side_effect=chmod_then_swap_file
        ):
            stage_overlay(load_profile("ew1200g-pro"), source_rootfs, staging_dest)

        self.assertFalse(
            swapped["value"],
            "permission normalization must not use path-based chmod after a symlink check",
        )
        self.assertEqual(
            os.stat(external_target).st_mode & 0o777,
            0o600,
            "a staged-file symlink race must not change an external file's mode",
        )

    def test_stage_overlay_permission_normalization_does_not_follow_directory_symlink_race(self):
        source_rootfs = os.path.join(self.temp_dir, "chmod-directory-race-source")
        os.makedirs(source_rootfs)
        external_target = os.path.join(self.temp_dir, "operator-owned-directory")
        os.makedirs(external_target)
        os.chmod(external_target, 0o700)

        staging_dest = os.path.join(self.temp_dir, "chmod-directory-race-staging")
        staged_target = os.path.join(staging_dest, "etc", "config")
        moved_target = staged_target + ".detached"
        normalization = {"started": False}
        swapped = {"value": False}
        original_calculate = packager.calculate_overlay_size
        original_chmod = packager.os.chmod

        def calculate_then_enable_normalization(path):
            result = original_calculate(path)
            normalization["started"] = True
            return result

        def chmod_then_swap_directory(path, mode, *args, **kwargs):
            if (
                normalization["started"]
                and os.path.abspath(os.fspath(path)) == staged_target
                and not swapped["value"]
            ):
                os.rename(staged_target, moved_target)
                os.symlink(external_target, staged_target, target_is_directory=True)
                swapped["value"] = True
            return original_chmod(path, mode, *args, **kwargs)

        with mock.patch.object(
            packager, "calculate_overlay_size",
            side_effect=calculate_then_enable_normalization,
        ), mock.patch.object(
            packager.os, "chmod", side_effect=chmod_then_swap_directory
        ):
            stage_overlay(load_profile("ew1200g-pro"), source_rootfs, staging_dest)

        self.assertFalse(
            swapped["value"],
            "permission normalization must not use path-based chmod after a symlink check",
        )
        self.assertEqual(
            os.stat(external_target).st_mode & 0o777,
            0o700,
            "a staged-directory symlink race must not change an external directory's mode",
        )

    def test_stage_overlay_permission_normalization_replaces_external_hardlink_before_mode_change(self):
        source_rootfs = os.path.join(self.temp_dir, "chmod-hardlink-source")
        utility_dir = os.path.join(source_rootfs, "usr", "sbin")
        os.makedirs(utility_dir)
        source_file = os.path.join(utility_dir, "diagnostic")
        with open(source_file, "w", encoding="utf-8") as fp:
            fp.write("#!/bin/sh\nexit 0\n")
        os.chmod(source_file, 0o644)

        staging_dest = os.path.join(self.temp_dir, "chmod-hardlink-staging")
        staged_file = os.path.join(staging_dest, "usr", "sbin", "diagnostic")
        external_target = os.path.join(self.temp_dir, "operator-owned-hardlink")
        original_calculate = packager.calculate_overlay_size
        linked = {"value": False}

        def calculate_then_link_staged_file(path):
            result = original_calculate(path)
            os.link(staged_file, external_target)
            linked["value"] = True
            return result

        with mock.patch.object(
            packager, "calculate_overlay_size",
            side_effect=calculate_then_link_staged_file,
        ):
            stage_overlay(load_profile("ew1200g-pro"), source_rootfs, staging_dest)

        self.assertTrue(linked["value"])
        self.assertEqual(
            os.stat(external_target).st_mode & 0o777,
            0o644,
            "normalizing a staged hardlink must not change the operator-owned inode mode",
        )
        self.assertEqual(os.stat(staged_file).st_mode & 0o777, 0o755)
        external_stat = os.stat(external_target)
        staged_stat = os.stat(staged_file)
        self.assertNotEqual(
            (external_stat.st_dev, external_stat.st_ino),
            (staged_stat.st_dev, staged_stat.st_ino),
        )
        self.assertEqual(external_stat.st_nlink, 1)
        self.assertEqual(staged_stat.st_nlink, 1)

    def test_generated_wrapper_manifest_is_independent_of_build_workspace(self):
        # The same synthetic image bytes must produce the same checksum
        # manifest regardless of the absolute workspace path.
        manifests = []
        for workspace_name in ("builder-one", "builder-two"):
            workspace = os.path.join(self.temp_dir, workspace_name)
            os.makedirs(workspace, exist_ok=True)
            staging = os.path.join(workspace, "staging")
            manifest = stage_overlay(load_profile("gl-mt1300"), DEFAULT_ROOTFS, staging)
            wrapper = os.path.join(workspace, "build.sh")
            generate_build_script(manifest, wrapper)

            builder = os.path.join(workspace, "imagebuilder")
            os.makedirs(builder)
            with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
                fp.write(
                    "image:\n\t@mkdir -p bin/targets/ramips/mt7621\n"
                    "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/synthetic.bin\n"
                )

            env = os.environ.copy()
            env["OPENWRT_IMAGEBUILDER_DIR"] = builder
            result = self._run_generated_wrapper(wrapper, workspace, env)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            manifest_path = os.path.join(builder, "RELEASE_MANIFEST.sha256")
            with open(manifest_path, "r", encoding="utf-8") as fp:
                lines = fp.read().splitlines()
            self.assertEqual(len(lines), 1)
            self.assertIn("bin/targets/ramips/mt7621/synthetic.bin", lines[0])
            self.assertNotIn(builder, lines[0])
            manifests.append(lines)

        self.assertEqual(
            manifests[0],
            manifests[1],
            "identical image bytes must produce workspace-independent checksum manifests",
        )


    def test_generated_wrapper_refuses_temp_manifest_symlink_created_by_make(self):
        # The Makefile runs after the wrapper's preflight checks. A compromised
        # builder must not replace the temporary manifest path with a symlink
        # and redirect the checksum write into an operator-owned file.
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "race-temp-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "race-temp-wrapper.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "race-temp-imagebuilder")
        os.makedirs(builder)
        external_target = os.path.join(self.temp_dir, "operator-temp-manifest.txt")
        sentinel = "KEEP-OPERATOR-TEMP-MANIFEST\n"
        with open(external_target, "w", encoding="utf-8") as fp:
            fp.write(sentinel)

        recipe = (
            "image:\n"
            "\t@mkdir -p bin/targets/ramips/mt7621\n"
            "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/synthetic.bin\n"
            "\t@ln -s " + shlex.quote(external_target) + " RELEASE_MANIFEST.sha256.tmp\n"
        )
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)

        self.assertNotEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("cannot create", (result.stderr + result.stdout).lower())
        self.assertTrue(os.path.islink(
            os.path.join(builder, "RELEASE_MANIFEST.sha256.tmp")
        ))
        with open(external_target, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)
        self.assertFalse(os.path.exists(
            os.path.join(builder, "RELEASE_MANIFEST.sha256")
        ))

    def test_generated_wrapper_refuses_final_manifest_symlink_created_by_make(self):
        # The final manifest path is also re-opened after the build. It must
        # not follow a symlink created after the earlier preflight check.
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "race-final-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "race-final-wrapper.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "race-final-imagebuilder")
        os.makedirs(builder)
        external_target = os.path.join(self.temp_dir, "operator-final-manifest.txt")
        sentinel = "KEEP-OPERATOR-FINAL-MANIFEST\n"
        with open(external_target, "w", encoding="utf-8") as fp:
            fp.write(sentinel)

        recipe = (
            "image:\n"
            "\t@mkdir -p bin/targets/ramips/mt7621\n"
            "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/synthetic.bin\n"
            "\t@ln -s " + shlex.quote(external_target) + " RELEASE_MANIFEST.sha256\n"
        )
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = self._run_generated_wrapper(wrapper, self.temp_dir, env)

        self.assertNotEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertNotEqual(result.returncode, 124, "manifest collision must fail promptly, not time out: " + result.stderr + result.stdout)
        self.assertIn("final checksum manifest path became occupied", (result.stderr + result.stdout).lower())
        self.assertTrue(os.path.islink(
            os.path.join(builder, "RELEASE_MANIFEST.sha256")
        ))
        with open(external_target, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)


    def test_stage_overlay_rejects_network_file_symlink_without_external_write(self):
        source_rootfs = os.path.join(self.temp_dir, "symlink-network-source")
        config_dir = os.path.join(source_rootfs, "etc", "config")
        os.makedirs(config_dir)
        external_target = os.path.join(self.temp_dir, "operator-network.conf")
        sentinel = "KEEP-OPERATOR-NETWORK-CONFIG\\n"
        with open(external_target, "w", encoding="utf-8") as fp:
            fp.write(sentinel)
        os.symlink(external_target, os.path.join(config_dir, "network"))

        with self.assertRaisesRegex(ValueError, "symlink"):
            stage_overlay(
                load_profile("ew1200g-pro"),
                source_rootfs,
                os.path.join(self.temp_dir, "symlink-network-staging"),
            )

        with open(external_target, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)

    def test_stage_overlay_rejects_config_directory_symlink_without_external_write(self):
        source_rootfs = os.path.join(self.temp_dir, "symlink-config-dir-source")
        etc_dir = os.path.join(source_rootfs, "etc")
        external_dir = os.path.join(self.temp_dir, "operator-config-dir")
        os.makedirs(etc_dir)
        os.makedirs(external_dir)
        external_target = os.path.join(external_dir, "network")
        sentinel = "KEEP-OPERATOR-CONFIG-DIRECTORY\\n"
        with open(external_target, "w", encoding="utf-8") as fp:
            fp.write(sentinel)
        os.symlink(external_dir, os.path.join(etc_dir, "config"))

        with self.assertRaisesRegex(ValueError, "symlink"):
            stage_overlay(
                load_profile("ew1200g-pro"),
                source_rootfs,
                os.path.join(self.temp_dir, "symlink-config-dir-staging"),
            )

        with open(external_target, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)

    def test_stage_overlay_rejects_appliance_profile_symlink_without_external_write(self):
        source_rootfs = os.path.join(self.temp_dir, "symlink-profile-source")
        os.makedirs(os.path.join(source_rootfs, "etc", "config"))
        profile_dir = os.path.join(source_rootfs, "etc", "blazepwifi")
        os.makedirs(profile_dir)
        external_target = os.path.join(self.temp_dir, "operator-appliance-profile.json")
        sentinel = '{"operator":"preserve"}\\n'
        with open(external_target, "w", encoding="utf-8") as fp:
            fp.write(sentinel)
        os.symlink(external_target, os.path.join(profile_dir, "appliance_profile.json"))

        with self.assertRaisesRegex(ValueError, "symlink"):
            stage_overlay(
                load_profile("ew1200g-pro"),
                source_rootfs,
                os.path.join(self.temp_dir, "symlink-profile-staging"),
            )

        with open(external_target, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)


    def test_stage_overlay_rejects_rental_destination_directory_symlink_without_external_write(self):
        source_rootfs = os.path.join(self.temp_dir, "symlink-rental-source")
        usr_dir = os.path.join(source_rootfs, "usr")
        external_dir = os.path.join(self.temp_dir, "operator-sbin")
        os.makedirs(usr_dir)
        os.makedirs(external_dir)
        external_target = os.path.join(external_dir, "blazerentalctl")
        sentinel = "KEEP-OPERATOR-RENTAL-EXECUTABLE"
        with open(external_target, "w", encoding="utf-8") as fp:
            fp.write(sentinel)
        os.symlink(external_dir, os.path.join(usr_dir, "sbin"))

        with self.assertRaisesRegex(ValueError, "symlink"):
            stage_overlay(
                load_profile("ew1200g-pro"),
                source_rootfs,
                os.path.join(self.temp_dir, "symlink-rental-staging"),
                include_rental=True,
            )

        with open(external_target, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), sentinel)


    def test_generate_build_script_refuses_symlinked_parent_directory_without_external_write(self):
        profile = load_profile("gl-mt1300")
        manifest = stage_overlay(
            profile, DEFAULT_ROOTFS,
            os.path.join(self.temp_dir, "staging_symlinked_script_parent")
        )
        external_dir = os.path.join(self.temp_dir, "operator-owned-output")
        os.makedirs(external_dir)
        parent_link = os.path.join(self.temp_dir, "build-output-link")
        os.symlink(external_dir, parent_link)
        script_path = os.path.join(parent_link, "generated-build.sh")

        with self.assertRaisesRegex(ValueError, "parent path contains a symlink or non-directory"):
            generate_build_script(manifest, script_path)

        self.assertTrue(os.path.islink(parent_link))
        self.assertFalse(os.path.lexists(os.path.join(external_dir, "generated-build.sh")))






    def test_generated_wrapper_timeout_terminates_make_process_group(self):
        if os.environ.get("PHX_REQUIRE_BWRAP") != "1":
            self.skipTest("Run in the dedicated release-imagebuilder-sandbox workflow")
        if not shutil.which("bwrap"):
            self.fail("PHX_REQUIRE_BWRAP=1 but bubblewrap is not installed")

        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "timeout-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "timeout-wrapper.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "timeout-imagebuilder")
        os.makedirs(builder)
        late_image = os.path.join(
            builder, "bin", "targets", "ramips", "mt7621", "late.img.gz"
        )
        recipe = (
            "image:\n"
            "\t@sleep 2\n"
            "\t@mkdir -p bin/targets/ramips/mt7621\n"
            "\t@printf 'LATE-WRITE' > bin/targets/ramips/mt7621/late.img.gz\n"
        )
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = self._run_generated_wrapper(
            wrapper, self.temp_dir, env, timeout_seconds=1
        )

        self.assertEqual(result.returncode, 125, result.stdout + result.stderr)
        self.assertIn("exceeded its 1s timeout", result.stderr)
        time.sleep(2.2)
        self.assertFalse(
            os.path.lexists(late_image),
            "timed-out ImageBuilder child process continued writing after the runner returned",
        )

    def test_generated_wrapper_contains_make_created_symlink_write_to_host(self):
        # This test runs only in the dedicated bubblewrap workflow. The sentinel
        # is deliberately outside both the ImageBuilder workspace and /tmp.
        if os.environ.get("PHX_REQUIRE_BWRAP") != "1":
            self.skipTest("Run in the dedicated release-imagebuilder-sandbox workflow")
        if not shutil.which("bwrap"):
            self.fail("PHX_REQUIRE_BWRAP=1 but bubblewrap is not installed")
        if not os.path.isdir("/var/tmp") or not os.access("/var/tmp", os.W_OK):
            self.fail("The dedicated Linux sandbox runner must provide writable /var/tmp")

        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "sandbox-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "sandbox-wrapper.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "sandbox-imagebuilder")
        os.makedirs(builder)
        external_dir = tempfile.mkdtemp(prefix="phx-imagebuilder-external-", dir="/var/tmp")
        try:
            external_target = os.path.join(external_dir, "operator-owned-sentinel.txt")
            sentinel = "KEEP-OPERATOR-OWNED-SENTINEL\n"
            with open(external_target, "w", encoding="utf-8") as fp:
                fp.write(sentinel)

            escaped_image = "bin/targets/ramips/mt7621/cache/escape.img.gz"
            symlink_marker = "bin/targets/ramips/mt7621/cache/symlink-created.txt"
            recipe = (
                "image:\n"
                "\t@mkdir -p bin/targets/ramips/mt7621/cache\n"
                "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/synthetic.bin\n"
                "\t@ln -s " + shlex.quote(external_target) + " " + escaped_image + "\n"
                "\t@printf 'SYMLINK-CREATED' > " + symlink_marker + "\n"
                "\t@printf 'BUILDER-OVERWRITE' > " + escaped_image + "\n"
            )
            with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
                fp.write(recipe)

            env = os.environ.copy()
            env["OPENWRT_IMAGEBUILDER_DIR"] = builder
            result = self._run_generated_wrapper(wrapper, self.temp_dir, env)

            escaped_path = os.path.join(builder, escaped_image)
            marker_path = os.path.join(builder, symlink_marker)
            self.assertIn("Building Appliance Firmware", result.stdout, result.stderr + result.stdout)
            self.assertNotEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(
                os.path.islink(escaped_path),
                result.stderr + result.stdout + "\nMakefile-created symlink should remain inside the disposable workspace",
            )
            self.assertTrue(os.path.isfile(marker_path), result.stderr + result.stdout)
            with open(external_target, "r", encoding="utf-8") as fp:
                self.assertEqual(
                    fp.read(), sentinel,
                    "ImageBuilder must not write through a symlink to a host-owned file",
                )
        finally:
            shutil.rmtree(external_dir, ignore_errors=True)


    def test_generated_wrapper_does_not_publish_partial_manifest_when_sort_fails(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "manifest-sort-failure-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "manifest-sort-failure-build.sh")
        generate_build_script(manifest, wrapper)

        builder = os.path.join(self.temp_dir, "manifest-sort-failure-builder")
        os.makedirs(builder, exist_ok=True)
        recipe = (
            "image:\n"
            "\t@mkdir -p bin/targets/ramips/mt7621\n"
            "\t@printf 'SYNTHETIC-NOT-FIRMWARE' > bin/targets/ramips/mt7621/synthetic.bin\n"
        )
        with open(os.path.join(builder, "Makefile"), "w", encoding="utf-8") as fp:
            fp.write(recipe)

        fake_bin = os.path.join(self.temp_dir, "manifest-sort-failure-bin")
        os.makedirs(fake_bin, exist_ok=True)
        fake_sort = os.path.join(fake_bin, "sort")
        with open(fake_sort, "w", encoding="utf-8") as fp:
            fp.write("#!/bin/sh\nprintf 'PARTIAL-CHECKSUM\\n'\nexit 42\n")
        os.chmod(fake_sort, 0o755)

        with open(wrapper, "r", encoding="utf-8") as fp:
            wrapper_content = fp.read()
        trusted_path = 'PATH="/usr/sbin:/usr/bin:/sbin:/bin"'
        self.assertIn(trusted_path, wrapper_content)
        wrapper_content = wrapper_content.replace(
            trusted_path,
            f'PATH="{fake_bin}:/usr/sbin:/usr/bin:/sbin:/bin"',
            1,
        )
        with open(wrapper, "w", encoding="utf-8") as fp:
            fp.write(wrapper_content)

        env = os.environ.copy()
        env["OPENWRT_IMAGEBUILDER_DIR"] = builder
        result = self._run_generated_wrapper(
            wrapper, self.temp_dir, env, timeout_seconds=60
        )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        final_manifest = os.path.join(builder, "RELEASE_MANIFEST.sha256")
        self.assertFalse(
            os.path.lexists(final_manifest),
            "A failed sort must never publish a partial final checksum manifest; "
            + result.stdout + result.stderr,
        )
        self.assertIn(
            "RELEASE-BLOCKED: checksum manifest sort failed",
            result.stderr,
        )
        sorted_temp = os.path.join(builder, "RELEASE_MANIFEST.sha256.sorted.tmp")
        self.assertTrue(os.path.isfile(sorted_temp))
        with open(sorted_temp, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), "PARTIAL-CHECKSUM\n")

    def _manifest_sync_script(self, wrapper):
        with open(wrapper, "r", encoding="utf-8") as fp:
            content = fp.read()
        begin_marker = "# PHX-MANIFEST-DURABILITY-BEGIN"
        end_marker = "# PHX-MANIFEST-DURABILITY-END"
        self.assertIn(begin_marker, content)
        self.assertIn(end_marker, content)
        publish = content.index('if ! ln "$SORTED_MANIFEST" "$OUT_MANIFEST"; then')
        begin = content.index(begin_marker)
        end = content.index(end_marker, begin) + len(end_marker)
        self.assertLess(publish, begin, "Manifest durability must follow atomic hard-link publication")
        self.assertLess(end, content.index('echo "Release manifest written to'))
        self.assertNotIn('rm -f "$SORTED_MANIFEST" "$TMP_MANIFEST"', content)
        return content[begin:end]

    def test_generated_wrapper_fsyncs_manifest_before_temporary_cleanup(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "manifest-durability-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "manifest-durability-build.sh")
        generate_build_script(manifest, wrapper)
        sync_script = self._manifest_sync_script(wrapper)

        builder = os.path.join(self.temp_dir, "manifest-durability-builder")
        os.makedirs(builder)
        final_name = "RELEASE_MANIFEST.sha256"
        sorted_name = "RELEASE_MANIFEST.sha256.sorted.tmp"
        temporary_name = "RELEASE_MANIFEST.sha256.tmp"
        final_path = os.path.join(builder, final_name)
        sorted_path = os.path.join(builder, sorted_name)
        temporary_path = os.path.join(builder, temporary_name)
        expected = "0123456789abcdef  bin/targets/ramips/mt7621/synthetic.bin\\n"
        with open(final_path, "w", encoding="utf-8") as fp:
            fp.write(expected)
        os.link(final_path, sorted_path)
        with open(temporary_path, "w", encoding="utf-8") as fp:
            fp.write("unsorted checksum input\\n")

        events = []
        original_fsync = os.fsync

        def record_fsync(file_descriptor):
            mode = os.fstat(file_descriptor).st_mode
            events.append("directory" if stat.S_ISDIR(mode) else "file")
            return original_fsync(file_descriptor)

        with mock.patch.object(packager.os, "fsync", side_effect=record_fsync):
            with mock.patch.object(
                sys,
                "argv",
                ["manifest-finalize", builder, final_name, sorted_name, temporary_name],
            ):
                exec(sync_script, {"__name__": "__main__"})

        self.assertEqual(
            events,
            ["file", "directory", "directory"],
            "Manifest bytes must sync before the published directory entry, then cleanup must sync",
        )
        self.assertTrue(os.path.isfile(final_path))
        with open(final_path, "r", encoding="utf-8") as fp:
            self.assertEqual(fp.read(), expected)
        self.assertFalse(os.path.lexists(sorted_path))
        self.assertFalse(os.path.lexists(temporary_path))

    def test_generated_wrapper_keeps_temporary_manifests_when_durability_sync_fails(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "manifest-durability-failure-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "manifest-durability-failure-build.sh")
        generate_build_script(manifest, wrapper)
        sync_script = self._manifest_sync_script(wrapper)

        builder = os.path.join(self.temp_dir, "manifest-durability-failure-builder")
        os.makedirs(builder)
        final_name = "RELEASE_MANIFEST.sha256"
        sorted_name = "RELEASE_MANIFEST.sha256.sorted.tmp"
        temporary_name = "RELEASE_MANIFEST.sha256.tmp"
        final_path = os.path.join(builder, final_name)
        sorted_path = os.path.join(builder, sorted_name)
        temporary_path = os.path.join(builder, temporary_name)
        with open(final_path, "w", encoding="utf-8") as fp:
            fp.write("0123456789abcdef  image.bin\\n")
        os.link(final_path, sorted_path)
        with open(temporary_path, "w", encoding="utf-8") as fp:
            fp.write("temporary checksum input\\n")

        with mock.patch.object(
            packager.os, "fsync", side_effect=OSError("simulated manifest durability failure")
        ):
            with mock.patch.object(
                sys,
                "argv",
                ["manifest-finalize", builder, final_name, sorted_name, temporary_name],
            ):
                with self.assertRaisesRegex(
                    SystemExit,
                    "RELEASE-BLOCKED: checksum manifest durability finalization failed",
                ):
                    exec(sync_script, {"__name__": "__main__"})

        self.assertTrue(os.path.isfile(final_path))
        self.assertTrue(os.path.isfile(sorted_path))
        self.assertTrue(os.path.isfile(temporary_path))


    def test_generated_wrapper_keeps_temporary_manifests_when_precleanup_directory_sync_fails(self):
        profile = load_profile("gl-mt1300")
        staging = os.path.join(self.temp_dir, "manifest-directory-sync-failure-staging")
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, staging)
        wrapper = os.path.join(self.temp_dir, "manifest-directory-sync-failure-build.sh")
        generate_build_script(manifest, wrapper)
        sync_script = self._manifest_sync_script(wrapper)

        builder = os.path.join(self.temp_dir, "manifest-directory-sync-failure-builder")
        os.makedirs(builder)
        final_name = "RELEASE_MANIFEST.sha256"
        sorted_name = "RELEASE_MANIFEST.sha256.sorted.tmp"
        temporary_name = "RELEASE_MANIFEST.sha256.tmp"
        final_path = os.path.join(builder, final_name)
        sorted_path = os.path.join(builder, sorted_name)
        temporary_path = os.path.join(builder, temporary_name)
        with open(final_path, "w", encoding="utf-8") as fp:
            fp.write("0123456789abcdef  image.bin\\n")
        os.link(final_path, sorted_path)
        with open(temporary_path, "w", encoding="utf-8") as fp:
            fp.write("temporary checksum input\\n")

        fsync_events = []
        original_fsync = os.fsync

        def fail_precleanup_directory_sync(file_descriptor):
            mode = os.fstat(file_descriptor).st_mode
            event = "directory" if stat.S_ISDIR(mode) else "file"
            fsync_events.append(event)
            if len(fsync_events) == 2:
                raise OSError("simulated pre-cleanup directory fsync failure")
            return original_fsync(file_descriptor)

        with mock.patch.object(
            packager.os, "fsync", side_effect=fail_precleanup_directory_sync
        ):
            with mock.patch.object(
                sys,
                "argv",
                ["manifest-finalize", builder, final_name, sorted_name, temporary_name],
            ):
                with self.assertRaisesRegex(
                    SystemExit,
                    "RELEASE-BLOCKED: checksum manifest durability finalization failed",
                ):
                    exec(sync_script, {"__name__": "__main__"})

        self.assertEqual(
            fsync_events,
            ["file", "directory"],
            "The pre-cleanup directory fsync must be attempted after the manifest inode fsync",
        )
        self.assertTrue(os.path.isfile(final_path))
        self.assertTrue(os.path.isfile(sorted_path))
        self.assertTrue(os.path.isfile(temporary_path))
        self.assertEqual(
            os.stat(final_path).st_ino,
            os.stat(sorted_path).st_ino,
            "A failed directory sync must preserve the published and sorted hard links",
        )
        self.assertEqual(os.stat(final_path).st_nlink, 2)


class TestImageBuilderSandboxTimeouts(unittest.TestCase):
    def test_unprivileged_identity_maps_only_the_invoking_uid_gid(self):
        with mock.patch.object(run_imagebuilder_sandbox.os, "getuid", return_value=1001):
            with mock.patch.object(run_imagebuilder_sandbox.os, "getgid", return_value=1001):
                with mock.patch.object(run_imagebuilder_sandbox.os, "geteuid", return_value=1001):
                    with mock.patch.object(run_imagebuilder_sandbox.os, "getegid", return_value=1001):
                        self.assertEqual(
                            run_imagebuilder_sandbox._invoking_unprivileged_identity(),
                            (1001, 1001),
                        )

    def test_unprivileged_identity_rejects_root_execution(self):
        with mock.patch.object(run_imagebuilder_sandbox.os, "getuid", return_value=0):
            with mock.patch.object(run_imagebuilder_sandbox.os, "getgid", return_value=0):
                with mock.patch.object(run_imagebuilder_sandbox.os, "geteuid", return_value=0):
                    with mock.patch.object(run_imagebuilder_sandbox.os, "getegid", return_value=0):
                        with self.assertRaisesRegex(PermissionError, "non-root"):
                            run_imagebuilder_sandbox._invoking_unprivileged_identity()

    def test_unprivileged_identity_rejects_mismatched_effective_ids(self):
        with mock.patch.object(run_imagebuilder_sandbox.os, "getuid", return_value=1001):
            with mock.patch.object(run_imagebuilder_sandbox.os, "getgid", return_value=1001):
                with mock.patch.object(run_imagebuilder_sandbox.os, "geteuid", return_value=0):
                    with mock.patch.object(run_imagebuilder_sandbox.os, "getegid", return_value=0):
                        with self.assertRaisesRegex(PermissionError, "mismatched effective"):
                            run_imagebuilder_sandbox._invoking_unprivileged_identity()

    def test_communicate_timeout_kills_bwrap_and_sandbox_process_groups(self):
        class TimedOutProcess:
            pid = 41001

            def __init__(self):
                self.timeouts = []
                self.returncode = None

            def communicate(self, timeout=None):
                self.timeouts.append(timeout)
                if len(self.timeouts) == 1:
                    raise subprocess.TimeoutExpired(
                        ["bwrap"], timeout,
                        output="partial stdout", stderr="partial stderr"
                    )
                self.returncode = -9
                return "partial stdout", "terminated stderr"

            def poll(self):
                return self.returncode

            def kill(self):
                self.returncode = -9

        process = TimedOutProcess()

        def no_process_groups_remain(pgid, signum):
            if signum == 0:
                raise ProcessLookupError()

        with mock.patch.object(
            run_imagebuilder_sandbox.os, "killpg", side_effect=no_process_groups_remain
        ) as killpg:
            (stdout, stderr), timed_out = run_imagebuilder_sandbox._communicate_with_timeout(
                process, timeout_seconds=1, child_pgid=41002
            )

        self.assertTrue(timed_out)
        self.assertIn("partial stdout", stdout)
        self.assertIn("terminated stderr", stderr)
        self.assertEqual(process.timeouts, [1, run_imagebuilder_sandbox.PROCESS_TERMINATION_GRACE_SECONDS])
        self.assertEqual(
            [(call.args[0], call.args[1]) for call in killpg.call_args_list],
            [
                (41001, run_imagebuilder_sandbox.signal.SIGTERM),
                (41002, run_imagebuilder_sandbox.signal.SIGTERM),
                (41001, run_imagebuilder_sandbox.signal.SIGKILL),
                (41002, run_imagebuilder_sandbox.signal.SIGKILL),
                (41001, 0),
                (41002, 0),
            ],
        )

    def test_communicate_normal_exit_reaps_detached_sandbox_process_group(self):
        class CompletedProcess:
            pid = 41011

            def __init__(self):
                self.communicate_calls = []

            def communicate(self, timeout=None):
                self.communicate_calls.append(timeout)
                return "build completed", ""

            def kill(self):
                raise AssertionError("completed process must not need direct kill")

        process = CompletedProcess()
        probes = {41011: 0, 41012: 0}

        def fake_killpg(pgid, signum):
            if signum == 0:
                probes[pgid] += 1
                if probes[pgid] >= 2:
                    raise ProcessLookupError()
            return None

        with mock.patch.object(
            run_imagebuilder_sandbox.os, "killpg", side_effect=fake_killpg
        ) as killpg:
            with mock.patch("time.sleep") as sleep:
                (stdout, stderr), blocked = run_imagebuilder_sandbox._communicate_with_timeout(
                    process, timeout_seconds=10, child_pgid=41012
                )

        self.assertFalse(blocked, stderr)
        self.assertEqual(stdout, "build completed")
        calls = [(call.args[0], call.args[1]) for call in killpg.call_args_list]
        self.assertIn(
            (41012, run_imagebuilder_sandbox.signal.SIGTERM),
            calls,
            "normal wrapper exit must terminate a detached sandbox child",
        )
        self.assertIn(
            (41012, run_imagebuilder_sandbox.signal.SIGKILL),
            calls,
            "detached sandbox child must be killed after the grace period",
        )
        self.assertIn(
            (41012, 0),
            calls,
            "runner must confirm the child process group no longer exists",
        )
        self.assertTrue(sleep.called, "runner must wait between process-group existence probes")

    def test_communicate_normal_exit_does_not_misclassify_release_blocked_output(self):
        class CompletedProcess:
            pid = 41015

            def communicate(self, timeout=None):
                return "", "RELEASE-BLOCKED: final checksum manifest was not published"

            def kill(self):
                raise AssertionError("completed process must not need direct kill")

        process = CompletedProcess()

        def no_process_groups_remain(pgid, signum):
            if signum == 0:
                raise ProcessLookupError()

        with mock.patch.object(
            run_imagebuilder_sandbox.os, "killpg", side_effect=no_process_groups_remain
        ):
            (stdout, stderr), blocked = run_imagebuilder_sandbox._communicate_with_timeout(
                process, timeout_seconds=10
            )

        self.assertFalse(
            blocked,
            "a normal wrapper failure diagnostic is not a process-group cleanup failure",
        )
        self.assertIn(
            "RELEASE-BLOCKED: final checksum manifest was not published",
            stderr,
        )

    def test_communicate_fails_closed_when_detached_group_survives_kill(self):
        class CompletedProcess:
            pid = 41021

            def communicate(self, timeout=None):
                return "build completed", ""

            def kill(self):
                raise AssertionError("completed process must not need direct kill")

        process = CompletedProcess()

        def persistent_group(pgid, signum):
            if signum == 0:
                return None
            return None

        with mock.patch.object(
            run_imagebuilder_sandbox.os, "killpg", side_effect=persistent_group
        ):
            with mock.patch.object(
                run_imagebuilder_sandbox, "PROCESS_TERMINATION_GRACE_SECONDS", 0.01
            ):
                clock = [0.0]

                def advance_clock():
                    clock[0] += 1.0
                    return clock[0]

                with mock.patch("time.monotonic", side_effect=advance_clock):
                    with mock.patch("time.sleep"):
                        (stdout, stderr), blocked = run_imagebuilder_sandbox._communicate_with_timeout(
                            process, timeout_seconds=10, child_pgid=41022
                        )

        self.assertTrue(
            blocked,
            "a command leader exiting must not hide a surviving sandbox process group",
        )
        self.assertIn("sandbox process group", stderr.lower())

    def test_runner_rejects_symlinked_bubblewrap_in_trusted_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "real-bwrap")
            link = os.path.join(directory, "bwrap")
            with open(target, "w", encoding="utf-8") as fp:
                fp.write("#!/bin/sh\\nexit 0\\n")
            os.chmod(target, 0o755)
            os.symlink(target, link)

            with mock.patch.object(
                run_imagebuilder_sandbox.os.path, "dirname", return_value="/usr/bin"
            ):
                self.assertFalse(
                    run_imagebuilder_sandbox._is_within_trusted_system_directories(link),
                    "a trusted-directory symlink must not redirect execution outside that directory",
                )

    def test_runner_rejects_setid_bubblewrap_in_trusted_directory(self):
        for mode in (0o4755, 0o2755):
            with self.subTest(mode=oct(mode)):
                with tempfile.TemporaryDirectory() as directory:
                    target = os.path.join(directory, "bwrap")
                    with open(target, "w", encoding="utf-8") as fp:
                        fp.write("#!/bin/sh\nexit 0\n")
                    with mock.patch.object(
                        run_imagebuilder_sandbox.os.path, "dirname", return_value="/usr/bin"
                    ):
                        with trusted_bwrap_metadata_patches(
                            run_imagebuilder_sandbox, target, file_mode=mode
                        ):
                            self.assertFalse(
                                run_imagebuilder_sandbox._is_within_trusted_system_directories(target),
                                "setuid/setgid Bubblewrap is not the approved unprivileged userns mode",
                            )

    def test_runner_rejects_group_or_world_writable_bubblewrap(self):
        for mode in (0o775, 0o757):
            with self.subTest(mode=oct(mode)):
                with tempfile.TemporaryDirectory() as directory:
                    target = os.path.join(directory, "bwrap")
                    with open(target, "w", encoding="utf-8") as fp:
                        fp.write("#!/bin/sh\nexit 0\n")
                    with mock.patch.object(
                        run_imagebuilder_sandbox.os.path, "dirname", return_value="/usr/bin"
                    ):
                        with trusted_bwrap_metadata_patches(
                            run_imagebuilder_sandbox, target, file_mode=mode
                        ):
                            self.assertFalse(
                                run_imagebuilder_sandbox._is_within_trusted_system_directories(target),
                                "group/world-writable Bubblewrap must not be trusted",
                            )

    def test_runner_rejects_symlinked_parent_redirect_outside_trusted_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "bwrap")
            with open(target, "w", encoding="utf-8") as fp:
                fp.write("#!/bin/sh\nexit 0\n")
            os.chmod(target, 0o755)
            with mock.patch.object(
                run_imagebuilder_sandbox.os.path, "dirname", return_value="/usr/bin"
            ):
                with mock.patch.object(
                    run_imagebuilder_sandbox.os.path,
                    "realpath",
                    return_value="/tmp/untrusted/bin",
                ):
                    self.assertFalse(
                        run_imagebuilder_sandbox._is_within_trusted_system_directories(target),
                        "a trusted-looking path must not resolve through an untrusted parent",
                    )

    def test_runner_rejects_untrusted_trusted_parent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "bwrap")
            with open(target, "w", encoding="utf-8") as fp:
                fp.write("#!/bin/sh\nexit 0\n")
            os.chmod(target, 0o755)
            with mock.patch.object(
                run_imagebuilder_sandbox.os.path, "dirname", return_value="/usr/bin"
            ):
                for mode, uid in ((0o777, 0), (0o755, 1000)):
                    with self.subTest(mode=oct(mode), uid=uid):
                        with trusted_bwrap_metadata_patches(
                            run_imagebuilder_sandbox,
                            target,
                            parent_mode=mode,
                            parent_uid=uid,
                        ):
                            self.assertFalse(
                                run_imagebuilder_sandbox._is_within_trusted_system_directories(target),
                                "trusted executable directories must be root-owned and not group/world writable",
                            )

    def test_runner_rejects_non_root_owned_bubblewrap(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "bwrap")
            with open(target, "w", encoding="utf-8") as fp:
                fp.write("#!/bin/sh\nexit 0\n")
            os.chmod(target, 0o755)
            with mock.patch.object(
                run_imagebuilder_sandbox.os.path, "dirname", return_value="/usr/bin"
            ):
                with trusted_bwrap_metadata_patches(
                    run_imagebuilder_sandbox, target, file_uid=1000
                ):
                    self.assertFalse(
                        run_imagebuilder_sandbox._is_within_trusted_system_directories(target),
                        "a Bubblewrap executable not owned by root is not trusted",
                    )

    def test_runner_accepts_regular_unprivileged_bubblewrap_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "bwrap")
            with open(target, "w", encoding="utf-8") as fp:
                fp.write("#!/bin/sh\nexit 0\n")
            os.chmod(target, 0o755)
            with mock.patch.object(
                run_imagebuilder_sandbox.os.path, "dirname", return_value="/usr/bin"
            ):
                with trusted_bwrap_metadata_patches(run_imagebuilder_sandbox, target):
                    self.assertTrue(
                        run_imagebuilder_sandbox._is_within_trusted_system_directories(target)
                    )

    def test_runner_accepts_bin_alias_resolving_to_trusted_usr_bin(self):
        target = "/bin/bwrap"
        with mock.patch.object(
            run_imagebuilder_sandbox.os.path, "dirname", return_value="/bin"
        ):
            with mock.patch.object(run_imagebuilder_sandbox.os, "access", return_value=True):
                with trusted_bwrap_metadata_patches(
                    run_imagebuilder_sandbox, target, parent_path="/usr/bin"
                ):
                    self.assertTrue(
                        run_imagebuilder_sandbox._is_within_trusted_system_directories(target)
                    )

    def test_runner_rejects_unbounded_build_timeout(self):
        with mock.patch.object(
            sys,
            "argv",
            [
                "run_imagebuilder_sandbox.py",
                "--cwd", ".",
                "--builder", "./builder",
                "--wrapper", "./build.sh",
                "--timeout-seconds", "0",
            ],
        ):
            result = run_imagebuilder_sandbox.main()

        self.assertEqual(result, 125)


if __name__ == "__main__":
    unittest.main()



