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


    def test_probe_rejects_setid_bubblewrap_in_trusted_directory(self):
        helper = self.helper_or_skip()
        with tempfile.TemporaryDirectory() as directory:
            for mode in (0o4755, 0o2755):
                with self.subTest(mode=oct(mode)):
                    path = self.make_fake_bwrap(directory, "exit 0\\n")
                    os.chmod(path, mode)
                    with mock.patch.object(helper.shutil, "which", return_value=path):
                        with mock.patch.object(helper.os.path, "dirname", return_value="/usr/bin"):
                            self.assertIsNone(
                                helper._find_trusted_bwrap(),
                                "setuid/setgid Bubblewrap is not the approved unprivileged userns mode",
                            )
                    os.unlink(path)

    def test_probe_rejects_group_or_world_writable_bubblewrap(self):
        helper = self.helper_or_skip()
        with tempfile.TemporaryDirectory() as directory:
            for mode in (0o775, 0o757):
                with self.subTest(mode=oct(mode)):
                    path = self.make_fake_bwrap(directory, "exit 0\\n")
                    os.chmod(path, mode)
                    with mock.patch.object(helper.shutil, "which", return_value=path):
                        with mock.patch.object(helper.os.path, "dirname", return_value="/usr/bin"):
                            self.assertIsNone(
                                helper._find_trusted_bwrap(),
                                "group/world-writable Bubblewrap must not be trusted",
                            )
                    os.unlink(path)

    def test_probe_accepts_regular_unprivileged_bubblewrap_mode(self):
        helper = self.helper_or_skip()
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_fake_bwrap(directory, "exit 0\\n")
            os.chmod(path, 0o755)
            with mock.patch.object(helper.shutil, "which", return_value=path):
                with mock.patch.object(helper.os.path, "dirname", return_value="/usr/bin"):
                    self.assertEqual(helper._find_trusted_bwrap(), path)

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


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_imagebuilder_sandbox", os.path.join(TOOLS_DIR, "run_imagebuilder_sandbox.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load release ImageBuilder sandbox runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestImageBuilderSandboxProcessCleanup(unittest.TestCase):
    def test_timeout_escalates_and_waits_for_outer_and_child_process_groups(self):
        runner = load_runner()
        process = mock.Mock()
        process.pid = 101
        process.stdout = None
        process.stderr = None
        process.communicate.side_effect = [
            runner.subprocess.TimeoutExpired(
                cmd=["bwrap"], timeout=0.01,
                output="partial stdout", stderr="partial stderr",
            ),
            ("final stdout", "final stderr"),
        ]

        with mock.patch.object(runner.os, "killpg") as killpg, mock.patch.object(
            runner, "_wait_for_process_groups_exit", return_value=[]
        ) as wait_groups:
            stdout, stderr = runner._terminate_process_groups(
                process, child_pgid=202, grace_seconds=0.01
            )

        self.assertEqual(stdout, "final stdout")
        self.assertEqual(stderr, "final stderr")
        self.assertEqual(
            killpg.call_args_list,
            [
                mock.call(101, runner.signal.SIGTERM),
                mock.call(202, runner.signal.SIGTERM),
                mock.call(101, runner.signal.SIGKILL),
                mock.call(202, runner.signal.SIGKILL),
            ],
            "timeout cleanup must escalate both the outer bwrap and --new-session child groups",
        )
        wait_groups.assert_called_once_with([101, 202], 0.01)
        self.assertEqual(process.communicate.call_count, 2)

    def test_successful_leader_exit_still_kills_detached_child_group(self):
        runner = load_runner()
        process = mock.Mock()
        process.pid = 301
        process.stdout = None
        process.stderr = None
        process.communicate.return_value = ("build output", "")

        with mock.patch.object(runner.os, "killpg") as killpg, mock.patch.object(
            runner, "_wait_for_process_groups_exit", return_value=[]
        ) as wait_groups:
            stdout, stderr = runner._terminate_process_groups(
                process, child_pgid=402, grace_seconds=0.01
            )

        self.assertEqual((stdout, stderr), ("build output", ""))
        self.assertEqual(
            killpg.call_args_list,
            [
                mock.call(301, runner.signal.SIGTERM),
                mock.call(402, runner.signal.SIGTERM),
                mock.call(301, runner.signal.SIGKILL),
                mock.call(402, runner.signal.SIGKILL),
            ],
            "a successful wrapper leader must not leave a detached sandbox child running",
        )
        wait_groups.assert_called_once_with([301, 402], 0.01)

    def test_timeout_result_preserves_partial_output_and_cleanup_diagnostics(self):
        runner = load_runner()
        process = mock.Mock()
        process.communicate.side_effect = runner.subprocess.TimeoutExpired(
            cmd=["bwrap"], timeout=1, output="partial build", stderr="partial error"
        )

        with mock.patch.object(
            runner,
            "_terminate_process_groups",
            return_value=("captured build output", "cleanup diagnostic"),
        ):
            (stdout, stderr), timed_out = runner._communicate_with_timeout(
                process, timeout_seconds=1, child_pgid=502
            )

        self.assertTrue(timed_out)
        self.assertEqual(stdout, "captured build output")
        self.assertIn("cleanup diagnostic", stderr)
        self.assertIn("partial error", stderr)

    def test_ordinary_release_blocked_output_is_not_misclassified_as_cleanup_failure(self):
        runner = load_runner()
        process = mock.Mock()
        process.communicate.return_value = (
            "wrapper output",
            "RELEASE-BLOCKED: approved site ULA /48 is not configured",
        )

        with mock.patch.object(
            runner, "_terminate_process_groups", return_value=("", "")
        ):
            (stdout, stderr), cleanup_failed = runner._communicate_with_timeout(
                process, timeout_seconds=1, child_pgid=602
            )

        self.assertFalse(cleanup_failed)
        self.assertEqual(stdout, "wrapper output")
        self.assertIn("approved site ULA /48", stderr)

    def test_unreaped_child_group_cleanup_error_fails_closed_after_successful_leader(self):
        runner = load_runner()
        process = mock.Mock()
        process.communicate.return_value = ("build output", "")

        cleanup_error = (
            "RELEASE-BLOCKED: sandbox process group(s) did not exit after SIGKILL: 702"
        )
        with mock.patch.object(
            runner, "_terminate_process_groups", return_value=("", cleanup_error)
        ):
            (stdout, stderr), cleanup_failed = runner._communicate_with_timeout(
                process, timeout_seconds=1, child_pgid=702
            )

        self.assertTrue(cleanup_failed)
        self.assertEqual(stdout, "build output")
        self.assertIn("did not exit after SIGKILL", stderr)


    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_real_detached_process_groups_are_terminated_and_reaped(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_path = os.path.join(temp_dir, "child.pid")
            ready_path = os.path.join(temp_dir, "child.ready")
            child_code = (
                "import signal, sys, time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "open(sys.argv[1], 'w', encoding='ascii').write('ready'); "
                "time.sleep(60)"
            )
            outer_code = "\n".join(
                [
                    "import os, signal, subprocess, sys, time",
                    "signal.signal(signal.SIGTERM, signal.SIG_IGN)",
                    "pid_path, ready_path, child_code = sys.argv[1:]",
                    "child = subprocess.Popen(",
                    "    [sys.executable, '-c', child_code, ready_path],",
                    "    start_new_session=True,",
                    "    stdout=subprocess.DEVNULL,",
                    "    stderr=subprocess.DEVNULL,",
                    ")",
                    "with open(pid_path, 'w', encoding='ascii') as fp:",
                    "    fp.write(str(child.pid))",
                    "deadline = time.monotonic() + 5",
                    "while not os.path.exists(ready_path) and time.monotonic() < deadline:",
                    "    time.sleep(0.01)",
                    "if not os.path.exists(ready_path):",
                    "    raise SystemExit(3)",
                    "print(child.pid, flush=True)",
                    "time.sleep(60)",
                ]
            )
            process = runner.subprocess.Popen(
                [
                    runner.sys.executable,
                    "-c",
                    outer_code,
                    pid_path,
                    ready_path,
                    child_code,
                ],
                start_new_session=True,
                stdout=runner.subprocess.PIPE,
                stderr=runner.subprocess.PIPE,
                text=True,
            )
            child_pgid = None
            cleanup_attempted = False
            try:
                ready, _, _ = runner.select.select([process.stdout], [], [], 5)
                self.assertTrue(
                    ready,
                    "outer process did not publish the detached child process-group ID",
                )
                line = process.stdout.readline()
                self.assertTrue(line.strip(), "detached child process-group ID was empty")
                child_pgid = int(line.strip())
                self.assertGreater(child_pgid, 0)

                _, stderr = runner._terminate_process_groups(
                    process, child_pgid=child_pgid, grace_seconds=2.0
                )
                self.assertEqual(stderr, "")
                self.assertEqual(process.returncode, -runner.signal.SIGKILL)
                with self.assertRaises(ProcessLookupError):
                    os.killpg(child_pgid, 0)
                with self.assertRaises(ProcessLookupError):
                    os.killpg(process.pid, 0)
                cleanup_attempted = True
            finally:
                if child_pgid is None and os.path.exists(pid_path):
                    with open(pid_path, "r", encoding="ascii") as fp:
                        child_pgid = int(fp.read())
                if not cleanup_attempted:
                    runner._terminate_process_groups(
                        process, child_pgid=child_pgid, grace_seconds=2.0
                    )


    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_real_successful_leader_exit_terminates_detached_child_group(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_path = os.path.join(temp_dir, "child.pid")
            ready_path = os.path.join(temp_dir, "child.ready")
            child_code = (
                "import signal, sys, time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "open(sys.argv[1], 'w', encoding='ascii').write('ready'); "
                "time.sleep(60)"
            )
            outer_code = "\n".join(
                [
                    "import os, subprocess, sys, time",
                    "pid_path, ready_path, child_code = sys.argv[1:]",
                    "child = subprocess.Popen(",
                    "    [sys.executable, '-c', child_code, ready_path],",
                    "    start_new_session=True,",
                    "    stdout=subprocess.DEVNULL,",
                    "    stderr=subprocess.DEVNULL,",
                    ")",
                    "with open(pid_path, 'w', encoding='ascii') as fp:",
                    "    fp.write(str(child.pid))",
                    "print(child.pid, flush=True)",
                    "deadline = time.monotonic() + 5",
                    "while not os.path.exists(ready_path) and time.monotonic() < deadline:",
                    "    time.sleep(0.01)",
                    "if not os.path.exists(ready_path):",
                    "    raise SystemExit(3)",
                    "print('outer-exit', flush=True)",
                ]
            )
            process = runner.subprocess.Popen(
                [
                    runner.sys.executable,
                    "-c",
                    outer_code,
                    pid_path,
                    ready_path,
                    child_code,
                ],
                start_new_session=True,
                stdout=runner.subprocess.PIPE,
                stderr=runner.subprocess.PIPE,
                text=True,
            )
            child_pgid = None
            cleanup_attempted = False
            try:
                ready, _, _ = runner.select.select([process.stdout], [], [], 5)
                self.assertTrue(
                    ready,
                    "outer process did not publish the detached child process-group ID",
                )
                line = process.stdout.readline()
                self.assertTrue(line.strip(), "detached child process-group ID was empty")
                child_pgid = int(line.strip())
                self.assertGreater(child_pgid, 0)

                deadline = runner.time.monotonic() + 5
                while not os.path.exists(ready_path) and runner.time.monotonic() < deadline:
                    runner.time.sleep(0.01)
                self.assertTrue(
                    os.path.exists(ready_path),
                    "detached child did not install its SIGTERM-ignore handler",
                )
                self.assertEqual(runner.os.getpgid(child_pgid), child_pgid)

                (stdout, stderr), cleanup_failed = runner._communicate_with_timeout(
                    process, timeout_seconds=5, child_pgid=child_pgid
                )
                self.assertFalse(cleanup_failed)
                self.assertEqual(process.returncode, 0)
                self.assertEqual(stdout.strip(), "outer-exit")
                self.assertEqual(stderr, "")
                with self.assertRaises(ProcessLookupError):
                    runner.os.killpg(child_pgid, 0)
                cleanup_attempted = True
            finally:
                if not cleanup_attempted:
                    if child_pgid is None and os.path.exists(pid_path):
                        with open(pid_path, "r", encoding="ascii") as fp:
                            child_pgid = int(fp.read())
                    runner._terminate_process_groups(
                        process, child_pgid=child_pgid, grace_seconds=2.0
                    )



    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_real_timeout_escalates_and_reaps_outer_and_detached_child_groups(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_path = os.path.join(temp_dir, "child.pid")
            ready_path = os.path.join(temp_dir, "child.ready")
            output_path = os.path.join(temp_dir, "output.ready")
            child_code = (
                "import signal, sys, time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "open(sys.argv[1], 'w', encoding='ascii').write('ready'); "
                "time.sleep(60)"
            )
            outer_code = "\n".join(
                [
                    "import os, signal, subprocess, sys, time",
                    "signal.signal(signal.SIGTERM, signal.SIG_IGN)",
                    "pid_path, ready_path, output_path, child_code = sys.argv[1:]",
                    "child = subprocess.Popen(",
                    "    [sys.executable, '-c', child_code, ready_path],",
                    "    start_new_session=True,",
                    "    stdout=subprocess.DEVNULL,",
                    "    stderr=subprocess.DEVNULL,",
                    ")",
                    "with open(pid_path, 'w', encoding='ascii') as fp:",
                    "    fp.write(str(child.pid))",
                    "deadline = time.monotonic() + 5",
                    "while not os.path.exists(ready_path) and time.monotonic() < deadline:",
                    "    time.sleep(0.01)",
                    "if not os.path.exists(ready_path):",
                    "    raise SystemExit(3)",
                    "print('partial-build-output', flush=True)",
                    "with open(output_path, 'w', encoding='ascii') as fp:",
                    "    fp.write('ready')",
                    "time.sleep(60)",
                ]
            )
            process = runner.subprocess.Popen(
                [
                    runner.sys.executable,
                    "-c",
                    outer_code,
                    pid_path,
                    ready_path,
                    output_path,
                    child_code,
                ],
                start_new_session=True,
                stdout=runner.subprocess.PIPE,
                stderr=runner.subprocess.PIPE,
                text=True,
            )
            child_pgid = None
            cleanup_attempted = False
            try:
                deadline = runner.time.monotonic() + 5
                while (
                    not os.path.exists(pid_path)
                    or not os.path.exists(ready_path)
                    or not os.path.exists(output_path)
                ) and runner.time.monotonic() < deadline:
                    runner.time.sleep(0.01)
                self.assertTrue(os.path.exists(pid_path), "outer process did not publish child PGID")
                self.assertTrue(
                    os.path.exists(ready_path),
                    "detached child did not install its SIGTERM-ignore handler",
                )
                self.assertTrue(
                    os.path.exists(output_path),
                    "outer process did not flush partial build output",
                )
                with open(pid_path, "r", encoding="ascii") as fp:
                    child_pgid = int(fp.read())
                self.assertGreater(child_pgid, 0)
                self.assertEqual(runner.os.getpgid(child_pgid), child_pgid)
                self.assertEqual(runner.os.getpgid(process.pid), process.pid)

                (stdout, stderr), timed_out = runner._communicate_with_timeout(
                    process, timeout_seconds=0.25, child_pgid=child_pgid
                )
                self.assertTrue(timed_out)
                self.assertEqual(process.returncode, -runner.signal.SIGKILL)
                self.assertIn("partial-build-output", stdout)
                self.assertEqual(stderr, "")
                for pgid in (process.pid, child_pgid):
                    with self.subTest(process_group=pgid):
                        with self.assertRaises(ProcessLookupError):
                            runner.os.killpg(pgid, 0)
                cleanup_attempted = True
            finally:
                if not cleanup_attempted:
                    if child_pgid is None and os.path.exists(pid_path):
                        with open(pid_path, "r", encoding="ascii") as fp:
                            child_pgid = int(fp.read())
                    runner._terminate_process_groups(
                        process, child_pgid=child_pgid, grace_seconds=2.0
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
