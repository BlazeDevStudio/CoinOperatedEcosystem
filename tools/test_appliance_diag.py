#!/usr/bin/env python3
"""Automated tests for blaze-appliance-diag runtime utility."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAG_SCRIPT = os.path.join(BASE_DIR, "Pisowifi", "openwrt", "rootfs", "usr", "sbin", "blaze-appliance-diag")


class TestApplianceDiag(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.isfile(DIAG_SCRIPT), f"Diag script not found: {DIAG_SCRIPT}")
        self.temp_dir = tempfile.mkdtemp(prefix="test_diag_")
        self.state_dir = os.path.join(self.temp_dir, "state")
        os.makedirs(self.state_dir, exist_ok=True)
        self.profile_path = os.path.join(self.temp_dir, "appliance_profile.json")

        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump({
                "profile_id": "ew1200g-pro",
                "name": "Ruijie RG-EW1200G Pro v1.1",
                "target_architecture": "ramips/mt7621",
                "hardware": {"min_free_overlay_kb": 2000}
            }, f)

        # Mock sysinfo
        self.board_file = os.path.join(self.temp_dir, "board_name")
        with open(self.board_file, "w", encoding="utf-8") as f:
            f.write("ruijie,rg-ew1200g-pro\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_diag(self, args=None, extra_env=None):
        cmd = ["sh", DIAG_SCRIPT] + (args or [])
        env = os.environ.copy()
        env["BP_STATE"] = self.state_dir
        env["BP_APPLIANCE_PROFILE"] = self.profile_path
        env["BP_SYSINFO_BOARD"] = self.board_file
        if extra_env:
            env.update(extra_env)
        return subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_healthy_cli_output(self):
        res = self.run_diag()
        self.assertEqual(res.returncode, 0, f"Expected 0, got {res.returncode}; stderr: {res.stderr}")
        self.assertIn("=== Blaze Appliance Diagnostics ===", res.stdout)
        self.assertIn("Profile:    [MATCHED", res.stdout)
        self.assertIn("Ruijie RG-EW1200G Pro v1.1", res.stdout)
        self.assertIn("Journals:   [OK] Transaction journals verified clean", res.stdout)
        self.assertIn("=== RESULT: HEALTHY ===", res.stdout)

    def test_healthy_json_output(self):
        res = self.run_diag(["--json"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["healthy"])
        self.assertEqual(data["profile"]["profile_id"], "ew1200g-pro")
        self.assertEqual(data["storage"]["status"], "OK")
        self.assertEqual(data["financial_journals"]["status"], "OK")

    def test_paid_state_uncertain_pinned(self):
        uncertain_file = os.path.join(self.state_dir, "paid-state-uncertain")
        with open(uncertain_file, "w") as f:
            f.write("reconciliation required\n")

        res = self.run_diag(["--json"])
        self.assertEqual(res.returncode, 2)
        data = json.loads(res.stdout)
        self.assertFalse(data["healthy"])
        self.assertEqual(data["financial_journals"]["status"], "FAIL_PAID_UNCERTAIN")
        self.assertIn("paid-state-uncertain pinned", data["financial_journals"]["message"])

    def test_pending_commit_record_detected(self):
        commit_file = os.path.join(self.state_dir, "voucher-txn.commit")
        with open(commit_file, "w") as f:
            f.write("VERSION=1\n")

        res = self.run_diag(["--json"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["healthy"])
        self.assertEqual(data["financial_journals"]["status"], "PENDING_ROLL_FORWARD")
        self.assertIn("voucher-txn", data["financial_journals"]["message"])

    def test_symlink_in_live_state_fails(self):
        target = os.path.join(self.temp_dir, "dummy_accounts.tsv")
        with open(target, "w") as f:
            f.write("data\n")
        symlink_path = os.path.join(self.state_dir, "accounts.tsv")
        os.symlink(target, symlink_path)

        res = self.run_diag(["--json"])
        self.assertEqual(res.returncode, 2)
        data = json.loads(res.stdout)
        self.assertFalse(data["healthy"])
        self.assertEqual(data["financial_journals"]["status"], "FAIL_UNTRUSTED_SYMLINK")

    def test_unconfigured_profile_fallback(self):
        os.remove(self.profile_path)
        res = self.run_diag(["--json"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["profile"]["status"], "UNCONFIGURED")


if __name__ == "__main__":
    unittest.main()
