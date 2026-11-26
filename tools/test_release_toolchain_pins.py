#!/usr/bin/env python3
"""Release-owned regression guards for deterministic Phoenix firmware CI toolchains."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "hardware-ci.yml"

EXPECTED_ACTIONS = {
    "actions/checkout": (
        "3d3c42e5aac5ba805825da76410c181273ba90b1",
        3,
    ),
    "arduino/setup-arduino-cli": (
        "b3cda96fddef6af6c56b4c5efb5c47e2357935db",
        2,
    ),
    "actions/upload-artifact": (
        "cf430e030ddbb5b0abf93d22962f4752f3646cd9",
        2,
    ),
}

ARDUINO_CLI_VERSION = "1.6.0"
BOARD_CORES = {
    "ESP8266": ("esp8266:esp8266", "3.1.2"),
    "ESP32": ("esp32:esp32", "3.3.13"),
}


def _release_sandbox_checkout_block(content: str) -> str:
    """Return the checkout step whose credential/ref settings are under review."""
    # Initial whole-workflow implementation is deliberately guarded by the
    # regression below; the corrected implementation must return one step only.
    return content


def _step_blocks(content: str, name: str) -> list[str]:
    marker = f"      - name: {name}\n"
    starts = [match.start() for match in re.finditer(re.escape(marker), content)]
    blocks = []
    for start in starts:
        body_start = start + len(marker)
        next_step = re.search(r"(?m)^      - (?:name|uses):", content[body_start:])
        end = body_start + next_step.start() if next_step else len(content)
        blocks.append(content[body_start:end])
    return blocks


class TestReleaseToolchainPins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_external_actions_use_reviewed_immutable_commits(self):
        for action, (expected_sha, expected_count) in EXPECTED_ACTIONS.items():
            refs = re.findall(
                rf"(?m)^\s*uses:\s*{re.escape(action)}@([^\s#]+)",
                self.workflow,
            )
            self.assertEqual(
                len(refs),
                expected_count,
                f"{action}: expected {expected_count} invocations, found {len(refs)}",
            )
            self.assertEqual(
                refs,
                [expected_sha] * expected_count,
                f"{action}: all invocations must use the reviewed immutable commit",
            )

    def test_arduino_cli_setup_is_version_pinned_and_runtime_checked(self):
        setup_blocks = _step_blocks(self.workflow, "Setup Arduino CLI")
        self.assertEqual(len(setup_blocks), 2)
        for index, block in enumerate(setup_blocks, start=1):
            self.assertIn(
                f"arduino/setup-arduino-cli@{EXPECTED_ACTIONS['arduino/setup-arduino-cli'][0]}",
                block,
                f"Arduino CLI setup {index} must use the reviewed immutable action commit",
            )
            self.assertRegex(
                block,
                r'(?m)^\s*version:\s*"1\.6\.0"\s*$',
                f"Arduino CLI setup {index} must pin version {ARDUINO_CLI_VERSION}",
            )

        for board in BOARD_CORES:
            blocks = _step_blocks(self.workflow, f"Install {board} Core")
            self.assertEqual(len(blocks), 1, f"missing unique {board} install step")
            self.assertIn("arduino-cli version", blocks[0])
            self.assertIn(r"Version: 1\.6\.0", blocks[0])
            self.assertIn(
                "RELEASE-TOOLCHAIN-RED",
                blocks[0],
                f"{board} install step must fail closed on a CLI version mismatch",
            )

    def test_board_core_versions_are_exact_and_runtime_verified(self):
        for board, (package, version) in BOARD_CORES.items():
            blocks = _step_blocks(self.workflow, f"Install {board} Core")
            self.assertEqual(len(blocks), 1, f"missing unique {board} install step")
            block = blocks[0]
            self.assertIn(
                f"arduino-cli core install {package}@{version}",
                block,
                f"{board} core must be installed at exact version {version}",
            )
            self.assertIn("arduino-cli core list", block)
            self.assertIn(version, block)
            self.assertIn(
                "RELEASE-TOOLCHAIN-RED",
                block,
                f"{board} installed core version must be checked before compilation",
            )

    def test_no_floating_board_core_install_commands_remain(self):
        floating = re.findall(
            r"(?m)^\s*arduino-cli core install (?:esp32:esp32|esp8266:esp8266)\s*$",
            self.workflow,
        )
        self.assertEqual(
            floating,
            [],
            "board core installs must include exact versions; floating latest is not reproducible",
        )


    def test_release_sandbox_checkout_guard_does_not_inherit_later_step_settings(self):
        malformed_workflow = (
            "      - name: Checkout exact PR head\\n"
            "        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\\n"
            "      - name: Unrelated later step\\n"
            "        run: echo unrelated\\n"
            "        env:\\n"
            "          persist-credentials: false\\n"
            "          ref: ${{ github.event.pull_request.head.sha || github.sha }}\\n"
        )
        checkout_block = _release_sandbox_checkout_block(malformed_workflow)
        self.assertNotIn("persist-credentials: false", checkout_block)
        self.assertNotIn(
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            checkout_block,
        )

    def test_release_imagebuilder_sandbox_uses_immutable_checkout_and_read_only_credentials(self):
        workflow = (
            ROOT / ".github" / "workflows" / "release-imagebuilder-sandbox.yml"
        ).read_text(encoding="utf-8")
        action_refs = re.findall(
            r"(?m)^\s*uses:\s*([^@\s#]+)@([^\s#]+)",
            workflow,
        )
        self.assertEqual(
            action_refs,
            [
                (
                    "actions/checkout",
                    EXPECTED_ACTIONS["actions/checkout"][0],
                )
            ],
            "the release sandbox must use only the reviewed immutable checkout action",
        )
        self.assertIn(
            "persist-credentials: false",
            workflow,
            "the release sandbox checkout must not retain a write-capable Git credential",
        )
        self.assertIn(
            "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
            workflow,
            "the release sandbox must validate the exact PR head or pushed commit",
        )
        self.assertIn(
            "permissions:\n  contents: read",
            workflow,
            "the release sandbox workflow must retain read-only repository permissions",
        )

if __name__ == "__main__":
    unittest.main()
