#!/usr/bin/env python3
"""Release-owned regression tests for bounded appliance profile diagnostics."""
import io
import json
import os
import tempfile
import stat
import time
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
            mock.patch.object(validator, "run_appliance_diagnostics", **run_patch) as run,
        ):
            result = validator.validate_profile("test-router.json", self.temp_base)

        return result, run

    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_appliance_diagnostics_run_has_a_hard_timeout(self):
        completed_stdout = json.dumps(
            {"profile": {"profile_id": "test-router", "status": "CONFIGURED"}}
        )
        process = mock.Mock()
        process.pid = 12345
        process.returncode = 0
        process.wait.return_value = 0

        with (
            mock.patch.object(
                validator.subprocess, "Popen", return_value=process
            ) as popen,
            mock.patch.object(
                validator, "_terminate_process_groups", return_value=(completed_stdout, "")
            ) as terminate,
        ):
            result = validator.run_appliance_diagnostics("test-router", {})

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, completed_stdout)
        self.assertEqual(process.wait.call_args.kwargs.get("timeout"), 30)
        self.assertTrue(popen.call_args.kwargs.get("start_new_session"))
        terminate.assert_called_once_with(process)

    def test_appliance_diagnostics_timeout_is_reported_as_profile_failure(self):
        timeout = RuntimeError(
            "blaze-appliance-diag timed out for test-router after 30 seconds"
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
                    validator.os,
                    "rmdir",
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
                    validator.os,
                    "rmdir",
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


    def test_main_labels_staged_profile_validation_as_host_ci_only(self):
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
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                validator.main()

            output = stdout.getvalue()

        self.assertIn("HOST-CI STAGED ROOTFS ONLY", output)
        self.assertIn("NOT HARDWARE ACCEPTANCE", output)
        self.assertNotIn("Hardware Appliance Profiles", output)
        self.assertNotIn(
            "ALL HARDWARE APPLIANCE PROFILES VALIDATED SUCCESSFULLY",
            output,
        )


    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_diagnostic_timeout_terminates_background_processes(self):
        with tempfile.TemporaryDirectory() as root:
            marker = os.path.join(root, "diagnostic-child-survived")
            script = os.path.join(root, "diagnostic.sh")
            with open(script, "w", encoding="utf-8") as fp:
                fp.write(
                    "#!/bin/sh\n"
                    "(sleep 1; printf 'survived' > \"$BLAZE_DIAG_TEST_MARKER\") &\n"
                    "sleep 10\n"
                )

            env = os.environ.copy()
            env["BLAZE_DIAG_TEST_MARKER"] = marker
            with (
                mock.patch.object(validator, "DIAG_SCRIPT", script),
                mock.patch.object(validator, "DIAGNOSTICS_TIMEOUT_SECONDS", 0.1),
            ):
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    validator.run_appliance_diagnostics("test-router", env)

            time.sleep(1.5)
            self.assertFalse(
                os.path.exists(marker),
                "diagnostic timeout left a background child running",
            )

    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_successful_diagnostic_exit_terminates_background_processes(self):
        with tempfile.TemporaryDirectory() as root:
            marker = os.path.join(root, "diagnostic-child-survived")
            script = os.path.join(root, "diagnostic.sh")
            with open(script, "w", encoding="utf-8") as fp:
                fp.write(
                    "#!/bin/sh\n"
                    "(sleep 1; printf 'survived' > \"$BLAZE_DIAG_TEST_MARKER\") &\n"
                    "exit 0\n"
                )

            env = os.environ.copy()
            env["BLAZE_DIAG_TEST_MARKER"] = marker
            with mock.patch.object(validator, "DIAG_SCRIPT", script):
                result = validator.run_appliance_diagnostics("test-router", env)

            self.assertEqual(result.returncode, 0)
            time.sleep(1.5)
            self.assertFalse(
                os.path.exists(marker),
                "successful diagnostic exit left a background child running",
            )


    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_wait_error_still_terminates_background_processes(self):
        with tempfile.TemporaryDirectory() as root:
            marker = os.path.join(root, "diagnostic-child-survived")
            script = os.path.join(root, "diagnostic.sh")
            with open(script, "w", encoding="utf-8") as fp:
                fp.write(
                    "#!/bin/sh\\n"
                    "(sleep 1; printf 'survived' > \\"$BLAZE_DIAG_TEST_MARKER\\") &\\n"
                    "sleep 10\\n"
                )

            env = os.environ.copy()
            env["BLAZE_DIAG_TEST_MARKER"] = marker
            real_popen = validator.subprocess.Popen

            def popen_with_one_wait_error(*args, **kwargs):
                process = real_popen(*args, **kwargs)
                original_wait = process.wait
                first_wait = True

                def fail_first_wait(*wait_args, **wait_kwargs):
                    nonlocal first_wait
                    if first_wait:
                        first_wait = False
                        raise OSError("injected diagnostic wait failure")
                    return original_wait(*wait_args, **wait_kwargs)

                process.wait = fail_first_wait
                return process

            with (
                mock.patch.object(validator, "DIAG_SCRIPT", script),
                mock.patch.object(
                    validator.subprocess,
                    "Popen",
                    side_effect=popen_with_one_wait_error,
                ),
            ):
                with self.assertRaisesRegex(
                    OSError, "injected diagnostic wait failure"
                ):
                    validator.run_appliance_diagnostics("test-router", env)

            time.sleep(1.5)
            self.assertFalse(
                os.path.exists(marker),
                "wait error left a background diagnostic child running",
            )

    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_wait_error_remains_primary_when_process_group_cleanup_raises(self):
        process = mock.Mock()
        process.pid = 12345
        process.wait.side_effect = OSError("primary diagnostic wait failure")

        with (
            mock.patch.object(
                validator.subprocess, "Popen", return_value=process
            ),
            mock.patch.object(
                validator,
                "_terminate_process_groups",
                side_effect=PermissionError("injected cleanup failure"),
            ) as terminate,
        ):
            with self.assertRaisesRegex(
                OSError, "primary diagnostic wait failure"
            ) as raised:
                validator.run_appliance_diagnostics("test-router", {})

        terminate.assert_called_once_with(process)
        notes = getattr(raised.exception, "__notes__", [])
        if hasattr(raised.exception, "add_note"):
            self.assertTrue(
                any("injected cleanup failure" in note for note in notes)
            )


if __name__ == "__main__":
    unittest.main()
