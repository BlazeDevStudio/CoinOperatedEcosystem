## PHX-RELEASE UTC14 — ImageBuilder execution boundary (CI pending)

- Active draft: PR #31, branch `phoenix/release-imagebuilder-failclosed-20261115`.
- Source/test head at handover preparation: `da93eafde167f6ada9c6c0ea19d1e3e2f285001b`.
- Scope: release-owned test harness, sandbox runner and CI only. No production packager, CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation changed.
- Regression evidence: run [#44098400955](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44098400955) reproduced a Makefile-created symlink write to an external sentinel (the sentinel changed to `BUILDER-OVERWRITE`). This is the decisive pre-sandbox RED.
- Earlier sandbox experiments are retained as failed evidence, not successes:
  - [#44098939249](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44098939249): UID probe could not bind the runner temp path; tests skipped.
  - [#44102142646](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44102142646): UID probe write denied.
  - [#44102797110](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44102797110) and [#44102941785](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44102941785): namespace identity reported `1001:1001`, but host-created file owner was `0:0`; caller ownership was not preserved.
  - [#44103570308](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44103570308): unprivileged bwrap failed loopback setup (`RTM_NEWADDR`).
  - [#44103764407](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44103764407): unprivileged bwrap failed mount propagation (`Failed to make / slave: Permission denied`).
- Current candidate implementation:
  - `tools/run_imagebuilder_sandbox.py` starts privileged bubblewrap, blocks until `newuidmap`/`newgidmap` map namespace UID/GID 0 to the invoking runner identity, then verifies the host owner of a probe file.
  - Root filesystem is read-only; only the disposable ImageBuilder directory is writable; `/tmp` is tmpfs; the child environment is cleared and rebuilt without runner credentials.
  - `--share-net` is deliberate because this hosted runner cannot configure loopback. **Network isolation is not claimed**; MASTER/QA must review this boundary.
  - The test harness routes all eight generated-wrapper executions through this helper when `PHX_REQUIRE_BWRAP=1`.
- Current exact-head Actions: [sandbox run #44104503489](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104503489) is **PENDING with no jobs returned**. No sandbox pass or ownership-preservation result is claimed. Case-collision [#44104503379](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104503379) passed; shared-contract/build run [#44104503348](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104503348) was still in progress at handover.
- Next: inspect exact-head sandbox CI; require both unchanged external sentinel and host owner == invoking UID/GID. If the privileged mapping fails, stop and ask MASTER to approve an alternative runner/container boundary. Obtain independent PHX-QA review before considering the helper accepted.
- Separate MASTER blocker: package configuration still carries the invalid placeholder ULA `fd00:db8:blaze::/48`; do not invent a replacement. MASTER/CORE must define the durable site-specific ULA interface before release changes it.
- Private Drive project registry v11 was not available through the connected Library surface during this activation. No older registry snapshot was substituted.


# PHX-RELEASE — ImageBuilder wrapper safety and operator handover

**Checkpoint:** 2026-11-17 UTC08. **Status:** DRAFT / SOURCE-TEST CI VERIFIED / PRODUCTION NO-GO.
**Current exact PR head:** `8cca7ff8e35c7b90fb3b88345a8ea65f92bc81b5`.  
**Repository:** `BlazeDevStudio/CoinOperatedEcosystem`.  
**Base:** integration candidate PR #26, source HEAD `b382d233ff06c8791b1028bed3c617cc7b670d12`.  
**Branch:** `phoenix/release-imagebuilder-failclosed-20261115`.

## Canonical ownership

Only `tools/package_appliance_firmware.py`, its `tools/test_package_appliance_firmware.py` regressions, and this release-specific handover are modified. No OpenWrt networking, accounting, Android, Windows, ESP firmware or financial schema is changed. MASTER controls actual integration order; QA must independently examine source.

## Verified source defect and bounded correction

Before this patch, generated ImageBuilder wrappers accepted an absent target image directory or a directory with zero firmware outputs, printing a misleading "completed successfully" message. They searched only the top architecture directory rather than exact target/subtarget, potentially including unrelated images. Their command could pass a relative `FILES` path, then change into ImageBuilder, resolving that overlay from the wrong working directory.

The proposed nonshipping wrapper requires an existing staged rootfs, an ImageBuilder Makefile, the expected exact `bin/targets/<target>/<subtarget>` directory, and at least one real `.bin` or `.img.gz` file. It generates a sorted SHA256 manifest only after these checks. Shell argument generation uses `shlex.quote` and an absolute staging path. The generated script prints **PREVIEW**; it is not a signed, flashable, or hardware-certified release.

**Source commit:** `45d960ab68fb47ac482db27ea4047c2d67f04531`.  
**Test commit:** `35098bbd912498ffcc6459b17064bf59d6684993`.

## Tests and rollback

New disposable GNU Make fixtures cover missing target directory, empty expected directory, images in the wrong subtarget, and a successful synthetic image using a relative staging path containing spaces. Every image from these fixtures is labeled `SYNTHETIC-NOT-FIRMWARE` and must never be shipped.

**Actual test execution:** NOT YET VERIFIED on this checkpoint; no real ImageBuilder toolchain, real OpenWrt binaries, signed release or hardware acceptance claimed. Existing native compile and physical/financial P0 release gates remain unchanged.

**Rollback:** do not merge the stacked draft, or revert only the bounded release-packager commits. Never use a generated SHA256 manifest as a substitute for signed source provenance, trusted build logs, exact target identification, recovery image testing or power-cut acceptance.

**NEXT EXACT ACTION:** create stacked draft PR against PR #26, run exact-head Python tool tests and all profile staging checks, inspect failed jobs, repair only measured REDs, request QA+MASTER review before any merge or release.

## Verified CI checkpoint — 2026-11-15

The first exact-head [GitHub Actions run #43635417891](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43635417891) checked out literal code-and-handover HEAD `b602486934cccc72a7b6bc2e19617b479162f3ff` and completed **SUCCESS**. The `validate` job proves **29/29 tools test cases PASS** (including all four new synthetic wrapper cases), **18/18 Shared contract tests PASS**, and **10/10 standalone + Rental staging profiles PASS**. The ESP8266 and ESP32 Arduino CLI compile jobs also completed **SUCCESS**, uploaded separate **nonproduction** artifacts:

- ESP8266 GitHub artifact ID `14129323398`, provider-reported outer ZIP SHA256 `4b45456a067d330c265e5bdf84aa71c2163aded18a40aca8df73ca18ee69a1cd`, 2,208,745 bytes.
- ESP32 GitHub artifact ID `14129283315`, provider-reported outer ZIP SHA256 `e12465d1aa79c7d83674d80e22ec093bfb7a9f2464aae9bf22f7ea269cffd230`, 7,418,618 bytes.

[Case-collision run #43635417892](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43635417892) **SUCCESS**. These are CI-provider artifact archive digests, **not independently downloaded firmware-byte or signer verification**. No physical router flash, actual ImageBuilder produced appliance image, customer cash, power cuts, 24-hour soak or hardware acceptance occurred. Source scripts and tested Python tests remain unchanged after the exact code-head run; this checkpoint is documentation only.

**New follow-up blocker routed to MASTER/CORE/HARDWARE:** `generate_network_uci` presently emits invalid ULA prefix `fd00:db8:blaze::/48` (non-hexadecimal IPv6 segment). This release PR deliberately does not change networking or VLAN ownership. Exact target OpenWrt bridge/DSA behavior and a valid prefix require independent correction and on-device verification before a release gate. Production remains **NO-GO**.

**NEXT EXACT ACTION:** independent PHX-QA + PHX-MASTER review of this PR's manifest admission, path quoting, synthetic acceptance limits, and staged hardware migration. Require a real version-pinned OpenWrt ImageBuilder build, exact target/flash-size verification, signed provenance, rollback package, and real noncustomer hardware acceptance before production.

## 2026-11-15 — PHX-RELEASE P1 stale-image/release-manifest fail-closed regression

**Owner/scope:** existing stacked DRAFT [PR #31](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/31) based on COE integration DRAFT #26. Owned source: `tools/package_appliance_firmware.py`, owned regression `tools/test_package_appliance_firmware.py`, this operator handover. No network UCI, controller/coin logic, Android/Windows or firmware code changed. No history deletion or forced merge.

**Observed source defect:** after `make image` succeeded, the generated script required only the existence of a matching image in the correct `bin/targets/<target>/<subtarget>`. A no-op build could therefore admit a prior run's `.bin`/`.img.gz`, creating a false fresh SHA256 release manifest. An existing `RELEASE_MANIFEST.sha256` was overwritten, even when linked to an outside file.

**Failing regression FIRST:** test-only commit `5de1cffe4d8f87a56ad6145361d39f20c10d2440`, [source-exact CI #43653119642](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653119642), validation job `132625717207` **RED**: 3 new cases failed with reported `FAILED (failures=3)`: `test_generated_wrapper_denies_stale_image_from_prior_build`, `test_generated_wrapper_denies_previous_manifest_without_clobber`, `test_generated_wrapper_denies_symlinked_manifest`. Existing 29 tests passed. ESP compiler jobs skipped after validation failure. These are disposable synthetic fixtures, not real device tests.

**Bounded source fix:** commit `cf8e49bdba8b2fe4d6f7a0619376063663a3bfd3`. Before `cd` and `make image`, the generated wrapper rejects a pre-existing release manifest with `-e` or `-L`, and rejects any pre-existing `.bin` or `.img.gz` under the **exact target/subtarget**, using a GNU/find-compatible first-match check. It preserves old data and tells the operator to supply a **clean ImageBuilder workspace** rather than silently delete or certify stale artifacts. Then existing post-build target presence, nonempty SHA256 and PREVIEW-only controls remain. Reusing a previously built ImageBuilder with existing images is intentionally refused: use a fresh workspace, preserving its old outputs separately.

**Green source-exact evidence:** [CI #43653187995](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653187995) at source SHA `cf8e49bdba8b2fe4d6f7a0619376063663a3bfd3`: validation job `132625925078` **SUCCESS**, 32/32 Python tool tests, including all 3 formerly RED cases now `ok`, 18/18 Shared tests, and 10/10 profile staging/diagnostics. [Case collision #43653187992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653187992) **SUCCESS**. ESP32 and ESP8266 **compile jobs still IN PROGRESS when this checkpoint was authored**; their result must be separately inspected, not assumed.

**Limitations:** no fresh real version-pinned ImageBuilder image was created by this synthetic test; sha256 is integrity metadata only, not a signature/provenance certificate. Fail-closed cleanliness does not independently prove image target correctness, firmware content, rollback/recovery, flash budget, financial durability, protected antirollback witness, 150 actual power cuts or 30-device/24-hour soak. Other network-owner routing defects including invalid ULA remain independently assigned. All release gates **NO-GO**.

**Rollback:** leave PR DRAFT/unmerged, or revert only the bounded test/source commits; never remove operator files automatically. **NEXT EXACT ACTION:** wait for full exact-SHA ESP32/8266 status, request independent MASTER/QA review of the preflight and the no-op stale-image denial, prove on genuine clean ImageBuilder and noncustomer hardware after separate authorization.

## PHX-RELEASE — 2026-11-16 UTC12 temporary checksum manifest guard

**DRAFT / PRODUCTION NO-GO.** Release-owned, reversible correction on PR #31 only. The generated ImageBuilder wrapper previously rejected an existing final `RELEASE_MANIFEST.sha256` but did not reject a preexisting `RELEASE_MANIFEST.sha256.tmp`. A successful build redirected `sha256sum` into that path, which could follow an operator-supplied symlink and overwrite an unrelated file. The wrapper now rejects existing files and dangling symlinks at the temporary manifest path **before** running make; it does not remove or overwrite them.

- Source fix: `262d72441532f6bb578dec19cf2ab9b25b087d64`.
- Negative fixture/test: `ec5a84e029f39f6d77a207f5abd69b589e019df4`; newline fixture correction `c28fac2543a0e185b1b8fe71b2cf4bfb5a02097d`.
- Test assertion: a symlinked temporary manifest must cause nonzero exit, preserve the external sentinel, preserve the symlink, and prevent the synthetic make image from being created.
- **Verification state at writing:** exact-head GitHub Actions run not yet returned by commit-run lookup; no passing test or hardware evidence is claimed. Existing historical CI results apply only to their recorded older SHAs.
- Rollback: revert these three narrowly scoped commits on the draft branch; no other role source was touched.
- Next: run/check exact-head packaging tests in GitHub Actions, inspect failures, request independent PHX-QA/PHX-MASTER review; do not merge or publish.

## PHX-RELEASE — 2026-11-16 UTC16 exact-head CI follow-up

- Draft branch source HEAD `8b0c70bb93e2b3f8eb75a45586a7b2e1a98d0398` has now completed [hardware/shared CI #43868484843](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43868484843) **SUCCESS**. Jobs: validation `133303086076` SUCCESS, ESP32 compile `133303165779` SUCCESS, ESP8266 compile `133303165826` SUCCESS. [Case-collision #43868484764](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43868484764) SUCCESS. This closes the previous *CI-not-yet-observed* evidence gap for the temporary-manifest guard at the tested SHA; it does not prove actual hardware, signing, or production acceptance.
- Review of generated wrapper and negative fixture confirms temporary-manifest symlink denial is represented in source. No new independent defect was established in this follow-up; no duplicate source fix was introduced.
- Independent PHX-QA/MASTER review, genuine clean version-pinned ImageBuilder output and authorized physical acceptance remain outstanding. No merge, publication, signing or device flashing. PRODUCTION NO-GO.

## PHX-RELEASE — 2026-11-16 UTC18 zero-byte output admission guard

**DRAFT / PRODUCTION NO-GO.** Release-only scope on COE draft PR #31. Existing wrapper previously treated a zero-byte `.bin` or `.img.gz` as a valid firmware output and emitted a SHA256 manifest. A SHA256 digest does not establish that an image has a payload. A new disposable synthetic Makefile fixture writes an empty `empty.bin` and asserts fail-closed refusal with no release manifest.

- Negative regression commits: `aa6cc55615452d02d7826c5896443447c9008033`, fixture escaping correction `ee93879602501d4a5022be857b435531da15ba38`.
- Release-owned source correction: `8a1ec3abbd1513333f53dbfb0aa0951f64b03425`. Generated shell wrapper rejects zero-length candidate image files before checksum generation; no operator files are deleted.
- **Verification at checkpoint:** exact-head GitHub Actions result not yet observed; do not claim a passing regression, real OpenWrt ImageBuilder output, signer, hardware, or production readiness. The new test and guard need exact-source CI and independent QA review.
- **Rollback:** revert the bounded regression and guard commits in the draft branch; do not merge or publish. MASTER owns integration order and cross-repo migration.

## PHX-RELEASE — 2026-11-16 UTC19 exact-source RED and fixture repair

- Source-exact PR merge checkout `be215b8815f83722dd02768d57ef7d03a7e1a400` included release branch `b64a54ae591d1f083faf31591c9da967b5d5c8e2`. [Hardware/shared CI #43927043796](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43927043796) **FAILED**: validation job `133509149092` failed at Python test-module import (line 280 `SyntaxError: unexpected character after line continuation character`); ESP32 and ESP8266 jobs **SKIPPED**, not passed. Hardware hardening and 18 shared tests passed before the packaging test import failure. [Case-collision #43927043852](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43927043852) **SUCCESS**.
- Bounded test-fixture-only correction: first commit `f1058d01be8cf9e60dee4f012063a7e753ceceed` incorrectly emitted literal line breaks inside a Python string (not a passing fix); follow-up `2a37a15d681e03d564e58216adec0480923775a2` corrected the fixture to valid quoted Python string concatenation with escaped Makefile newline/tab characters. Both are retained in history. The release guard source was not changed.
- **Verification:** exact-head GitHub Actions for the corrected fixture are pending; no passing result is asserted for this HEAD. PHX-QA must independently inspect and execute the negative regression, and PHX-MASTER must approve integration sequencing. Rollback: revert the two fixture-only repair commits if necessary. No signing, merge, publication, device flash, or production admission.

## PHX-RELEASE — 2026-11-16 UTC20 corrected fixture exact-source CI

- Corrected release draft source `d35edcfeff8ff00fb504b7c959ac5441ba66823a` now has [hardware/shared CI #43936224724](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43936224724) **COMPLETED SUCCESS**: validation job `133541555191` SUCCESS, ESP8266 compile `133541627828` SUCCESS, ESP32 compile `133541627932` SUCCESS. [Case-collision #43936224656](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43936224656) **COMPLETED SUCCESS**. These runs supersede the prior *not-yet-CI-verified* status for the corrected fixture at that exact commit, but do not erase historical RED or the malformed intermediate fix.
- This is synthetic/CI verification only, not an independent PHX-QA approval, actual approved OpenWrt ImageBuilder firmware, real signer-positive test, hardware acceptance, or production admission. MASTER owns integration sequencing; PHX-QA owns independent negative-path review. No merge, signing, publishing, hardware flash or customer migration. **PRODUCTION NO-GO**.


## PHX-RELEASE — 2026-11-16 UTC22 relative ImageBuilder workspace path

**DRAFT / source CI VERIFIED at `42d524c1fdc3b523724242b2d5ec67d8e38336e7` / PRODUCTION NO-GO.**

- **Reproduced defect:** the generated wrapper retained a relative `OPENWRT_IMAGEBUILDER_DIR` in `BUILD_DIR`, then derived `BIN_DIR`, `OUT_MANIFEST` and `TMP_MANIFEST` before `cd "$BUILD_DIR"`. After changing directory, those relative paths resolved under the builder a second time. A valid target/subtarget output was therefore rejected as missing (fail-closed false-negative).
- **Regression:** `test_generated_wrapper_relative_imagebuilder_dir_uses_absolute_path` runs a disposable local Makefile with a synthetic `SYNTHETIC-NOT-FIRMWARE` output and a relative workspace override. It verifies the output manifest is written in the intended workspace.
- **Test-first history:** `4ccb813e42a7003951c9fdf4f442a363bb50a8bc` first introduced the regression, but its Makefile fixture was over-escaped; [run #43967658042](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43967658042) failed because the fixture did not define a valid Make target. This was a test-authoring failure, not product-defect evidence. Fixture escaping was corrected in `6ed1efd31eda00969d59c786b91ec8ca7d60e7c3`; exact-source [PR run #43967768677](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43967768677) and [push run #43967757000](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43967757000) then failed at the new test with `RELEASE-BLOCKED: target/subtarget image directory missing: relative-imagebuilder/bin/targets/ramips/mt7621`. The separate [case-collision run #43967768673](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43967768673) passed.
- **Scoped source fix:** `42d524c1fdc3b523724242b2d5ec67d8e38336e7` normalizes a relative workspace to `$(pwd -P)/$BUILD_DIR` before any target or manifest path is derived. Absolute workspace overrides remain unchanged. Only `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py` changed in this source-fix stack; no CORE, RENTAL, PISONET, HARDWARE, QA or MASTER files changed.
- **Exact-source Actions:** [PR run #43967851563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43967851563) and [push run #43967843000](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43967843000) both completed SUCCESS: firmware-hardening/shared-contract validation, ESP32 compile and ESP8266 compile all passed. Validation included 18 firmware-hardening tests, 18 shared-contract tests, 35 packaging/tool tests (including the new regression), and 10/10 appliance profile staging checks. [Case-collision run #43967851889](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43967851889) completed SUCCESS.
- **Evidence limits:** the ImageBuilder test uses a synthetic Makefile and a deliberately non-firmware sentinel. ESP32/ESP8266 jobs compile firmware source; they do not create approved OpenWrt ImageBuilder target images. No real ImageBuilder binary, signing, device flash, physical acceptance or production readiness is claimed.
- **Rollback:** revert the test/source commits on this existing draft branch; do not merge or publish. MASTER owns integration sequencing and cross-repository migration.



## PHX-RELEASE — 2026-11-16 UTC23 fresh-output staging guard

**DRAFT / release-source validation PASS; ESP32 compile pending at this checkpoint / PRODUCTION NO-GO.**

- **Reproduced destructive defect:** `stage_overlay()` previously called `shutil.rmtree(staging_dir)` whenever the requested output existed. A mistyped `--output` could therefore erase operator files; specifying the source rootfs itself as output deleted that source tree before `copytree` failed; a new destination nested inside the source rootfs was also accepted.
- **Test-first RED:** commit `bfe9346fb5a6a02a35d90ed8110314751e8ad307` added three disposable-directory regressions: preserve an existing output sentinel, refuse source==output without deleting source, and refuse a nested destination. Exact push [#43977976555](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43977976555) **FAILED as expected** in the packaging suite: two assertion failures and one error demonstrated overwrite, nested-path acceptance, and source-rootfs deletion. Firmware-hardening and shared-contract steps passed; end-to-end profile validation and both board compile jobs were skipped after the packaging failure. Separate case-collision [#43977981689](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43977981689) **SUCCESS**.
- **Scoped source fix:** [`a2fff0ed`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a2fff0ed4ce00251a6062fd2b31654c412ddbd77) resolves source/output paths, requires a real source directory, rejects existing output paths with `lexists` (including symlinks), rejects source/output ancestor/descendant overlap, and never deletes existing output. The caller must now provide a fresh destination directory; this is intentional fail-closed behavior. Test-first commit is [`bfe9346f`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/bfe9346fb5a6a02a35d90ed8110314751e8ad307).
- **Exact-source verification at source HEAD:** [run #43978080862](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43978080862) at `a2fff0ed`: validation **SUCCESS** (firmware-hardening, shared-contract and packaging tests; 38 packaging/tool tests including all three new regressions; 10/10 profile staging checks). ESP8266 compile **SUCCESS**. ESP32 compile was **IN PROGRESS** at this checkpoint and is not credited. No failed job was reclassified as passing.
- **Scope:** only `tools/test_package_appliance_firmware.py` and `tools/package_appliance_firmware.py` changed in the source/test stack; this handover records the release-owned work. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation files changed.
- **Evidence limits:** regression fixtures use temporary directories and a synthetic rootfs. The ImageBuilder wrapper still uses a synthetic Makefile sentinel for its preview test. Board jobs compile firmware source; they do not produce real approved OpenWrt ImageBuilder target images or establish physical hardware acceptance.
- **Rollback:** revert the source/test commits on this existing draft branch. Do not merge, publish, sign, flash, or use real customer money. PHX-QA independent review and PHX-MASTER integration sequencing remain required.


## PHX-RELEASE — 2026-11-17 UTC00 directory-symlink permission guard

**DRAFT / release-source CI verified / PRODUCTION NO-GO.**

- **New test-first regression:** commit [`3ab3f04f`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3ab3f04f29f40c4563f3c1f7363ca753f36ab755) added `test_stage_overlay_does_not_chmod_external_directory_symlink_target`. It creates a disposable rootfs containing a directory symlink to an operator-owned external directory with mode 0700 and verifies staging preserves the link, target mode and target contents.
- **Exact RED:** [Actions #43985581376](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43985581376) **FAILED** in validation job 133712751710: the new test observed mode 0755 after staging instead of the original 0700. The other 38 packaging/tool tests passed; firmware-hardening and shared-contract validation passed; ESP32/ESP8266 compile jobs were skipped after the packaging failure. Separate [case-collision #43985581361](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43985581361) **SUCCESS**.
- **Source correction:** commit [`abd5d15c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/abd5d15c2fc1b00893721e4c53988843b678101d) skips directory symlinks during permission normalization. `os.walk` lists symlinked directories in `dirs` even when it does not recurse into them; `os.chmod` follows those links by default. The guard now calls chmod only for non-symlink directories.
- **Exact source-head CI:** [Actions #43985659576](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43985659576) **COMPLETED SUCCESS**: firmware-hardening/shared-contract validation SUCCESS; packaging/tool suite **39 tests PASS**; ESP32 compile SUCCESS; ESP8266 compile SUCCESS. [Case-collision #43985659547](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43985659547) **SUCCESS**.
- **Scope:** test and source changes are limited to `tools/test_package_appliance_firmware.py` and `tools/package_appliance_firmware.py`; this section is the narrow release handover update. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation files changed.
- **Evidence limits:** the regression uses temporary directories and a synthetic rootfs. Board jobs compile firmware source; they do not create approved OpenWrt ImageBuilder target binaries or establish external-board, filesystem or physical acceptance.
- **Rollback:** revert the test/source commits on this existing draft branch; do not merge or publish. Independent PHX-QA review and PHX-MASTER integration sequencing remain required.


## PHX-RELEASE — 2026-11-17 UTC01 workspace-independent ImageBuilder checksum manifest

**DRAFT / exact-source CI verified / PRODUCTION NO-GO.**

- **Defect reproduced:** the generated wrapper ran `sha256sum` against absolute `$BUILD_DIR/bin/targets/<target>/<subtarget>` paths. Identical synthetic image bytes produced manifest entries containing different absolute workspace prefixes, so the checksum manifest itself was not reproducible across otherwise identical build roots.
- **Test-first history:** commit [`029944ce`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/029944ce081e73d429061e15faf0056c7b6157a1) introduced a two-workspace regression but its Makefile fixture over-escaped newline/tab sequences. [PR run #43994966840](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43994966840) failed at `make` because the fixture did not define a valid recipe; this is a test-authoring failure, not product evidence. The separate case-collision [#43994966877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43994966877) passed.
- **Fixture correction:** [`59fb62c3`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/59fb62c3a55212f992a260521ea87979fa36b75c) corrected the fixture escaping. Exact-source [run #43995132578](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43995132578) then failed only at the new regression: 40 packaging tests ran, with the absolute builder path found in the manifest entry. Validation failed and ESP32/ESP8266 jobs were skipped; no false PASS is recorded.
- **Scoped source fix:** [`f82305e2`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/f82305e2143a7b492dbc418158a21d2444541596) uses a target-relative `IMAGE_REL_DIR` after the wrapper has changed into `$BUILD_DIR`. The pre-build stale-image guard still uses its absolute path; post-build empty-image checks and `sha256sum` now operate on relative target/subtarget paths. Existing deterministic C-locale sorting and temporary-manifest admission remain unchanged.
- **Exact-source PR verification at `f82305e2`:** [Actions #43995365285](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43995365285) **COMPLETED SUCCESS** — validation job 133745958204 PASS, ESP32 job 133746022381 PASS, ESP8266 job 133746022332 PASS. The validation log confirms the new workspace-independence regression PASS, 40/40 packaging/tool tests PASS, and 10/10 appliance profile staging checks PASS; firmware-hardening and shared-contract steps also passed. [Case-collision #43995365275](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43995365275) PASS (job 133745957504).
- **Scope:** test/source changes touch only `tools/test_package_appliance_firmware.py` and `tools/package_appliance_firmware.py`; this section updates this release-owned handover only. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation files or shared interfaces changed.
- **Evidence limits:** the regression uses two disposable workspaces and a synthetic Makefile writing `SYNTHETIC-NOT-FIRMWARE`. It proves manifest path determinism for synthetic bytes only; it does not produce or approve OpenWrt firmware. ESP32/ESP8266 jobs compile firmware source and are not hardware acceptance.
- **Coordination snapshot:** Experiments #242 remains at `734b89d9` with Windows handover/build run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) SUCCESS. #291 remains at `2c4edff2` with [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) handover/build SUCCESS and publisher SKIPPED. COE integration #26 remains at `b382d233`; its five exact-head workflow records remain QUEUED with no jobs returned. MASTER #288 current head `d047c494` retains the release workflow as reimplementation-review, not blind-copy authorization.
- **Registry provenance:** the accessible Library surfaces surfaced a secondary checkpoint naming the canonical private registry v11, but not the canonical Drive file itself. Registry v11 was therefore not independently re-read in this activation; no private identifiers or contents are copied into this repository.
- **Rollback:** revert the source fix, fixture correction and test-first regression commits on this existing draft branch if required. Do not merge or publish. Independent PHX-QA review and PHX-MASTER integration sequencing remain required.



## PHX-RELEASE — 2026-11-17 UTC02 fail-closed generated wrapper destination

**DRAFT / exact-source CI verified / PRODUCTION NO-GO.**

- **Defect:** `generate_build_script()` opened the caller-selected `script_path` with `open(..., "w")`, then chmod'ed it. An existing operator file was truncated, and a final-component symlink was followed, overwriting its external target. This contradicted the packager's existing fail-closed destination policy.
- **Test-first regression:** commit [`e1139084`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e11390840907820992553de0019f020adbf7a7c9) adds two disposable-path tests: an existing regular file must remain byte-identical, and an existing symlink must remain a symlink while its external target remains unchanged.
- **Exact RED:** [Actions #44001740938](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44001740938) **FAILED as expected** in validation job 133767235554. All 40 pre-existing packaging tests passed; both new regressions failed because `FileExistsError` was not raised. Shared-contract validation (18 tests) passed. ESP32 and ESP8266 compile jobs were **SKIPPED** after validation failed. Separate [case-collision #44001740992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44001740992) **SUCCESS**.
- **Source correction:** commit [`2676011c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2676011c2a5590453b587ce8352220c911e21ad1) creates the requested wrapper with `os.open(O_WRONLY | O_CREAT | O_EXCL)`; existing files and final-component symlinks are rejected without truncation or following. The descriptor is chmod'ed with `fchmod` where available, preserving executable mode without a path-following chmod on POSIX.
- **Exact source-head verification:** [Actions #44001859432](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44001859432) **COMPLETED SUCCESS**: validation job 133767636144 PASS (42/42 packaging/tool tests, including both new regressions; 18 shared-contract tests PASS); ESP8266 job 133767688170 PASS; ESP32 job 133767688210 PASS. Separate [case-collision #44001859509](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44001859509) **SUCCESS**.
- **Scope:** only `tools/test_package_appliance_firmware.py` and `tools/package_appliance_firmware.py` changed for the test/source work; this section is the release-owned handover update. No other subsystem or shared interface changed.
- **Evidence limits:** tests use temporary files and symlinks on the CI runner. They prove fail-closed output-path behavior for the generated wrapper, not actual OpenWrt firmware creation, signing, hardware acceptance or production readiness.
- **Operator note:** the requested build-script output path must be new. If it already exists, the operator must inspect and remove/rename it explicitly before retrying; the packager will not overwrite or delete it.
- **Rollback:** revert the source and test commits on this existing draft branch. Do not merge or publish. Independent PHX-QA review and PHX-MASTER integration sequencing remain required.


## PHX-RELEASE — 2026-11-17 UTC03 post-preflight manifest-path substitution guard

**DRAFT / source-head CI verified / PRODUCTION NO-GO.**

- **Reproduced defect:** the generated shell wrapper checked RELEASE_MANIFEST.sha256.tmp and RELEASE_MANIFEST.sha256 before invoking make image. A compromised or unexpected ImageBuilder Makefile could create either path as a symlink after preflight. The later find redirection or sort redirection followed that symlink and could overwrite an external operator-owned file.
- **Test-first commit:** [608e3a02](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/608e3a025d52cfaa2c030f2b8388e36c05b8c73a) adds two disposable Makefile regressions. Each creates a symlink to an external sentinel during make image, one for the temporary manifest and one for the final manifest.
- **Exact RED:** [Actions #44009189152](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44009189152), validation job 133791793399, FAILED as expected: 44 packaging/tool tests ran and the two new regressions failed because the wrapper returned success and completed manifest generation despite the build-created symlinks; the other 42 packaging tests passed. Firmware-hardening and shared-contract validation steps passed. End-to-end profile staging and ESP32/ESP8266 compile jobs were SKIPPED after validation failed. Separate case-collision [#44009189247](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44009189247) SUCCESS.
- **Scoped source fix:** [df58e380](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/df58e380f6c25c1f0934030f11fee2029b9fbd1f) adds POSIX shell set -C (noclobber) before build execution. Subsequent generated manifest redirections now fail when either path exists at open time, including a symlink created after preflight. The wrapper still refuses pre-existing paths and does not delete operator data.
- **Exact source-head PR verification at df58e380:** [Actions #44009316223](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44009316223) COMPLETED SUCCESS. Validation job 133792207525 PASS; the packaging/tool suite ran 44 tests, including both new post-preflight symlink regressions, all PASS. ESP32 job 133792250783 PASS; ESP8266 job 133792250854 PASS. Separate case-collision [#44009316195](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44009316195) SUCCESS. These are exact-source software CI results only.
- **Scope:** test/source changes are limited to tools/test_package_appliance_firmware.py and tools/package_appliance_firmware.py; this section updates only this release-owned handover. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation, networking, shared contract or financial source was changed.
- **Evidence limits:** both new cases use a disposable synthetic Makefile and SYNTHETIC-NOT-FIRMWARE bytes. ESP32/ESP8266 jobs compile their firmware source; they do not create approved OpenWrt ImageBuilder target binaries. No signer-positive test, protected signer, physical flash, customer funds, hardware acceptance or production readiness is claimed.
- **Coordination snapshot:** MASTER #288 is at 2c2b517995365e23d89e423e2b9faeac4135381f; its PHX-RELEASE workflow route remains reimplementation-review, not blind-copy authorization. Experiments #242 remains at 734b89d9e7792247e8376335c3f3685500ab3f89, but its recorded base 6d4c9b48 has drifted from the live blazepwifi-v0.6.0-audit-foundation branch 2fbd2475e9f54878c316fa7cea2f228386b0e859; MASTER must reconcile before migration. Publisher isolation #291 remains at 2c4edff231d9b2819415086825530d80b8801307; Windows run [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) handover/build PASS, publisher SKIPPED. COE integration #26 remains at b382d233ff06c8791b1028bed3c617cc7b670d12; five workflows remain QUEUED with no jobs returned. COE packager #31 remains a draft on this branch, based on #26. No submitted independent review exists on #31 at this checkpoint.
- **Registry provenance:** a recursive Library metadata listing found only older registry snapshots through v7 and the 2026-10-26 baseline; canonical private Drive registry v11 was not present in the accessible Library. No older snapshot was substituted for v11, and no private contents or identifiers were copied.
- **Hardware coordination:** PHX-HARDWARE's UTC03 request on control issue #172 concerns poll/config admission and hardware trust boundaries. This release change does not touch those files; PHX-MASTER/CORE/QA retain ownership and should coordinate that request separately.
- **Rollback:** revert only the test/source commits on this existing draft branch if required. Leave the PR draft and unmerged. Independent PHX-QA review and PHX-MASTER integration sequencing remain required.


## PHX-RELEASE — 2026-11-17 UTC04 reject symlinked firmware candidates

**DRAFT / source validation PASS; ESP32 compile pending at source-head checkpoint / PRODUCTION NO-GO.**

- **Reproduced packaging defect:** the wrapper searched firmware outputs with find -type f for *.bin and *.img.gz. A symlink with one of those firmware suffixes was silently omitted from the checksum manifest. When a regular image and a symlinked image were both present, the wrapper returned success and wrote a manifest containing only the regular file, leaving an unmanifested firmware-looking candidate in the ImageBuilder output tree.
- **Test-first regression:** commit [2f7ffd79](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2f7ffd79e8fbead028315ab91706226343fd955c) adds a synthetic Makefile case that emits a regular .bin plus a symlinked .img.gz pointing to an external sentinel. It asserts fail-closed rejection, no manifest, and unchanged external target bytes.
- **Exact RED retained:** [push run #44016028491](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44016028491) and [PR validation run #44016036834](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44016036834) **FAILED as expected** in the new regression: result.returncode was 0, proving the wrapper accepted the output set. The suite ran 45 tests with one failure; all other tests passed. ESP32/ESP8266 jobs were skipped after validation failed. Separate [case-collision run #44016036715](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44016036715) **SUCCESS**.
- **Scoped source fix:** commit [5b1ba381](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5b1ba381954e51a313046c5b543da70bcddd94bd) checks for -type l firmware-suffix candidates in the expected target/subtarget tree before empty-file validation or checksum generation. Any symlinked .bin/.img.gz now produces RELEASE-BLOCKED: symlinked firmware image and exits without writing a manifest. Regular-file image discovery, empty-image rejection, deterministic relative-path checksums, and manifest noclobber remain unchanged.
- **Exact source-head verification at 5b1ba381:** [PR run #44016089447](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44016089447) validation **SUCCESS** (45 packaging tests, including the new symlink-candidate regression, all PASS); ESP8266 compile **SUCCESS**; ESP32 compile was **IN PROGRESS** at this handover checkpoint and is not credited. Push run [#44016083243](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44016083243) had validation and ESP8266 **SUCCESS**, ESP32 **IN PROGRESS**. Separate [case-collision #44016089435](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44016089435) **SUCCESS**.
- **Scope:** test-only commit changes tools/test_package_appliance_firmware.py; source fix changes tools/package_appliance_firmware.py; this section changes only this release-owned handover. No CORE, RENTAL, PISONET, HARDWARE, QA, MASTER, shared interface, network, or financial source changed.
- **Evidence limits:** the regression uses a synthetic Makefile, disposable files and EXTERNAL-SYNTHETIC-NOT-FIRMWARE bytes. It proves the packager refuses symlinked firmware candidates; it does not create or approve OpenWrt images. Firmware board jobs compile ESP sources and are not physical hardware acceptance.
- **Coordination snapshot:** MASTER draft #288 HEAD fc9ba1391908f8d49d8f9e9c578e43b49e21417f; its release workflow route remains reimplementation-review, not blind-copy authorization. Experiments release #242 HEAD 734b89d9e7792247e8376335c3f3685500ab3f89, base 6d4c9b487af4d768c4d7627654d119417fcc6e00, while the live development base branch is 2fbd2475e9f54878c316fa7cea2f228386b0e859; MASTER must reconcile this drift before migration. Publisher-isolation #291 HEAD 2c4edff231d9b2819415086825530d80b8801307 has Windows handover/build PASS and publisher SKIPPED on PR validation. COE integration #26 HEAD b382d233ff06c8791b1028bed3c617cc7b670d12 has eight associated queued workflow runs (five PR-triggered and three push-triggered); all eight returned zero jobs, so integration CI is not verified. COE release packager #31 remains OPEN/DRAFT, based on #26; no independent PHX-QA review is present.
- **Registry provenance:** the accessible Library copy of BLAZE_PROJECT_REGISTRY.json is a historical 2026-10-26 snapshot (version 1), not canonical private Drive registry v11. The exact v11 file was not retrievable through the connected file surface; no substitute or private identifiers/contents are copied.
- **Rollback:** revert only the test/source commits on this existing draft branch if required. Keep PR #31 draft and unmerged. Independent PHX-QA review and PHX-MASTER integration sequencing remain required.


## PHX-RELEASE — 2026-11-17 UTC05 staged-overlay symlink containment

**DRAFT / source validation PASS; board compile pending at source checkpoint / PRODUCTION NO-GO.**

- **Reproduced defect:** `stage_overlay()` preserves source-rootfs symlinks via `shutil.copytree(..., symlinks=True)`. It then wrote generated `etc/config/network` and `etc/blazepwifi/appliance_profile.json` with ordinary `open(..., "w")`. A copied file symlink or parent-directory symlink could therefore redirect those writes outside the fresh staging tree. The optional Rental overlay used `os.makedirs(..., exist_ok=True)` and `shutil.copy2()` similarly, allowing a symlinked `usr/sbin` destination to redirect `blazerentalctl` writes and later permission normalization.
- **Test-first config-path regressions:** [commit `f1fc8d24`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/f1fc8d2408aa47996479bfa09c0b78589e70b207) adds three cases: `etc/config/network` file symlink, `etc/config` directory symlink, and `etc/blazepwifi/appliance_profile.json` file symlink. Exact RED [run #44022173832](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44022173832), validation job 133833964169, FAILED: all three new tests reported `ValueError not raised`; the other 45 packaging/tool tests and 18 shared-contract tests passed. ESP32/ESP8266 compile and profile staging jobs were skipped after validation failure.
- **Rental-path regression:** [commit `8e1248d8`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8e1248d8b0625800a0d75a6f602e4e7a057c2c04) adds a symlinked `usr/sbin` destination test with an external operator sentinel. Exact RED [PR run #44022515068](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44022515068), validation job 133835139148, FAILED: the new test reported `ValueError not raised`; the other 48 packaging/tool tests and 18 shared-contract tests passed. ESP32/ESP8266 compile jobs were skipped. Separate case-collision [#44022514996](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44022514996) SUCCESS.
- **Config-path source correction:** [commit `10015f20`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/10015f201b7216bac34c8ddfe612470b905df809) adds a directory-chain verifier using `lstat` and a staged-file writer that rejects symlink/non-regular final destinations and uses `O_NOFOLLOW` where available. Generated network and appliance-profile writes now pass through those helpers.
- **Rental-path source correction:** [commit `e4662cab`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e4662cab7b9d416744e8f048285aebc1e539bdb0) extends the same checked-directory and no-follow file-write path to all optional Rental destinations (`usr/lib/blazerental`, `usr/sbin`, `www/cgi-bin`, `etc/blazerental`). Rental source files are required to be regular files before copying; the staged Rental configuration directory is chmod'ed only after its path is verified.
- **Source/test-head validation at `e4662cab`:** PR [run #44022589488](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44022589488) validation job 133835266289 **SUCCESS**: 49/49 packaging/tool tests, including all four new symlink regressions, 18 shared-contract tests, and 10/10 appliance profile staging validations. ESP32 and ESP8266 compile jobs were **IN PROGRESS** at this handover checkpoint and are not credited. Push [run #44022583642](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44022583642) validation also **SUCCESS**; board compiles still in progress. Case-collision [#44022514996](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44022514996) SUCCESS.
- **Scope:** only `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, and this release-owned handover changed. No CORE, RENTAL, PISONET, HARDWARE, QA, MASTER implementation, shared interface, network, financial source, signing policy or publisher workflow changed.
- **Evidence limits:** tests use temporary rootfs trees and external sentinel files on GitHub-hosted CI. They establish staged path containment for the tested config/Rental destinations; they do not create approved OpenWrt images, validate a protected signer, flash hardware or establish physical acceptance.
- **Coordination:** PR #31 remains stacked on COE integration #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`. MASTER #288 route for release workflow migration remains `reimplementation-review`, not blind-copy authorization. Experiments #242/#291 remain separate Windows release drafts; #242's base SHA still differs from its live development branch and requires MASTER reconciliation before migration. COE #26 integration workflow records remain queued; do not count them as passing.
- **Registry provenance:** canonical private Drive project registry v11 was not directly retrievable through the available Library/Drive surface in this activation. Older Library snapshots are not substituted, and no private identifiers or contents are published.
- **Rollback:** revert only the scoped test/source commits on this existing draft branch. Keep PR #31 draft and unmerged pending independent PHX-QA review and PHX-MASTER integration sequencing.


## PHX-RELEASE — 2026-11-17 UTC06 reject symlinked build-script parent paths

**DRAFT / exact source-and-test CI verified / PRODUCTION NO-GO.**

- **Reproduced defect:** generate_build_script() used exclusive os.open(script_path, O_CREAT | O_EXCL), which protected an existing final filename and final-component symlink but still followed a symlink in a parent directory. A requested path such as build-output-link/generated-build.sh, where build-output-link points to an operator-owned directory, could create the generated script outside the intended output tree.
- **Test-first regression:** [commit bf3abf08](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/bf3abf0814be6a25e9da3f7351371022aa9a77cb) adds a disposable external output directory and a symlinked parent. The regression requires rejection, preservation of the parent symlink, and no generated file in the external target.
- **Exact RED retained:** [run #44030112610](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44030112610), validation job 133859731263, **FAILED as expected**: 50 packaging/tool tests ran; the new parent-symlink regression failed because the previous implementation did not raise. Firmware hardening and shared-contract validation passed; profile staging and ESP32/ESP8266 jobs were skipped after the packaging test failure. Separate case-collision [#44030112612](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44030112612) **SUCCESS**.
- **Source correction:** [commit df66ede3](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/df66ede3b614f13255d6a48aafca3b0326d1028f) adds descriptor-relative parent traversal from the filesystem root. Each parent component is opened with O_DIRECTORY | O_NOFOLLOW; the final script is created relative to the verified directory descriptor with O_CREAT | O_EXCL | O_NOFOLLOW. Platforms without POSIX dir_fd, O_DIRECTORY, and O_NOFOLLOW support fail closed rather than falling back to path-following creation.
- **Intermediate source-head failure preserved:** [run #44030368940](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44030368940) **FAILED only because the test's expected error-message regex did not match the new helper's actual ValueError text**. The log shows the helper raised ValueError: Build script parent path contains a symlink or non-directory; the test expected a different word order. This was a test assertion mismatch, not a source-path escape after the correction. Separate case-collision [#44030368973](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44030368973) **SUCCESS**.
- **Test assertion correction:** [commit d59b8bf8](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/d59b8bf83e9c4e86e1f80c7e374511b4adb7d578) aligns the assertion with the helper's explicit rejection message; no source behavior changed in this commit.
- **Exact source/test-head verification at d59b8bf8:** [run #44030440029](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44030440029) **COMPLETED SUCCESS**. Validation job 133860832001 **PASS**: 50/50 packaging/tool tests, 18/18 shared-contract tests, and all appliance profile staging checks. ESP8266 compile job 133861040886 **PASS**; ESP32 compile job 133861040965 **PASS**. Final case-collision [#44030440007](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44030440007) **SUCCESS**. These are exact-source software CI results.
- **Scope:** only tools/package_appliance_firmware.py, tools/test_package_appliance_firmware.py, and this release-owned handover changed. No CORE, RENTAL, PISONET, HARDWARE, QA, MASTER implementation, shared contract, network configuration, financial state, signer or publisher workflow was modified.
- **Evidence limits:** the regression uses temporary directories and a synthetic generated script. It proves symlinked parent-path rejection on the Linux CI runner; it does not create an approved OpenWrt ImageBuilder binary, sign firmware, flash hardware, or establish physical acceptance.
- **Live coordination at this checkpoint:** MASTER draft #288 is 7616a3d5de69f4e6d7d9905fc91d0c7500bdfd68; its release workflow route remains reimplementation-review, not blind-copy authorization. Experiments #242 is 734b89d9e7792247e8376335c3f3685500ab3f89, still based on 6d4c9b487af4d768c4d7627654d119417fcc6e00, while the live blazepwifi-v0.6.0-audit-foundation branch is 2fbd2475e9f54878c316fa7cea2f228386b0e859; MASTER must reconcile this drift before migration. Publisher-isolation #291 is 2c4edff231d9b2819415086825530d80b8801307; Windows run [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) handover/build **PASS**, publisher **SKIPPED**. Its workflow has global contents: read and job-scoped contents: write only for the gated publisher. COE integration #26 remains b382d233ff06c8791b1028bed3c617cc7b670d12; its five PR-triggered workflow runs remain **QUEUED** with no jobs returned. PR #31 remains stacked on #26 and is not integration acceptance.
- **MASTER/HARDWARE blocker:** latest control-plane #172 UTC06 checkpoint reports HARDWARE #315 at eeb16bf6daf9c67294bf1f3677acd53262679ca0; focused source-extracted host lab run [#44028990570](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44028990570) passed, but Full validation [#44028990577](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44028990577) failed in the QA-owned poll-loop extractor because dependencies pendingPostAttempted, acceptPollResponse(), and markPendingPostAttempt() were omitted. This is another role's task; RELEASE did not edit hardware or QA source. MASTER's UTC05 migration audit still blocks COE #26 firmware promotion due source/destination remote-config and quarantine-route mismatches.
- **Registry provenance:** canonical private Drive project registry v11 was not retrievable through the connected Library/Drive surface; the exact-title Library search surfaced historical snapshots only through v7 and older 2026-10-26 copies. No substitute was used and no private identifiers or contents were copied.
- **Review and rollback:** no independent submitted review was present on #31, #242 or #291 at this check. Revert only the scoped test/source commits on this existing draft branch if required. Keep #31 draft and unmerged pending PHX-QA review, MASTER integration sequencing, and the independent production gates.

- **Final handover-head verification at 81ab1342:** [run #44030946665](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44030946665) **COMPLETED SUCCESS** after this UTC06 handover update: validation job 133862469376 PASS (50/50 packaging/tool tests, 18/18 shared contracts, appliance profile staging PASS); ESP8266 job 133862524907 PASS; ESP32 job 133862524902 PASS. Final case-collision [#44030946587](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44030946587) **SUCCESS**. This closes the earlier in-progress note in the same UTC06 checkpoint; these remain software CI results, not physical acceptance.


## PHX-RELEASE — 2026-11-17 UTC07 generated ImageBuilder shell syntax guard

**DRAFT / test-only release cleanup / exact-source CI complete / PRODUCTION NO-GO.**

- **Cleanup:** added a regression guard for the generated POSIX ImageBuilder wrapper. The test creates a disposable profile staging tree, emits the wrapper, and runs `sh -n` against the exact generated file. This protects future edits to shell interpolation/line boundaries; it is not a claim that a product defect was found. The existing generated wrapper passed the syntax check, so no runtime source change was justified in this activation.
- **Test commit:** [`52331731`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/523317314c91ad986b74c0724c7bf6c448f34ff1) changes only `tools/test_package_appliance_firmware.py`, adding `test_generated_build_script_passes_posix_shell_syntax_check`.
- **Exact-source Actions:** [PR run #44037436216](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44037436216) completed SUCCESS at test HEAD `523317314c91ad986b74c0724c7bf6c448f34ff1`: firmware hardening/shared-contract validation PASS; packaging suite **51/51 PASS**; shared contracts **18/18 PASS**; appliance profile staging **10/10 PASS**; ESP8266 compile PASS; ESP32 compile PASS. [Case-collision run #44037435969](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44037435969) completed SUCCESS.
- **Scope:** test-only change in the existing COE draft #31 branch `phoenix/release-imagebuilder-failclosed-20261115`; no production packager behavior, CORE, RENTAL, PISONET, HARDWARE, QA, MASTER, network, financial or shared-interface source changed. Rollback is limited to reverting this single test commit.
- **Live coordination:** MASTER #288 HEAD `c121d651919c4099390d0a78c4cc0e8179e0c3ca`; its release route remains `reimplementation-review`, not blind workflow copying. Experiments #242 HEAD `734b89d9e7792247e8376335c3f3685500ab3f89`, base `6d4c9b487af4d768c4d7627654d119417fcc6e00`; the live `blazepwifi-v0.6.0-audit-foundation` base branch is `2fbd2475e9f54878c316fa7cea2f228386b0e859`, so MASTER must reconcile the drift before migration. Publisher-isolation #291 HEAD `2c4edff231d9b2819415086825530d80b8801307`, based on #242; Windows run [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) handover/build PASS and `publish-release` SKIPPED. COE integration #26 HEAD `b382d233ff06c8791b1028bed3c617cc7b670d12` still has five PR workflows queued with no jobs returned. COE packager #31 is now at test HEAD `523317314c91ad986b74c0724c7bf6c448f34ff1`, still open/draft and stacked on #26.
- **Cleanup-first:** issue #266 assigns PHX-RELEASE cleanup to PR #242 build/version/manifest/signing configuration; this activation did not duplicate #242 or #291 work. The COE #31 test guard is isolated to its existing release-packager branch and does not authorize integration.
- **Independent review:** no submitted PR reviews are present on #31, #242 or #291 at this check. PHX-QA independent review and PHX-MASTER integration sequencing remain outstanding.
- **Registry provenance:** canonical private Drive registry v11 was not retrievable from the available Library search. Historical v4/v7 snapshots and the 2026-10-26 baseline were not substituted; no private identifiers or contents were copied.
- **Evidence limits:** `sh -n`, synthetic staging, ESP board compilation and GitHub-hosted CI are software evidence only. No real OpenWrt ImageBuilder target binary, protected signature, hardware flash, power-cut test, customer payment or production acceptance is established.
- **Next:** continue only with a newly reproduced release-owned defect or a specifically assigned #242 cleanup; retain #31 draft/unmerged pending independent QA and MASTER review.

## PHX-RELEASE — 2026-11-17 UTC08: pre-build ImageBuilder symlink admission

**Disposition:** DRAFT / source-test CI verified / PRODUCTION NO-GO. Existing COE draft PR #31 remains open and unmerged; this work does not authorize integration PR #26.

### Defect and correction

The generated ImageBuilder wrapper previously checked stale regular firmware files, but did not reject a pre-existing symlinked target/subtarget output directory or a symlinked firmware-looking candidate before running `make image`. The build could therefore follow the symlink and write outside the intended workspace before the later post-build checks ran.

The wrapper now walks the expected `bin/targets/<target>/<subtarget>` components before the build and rejects any symlinked component. It also rejects pre-existing symlinked `.bin` / `.img.gz` candidates in the target output directory before invoking Make. Existing output and manifest contents are preserved; no cleanup or overwrite is attempted.

### Test-first history

- Test commit [`5b250640`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5b2506406e791bd99371240368c7a56710ff43d0) added pre-build rejection cases for a symlinked firmware candidate and a symlinked target output directory.
- Exact RED [run #44048108914](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44048108914), validation job 133918750215: **FAILED as expected**. Both new tests failed against the old wrapper; the existing post-build symlink rejection happened too late, and the target-directory symlink was not rejected before Make. ESP32/ESP8266 compile jobs were skipped after validation failure. Case-collision [#44048108945](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44048108945) passed.
- Assertion-strengthening test commit [`eeebd357`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/eeebd357df6b89b95d7d1eea4f00c3aa4915260d) added external-sentinel checks proving the old Make invocation overwrote the symlink target and created an image through the symlinked output directory.
- Second exact RED [run #44048348979](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44048348979), validation job 133919557342: **FAILED as expected**. Both regressions failed; the log shows the external image sentinel changed from `KEEP-OPERATOR-IMAGE` to `SYNTHETIC-NOT-FIRMWARE`, and the external output-directory test observed the unintended generated file. Compile jobs were skipped. Case-collision [#44048348915](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44048348915) passed.
- Source correction [`8cca7ff8`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8cca7ff8e35c7b90fb3b88345a8ea65f92bc81b5) adds the fail-closed pre-build checks.

### Exact-source verification

At source/test head `8cca7ff8e35c7b90fb3b88345a8ea65f92bc81b5`, [run #44048543517](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44048543517) completed **SUCCESS**:
- Packaging/tool tests: **53/53 PASS**.
- Shared contracts: **18/18 PASS**.
- Appliance profiles: **10/10 PASS**.
- ESP8266 compilation: PASS.
- ESP32 compilation: PASS.

Case-collision [run #44048543532](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44048543532) completed SUCCESS.

### Ownership, provenance and limits

Only `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, and this release-owned handover are in scope. The regression uses synthetic files and a disposable Makefile; it is not a real OpenWrt ImageBuilder build or firmware authenticity check.

Live release references at this checkpoint: MASTER #288 `349c5e24c3083dc78ffe9fe96e495d66285b7f2d`; Experiments #242 `734b89d9e7792247e8376335c3f3685500ab3f89` (base `6d4c9b487af4d768c4d7627654d119417fcc6e00`, while the live development base branch is `2fbd2475e9f54878c316fa7cea2f228386b0e859`); publisher-isolation #291 `2c4edff231d9b2819415086825530d80b8801307`; COE integration #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`; this packager #31 `8cca7ff8e35c7b90fb3b88345a8ea65f92bc81b5`.

PR #291 keeps global workflow permissions read-only and scopes `contents: write` to the gated publisher job; its exact-head Windows run #43744993487 passed handover/build and skipped the publisher. PR #242 still has workflow-level `contents: write`; do not copy it blindly. COE #26's five PR-triggered workflows remain queued with no jobs returned, and MASTER's source/staging parity holds remain in force. No independent PR reviews were present on #31, #242 or #291 at this check.

The canonical private Drive registry v11 was not directly retrievable through the connected Library surface. No historical registry was substituted and no private identifiers or contents were copied.

**No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred.** Production remains NO-GO pending protected signer and independent freshness witness, durable financial accounting/migration, independent QA/MASTER approval, real approved target binaries, 150 physical power cuts and a 30-device/24-hour soak.

## PHX-RELEASE — 2026-11-17 UTC09 reject symlinked directories hiding firmware candidates

**DRAFT / exact validation PASS / ESP8266 PASS / ESP32 compile pending at source checkpoint / PRODUCTION NO-GO.**

- **Freshness and ownership:** re-read Experiments control-plane issue #172, cleanup-first #266, MASTER draft #288 at 47f2f6e9107f58902396d5731cfcd77b80598eb5, release drafts #242 (734b89d9e7792247e8376335c3f3685500ab3f89) and #291 (2c4edff231d9b2819415086825530d80b8801307), COE integration #26 (b382d233ff06c8791b1028bed3c617cc7b670d12) and packager #31. The exact #31 branch was phoenix/release-imagebuilder-failclosed-20261115; base remained #26. No other role-owned source or shared interface was changed.
- **Reproduced defect:** the post-build wrapper searched for symlinks named *.bin or *.img.gz, then used find -type f to create the checksum manifest. POSIX find does not descend a symlinked directory by default. A symlinked directory with a non-firmware-looking name (for example linked-images/) could therefore hide nested firmware-looking files from both checks; with a separate regular .bin present, the wrapper could still return success and write a manifest omitting the hidden candidate.
- **Test-first regression:** [commit 3f0e712c](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3f0e712cea158b5cc4e9ef5fc3a15ac40a0b772b) adds a synthetic Makefile fixture with a regular image plus an external directory symlink containing hidden.img.gz. The first fixture attempt had a Makefile recipe tab-escaping error; [PR run #44053458853](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053458853) and [push run #44053449000](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053449000) failed at the packaging step with Makefile:5: missing separator. This was a test-authoring failure, not product evidence. Case-collision [#44053458845](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053458845) passed.
- **Fixture correction:** [commit 9c660ee8](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/9c660ee897a00eb0bb21c18a3aa25bd5a959f2e4) emits a real tabbed Makefile recipe. Exact test-first RED [PR run #44053608136](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053608136), validation job 133937237795, FAILED as expected: the new regression observed wrapper exit code 0 (AssertionError: 0 == 0), proving the symlinked directory was not rejected. The suite ran 54 tests with exactly this new regression failing; other packaging tests passed. Board compilation was skipped after validation failed. Case-collision [#44053608137](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053608137) passed. Push [#44053599229](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053599229) failed on the same test-first defect.
- **Source correction:** [commit 6193bf7b](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6193bf7b53399b4051efa06e7783f6aa50319f9a) rejects any symlink entry anywhere under the exact target/subtarget firmware output tree before image admission and manifest generation. This is intentionally fail-closed: it prevents a symlinked directory from hiding nested candidates and avoids silently omitting entries from the checksum manifest. Existing regular-file discovery, empty-image checks, deterministic sorting, stale-output guards and noclobber manifest handling remain intact.
- **Exact source/test-head CI at 6193bf7b:** PR [run #44053717428](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053717428), validation job 133937593561, PASS: 54/54 packaging/tool tests, 18/18 shared contracts, 10/10 appliance profile staging and firmware-hardening/syntax checks. ESP8266 job 133937658166 PASS. ESP32 job 133937658237 was IN PROGRESS at this source checkpoint and is not credited. Case-collision [#44053717488](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053717488) PASS. Push [#44053704981](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44053704981) validation and ESP8266 PASS; ESP32 was IN PROGRESS. These are synthetic host CI and ESP firmware compilation, not a real OpenWrt ImageBuilder artifact or physical hardware acceptance.
- **Scope:** only tools/package_appliance_firmware.py, tools/test_package_appliance_firmware.py and this release-owned handover changed. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation, shared interface, firmware source, network, financial source, signing policy or publisher workflow changed.
- **Cross-repository release audit:** MASTER #288 HEAD 47f2f6e9107f58902396d5731cfcd77b80598eb5 retains release workflow migration as reimplementation-review, not byte-for-byte copy permission. Experiments #242 HEAD 734b89d9e7792247e8376335c3f3685500ab3f89 still has base 6d4c9b487af4d768c4d7627654d119417fcc6e00, differing from the live development branch 2fbd2475e9f54878c316fa7cea2f228386b0e859; MASTER must reconcile before migration. #242 workflow grants contents: write at workflow scope. Publisher-isolation #291 HEAD 2c4edff231d9b2819415086825530d80b8801307 changes workflow-level permission to contents: read and confines contents: write to a separate gated publisher job; exact run #43744993487 had handover/build PASS and publish-release SKIPPED on PR validation. COE #26 remains at b382d233ff06c8791b1028bed3c617cc7b670d12; eight associated PR/push Actions runs remain QUEUED with zero jobs, so integration is not verified. #31 remains OPEN/DRAFT/UNMERGED and stacked on #26. No independent PHX-QA review is present on #31.
- **Registry provenance:** the accessible Library contains historical registry snapshots v3–v7 dated 2026-10-26/27, not canonical private Drive registry v11. The exact v11 source was not retrievable through the connected file surface; no substitute, private identifiers or contents were copied.
- **Rollback:** revert only the scoped test/source commits on this existing draft branch if required. Keep PR #31 draft and unmerged pending independent PHX-QA review and PHX-MASTER integration sequencing.


## PHX-RELEASE — 2026-11-17 UTC10 pre-build nested output-symlink containment

**Status: source/test head verified by Actions; final documentation-head CI pending after this handover commit; PR remains DRAFT / PRODUCTION NO-GO.**

### Defect and bounded correction

The pre-build ImageBuilder guard rejected symlinks whose names ended in `.bin` or `.img.gz`, and rejected symlinked fixed path components (`bin/targets/<target>/<subtarget>`). It did not reject a pre-existing nested symlink directory with an arbitrary name under the existing target output tree. A Makefile recipe could write through that directory to an external operator-owned location before the post-build symlink scan ran. The later scan failed, but only after the external write had happened.

The wrapper now scans the existing target output directory for **any** symlink before invoking `make image`, failing closed before the builder can follow a nested link. The existing suffix-specific stale-image check and post-build full-tree symlink check remain in place.

### Test-first history and exact RED

- Regression test commit [`2be60d4a`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2be60d4ab9e4b96072c047e9b7e0d86f9d352bb4) introduced a synthetic Makefile that attempts to write `cache/escaped.img.gz` through a pre-existing `cache` directory symlink.
- Fixture correction [`8e62290e`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8e62290ee36c22b96d9fb1af248315f30a87996f) corrected the Makefile newline/tab escapes before the meaningful regression run.
- Assertion-order correction [`0e2bbf90`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0e2bbf9088e279108c660ac73219c9bf2e96bc1d) made the external-write absence assertion execute before checking the diagnostic text.
- Intermediate run [#44063492968](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44063492968) failed at the diagnostic-message assertion because the old wrapper emitted its post-build symlink error; it is **not** counted as the decisive external-write RED.
- Decisive test-first RED [#44063605201](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44063605201), validation job `133971478175`: **FAILED as expected**. The new test failed because `escaped.img.gz` existed in the external operator directory (`AssertionError: True is not false`), proving the old wrapper wrote through the nested symlink before post-build detection. The suite ran 55 tests with exactly the new regression failing; other packaging tests passed. Firmware-hardening and shared-contract steps passed; end-to-end profile staging and both board compile jobs were skipped after validation failure. Case-collision [#44063605101](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44063605101) **SUCCESS**.

### Source fix and exact-source verification

- Source correction [`e3e7c14c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e3e7c14c8faefbf70f514ee1920e18c7bd35a707) adds a pre-build `find "$BIN_DIR" -type l -print -quit` guard for every pre-existing symlink entry under the expected target/subtarget output tree. It preserves the prior specific firmware-symlink diagnostic and post-build scan.
- Exact source/test-head PR run [#44063693594](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44063693594): validation job `133971790029` **SUCCESS** (55/55 packaging tests; 10/10 appliance profiles; firmware-hardening/syntax and shared-contract/router-profile validation steps passed). ESP8266 job `133971892483` **SUCCESS**; ESP32 job `133971892406` **SUCCESS**. Case-collision [#44063693562](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44063693562) **SUCCESS**.
- These are synthetic host packaging tests, profile validation and firmware compilation only. No real OpenWrt ImageBuilder image, signed artifact, physical hardware or production acceptance is claimed.

### Current ownership, provenance and blockers

- Current COE packager PR #31 source/test HEAD: `e3e7c14c8faefbf70f514ee1920e18c7bd35a707`; base #26 HEAD: `b382d233ff06c8791b1028bed3c617cc7b670d12`. PR remains OPEN / DRAFT / UNMERGED.
- MASTER PR #288 HEAD: `8bffe20f4a0ff5b722766c42d7dd3f03e97bee78`; its routing manifest classifies the Phoenix release workflow route as **reimplementation-review**, not blind-copy permission.
- Experiments PR #242 HEAD: `734b89d9e7792247e8376335c3f3685500ab3f89`; base `6d4c9b487af4d768c4d7627654d119417fcc6e00` remains behind the live development branch `2fbd2475e9f54878c316fa7cea2f228386b0e859`. Its workflow still grants workflow-level `contents: write`; MASTER must reconcile the base and permission model before any migration.
- Experiments PR #291 HEAD: `2c4edff231d9b2819415086825530d80b8801307`; global workflow permission is `contents: read`, while the separate gated `publish-release` job alone receives `contents: write`. Exact Windows run [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487): handover/build **SUCCESS**, publisher **SKIPPED**.
- COE integration PR #26 remains at `b382d233ff06c8791b1028bed3c617cc7b670d12`. Five workflow runs (`43096752609`, `43096752632`, `43096752800`, `43096752563`, `43096752557`) remain **QUEUED**; each job listing returned zero jobs. This is not integration acceptance.
- No submitted independent reviews were returned for #31, #242 or #291.
- Canonical private Drive project registry v11 was not retrievable through the available Library listing/search in this activation. No historical snapshot was substituted and no private identifiers or contents were copied.

Only `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, and this release-owned handover changed. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation, shared interface, firmware source, networking, financial source, signer or publisher workflow was changed. Rollback is limited to reverting the scoped test/source commits on this existing draft branch.

**No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred.** Production remains NO-GO pending protected signer and independent freshness witness, durable financial accounting/migration, independent QA/MASTER approval, real approved target binaries, 150 physical power cuts and a 30-device/24-hour soak.


## PHX-RELEASE 2026-11-17 UTC11 — custom-profile UCI injection guard

**DRAFT / exact source-test CI verified / PRODUCTION NO-GO.** Role lock: `PHX-RELEASE/2026-11-17T11Z`. Existing COE release-packager PR #31 remains OPEN / DRAFT / UNMERGED on `phoenix/release-imagebuilder-failclosed-20261115`, based on integration PR #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`.

### Defect and bounded correction

`generate_network_uci()` interpolated custom JSON profile values directly into single-quoted OpenWrt UCI syntax. A quote/newline in `networking.wan_interface`, a bridge `ports[].interface`, or a VLAN ID could inject additional UCI configuration into the staged appliance overlay.

- Test-first regression: [`449987fc`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/449987fc283bfd9fb701184cba8c72232d4a5796) adds three custom-profile injection cases (WAN interface, bridge port interface, guest VLAN).
- Expected RED retained: push [#44072555185](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44072555185) and PR [#44072564550](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44072564550) failed in `Validate appliance firmware packaging & tools`; downstream profile staging and board compile jobs were skipped. The test-only commit requires these unsafe values to raise `ValueError`. Case-collision [#44072564552](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44072564552) passed.
- Source fix: [`c99cc468`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/c99cc468ed4edc0545f57558f2cbf8b44cb9c8b7) validates every UCI interface token against a 1–15 character Linux interface-name allowlist and requires each configured VLAN ID to be an integer in 1–4094 (rejecting booleans and strings) before emitting any UCI text. Canonical profiles retain their existing output.
- Exact source/test-head PR run [#44072905745](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44072905745) and push run [#44072891387](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44072891387) both completed SUCCESS: firmware hardening/syntax, shared contracts/router profiles, appliance packaging/tool tests, all appliance-profile staging, ESP8266 compilation and ESP32 compilation/artifact upload all passed. Case-collision [#44072905603](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44072905603) passed.

This verifies generated UCI validation and CI firmware compilation only. It is not a real OpenWrt ImageBuilder binary, physical router acceptance, coin/electrical test, or production release.

### Ownership and next action

Only `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, and this release-owned handover changed. No shared interface, CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was modified. PHX-QA should independently review the custom-profile negative cases; PHX-MASTER retains integration and release-gate authority. Keep PR #31 draft and unmerged.

Private Drive registry v11 remains unavailable through the exposed Library search; no older snapshot was substituted. No signer, real key, tag, publication, hardware flash, payment migration or customer deployment occurred. Production remains NO-GO pending protected signer and independent freshness witness, durable financial accounting/migration, independent QA/MASTER approval, real approved target binaries, 150 physical power cuts and a 30-device/24-hour soak.


### UTC11 final handover-head CI completion

The preceding UTC11 checkpoint recorded the documentation-head ESP32 job as still running. It subsequently completed:

- Final PR-head [#44073554457](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44073554457): **COMPLETED SUCCESS** — packaging/firmware/shared-contract validation, all appliance profiles, ESP8266 compile/artifact upload and ESP32 compile/artifact upload all PASS.
- Final push-head [#44073545179](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44073545179): **COMPLETED SUCCESS** — validation, ESP32 and ESP8266 jobs all PASS.
- Final case-collision [#44073554397](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44073554397): **COMPLETED SUCCESS**.

These are exact documentation-head CI results for `d6641c3ed18ddd993b27b8ed4613c803da2d78b5`; the next docs-only handover commit will require its own exact-head CI.


## PHX-RELEASE — 2026-11-17 UTC12 UCI serialization correction

**Status:** source/test-head CI completed successfully; this handover update requires its own exact-head CI. PR #31 remains OPEN / DRAFT / UNMERGED. Production remains NO-GO.

### Defect and bounded correction

At the prior PR head, generate_network_uci() used double-escaped Python string literals for all UCI indentation (\\t) and joined sections with a double-escaped separator (\\n). The returned text therefore contained literal backslash-t/backslash-n characters rather than actual tab indentation and newline separators. Existing tests checked only fragments such as "option name 'br-lan'", so they did not catch the malformed serialized file written into the staged rootfs.

- Test-first regression: [commit 9f831b1d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/9f831b1d00c0d07c234604de323a544836686390) adds test_generate_network_uci_uses_real_newlines_and_tabs.
- Exact-source RED: [Actions #44082821393](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44082821393), validation job 134037492103, **FAILED as expected**. 57 packaging tests ran; exactly the new serializer regression failed because the output contained literal \\n and \\t sequences and no real newline. The other 56 packaging tests passed. Firmware-hardening and shared-contract checks passed; profile staging and ESP32/ESP8266 jobs were skipped after validation failure. [Case-collision #44082821348](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44082821348) **SUCCESS**.
- Source correction: [commit 8edb1034](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8edb10348050e0aaaa59cc8e0c3ddb1b60a6415a) changes only UCI serialization escapes inside generate_network_uci(): actual tab indentation and actual newline section separators. It preserves all existing network values, interface/VLAN validation, profile schema and output ordering.

### Exact source/test-head CI

At source/test HEAD 8edb10348050e0aaaa59cc8e0c3ddb1b60a6415a:

- [Actions #44083065438](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44083065438) **COMPLETED SUCCESS**. Validation job 134038325362 passed: 57/57 packaging/tool tests, 18/18 Shared contract tests, 10/10 appliance profile staging, and firmware-hardening/syntax checks. ESP32 job 134038405788 **SUCCESS**; ESP8266 job 134038405792 **SUCCESS**; both compile and artifact-upload steps passed.
- [Case-collision #44083065418](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44083065418) **SUCCESS**.

These are hosted synthetic packaging/profile tests and ESP compilation only. No OpenWrt uci parser, real ImageBuilder, actual appliance binary, physical router, electrical/coin test or hardware acceptance was run.

### Coordination and remaining blockers

- The separate MASTER UTC11 audit [commit 5d5ca7a0](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5d5ca7a04b81abe3e2771c7ba0f4e0ff135164db) identified the still-invalid literal fd00:db8:blaze::/48. This UTC12 correction deliberately did **not** change that value, add a profile field, or redefine the networking contract. PHX-MASTER / networking owners must specify the canonical ULA source and per-profile contract before release-owned code can consume it.
- #26 remains OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12; its five known workflow runs still return zero jobs. No integration acceptance is inferred.
- #242 remains at 734b89d9e7792247e8376335c3f3685500ab3f89; its release workflow still grants workflow-level contents: write. #291 at 2c4edff231d9b2819415086825530d80b8801307 has global contents: read and isolates contents: write to the gated publish-release job. Its Windows build/handover passed in [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487); publisher skipped. No independent QA/MASTER reviews are recorded for #242/#291/#31.
- The canonical private Drive registry v11 was not present in the accessible Library listing. The read-only listing covered 1,422 entries and exposed only registry snapshots v3–v7 plus an unversioned registry file; none was substituted for v11 and no private contents were copied to GitHub.

Only tools/package_appliance_firmware.py, tools/test_package_appliance_firmware.py, and this release-owned handover are in scope. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was modified. No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred.

**Next exact action:** obtain PHX-QA and PHX-MASTER review of the serializer correction; separately resolve the canonical ULA contract and the #242/#291 migration ordering before any integration.


## PHX-RELEASE 2026-11-17 UTC15 — generated ImageBuilder shell runtime correction

**Status at handover edit:** release source correction committed; exact-source mandatory-bubblewrap CI is still pending/in progress; COE #31 remains OPEN / DRAFT / UNMERGED; PRODUCTION NO-GO.

### Master finding and source-grounded reproduction

PHX-MASTER audit `COE_GENERATED_WRAPPER_LITERAL_ESCAPE_AUDIT_20261117_UTC15.md` at Experiments commit `ff543f7c828ebac76fb7923f4f2bbefd54fd4ad8` identified a generated-shell defect at the prior COE #31 source head `d45b84c67dc587fca6226662cb1d8bc59bdb11ae`, packager blob `fd558928b2869ce1f4b2cb2776b405b4b723b310`, around the empty-image guard. The Python triple-quoted template emitted literal backslash-n text between the `EMPTY_IMAGE` assignment, its `if` guard, and the following checksum command. MASTER's bounded emitted-fragment reproduction reported `sh -n` exit 0 but execution exit 2 with `Syntax error: Bad fd number`. That was a minimal shell reproduction, not a full packager suite or real ImageBuilder run.

### Test-first regression and source correction

- Test-first commit [`293a006d`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/293a006d6809493ba164f10d1e2917e8979e1633) adds `test_generated_wrapper_emits_empty_image_guard_as_real_shell_lines`. It asserts the generated wrapper contains actual line breaks rather than literal backslash-n separators. Existing `test_generated_wrapper_denies_empty_firmware_payload` exercises the empty-image runtime denial; existing `test_generated_wrapper_relative_stage_uses_absolute_path` is the positive synthetic wrapper/manifest path.
- Source fix [`b14841e7`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b14841e75d57144f8c72867ef54fdff796b9483d) replaces only the five literal newline escapes in the generated shell template with actual source line breaks. The empty-image predicate, diagnostic, exit code, checksum command, and manifest admission behavior are otherwise unchanged.
- Scope is limited to `tools/test_package_appliance_firmware.py` and `tools/package_appliance_firmware.py` for these two commits. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was modified.

### Exact-source Actions observations — do not infer terminal results

At test-only HEAD `293a006d6809493ba164f10d1e2917e8979e1633`:
- PR sandbox run [`#44112555269`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44112555269) and push sandbox run [`#44112536876`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44112536876) both reached the mandatory-bubblewrap packaging-regression step and were **IN_PROGRESS** at handover edit. No RED/PASS conclusion is claimed yet.
- Case-collision [`#44112555289`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44112555289) **COMPLETED SUCCESS**.
- PR shared/hardware run [`#44112555356`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44112555356) and push shared/hardware run [`#44112536917`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44112536917) were **QUEUED/IN_PROGRESS** at handover edit.

At source-fix HEAD `b14841e75d57144f8c72867ef54fdff796b9483d`:
- Push sandbox run [`#44112759405`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44112759405) was **PENDING** behind the earlier exact-head sandbox invocation at handover edit. Recheck PR/push runs and job conclusions before marking the correction VERIFIED.
- Prior sandbox run [`#44104956173`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104956173) at the pre-fix `d45b84c` head was **CANCELLED** before the mandatory test step; it is not acceptance evidence.

### Separate remaining P0 boundaries

- `tools/run_imagebuilder_sandbox.py` is currently invoked by the CI test harness only. The generated operator build entrypoint still does not invoke it. Do not claim actual operator builds are sandboxed. The runner uses bubblewrap `--share-net`; network isolation is explicitly **not** claimed.
- The generated ULA remains invalid: `fd00:db8:blaze::/48`. PHX-MASTER/networking owners must define the canonical site-scoped RFC 4193 ULA contract; this release correction did not change networking.
- COE #26 remains at `b382d233ff06c8791b1028bed3c617cc7b670d12`; five PR workflows remain QUEUED with zero jobs. No integration acceptance is established.
- Experiments #242 remains at `734b89d9e7792247e8376335c3f3685500ab3f89` with base `6d4c9b487af4d768c4d7627654d119417fcc6e00`, while the comparison-only live development branch is `2fbd2475e9f54878c316fa7cea2f228386b0e859`; workflow-level `contents: write` remains a MASTER reconciliation item. #242 run [`#40882814472`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) passed handover/build only.
- Experiments #291 remains at `2c4edff231d9b2819415086825530d80b8801307`; its global workflow permission is read-only and write permission is isolated to the gated publisher. Run [`#43744993487`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) passed handover/build; publisher was SKIPPED.
- No submitted reviews were returned for #31, #242, #291 or MASTER #288.
- Canonical private Drive project registry v11 was not found in the accessible Library search; only older snapshots and a checkpoint reference were visible. No older snapshot was substituted and no private identifiers/contents were copied.

**Next exact action:** PHX-RELEASE rechecks terminal status of #44112555269/#44112536876 and #44112759405, then verifies the final PR-head sandbox run including both empty-image denial and positive synthetic wrapper/manifest paths. PHX-QA independently executes those same cases at the corrected exact head. MASTER retains ULA, integration, migration and production-gate ownership.

No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred. Production remains NO-GO.


## PHX-RELEASE 2026-11-17 UTC16 — generated operator entrypoint write-boundary enforcement

**Status:** operator wrapper now routes through the release-owned ImageBuilder runner by default; exact-head mandatory-runner CI is pending; shared packaging validation passes; PHX-QA/MASTER review pending; COE #31 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Source and test commits

The UTC15 audit at MASTER #288 identified that the CI test harness invoked `run_imagebuilder_sandbox.py`, while the generated operator build script still invoked `make image` directly. This UTC16 change addresses that source-level routing gap without changing the shared networking contract or any other role's implementation.

- Test-first routing regression: [`670efd23`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/670efd234877f0bc7981a6745a6ae6822cfff5b9) adds a disposable Makefile that would create a synthetic image and a fake `sudo` that records the required runner invocation.
- Fixture correction: [`6bc50873`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6bc5087351fac3467ed15292bf06464bd8c8a75d) fixes the test's Makefile/tab and fake-sudo newline escapes. The first test commit's initial failure was a fixture-authoring error, not valid defect evidence.
- Packager source correction: [`382bf1b9`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/382bf1b9d2f55a3c7847fcdc314598f238b17145) makes the generated wrapper locate and SHA-256-pin the release-owned runner, reject changed/missing runner or symlinked build/script paths, and invoke `sudo -- python3 run_imagebuilder_sandbox.py` before any ImageBuilder Makefile execution when the runner marker/probe is absent.
- Runner marker: [`a0cfa46d`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a0cfa46d55bd55dd7a7f889329cae704fc394fa8) sets the explicit in-runner marker only after bubblewrap user-namespace setup and the ownership probe.
- Probe-name validation: [`c0a88bed`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/c0a88bed2c9079f69c10621f022d5baf53309748) restricts accepted probe basenames to the runner's PID form or the test-only fixture name, preventing path components from being supplied through the marker.

Current source/test blobs:
- `tools/package_appliance_firmware.py`: `f819ef1cd5265ff026e8a98ad9541c36ed087617`
- `tools/test_package_appliance_firmware.py`: `a5310f90d0405afeeedb2a5981700945f4270aad`
- `tools/run_imagebuilder_sandbox.py`: `ce098e44e847c265604e3dbb5d8df505025dd0ad`
- `.github/workflows/release-imagebuilder-sandbox.yml`: `151c052f36664c1cb70138e7f135a5570909e09e` (unchanged)

The generated wrapper fails closed if Python 3, sudo, sha256sum, the pinned runner, or the expected build paths are unavailable. The runner is pinned at wrapper-generation time; regenerate the wrapper if the runner source changes. Only the three files above and this release-owned handover are in scope. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation, network interface, ULA contract, financial schema or shared interface was modified.

### Exact-source CI — current truth

**Test-first history**
- At initial test-only HEAD `670efd234877f0bc7981a6745a6ae6822cfff5b9`, shared validation [#44124301394](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124301394) failed in the new routing test because the fixture contained literal backslash-n text; this is a test-authoring failure, not a valid RED. The dedicated runner run [#44124301544](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124301544) was still IN_PROGRESS at the last check.
- At corrected test-only HEAD `6bc5087351fac3467ed15292bf06464bd8c8a75d`, shared validation [#44124381732](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124381732) produced the decisive RED: the new test expected fake-sudo exit 73 but got 0 because the old generated wrapper executed the synthetic Makefile directly. Case-collision [#44124381692](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124381692) passed. Dedicated runner run [#44124381729](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124381729) was cancelled before jobs.

**Source/runner correction**
- Source-head dedicated runner [#44124576753](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124576753) was CANCELLED before jobs; shared validation [#44124576564](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124576564) was CANCELLED; case-collision [#44124576801](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124576801) passed.
- Runner-marker head dedicated runner [#44124622906](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124622906) was CANCELLED before jobs. Shared validation [#44124622561](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124622561) passed validation but both board compile jobs were cancelled; case-collision [#44124622790](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124622790) passed.
- Current source/test head `c0a88bed2c9079f69c10621f022d5baf53309748`: dedicated runner run [#44124724541](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124724541) is PENDING with no jobs returned. Shared/firmware run [#44124724509](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124724509): validation job `134185444908` completed SUCCESS; packaging suite ran 60 tests with 1 skipped (59 passed), appliance profiles 10/10 passed; ESP8266 job `134185549493` completed SUCCESS; ESP32 job `134185549576` was IN_PROGRESS during core installation. Case-collision [#44124724661](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124724661) passed.

No exact-head mandatory-runner PASS is claimed. The earlier final-head run [#44113058229](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058229) was CANCELLED before jobs; its shared/hardware and case-collision runs were scoped successes only.

### Boundary limitation and remaining blockers

This runner is a **host write-confinement boundary**, not a complete security sandbox:
- The host root is read-only but still readable inside the namespace; it is not a confidentiality boundary.
- `--share-net` intentionally keeps the host network; network isolation is not present or claimed.
- Do not run untrusted third-party Makefiles on a build host containing secrets or sensitive readable files. A dedicated isolated build host / confidentiality boundary still requires PHX-MASTER and PHX-QA approval.
- Exact-head CI must prove the newuidmap/newgidmap ownership probe succeeds and the generated wrapper's Makefile invocation is actually inside the restricted writable ImageBuilder bind. If it fails, stop and ask MASTER to approve a supported isolated-host alternative rather than weakening the checks.

Separate networking P0 remains: the packager still emits invalid placeholder ULA `fd00:db8:blaze::/48`. Do not invent a fixed replacement. PHX-CORE/COE owner must define installation-scoped durable ULA provisioning; PHX-RELEASE then implements the agreed validation/generation and tests, with independent PHX-QA review.

### Cross-repository provenance and ownership

- MASTER #288 current branch head is `86b91edd2864d796487a9da56a8267ae44ca771c` (newer than the #172 body's 15:45 snapshot `5e11daf8)); all changed paths remain under `coordination/phoenix/`. The control-plane index needs a refresh by MASTER.
- Experiments #242 remains `734b89d9e7792247e8376335c3f3685500ab3f89`; its workflow-level `contents: write` remains a MASTER reconciliation item. Run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) passed handover/build only.
- Experiments #291 remains `2c4edff231d9b2819415086825530d80b8801307`; global workflow permission is read-only and write permission is isolated to the gated publisher. Run [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) passed handover/build; publisher skipped.
- COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows remain queued with zero jobs. No combined integration acceptance is established.
- COE release #31 remains stacked on #26, draft and unmerged. No submitted independent reviews were found on #31, #242, #291 or #288.

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the connected Library/Drive surface; only v3–v7 snapshots were returned. No older snapshot was substituted and no private contents or identifiers were copied.

**Next exact action:** recheck [#44124724541](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124724541) and [#44124724509](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44124724509) until terminal; inspect the runner job logs, then request PHX-QA to independently verify the exact final head. MASTER retains ULA, host-isolation acceptance, integration sequencing and production-gate ownership.

No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred. Production remains **NO-GO**.


## PHX-RELEASE 2026-11-17 UTC17 — bounded ImageBuilder child/process-group timeouts; hosted-runner UID-map blocker

**Status:** bounded timeout controls and regression tests are committed; shared packaging/profile validation and case-collision pass; the mandatory real-bubblewrap workflow fails before the timeout path because the hosted runner rejects the current UID mapping. No exact-head sandbox PASS; COE #31 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Control-plane and ownership readback

At this activation, PHX-RELEASE re-read live Experiments issue #172, cleanup-first #266, MASTER #288 and coordination/phoenix/OWNERSHIP_ROUTES.json, plus release drafts #242/#291 and COE #26/#31. MASTER #288 was at f8f5169b0f06f52f19f6889fd66ae84bb9461a93; its routes remain DRAFT_REVIEW_ONLY. The PHX-RELEASE route for .github/workflows/blazepwifi-build.yml to .github/workflows/pisowifi-ci.yml is reimplementation-review, not copy authorization.

- Experiments #242 remained at 734b89d9e7792247e8376335c3f3685500ab3f89; its blazepisonet-softtimer-release.yml still has workflow-level contents: write. Its current handover/build evidence is scoped only; signing/publishing are not acceptance.
- Experiments #291 remained at 2c4edff231d9b2819415086825530d80b8801307; its workflow has global contents: read and isolates contents: write to the gated publish-release job. [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) passed handover/build; publisher was skipped.
- COE integration #26 remained at b382d233ff06c8791b1028bed3c617cc7b670d12; its five PR workflows still returned queued/no-job state. #31 remains stacked on #26.
- No submitted independent reviews were found on #31, #242, #291 or #288.
- The exact private BLAZE_PROJECT_REGISTRY_v11_20261027.json was not present in the fully paginated accessible Library listing (1,422 entries checked). The older v3-v7 snapshots and the v11 reference in a checkpoint were not substituted for the canonical file; no private contents or identifiers were copied.

### Test-first regression and source changes

All commits are on the existing isolated branch phoenix/release-imagebuilder-failclosed-20261115.

- Test-first timeout API regressions: [dbb9995c](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/dbb9995ca7646e6bffc0e4043e92ff72e89a1a18). Added unit checks for finite UID/GID helper timeout, fail-closed mapping timeout, TERM/KILL delivery to both outer bubblewrap and inner --new-session process groups, and invalid build-timeout rejection.
- Source correction: [d8206c42](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/d8206c423c6c3e05cc920e0edf6024bec2859f4a). newuidmap/newgidmap each receive a 10-second timeout; namespace-info wait remains bounded at 30 seconds; ImageBuilder runtime is bounded by --timeout-seconds (default 3,600; maximum 14,400); timed-out execution sends TERM then KILL to both the outer bwrap process group and the inner child process group, with bounded cleanup waits.
- Dedicated timeout integration regression and bounded test harness: [2dc2409b](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2dc2409bdc6938c73ba05326555c1daa7ba084e0). The CI harness gives sandbox invocations a 60-second default and a 90-second outer subprocess limit; the new real-bwrap test requests a 1-second build limit and checks that a delayed synthetic Makefile write does not occur after the runner returns.
- Sandbox workflow queue correction: [72b4692b](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/72b4692bd9b35410628bb213527634c2b34b0298) enables cancellation of superseded runs; [45f793db](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/45f793db86a4e9c4f695a5fdf248c8099f4d96ea) moves this revision to a new concurrency-group key so stale pre-timeout runs do not block the bounded-runner checks.
- Only release-owned files changed: tools/run_imagebuilder_sandbox.py, tools/test_package_appliance_firmware.py, this handover, and .github/workflows/release-imagebuilder-sandbox.yml. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was changed.

### Exact-source Actions — current truth

**Test-first HEAD dbb9995c**
- PR validation [#44135988042](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44135988042) failed in packaging validation as expected because the new tests referenced timeout helpers not yet implemented: 64 tests, 4 errors, 1 skipped; 59 existing tests passed. This is the test-first RED, not a post-fix result.
- Case-collision [#44135987552](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44135987552) completed SUCCESS.
- Pre-fix dedicated sandbox runs [#44135987138](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44135987138) and [#44135969825](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44135969825) were later CANCELLED when the old queue was superseded; neither is a pass.

**Source/test HEAD d8206c42**
- PR shared/hardware [#44136195426](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44136195426): packaging validation and 10/10 appliance profiles PASS; ESP8266 compile/artifact PASS; ESP32 was still in progress at the last observation.
- Push shared/hardware [#44136183350](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44136183350): validation and ESP8266 PASS; ESP32 was still in progress at the last observation.

**Final pre-handover HEAD 45f793db**
- PR shared/hardware [#44136889893](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44136889893): firmware hardening/shared validation and appliance packaging/profile validation completed SUCCESS; ESP8266 compile/artifact PASS; ESP32 was still in progress at the last observation.
- Case-collision [#44136889905](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44136889905): SUCCESS.
- Mandatory PR sandbox [#44136889859](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44136889859), job 134228748594: FAILURE. The runner reached the new timeout unit tests (all four passed), but real-bwrap integration failed before ImageBuilder execution. The exact error was newuidmap: uid range [0-1) -> [1001-1002) not allowed. Twenty integration assertions then failed because namespace setup never completed; the new 1-second timeout test did not reach its timeout path. This is an environment/UID-map authorization blocker, not evidence that process-group timeout enforcement passed.
- Mandatory push sandbox [#44136879568](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44136879568): FAILURE at the same UID-map setup gate.
- The new concurrency key successfully allowed the exact-head PR sandbox workflow to start rather than remain behind the older queued run.

### Exact next owner action / security boundary

PHX-MASTER and PHX-QA must approve the least-privilege user-namespace ownership model before PHX-RELEASE changes privilege handling:

1. Preferred candidate for review: run the sandbox runner as the invoking unprivileged build user so namespace root maps to that same host UID/GID, rather than launching the bwrap parent as root and asking newuidmap to map host UID 1001 into it.
2. Alternative only if explicitly approved: provision the narrowest ephemeral subordinate UID/GID mapping on the hosted runner and prove the mapping is limited to the build user.

Do not weaken the owner probe, skip the mandatory bubblewrap test, assume /etc/subuid contents, or claim the 1-second integration timeout passed. The current --share-net setting still does not provide network isolation, and the read-only host root remains readable; this is not an untrusted-build confidentiality boundary.

**Next exact action:** obtain PHX-MASTER/PHX-QA decision on the user-namespace mapping model; then reproduce the mapping on the exact hosted-runner image and rerun the mandatory bwrap integration, including the delayed-write timeout test. Until that is green, the runtime boundary is not accepted.

No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred. Production remains **NO-GO**.


### UTC17 final handover-head CI follow-up

At handover HEAD feb9d9d5b8590f3a692c373329a3d5610a5613cc:
- PR mandatory sandbox [#44137530498](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137530498) **FAILURE**; push mandatory sandbox [#44137518573](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137518573) **FAILURE**. Both reproduce the same newuidmap denial, UID range [0-1) -> [1001-1002) not allowed. The 1-second timeout integration did not reach its timeout path.
- PR shared/hardware [#44137530517](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137530517): firmware hardening, shared-contract/router validation, packaging and 10 appliance profiles **PASS**; ESP8266 compile/artifact **PASS**; ESP32 compile **IN PROGRESS** at the last observation.
- Push shared/hardware [#44137518704](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137518704): validation and 10 profiles **PASS**; ESP8266 compile/artifact **PASS**; ESP32 compile **IN PROGRESS** at the last observation.
- Case-collision [#44137530364](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137530364): **PASS**.

The source/test files and sandbox workflow were unchanged by this follow-up; only this handover was updated. No sandbox runtime acceptance is claimed.


## PHX-RELEASE UTC18 — unprivileged single-ID user-namespace trial

**Disposition: SOURCE TRIAL COMMITTED / SHARED CI PASS / HOSTED-RUNNER USERNS BLOCKED / PRODUCTION NO-GO.**

The PHX-MASTER decision at Experiments commit [0b5adc04](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/0b5adc046d6da13e3dd1913e8658e96e712f2bea) approved only an unprivileged single-ID user-namespace implementation trial and independent QA review. It prohibits runner elevation, SUDO_UID/SUDO_GID, newuidmap/newgidmap, subordinate-ID ranges and broad host identity grants.

### Exact release branch and commits

- COE draft PR #31 remains OPEN / DRAFT / UNMERGED, based on integration PR #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Branch: `phoenix/release-imagebuilder-failclosed-20261115`.
- Final source/test head before this handover: `753326dcad460f7f0a3f7ce81f62a0dfb1890a53`.
- Test-first direct-unprivileged-entrypoint regression: [d206a700](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/d206a7009f7008be9a8b1c142d076a2d00bf72bb).
- Runner single-ID/non-root implementation: [3a822c25](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3a822c25dde9e5cbca81f3544d20da67528dc549).
- Generated operator wrapper no longer elevates with sudo: [e238d617](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e238d617bd2673bbae9b6528267bae590be15d67).
- Identity regression tests: [41ff6805](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/41ff6805017dd56a1275cffcccff3df55c31ea27).
- CI removes uidmap package dependency and verifies a non-root runner: [86862439](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/86862439a38074d1a8b351422bb07c863be6b6b8).
- Corrected generated-shell f-string escaping after an intermediate authoring error: [ef05aa44](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/ef05aa44e46f46add9519fdf750da2569f93fe23).
- Corrected test fixture newline escaping: [753326dc](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/753326dcad460f7f0a3f7ce81f62a0dfb1890a53).

Only release-owned runner, packager wrapper, test and sandbox-workflow paths changed. The runner still uses a read-only host-root bind, a writable disposable ImageBuilder tree, an ownership probe, bounded child execution and process-group cleanup. `--share-net` remains explicit: network isolation and host-file confidentiality are **not** claimed.

### RED and exact-source CI

- Test-first RED [#44145358339](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44145358339): **FAILED as expected** before source implementation. The prior runner rejected direct non-root invocation with `sandbox runner must be invoked through sudo`; 21 tests failed on that obsolete privileged assumption. Case-collision [#44145358428](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44145358428): PASS.
- Intermediate source/workflow head [#44146213670](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44146213670) and shared validation [#44146213704](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44146213704): **FAILED due to a generated-wrapper Python f-string NameError** (`PHX_BWRAP_OWNER_PROBE`). This was an implementation/template authoring error, not an expected security RED; corrected in ef05aa44. Case-collision [#44146213492](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44146213492): PASS.
- Corrected source/test head [#44146780982](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44146780982): **FAILED at the real bubblewrap setup** with `bwrap: setting up uid map: Permission denied`. The 53-test suite recorded 20 failures because the unprivileged namespace could not be created and the ownership probe was absent. The real symlink and 1-second delayed-write timeout paths were **not reached**. This is an environment-policy blocker, not a passing sandbox result.
- Shared validation [#44146781248](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44146781248): **SUCCESS**; firmware-hardening/shared-contract validation PASS, ESP32 compile/artifact PASS, ESP8266 compile/artifact PASS.
- Case-collision [#44146780932](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44146780932): **SUCCESS**.

The unprivileged single-ID trial is therefore **not runtime accepted**. Do not restore sudo, uidmap helpers, subordinate-ID grants or an unsandboxed fallback to make CI green.

### Cross-repository state and owner actions

- MASTER #288 remains OPEN/DRAFT at `0b5adc046d6da13e3dd1913e8658e96e712f2bea`; no PR-triggered run returned.
- Experiments #242 remains `734b89d9e7792247e8376335c3f3685500ab3f89`; exact PR run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472): handover and Windows build PASS.
- Experiments #291 remains `2c4edff231d9b2819415086825530d80b8801307`; [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487): handover/build PASS; publisher SKIPPED.
- COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows remain QUEUED with zero jobs returned.
- Independent PHX-QA review on COE #31: none submitted at this checkpoint.
- Canonical private Drive registry v11 was not directly retrievable. An accessible private checkpoint references the canonical v11 filename for provenance only; it is not a replacement registry. No private identifiers or contents are copied here.

**Next exact owner action:** PHX-MASTER / repository owner must provision or authorize a disposable, isolated, no-secret runner whose unprivileged user-namespace policy is explicitly enabled and independently reviewed. PHX-QA must independently review the exact candidate SHA and prove single-ID mapping, host ownership, external-sentinel containment, timeout cleanup and fail-closed behavior there. If no such runner is authorized, keep the sandbox acceptance BLOCKED.

No merge, signing, publication, hardware flashing, payment migration, customer deployment or physical acceptance occurred. **PRODUCTION NO-GO remains mandatory.**


## PHX-RELEASE UTC19 — BlazeRental configuration directory permission preservation

**Disposition: SOURCE/TEST COMMITTED / SHARED + BOARD CI PASS / MANDATORY BUBBLEWRAP STILL BLOCKED / PRODUCTION NO-GO.**

COE [draft PR #31](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/31) remains OPEN / DRAFT / UNMERGED on `phoenix/release-imagebuilder-failclosed-20261115`, based on integration #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`.

A test-first regression found that `stage_overlay(include_rental=True)` created `etc/blazerental` and chmodded it to 0700, but the later generic directory normalization loop reset every directory to 0755. The final staged mode was therefore 493 (0755), not 448 (0700). This contradicted the packager's explicit private-directory intent.

**Commits**
- Test-first assertion: [69239e3d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/69239e3de2393eb5d4a042ef0a85be0e47789652) adds an exact final-mode assertion to `test_stage_overlay_with_rental`.
- Source correction: [fc7c632d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/fc7c632d7e0330b57d8ff7d1f4ab96c6e78cc042) applies the 0700 mode during the final directory normalization pass, while retaining 0755 for ordinary directories. The early chmod was removed so the intended mode is not overwritten.
- This task changed only `tools/test_package_appliance_firmware.py` and `tools/package_appliance_firmware.py`; no Rental source or shared interface was changed.

**Exact-source Actions**
- Test-first RED: [#44155814677](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44155814677), validation job 134296122924 **FAILED AS EXPECTED**. The suite ran 66 tests with one failure and two skips; the failure was exactly `AssertionError: 493 != 448` in `test_stage_overlay_with_rental`. Firmware-hardening and shared-contract validation steps passed; later profile/board jobs were skipped after the validation failure. Case-collision [#44155814809](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44155814809) **SUCCESS**.
- Source/test HEAD `fc7c632d7e0330b57d8ff7d1f4ab96c6e78cc042`: [shared/hardware run #44156008013](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44156008013) **SUCCESS**. Firmware-hardening, shared contracts, appliance packaging/tool tests, and all 10 profile staging validations passed. ESP32 and ESP8266 compilation plus artifact upload both completed **SUCCESS**. Case-collision [#44156008017](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44156008017) **SUCCESS**.
- Mandatory bubblewrap [#44156008032](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44156008032) **FAILED at namespace setup**, not at this permission correction: `bwrap: setting up uid map: Permission denied`; runner then reported `sandbox did not create its ownership probe`. 53 sandbox integration assertions ran, 20 failed because the namespace was not created. The symlink/timeout execution paths were not reached. This remains an infrastructure/UID-map blocker and is not counted as sandbox acceptance.

**Current coordination refs**
- MASTER #288: `598481bfc2eb91efd1f6cb1ced96752de615973c`, draft; ownership routes remain `DRAFT_REVIEW_ONLY`.
- Experiments #242: `734b89d9e7792247e8376335c3f3685500ab3f89`, base `6d4c9b487af4d768c4d7627654d119417fcc6e00); workflow-level `contents: write` remains. Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) handover/build **SUCCESS**; signing and publication steps **SKIPPED**.
- Experiments #291: `2c4edff231d9b2819415086825530d80b8801307`, based on #242; global `contents: read`, write permission isolated to gated publisher. Windows run [#43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) handover/build and credential-free publisher mock **SUCCESS**; actual `publish-release` job **SKIPPED**.
- COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; five PR-triggered workflows remain QUEUED with no jobs returned. No combined integration acceptance is claimed.

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found after a fully paginated metadata-only listing of 1,422 accessible Library entries. No older snapshot was substituted; no private contents or identifiers were copied.

**Next owner actions**
1. PHX-QA independently review the final 0700 permission assertion and source correction at the exact final PR head.
2. Infrastructure owner must provision/authorize the disposable no-secret runner with unprivileged user namespaces enabled; PHX-RELEASE must rerun mandatory bubblewrap tests there without sudo, uidmap helpers, broad subordinate-ID grants or an unsandboxed fallback.
3. PHX-MASTER / PHX-CORE / PHX-RELEASE must define the durable site-scoped RFC 4193 ULA provisioning contract before changing the invalid `fd00:db8:blaze::/48` placeholder. No value is invented here.
4. COE integration owner must diagnose the five queued #26 workflows and resolve source/target provenance before migration.

Shared CI and board compilation are software evidence only. No approved OpenWrt ImageBuilder target binary, physical flash, power-cut/soak acceptance, protected signer, independent freshness witness, durable financial migration, or customer deployment is established. No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**



## PHX-RELEASE UTC19 — overlay file-mode classification relative to staging root

**Disposition: TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / SOURCE-TEST VALIDATION PASS / ESP8266 PASS / ESP32 IN PROGRESS AT CHECKPOINT / MANDATORY BUBBLEWRAP BLOCKED / PRODUCTION NO-GO.**

COE [draft PR #31](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/31) remains OPEN / DRAFT / UNMERGED on `phoenix/release-imagebuilder-failclosed-20261115`, based on integration #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`.

**Defect:** the staging permission normalizer searched the absolute staged file path for `/cgi-bin/`, `/init.d/`, and `/usr/sbin/`. If an operator chose a staging parent whose own path contained one of those markers, ordinary generated configuration/metadata files were incorrectly chmodded executable. The disposable regression used a staging parent containing `/usr/sbin/`; generated `etc/config/network` became mode 0755 (493) instead of 0644 (420), while an actual overlay `usr/sbin/diagnostic` must remain executable.

**Commits**
- Test-first regression: [`fa8a347a`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/fa8a347a65608926a03bd6ac66a51d9d573cfa51) adds `test_stage_overlay_file_modes_are_relative_to_staging_root`, asserting ordinary config/profile metadata remain 0644 and a real overlay `usr/sbin` utility remains 0755.
- Source correction: [`15ca3499`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/15ca3499aefd9836acc592256309834d0e0747b1) classifies executable locations from `os.path.relpath(fp, staging_dir)`, preserving existing `cgi-bin`, `init.d`, `usr/sbin`, and `.sh` behavior without letting the operator's absolute staging path influence modes.
- Only `tools/test_package_appliance_firmware.py` and `tools/package_appliance_firmware.py` changed in the source/test stack. No CORE, RENTAL, PISONET, HARDWARE, QA, MASTER or shared-interface source was modified.

**Exact-source RED**
- Push [#44158122050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158122050), validation job `134304272365`: **FAILED AS EXPECTED**. The packaging suite ran 67 tests with one failure and two intentional skips. The sole failure was the new regression: `AssertionError: 493 != 420` for generated UCI config beneath a staging path containing `/usr/sbin/`. Firmware-hardening and shared-contract validation passed; profile and board jobs were skipped after the test failure.
- Case-collision [#44158132260](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158132260): **SUCCESS**.

**Source/test-head verification at `15ca3499aefd9836acc592256309834d0e0747b1`**
- Push shared/hardware [#44158211374](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158211374), validation job `134304585160`: **SUCCESS**. Packaging/tool tests: 67 run, two intentional sandbox-only skips; all non-skipped tests passed. Shared contracts: 18/18 PASS. Appliance profile staging: 10/10 PASS.
- ESP8266 compile/artifact job `134304669429`: **SUCCESS**.
- ESP32 job `134304669517`: **IN PROGRESS** when this handover was written; do not credit as passed until terminal.
- PR shared/hardware [#44158225192](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158225192), validation job `134304636627`: **SUCCESS**; ESP8266 job `134304742300` **SUCCESS**; ESP32 job `134304742277` **IN PROGRESS** at this checkpoint.
- Case-collision [#44158225228](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158225228): **SUCCESS**.

**Separate mandatory bubblewrap result — not acceptance**
- Push sandbox [#44158211439](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158211439), job `134304584928`: **FAILED** at host namespace setup, `bwrap: setting up uid map: Permission denied`.
- PR sandbox [#44158225148](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158225148), job `134304685630`: **FAILED** with the same UID-map denial. The run reported 54 tests and 20 failures because namespace/ownership-probe setup never succeeded; the symlink-confinement and timeout execution paths were not reached. Do not weaken the approved single-ID model or add sudo/uidmap/subordinate-ID fallback.

**Remaining independent blockers:** canonical private Drive registry v11 remains inaccessible through the exposed Library surface; no older snapshot was substituted. The packager still emits invalid ULA `fd00:db8:blaze::/48`, which requires the MASTER/CORE installation-scoped ULA contract. COE #26 remains unaccepted with eight queued workflow runs (five PR-triggered and three push-triggered; zero completed jobs). The sandbox still needs an authorized disposable no-secret runner with unprivileged user namespaces enabled and independent PHX-QA review. No approved real OpenWrt ImageBuilder image, signer/freshness witness, durable financial migration, physical flash, 150 power cuts, or 30-device/24-hour soak is established. No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**
