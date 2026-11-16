#!/usr/bin/env python3
"""Automated tests for Appliance Firmware Packager and ImageBuilder Configurator."""
import json
import os
import shlex
import shutil
import subprocess
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

    def _run_mock_imagebuilder(self, image_subpath=None, mkdir_subtarget=False,
                               preexisting_image=False, preexisting_manifest=False,
                               manifest_symlink=False, temp_manifest_symlink=False):
        """Execute a generated wrapper against a disposable local Makefile."""
        profile = load_profile("gl-mt1300")
        stage_absolute = os.path.join(self.temp_dir, "staging with spaces")
        stage_relative = os.path.relpath(stage_absolute, os.getcwd())
        manifest = stage_overlay(profile, DEFAULT_ROOTFS, stage_relative)
        wrapper = os.path.join(self.temp_dir, "nonshipping-build.sh")
        generate_build_script(manifest, wrapper)

        fake_builder = os.path.join(self.temp_dir, "fake-imagebuilder")
        os.makedirs(fake_builder, exist_ok=True)
        recipe = 'image:\n\t@test -d "$(FILES)"\n'
        if mkdir_subtarget:
            recipe += '\t@mkdir -p bin/targets/ramips/mt7621\n'
        if image_subpath is not None:
            # Fixture paths are hardcoded by these tests, never user input.
            recipe += '\t@mkdir -p "$(dir ' + image_subpath + ')"\n'
            recipe += '\t@printf "SYNTHETIC-NOT-FIRMWARE" > ' + image_subpath + '\n'
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
        result = subprocess.run(
            ["sh", wrapper], cwd=self.temp_dir, env=env,
            capture_output=True, text=True, check=False
        )
        return result, fake_builder, wrapper, stage_absolute

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
        result = subprocess.run(["sh", wrapper], cwd=self.temp_dir, env=env,
                                capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE-BLOCKED: empty firmware image", result.stderr)
        self.assertFalse(os.path.exists(os.path.join(builder, "RELEASE_MANIFEST.sha256")))

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



