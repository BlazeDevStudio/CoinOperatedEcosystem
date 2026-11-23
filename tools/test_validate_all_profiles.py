#!/usr/bin/env python3
"""Release-owned regression tests for bounded appliance profile diagnostics."""
import io
import json
import os
import tempfile
import stat
import subprocess
import unittest
from types import SimpleNamespace
from unittest import mock

import validate_all_profiles as validator


class TestValidateProfileDiagnostics(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "profile_id": "test-router",
            "name": "Test Router",
            "target_architecture": "test/target",
            "hardware": {
                "flash_kb": 1024,
                "min_free_overlay_kb": 128,
            },
        }
        self.temp_base = "/tmp/phx-profile-validation"
        self.stage_no_rental = validator.os.path.join(
            self.temp_base, "stage_test-router_standalone"
        )
        self.script_standalone = validator.os.path.join(
            self.temp_base, "build_test-router.sh"
        )
        self.network_uci = validator.os.path.join(
            self.stage_no_rental, "etc", "config", "network"
        )

    def _validate(self, *, run_result=None, run_error=None):
        content_by_path = {
            self.network_uci: "config device 'br_lan'\n",
            self.script_standalone: "PROFILE=test-router\n",
        }

        def fake_open(path, mode="r", encoding=None):
            try:
                return io.StringIO(content_by_path[path])
            except KeyError as exc:
                raise AssertionError(f"unexpected file read: {path}") from exc

        run_patch = {"return_value": run_result}
        if run_error is not None:
            run_patch = {"side_effect": run_error}

        with (
            mock.patch.object(validator, "load_profile", return_value=self.profile),
            mock.patch.object(
                validator,
                "stage_overlay",
                side_effect=[
                    {"overlay_size_kb": 1},
                    {"overlay_size_kb": 1},
                ],
            ),
            mock.patch.object(validator, "generate_build_script"),
            mock.patch.object(validator.os.path, "isfile", return_value=True),
            mock.patch.object(
                validator.os,
                "stat",
                return_value=SimpleNamespace(
                    st_mode=stat.S_IFREG | stat.S_IXUSR
                ),
            ),
            mock.patch("builtins.open", side_effect=fake_open),
            mock.patch.object(validator.subprocess, "run", **run_patch) as run,
        ):
            result = validator.validate_profile("test-router.json", self.temp_base)

        return result, run

    def test_appliance_diagnostics_run_has_a_hard_timeout(self):
        completed = SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {"profile": {"profile_id": "test-router", "status": "CONFIGURED"}}
            ),
            stderr="",
        )

        result, run = self._validate(run_result=completed)

        self.assertEqual(result["profile_id"], "test-router")
        self.assertEqual(run.call_args.kwargs.get("timeout"), 30)

    def test_appliance_diagnostics_timeout_is_reported_as_profile_failure(self):
        timeout = subprocess.TimeoutExpired(
            cmd=["sh", validator.DIAG_SCRIPT, "--json"],
            timeout=30,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            r"blaze-appliance-diag timed out for test-router after 30 seconds",
        ):
            self._validate(run_error=timeout)


    def _main_fixture(self, root):
        profiles_dir = os.path.join(root, "profiles")
        os.mkdir(profiles_dir)
        with open(os.path.join(profiles_dir, "test-router.json"), "w", encoding="utf-8") as fp:
            fp.write("{}\n")
        staging_dir = os.path.join(root, "validation")
        os.mkdir(staging_dir)
        return profiles_dir, staging_dir

    def test_main_fails_closed_when_validation_workspace_cleanup_fails(self):
        with tempfile.TemporaryDirectory() as root:
            profiles_dir, staging_dir = self._main_fixture(root)
            result = {
                "profile_id": "test-router",
                "name": "Test Router",
                "architecture": "test/target",
                "standalone_kb": 1,
                "rental_bundle_kb": 1,
                "diag_status": "CONFIGURED",
            }
            with (
                mock.patch.object(validator, "PROFILES_DIR", profiles_dir),
                mock.patch.object(validator.tempfile, "mkdtemp", return_value=staging_dir),
                mock.patch.object(validator, "validate_profile", return_value=result),
                mock.patch.object(
                    validator.shutil,
                    "rmtree",
                    side_effect=PermissionError("injected workspace cleanup failure"),
                ),
                mock.patch("sys.stderr", new_callable=io.StringIO) as stderr,
            ):
                with self.assertRaises(SystemExit) as raised:
                    validator.main()

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("validation workspace cleanup failed", stderr.getvalue())
            self.assertTrue(os.path.isdir(staging_dir))

    def test_main_preserves_primary_interruption_when_workspace_cleanup_fails(self):
        with tempfile.TemporaryDirectory() as root:
            profiles_dir, staging_dir = self._main_fixture(root)
            with (
                mock.patch.object(validator, "PROFILES_DIR", profiles_dir),
                mock.patch.object(validator.tempfile, "mkdtemp", return_value=staging_dir),
                mock.patch.object(
                    validator,
                    "validate_profile",
                    side_effect=KeyboardInterrupt("primary profile interruption"),
                ),
                mock.patch.object(
                    validator.shutil,
                    "rmtree",
                    side_effect=PermissionError("injected workspace cleanup failure"),
                ),
                mock.patch("sys.stderr", new_callable=io.StringIO) as stderr,
            ):
                with self.assertRaisesRegex(
                    KeyboardInterrupt, "primary profile interruption"
                ):
                    validator.main()

            self.assertIn("preserving primary KeyboardInterrupt", stderr.getvalue())
            self.assertTrue(os.path.isdir(staging_dir))


if __name__ == "__main__":
    unittest.main()
