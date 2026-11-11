#!/usr/bin/env python3
"""Automated tests for Appliance Firmware Packager and ImageBuilder Configurator."""
import json
import os
import shutil
import tempfile
import unittest

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
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_all_profiles(self):
        for pid in self.profiles:
            p = load_profile(pid)
            self.assertEqual(p["profile_id"], pid)
            self.assertIn("target_architecture", p)
            self.assertIn("hardware", p)
            self.assertIn("networking", p)

    def test_generate_network_uci_ew1200g_pro(self):
        p = load_profile("ew1200g-pro")
        uci = generate_network_uci(p)
        self.assertIn("option name 'br-lan'", uci)
        self.assertIn("option vlan_filtering '1'", uci)
        self.assertIn("list ports 'lan1 lan2 lan3'", uci)
        self.assertIn("option device 'br-lan.10'", uci)
        self.assertIn("option device 'br-lan.20'", uci)
        self.assertIn("option device 'wan'", uci)

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
        self.assertIn("FILES=\"/tmp/staging\"", cmd)

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

        ctl_path = os.path.join(staging_dest, "usr", "sbin", "blazerentalctl")
        mode = os.stat(ctl_path).st_mode
        self.assertTrue(bool(mode & 0o111), "blazerentalctl must be executable (0755)")

        cgi_path = os.path.join(staging_dest, "www", "cgi-bin", "blazerental")
        mode = os.stat(cgi_path).st_mode
        self.assertTrue(bool(mode & 0o111), "cgi-bin/blazerental must be executable (0755)")

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


if __name__ == "__main__":
    unittest.main()



