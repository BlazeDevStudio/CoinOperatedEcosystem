# PHX-RELEASE — ImageBuilder wrapper safety and operator handover

**Checkpoint:** 2026-11-15 Asia/Manila. **Status:** DRAFT / CI PENDING / PRODUCTION NO-GO.  
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

