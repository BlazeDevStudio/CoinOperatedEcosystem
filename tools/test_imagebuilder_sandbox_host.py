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
HANDOVER_PATH = os.path.join(TOOLS_DIR, "RELEASE_PACKAGER_HANDOVER.md")


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

    def test_probe_command_hides_host_credential_and_external_mount_paths(self):
        helper = self.helper_or_skip()
        command = helper.build_probe_command("/usr/bin/bwrap")
        tmpfs_paths = {
            command[index + 1]
            for index, token in enumerate(command[:-1])
            if token == "--tmpfs"
        }
        self.assertEqual(
            tmpfs_paths,
            {"/tmp", "/home", "/root", "/run", "/mnt", "/media", "/srv"},
        )

    def test_handover_describes_the_current_unprivileged_user_namespace(self):
        with open(HANDOVER_PATH, "r", encoding="utf-8") as fp:
            handover = fp.read()
        marker = "- Current candidate implementation:"
        self.assertIn(marker, handover, "release handover must retain a current implementation section")
        section = handover.split(marker, 1)[1].split("- Current exact-head Actions:", 1)[0]
        normalized = " ".join(section.split()).replace("**", "")
        self.assertIn(
            "single-ID user namespace",
            normalized,
            "handover must describe the runner's actual single-ID user namespace",
        )
        self.assertIn(
            "does not invoke `sudo`, `newuidmap`, or `newgidmap`",
            normalized,
            "handover must not claim external privileged mapping helpers",
        )
        self.assertNotIn(
            "starts privileged bubblewrap",
            normalized.lower(),
            "handover must not describe the current unprivileged runner as privileged",
        )
        self.assertNotIn(
            "blocks until `newuidmap`/`newgidmap`",
            normalized,
            "handover must not claim mapping helpers are used",
        )
        self.assertIn("`--share-net` is deliberate", normalized)
        self.assertIn("network isolation is not claimed", normalized.lower())


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

    def test_probe_resolves_bubblewrap_from_trusted_system_path_only(self):
        helper = self.helper_or_skip()
        with mock.patch.object(helper.shutil, "which", return_value=None) as which:
            ready, detail = helper.check_host(timeout_seconds=1)
        self.assertFalse(ready)
        self.assertIn("not found", detail.lower())
        which.assert_called_once_with("bwrap", path="/usr/bin:/bin")


    def test_probe_rejects_symlinked_bubblewrap_in_trusted_directory(self):
        helper = self.helper_or_skip()
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "real-bwrap")
            link = os.path.join(directory, "bwrap")
            with open(target, "w", encoding="utf-8") as fp:
                fp.write("#!/bin/sh\\nexit 0\\n")
            os.chmod(target, 0o755)
            os.symlink(target, link)

            with mock.patch.object(helper.shutil, "which", return_value=link):
                with mock.patch.object(helper.os.path, "dirname", return_value="/usr/bin"):
                    self.assertIsNone(
                        helper._find_trusted_bwrap(),
                        "a trusted-directory symlink must not redirect execution outside that directory",
                    )


    def test_probe_blocks_when_bubblewrap_is_missing(self):
        helper = self.helper_or_skip()
        with mock.patch.object(helper.shutil, "which", return_value=None):
            ready, detail = helper.check_host(timeout_seconds=1)
        self.assertFalse(ready)
        self.assertIn("not found", detail.lower())


    def test_workflow_runs_host_unit_tests_before_bwrap_availability_gate(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as fp:
            workflow = fp.read()
        tests_position = workflow.find("Run sandbox host preflight unit tests")
        availability_position = workflow.find("Verify bubblewrap availability (no privileged install)")
        self.assertGreater(tests_position, -1)
        self.assertGreater(availability_position, -1)
        self.assertLess(
            tests_position,
            availability_position,
            "pure host-preflight unit tests must run before the real-host Bubblewrap availability gate",
        )


    def test_workflow_triggers_for_release_child_branch(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as fp:
            workflow = fp.read()
        pull_request_section = workflow.split("  pull_request:", 1)[1].split("  push:", 1)[0]
        push_section = workflow.split("  push:", 1)[1].split("  workflow_dispatch:", 1)[0]
        self.assertIn(
            "      - phoenix/release-imagebuilder-failclosed-20261115",
            pull_request_section,
            "the mandatory sandbox must run when a release child PR targets the packager branch",
        )
        self.assertIn(
            "      - phoenix/release-build-script-publication-safety-20261117",
            push_section,
            "the mandatory sandbox must run on the release child branch after reconciliation",
        )


    def test_workflow_requires_existing_bubblewrap_without_privileged_install(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as fp:
            workflow = fp.read()
        bootstrap_section = workflow.split(
            "      - name: Verify bubblewrap availability (no privileged install)", 1
        )[1].split("      - name: Verify unprivileged single-ID runner identity", 1)[0]
        self.assertIn(
            "command -v bwrap",
            bootstrap_section,
            "sandbox workflow must fail closed when bubblewrap is unavailable",
        )
        self.assertIn("bwrap --version", bootstrap_section)
        self.assertIn(
            "RELEASE-BLOCKED: bubblewrap is not installed on this runner",
            bootstrap_section,
            "missing Bubblewrap must report the boundary block explicitly",
        )
        self.assertIn(
            "exit 125",
            bootstrap_section,
            "missing Bubblewrap must use the standard release-blocked exit code",
        )
        self.assertNotRegex(
            bootstrap_section,
            r"\\bsudo\\s+apt-get\\b",
            "sandbox workflow must not install runtime dependencies with sudo",
        )
        self.assertNotIn(
            "apt-get install",
            bootstrap_section,
            "sandbox workflow must not mutate the hosted runner before the NO-GO preflight",
        )


    def test_workflow_uses_immutable_node24_checkout_action(self):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as fp:
            workflow = fp.read()
        checkout_step = workflow.split(
            "      - name: Checkout exact PR head", 1
        )[1].split("      - name: Install bubblewrap", 1)[0]
        self.assertIn(
            "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            checkout_step,
            "sandbox checkout must use the reviewed immutable Node24 action commit",
        )
        self.assertIn(
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            checkout_step,
            "sandbox must continue checking out the exact triggering PR/push SHA",
        )
        self.assertIn(
            "persist-credentials: false",
            checkout_step,
            "sandbox checkout must not persist the workflow token in Git config",
        )
        self.assertNotRegex(
            checkout_step,
            r"uses:\s*actions/checkout@v",
            "sandbox checkout must not use a mutable version tag",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
