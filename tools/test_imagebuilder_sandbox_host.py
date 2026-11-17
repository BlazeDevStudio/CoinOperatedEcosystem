#!/usr/bin/env python3
"""Synthetic tests for the release-owned ImageBuilder host preflight."""
import importlib.util
import os
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
HELPER_PATH = os.path.join(TOOLS_DIR, "check_imagebuilder_sandbox_host.py")
WORKFLOW_PATH = os.path.join(
    REPO_ROOT, ".github", "workflows", "release-imagebuilder-sandbox.yml"
)


def load_helper():
    spec = importlib.util.spec_from_file_location(
        "check_imagebuilder_sandbox_host", HELPER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load release sandbox host preflight helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestImageBuilderSandboxHostPreflight(unittest.TestCase):
    def helper_or_skip(self):
        if not os.path.isfile(HELPER_PATH):
            self.skipTest("helper implementation is introduced by the source commit")
        return load_helper()

    def make_fake_bwrap(self, directory, script):
        path = os.path.join(directory, "bwrap")
        with open(path, "w", encoding="utf-8") as fp:
            fp.write("#!/bin/sh\n")
            fp.write(script)
        os.chmod(path, 0o755)
        return path

    def test_preflight_helper_exists(self):
        self.assertTrue(
            os.path.isfile(HELPER_PATH),
            "release sandbox workflow requires a dedicated host capability preflight",
        )

    def test_workflow_preflights_before_mandatory_packaging_regressions(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as fp:
            workflow = fp.read()
        preflight_position = workflow.find(
            "Preflight unprivileged bubblewrap namespace"
        )
        regressions_position = workflow.find(
            "Run packaging regressions with mandatory bubblewrap"
        )
        self.assertGreater(
            preflight_position,
            -1,
            "sandbox workflow must explicitly preflight the required user namespace",
        )
        self.assertGreater(
            regressions_position,
            preflight_position,
            "host preflight must run before the sandbox-dependent regression suite",
        )
        self.assertIn(
            "python3 tools/check_imagebuilder_sandbox_host.py",
            workflow[preflight_position:regressions_position],
        )

    def test_probe_command_uses_approved_single_id_namespace_without_fallback(self):
        helper = self.helper_or_skip()
        command = helper.build_probe_command("/usr/bin/bwrap")
        for token in (
            "--unshare-all",
            "--share-net",
            "--unshare-user",
            "--ro-bind",
            "/",
            "--tmpfs",
            "/tmp",
            "--uid",
            "0",
            "--gid",
            "0",
        ):
            self.assertIn(token, command)
        lowered = " ".join(command).lower()
        self.assertNotIn("sudo", lowered)
        self.assertNotIn("newuidmap", lowered)
        self.assertNotIn("newgidmap", lowered)

    def test_probe_accepts_a_supported_fake_host(self):
        helper = self.helper_or_skip()
        with tempfile.TemporaryDirectory() as directory:
            fake = self.make_fake_bwrap(directory, "exit 0\n")
            ready, detail = helper.check_host(fake, timeout_seconds=1)
        self.assertTrue(ready, detail)
        self.assertIn("namespace", detail.lower())

    def test_probe_reports_uid_map_denial_as_blocked(self):
        helper = self.helper_or_skip()
        with tempfile.TemporaryDirectory() as directory:
            fake = self.make_fake_bwrap(
                directory,
                "echo 'bwrap: setting up uid map: Permission denied' >&2\nexit 1\n",
            )
            ready, detail = helper.check_host(fake, timeout_seconds=1)
        self.assertFalse(ready)
        self.assertIn("uid map", detail.lower())
        self.assertIn("permission denied", detail.lower())

    def test_probe_times_out_without_falling_back(self):
        helper = self.helper_or_skip()
        with tempfile.TemporaryDirectory() as directory:
            fake = self.make_fake_bwrap(directory, "exec sleep 2\n")
            ready, detail = helper.check_host(fake, timeout_seconds=0.05)
        self.assertFalse(ready)
        self.assertIn("timed out", detail.lower())

    def test_probe_blocks_when_bubblewrap_is_missing(self):
        helper = self.helper_or_skip()
        with mock.patch.object(helper.shutil, "which", return_value=None):
            ready, detail = helper.check_host(timeout_seconds=1)
        self.assertFalse(ready)
        self.assertIn("not found", detail.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
