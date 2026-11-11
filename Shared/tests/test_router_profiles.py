#!/usr/bin/env python3
"""Automated tests for Router Hardware Profiles and Schema Validation."""
import json
import os
import re
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTER_PROFILE_DIR = os.path.join(BASE_DIR, "contracts", "router-profile")
SCHEMA_PATH = os.path.join(ROUTER_PROFILE_DIR, "schema_v1.json")
PROFILES_DIR = os.path.join(ROUTER_PROFILE_DIR, "profiles")


class TestRouterProfiles(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.isfile(SCHEMA_PATH), f"Missing schema file: {SCHEMA_PATH}")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        self.assertTrue(os.path.isdir(PROFILES_DIR), f"Missing profiles directory: {PROFILES_DIR}")
        self.profile_files = [
            f for f in os.listdir(PROFILES_DIR) if f.endswith(".json")
        ]
        self.assertGreaterEqual(len(self.profile_files), 3, "Expected at least 3 profiles (ew1200g-pro, r281, x86_64)")

    def test_schema_structure(self):
        self.assertEqual(self.schema["$schema"], "http://json-schema.org/draft-07/schema#")
        self.assertIn("required", self.schema)
        for req in ["profile_id", "name", "version", "target_architecture", "detection", "hardware", "networking"]:
            self.assertIn(req, self.schema["required"])

    def test_profiles_conform_to_schema(self):
        for pf in self.profile_files:
            path = os.path.join(PROFILES_DIR, pf)
            with open(path, "r", encoding="utf-8") as f:
                p = json.load(f)

            # Validate top-level required fields
            for field in self.schema["required"]:
                self.assertIn(field, p, f"Profile {pf} missing required field '{field}'")

            # Validate detection
            self.assertIn("board_name_pattern", p["detection"])
            self.assertIn("model_pattern", p["detection"])
            re.compile(p["detection"]["board_name_pattern"])
            re.compile(p["detection"]["model_pattern"])

            # Validate hardware constraints
            hw = p["hardware"]
            self.assertGreaterEqual(hw["flash_kb"], 8192, f"Profile {pf} flash below 8MB limit")
            self.assertGreaterEqual(hw["ram_mb"], 64, f"Profile {pf} RAM below 64MB limit")
            self.assertGreaterEqual(hw["min_free_overlay_kb"], 1000, f"Profile {pf} overlay threshold below 1MB")
            self.assertIn(hw["storage_type"], ["nor_spi", "nand_spi", "emmc", "disk"])

            # Validate networking
            net = p["networking"]
            self.assertTrue(net["wan_interface"])
            self.assertTrue(net["lan_interface"])
            self.assertIn(net["switch_type"], ["dsa", "swconfig", "generic"])
            self.assertGreaterEqual(len(net["ports"]), 1)

            # Validate port definitions
            for port in net["ports"]:
                self.assertTrue(port["label"])
                self.assertTrue(port["interface"])
                self.assertGreater(port["speed_mbps"], 0)

            # Validate VLAN isolation IDs
            vlans = net["default_vlan_ids"]
            for vlan_key in ["lan", "guest", "vendo"]:
                self.assertIn(vlan_key, vlans)
                vid = vlans[vlan_key]
                self.assertIsInstance(vid, int)
                self.assertGreaterEqual(vid, 1)
                self.assertLessEqual(vid, 4094)

            # Ensure distinct VLAN IDs for separation
            vlan_set = {vlans["lan"], vlans["guest"], vlans["vendo"]}
            self.assertEqual(len(vlan_set), 3, f"Profile {pf} has overlapping default VLAN IDs: {vlans}")

    def test_ew1200g_pro_sysinfo_detection(self):
        path = os.path.join(PROFILES_DIR, "ew1200g-pro.json")
        with open(path, "r", encoding="utf-8") as f:
            p = json.load(f)

        board_re = re.compile(p["detection"]["board_name_pattern"], re.IGNORECASE)
        model_re = re.compile(p["detection"]["model_pattern"], re.IGNORECASE)

        # Genuine sysinfo matching
        self.assertTrue(board_re.match("ruijie,rg-ew1200g-pro-v1"))
        self.assertTrue(board_re.match("ruijie,rg-ew1200g-pro"))
        self.assertTrue(model_re.match("Ruijie RG-EW1200G Pro v1.1"))
        self.assertTrue(model_re.match("RG-EW1200G PRO"))

        # Non-matching devices must fail
        self.assertFalse(board_re.match("notion,r281"))
        self.assertFalse(model_re.match("Notion R281"))
        self.assertFalse(board_re.match("x86/64"))

        # MediaTek MT7621 specific constraints
        self.assertEqual(p["target_architecture"], "ramips/mt7621")
        self.assertEqual(p["hardware"]["flash_kb"], 16384)
        self.assertEqual(p["hardware"]["ram_mb"], 128)
        self.assertEqual(p["hardware"]["storage_type"], "nor_spi")
        self.assertEqual(p["networking"]["switch_type"], "dsa")
        self.assertEqual(len(p["networking"]["ports"]), 4)

    def test_r281_sysinfo_detection(self):
        path = os.path.join(PROFILES_DIR, "r281.json")
        with open(path, "r", encoding="utf-8") as f:
            p = json.load(f)

        board_re = re.compile(p["detection"]["board_name_pattern"], re.IGNORECASE)
        model_re = re.compile(p["detection"]["model_pattern"], re.IGNORECASE)

        self.assertTrue(board_re.match("notion,r281"))
        self.assertTrue(model_re.match("Notion R281"))
        self.assertFalse(board_re.match("ruijie,rg-ew1200g-pro-v1"))

        self.assertEqual(p["target_architecture"], "ramips/mt7621")
        self.assertEqual(p["hardware"]["flash_kb"], 32768)
        self.assertEqual(p["hardware"]["ram_mb"], 128)

    def test_x86_64_sysinfo_detection(self):
        path = os.path.join(PROFILES_DIR, "x86_64.json")
        with open(path, "r", encoding="utf-8") as f:
            p = json.load(f)

        board_re = re.compile(p["detection"]["board_name_pattern"], re.IGNORECASE)
        model_re = re.compile(p["detection"]["model_pattern"], re.IGNORECASE)

        self.assertTrue(board_re.match("x86/64"))
        self.assertTrue(board_re.match("generic"))
        self.assertTrue(model_re.match("QEMU Standard PC (i440FX + PIIX, 1996)"))
        self.assertTrue(model_re.match("Generic PC"))

        self.assertEqual(p["target_architecture"], "x86/64")
        self.assertEqual(p["hardware"]["storage_type"], "disk")

    def test_orangepi_sysinfo_detection(self):
        path = os.path.join(PROFILES_DIR, "orangepi-r1-plus-lts.json")
        with open(path, "r", encoding="utf-8") as f:
            p = json.load(f)

        board_re = re.compile(p["detection"]["board_name_pattern"], re.IGNORECASE)
        model_re = re.compile(p["detection"]["model_pattern"], re.IGNORECASE)

        self.assertTrue(board_re.match("xunlong,orangepi-r1-plus-lts"))
        self.assertTrue(board_re.match("orangepi-r1-plus"))
        self.assertTrue(model_re.match("Xunlong Orange Pi R1 Plus LTS"))

        self.assertEqual(p["target_architecture"], "rockchip/arm64")
        self.assertEqual(p["hardware"]["storage_type"], "emmc")
        self.assertEqual(p["hardware"]["ram_mb"], 1024)


if __name__ == "__main__":
    unittest.main()
