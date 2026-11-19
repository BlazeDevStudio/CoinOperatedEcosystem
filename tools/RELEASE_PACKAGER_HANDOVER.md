## PHX-RELEASE UTC02 — sandbox identity handover correction (2026-11-19)

- Active draft: [COE PR #35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`.
- Base #31: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Test-first commit: [`4329380`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/432938075871979c8a8892300135cb0eee115a3c).
- Expected RED: shared validation [#44443563240](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44443563240) failed at the new handover-consistency assertion (108 tests ran, one expected failure, two intentional sandbox-only skips). Mandatory sandbox [#44443563538](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44443563538) also stopped at the same host-preflight test; its Bubblewrap/runtime steps were skipped.
- Corrected the stale current-candidate description: the runner uses an unprivileged single-ID user namespace and no `sudo`/`newuidmap`/`newgidmap`; the read-only root, writable builder bind, tmpfs masks, cleared environment, and deliberately shared network are now described consistently with source.
- This is a source-to-handover consistency correction only. It does not change sandbox behavior, provide network isolation, or establish Bubblewrap runtime acceptance. The hosted runner still lacks pre-provisioned `bwrap`; no unsandboxed fallback is permitted.
- No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER files were changed.

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
  - `tools/run_imagebuilder_sandbox.py` requires a non-root caller whose effective UID/GID match the real UID/GID, finds Bubblewrap only through the trusted `/usr/bin:/bin` path, and starts it directly in an **unprivileged single-ID user namespace**. Bubblewrap maps only the invoking host UID/GID to namespace root (`--uid 0`, `--gid 0`); the runner receives the namespace child PID through `--info-fd` and verifies the host owner of its probe file before accepting a build. It does **not** invoke `sudo`, `newuidmap`, or `newgidmap`.
  - The host root is mounted read-only. The disposable ImageBuilder directory is the only writable host bind; `/tmp`, `/home`, `/root`, `/run`, `/mnt`, `/media`, and `/srv` are overlaid with ephemeral tmpfs mounts. The child environment is cleared and rebuilt with a minimal PATH/HOME/TMPDIR and no runner credentials.
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


## PHX-RELEASE UTC20 — reject symlinked ImageBuilder runner paths

**Disposition: TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / SOURCE-HEAD PACKAGING VALIDATION PASS / BOARD BUILDS IN PROGRESS AT HANDOVER WRITE / MANDATORY BUBBLEWRAP STILL HOST-BLOCKED / PRODUCTION NO-GO.**

COE [draft PR #31](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/31) remains OPEN / DRAFT / UNMERGED on `phoenix/release-imagebuilder-failclosed-20261115`, based on integration #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`.

**Defect:** `generate_build_script()` called `realpath()` before `islink()`. That erased evidence that the repository-owned `run_imagebuilder_sandbox.py` candidate was a symlink, including when a parent directory was a symlink. The external target then appeared to be a regular file and its digest/path were embedded in the generated operator wrapper. At runtime the wrapper checked only the final component with `[ -L "$RUNNER_PATH" ]`, so a symlinked parent could still redirect execution.

**Test-first commits**
- Initial regression: [`8cb368ee`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8cb368ee2b79f2552313aa2985726e8ac5533be0) adds final-component and parent-directory runner symlink cases plus a runtime parent-symlink case.
- Parent-path fixture correction: [`4c6aae8f`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4c6aae8f9e208e10586b3c11bb947b133e2861ac).
- Deterministic fake-runner fixture: [`1ecb9c1f`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/1ecb9c1f4de5254e7f5c6878fa2e4f68d49707d5).

**Exact RED at test HEAD `1ecb9c1f`**
- Push shared/hardware [#44167797588](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44167797588), validation job `134338417867`: **FAILED AS EXPECTED**. 69 packaging tests ran, 3 new assertions failed, 2 sandbox-only tests skipped. Both generation-time cases reported `FileNotFoundError not raised`; the runtime case observed the fake runner execute through the symlinked parent (exit 0) instead of the wrapper rejecting the path.
- PR shared/hardware [#44167808320](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44167808320): **FAILED** on the same test-first head.
- The initial test commit's [#44167665421](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44167665421) also failed with 3 assertions; the deterministic fixture correction above removes its earlier runner-side effect ambiguity.

**Source correction**
- [`e9a5f5fc`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e9a5f5fcd90b855d439ec800a7f4c872e4bfc066) preserves the absolute runner candidate before canonicalization, rejects any path whose `realpath` differs, opens with `O_NOFOLLOW`, verifies a regular file with `fstat`, and hashes the opened descriptor. The generated shell now compares the runtime real path with the embedded path before hashing or invoking the runner, rejecting symlinked parent directories as well as final-component symlinks.

**Source/test-head CI at `e9a5f5fc`**
- Push shared/hardware [#44167890107](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44167890107): validation job `134338741317` **SUCCESS**; 69 packaging tests, 2 intentional sandbox-only skips; shared contracts and 10/10 appliance profiles passed. ESP8266 job `134338875453` and ESP32 job `134338875616` were **IN PROGRESS** when this handover was written.
- Push case-collision [#44167899992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44167899992): status was still IN PROGRESS at this handover write.
- The separate mandatory sandbox [#44167890159](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44167890159) **FAILED** at the existing hosted-runner user-namespace gate: `bwrap: setting up uid map: Permission denied`. The mandatory job reported 20 failures because the ownership probe could not be created; sandbox-dependent symlink and real timeout execution paths were not reached. This does not negate the shared packaging validation, and it is not a sandbox acceptance.

Only `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, and this release-owned handover changed. No CORE, RENTAL, PISONET, HARDWARE, QA, MASTER, shared contract or destination integration source was modified.

**Remaining blockers:** the hosted Actions runner still needs an authorized disposable no-secret environment with unprivileged user namespaces; do not add sudo, uidmap helpers, broad subordinate-ID grants or an unsandboxed fallback. The invalid `fd00:db8:blaze::/48` remains blocked on the MASTER/CORE durable site-scoped RFC 4193 ULA contract. COE #26 still has five queued workflows and no combined integration acceptance. The canonical private Drive registry v11 remains unavailable through the exposed Library surface; older v3–v7 snapshots were not substituted. No real OpenWrt target image, protected signer/freshness witness, financial migration, physical flash, 150 power cuts, or 30-device/24-hour soak is established. No merge, signing, publication, hardware flashing, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC21 — fail fast on unsupported bubblewrap hosts

**Disposition: TEST-FIRST RED REPRODUCED / PREFLIGHT UNIT TESTS 7/7 PASS / HOST USER-NAMESPACE PREFLIGHT FAILS CLOSED / SANDBOX ACCEPTANCE NOT ESTABLISHED / PRODUCTION NO-GO.**

COE [draft PR #31](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/31) remains OPEN / DRAFT / UNMERGED on \`phoenix/release-imagebuilder-failclosed-20261115\`, based on integration #26 at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`. Source implementation head before this handover update: \`1701d5ad6887d286b8642b63993cf49d0725fd99\`.

### Why this bounded CI change was selected

The mandatory sandbox workflow previously ran the full bubblewrap integration suite on a hosted runner that cannot create the approved unprivileged user namespace. The runner failed before its ownership probe, and the suite reported many environment-induced failures that obscured the single host prerequisite. This change adds an explicit, bounded preflight so an unsupported host is reported once and the sandbox-dependent regression suite is not launched.

### Test-first regression

- Test-only commit: [\`f3b11dd6\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/f3b11dd6c79e40f3eb7ba07d91c3d99ff7088b7e) adds the preflight tests and wires them into the dedicated release workflow.
- Push shared/hardware run [#44178649070](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44178649070), validation job \`134376728628\`: **FAILED AS EXPECTED**. 76 tests ran; the two new assertions failed because the helper and preflight step were not yet implemented; seven helper-dependent tests were skipped. The pre-existing packaging tests passed. Board jobs were skipped after validation failed.
- PR shared/hardware run [#44178655868](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44178655868), validation job \`134376751219\`: **FAILED** on the same test-only head; board jobs skipped.
- Case-collision [#44178655981](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44178655981): **SUCCESS**.

### Source correction

- Implementation commit: [\`1701d5ad\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/1701d5ad6887d286b8642b63993cf49d0725fd99).
- Adds \`tools/check_imagebuilder_sandbox_host.py\`. Its 10-second probe mirrors the approved unprivileged single-ID namespace flags (\`--unshare-all --share-net --unshare-user\)), read-only host-root bind, dev/proc mounts, tmpfs-only write, namespace UID/GID 0, cleared child environment and a bounded scratch-file check. It has no sudo, uidmap-helper, subordinate-ID or unsandboxed fallback.
- The release workflow runs the synthetic preflight tests, verifies the invoking non-root identity, then executes the real host preflight before the mandatory packaging regression suite. If namespace creation is denied, it exits 125 with a \`RELEASE-BLOCKED\` message and skips the sandbox-dependent suite.
- Files changed for this task: \`.github/workflows/release-imagebuilder-sandbox.yml\`, \`tools/check_imagebuilder_sandbox_host.py\`, and \`tools/test_imagebuilder_sandbox_host.py\`. This handover is the only documentation change. No packager/runner implementation, CORE, RENTAL, PISONET, HARDWARE, QA, MASTER or shared-interface source was changed.

### Exact-source Actions at \`1701d5ad\`

- Push sandbox [#44178760433](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44178760433), job \`134377112586\`: **FAILED CLOSED AT HOST PREFLIGHT**. Synthetic host-preflight tests **7/7 PASS**; unprivileged identity check **PASS**; real preflight returned exit 125 with \`bwrap: setting up uid map: Permission denied\`. The packaging regression step was **SKIPPED** by the preflight guard. This is not sandbox acceptance.
- PR sandbox [#44178775697](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44178775697), job \`134377164228\`: same exact-source result; 7/7 preflight unit tests pass, host preflight fails closed, packaging suite skipped.
- Push shared/hardware [#44178760777](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44178760777): validation job \`134377113924\` **SUCCESS**; ESP8266 job \`134377208168\` **SUCCESS**; ESP32 job \`134377207958\` was **IN PROGRESS** at handover time.
- PR shared/hardware [#44178775485](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44178775485): validation job \`134377164143\` **SUCCESS**; ESP8266 job \`134377265727\` **SUCCESS**; ESP32 job \`134377266259\` was **IN PROGRESS** at handover time.
- Case-collision [#44178775640](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44178775640): **SUCCESS**.

### Evidence limits and remaining blockers

The new preflight proves only that the host can create the required user namespace, map the invoking identity to namespace root, and write to its isolated tmpfs. It does **not** prove the runner's host-side builder ownership probe, symlink containment, actual ImageBuilder execution, process-group timeout/cleanup, network isolation, or confidentiality. The real sandbox-dependent tests remain unexecuted until the infrastructure owner provides an authorized disposable, ephemeral, no-secret runner with unprivileged user namespaces enabled. Do not add sudo, newuidmap/newgidmap, broad subordinate-ID grants or an unsandboxed fallback.

The invalid \`fd00:db8:blaze::/48\` remains a separate MASTER/CORE P0. Master’s UTC19 audit requires an installation/site-scoped RFC 4193 /48 that remains durable across reboot/upgrade/restore and is shared by devices on the same LAN; no prefix is guessed and no profile/interface change is made before the CORE/MASTER contract is approved. Canonical private Drive registry v11 remains inaccessible through the exposed Library surface; no v3–v7 substitute is used. COE #26 remains draft with eight queued workflows and zero completed jobs; MASTER #288 has no current-head workflow runs. No independent PHX-QA review is recorded on #31.

No merge, signing, publication, real OpenWrt firmware admission, hardware flash, payment migration or customer deployment occurred. No physical acceptance is established: 150 power cuts and 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO.**


## PHX-RELEASE 2026-11-18 UTC00 — bound synthetic ImageBuilder wrapper invocations

**Disposition: TEST-FIRST RED REPRODUCED / MOCK EXECUTION PROCESS-GROUP TIMEOUT FIXED / SOURCE-HEAD SHARED CI + BOTH BOARD COMPILES PASS / CASE-COLLISION PASS / MANDATORY BUBBLEWRAP HOST PREFLIGHT STILL BLOCKED / PRODUCTION NO-GO.**

COE [draft PR #31](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/31) remains OPEN / DRAFT / UNMERGED on \`phoenix/release-imagebuilder-failclosed-20261115\`, based on integration #26 at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`.

### Defect and scope

The test helper \`TestPackageApplianceFirmware._run_generated_wrapper()\` accepted \`timeout_seconds\`, but the non-\`PHX_REQUIRE_BWRAP\` mock-execution branch called \`subprocess.run()\` without applying that timeout. A stalled synthetic Makefile could therefore hold the shared CI test process until the outer workflow timeout. The real sandbox branch already passed its timeout to \`run_imagebuilder_sandbox.py\`; this change aligns the non-sandbox mock branch with the same bounded execution contract.

Only \`tools/test_package_appliance_firmware.py\` changed. No production packager, sandbox runner, firmware, profile, shared contract, CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source changed.

### Test-first progression

- Initial test commit [\`a2d7ab8f\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a2d7ab8f33b5320ecdf0e01b5f96ee5c026b2a1b) had a fixture-ordering mistake: the sleep recipe was appended after the Makefile had been written. Shared run [#44206073239](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206073239) failed at the target-directory assertion, so this run is **test-authoring failure, not product evidence**. The separate sandbox run [#44206073161](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206073161) failed at the existing hosted UID-map preflight; case-collision [#44206073160](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206073160) passed.
- Fixture correction [\`8d4ed816\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8d4ed81611896f239ad12374cc9b875c66c1f301) moved the bounded sleep/late-marker recipe before the Makefile write.
- Corrected test-first RED: shared run [#44206156044](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206156044) failed at the new assertion because the mock helper waited for the 3-second Makefile recipe and returned the later missing-image error instead of timeout status 124. The suite ran 77 tests with one expected new failure and two intentional sandbox-only skips. Sandbox [#44206156052](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206156052) remained blocked at host UID-map setup; case-collision [#44206156078](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206156078) passed.
- Source correction [\`46e0d55e\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/46e0d55e1ccf9aa4646295f7201c50284c7c4518) starts the mock wrapper in its own session and uses the existing release runner's process-group timeout/termination helper. A timeout returns synthetic status 124 with a \`RELEASE-BLOCKED\` message; the test asserts the late marker is not written and the ownership probe is removed. The real bubblewrap runner path is unchanged.

### Exact source/test-head Actions at \`46e0d55e\`

- Shared/hardware [#44206299623](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206299623): **COMPLETED SUCCESS**. Firmware-hardening/shared validation passed; Python suite **77 tests, 2 intentional sandbox-only skips**; all 10 appliance profiles passed; ESP8266 compile/artifact upload passed; ESP32 compile/artifact upload passed. The new timeout regression passed.
- Case-collision [#44206299677](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206299677): **COMPLETED SUCCESS**.
- Mandatory sandbox [#44206299772](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206299772): **FAILED CLOSED AT HOST PREFLIGHT** with \`bwrap: setting up uid map: Permission denied\`, exit 125. The sandbox-dependent packaging regression suite was **SKIPPED**. This is a hosted-runner capability blocker, not a source-test failure or sandbox acceptance.

The ESP32/ESP8266 compile outputs are synthetic CI artifacts for the existing Hardware workflow; they are not release-approved target images, physical hardware evidence, or production packages. No ImageBuilder firmware image was built or admitted by this task.

### Current coordination / remaining gates

- MASTER #288: \`phoenix/master-coordination@f657a177e17b61e54dc507984c551cfc65a9f10a\`, OPEN/DRAFT; 64 changed paths remain under \`coordination/phoenix/\`. \`OWNERSHIP_ROUTES.json\` remains \`DRAFT_REVIEW_ONLY\`; the PHX-RELEASE workflow route is reimplementation-review, not a copy/move authorization.
- Experiments #242: \`734b89d9e7792247e8376335c3f3685500ab3f89\`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) handover/build SUCCESS.
- Experiments #291: \`a74b8b940fba3aa8651f1a9ee8bbf23cf112726e\`; Windows run [#44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756) handover/build SUCCESS; write-privileged publisher SKIPPED. No independent submitted reviews were returned for #291.
- COE integration #26 remains OPEN/DRAFT at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`; five PR-triggered workflows are QUEUED with zero jobs returned. No combined integration acceptance.
- No independent PHX-QA review was returned for COE #31.
- The invalid \`fd00:db8:blaze::/48\` remains blocked on the MASTER/CORE installation-scoped RFC 4193 ULA contract; PHX-RELEASE did not invent a replacement.
- The canonical private Drive registry v11 remains unavailable through the exposed Library/connector surface; no older snapshot was substituted and no private identifiers or contents were published.

**Next:** PHX-QA independently reviews the timeout test at \`46e0d55e\`; infrastructure owner supplies an authorized disposable, ephemeral, no-secret runner with unprivileged user namespaces for the mandatory sandbox suite; MASTER/CORE resolve durable site-scoped ULA provisioning. No merge, signing, publication, hardware flash, payment migration or customer deployment. Physical acceptance remains NOT TESTED: 150 power cuts and 30-device/24-hour soak. **PRODUCTION NO-GO.**


## PHX-RELEASE 2026-11-18 UTC01 — reject symlinked staging-output parents

**Disposition: TEST-FIRST RED REPRODUCED / PACKAGER FIX COMMITTED / SOURCE-HEAD SHARED VALIDATION PASS / CASE-COLLISION PASS / BOARD COMPILES IN PROGRESS AT HANDOVER / MANDATORY BUBBLEWRAP PREFLIGHT HOST-BLOCKED / PRODUCTION NO-GO.**

COE [draft PR #31](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/31) remains OPEN / DRAFT / UNMERGED on `phoenix/release-imagebuilder-failclosed-20261115`, based on integration #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`.

### Defect and bounded correction

`stage_overlay()` rejected an existing requested destination, but then called `os.path.realpath()` on a not-yet-existing destination. If an operator-selected parent component was a symlink, the resolved path pointed into the symlink target and `copytree()` created the new staging tree there instead of refusing the ambiguous path.

The correction checks that the requested absolute parent path equals its resolved real path before any copy, rejects a symlinked parent with `ValueError`, and retains the already-validated requested destination path rather than replacing it with a resolved target. Existing output, source/output overlap and staged-content symlink protections are unchanged. No external path is created or deleted on rejection.

Only these release-owned files changed in the source/test stack:
- `tools/test_package_appliance_firmware.py`
- `tools/package_appliance_firmware.py`

### Test-first progression

- Test-first regression [`b241e868`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b241e8686ec60b39ed7cbf5bcb2c1f040b5b4a6f) creates an external operator-owned parent with a sentinel, symlinks the requested staging parent to it, and requires rejection before staging creation. It also asserts the symlink, sentinel and source marker remain unchanged.
- Exact RED: PR shared validation [#44213469913](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213469913) and push shared validation [#44213465845](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213465845) both **FAILED at the new assertion**: `AssertionError: ValueError not raised`. Each run executed 78 packaging/tool tests with one expected failure and two intentional sandbox-only skips. ESP8266/ESP32 compile jobs were **SKIPPED** after the validation failure. Case-collision [#44213469942](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213469942) **PASS**.
- Source correction [`2d6d80fe`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2d6d80feb3208d03d0dda8be3d13ba31e0d10371) adds the parent-path rejection before `copytree()`; no other subsystem or shared interface changed.

### Exact source/test-head CI at `2d6d80fe`

- PR shared/hardware [#44213536857](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213536857): validation job **SUCCESS**. The packaging/tool suite ran **78 tests, 2 intentional sandbox-only skips**, including the new symlink-parent regression; firmware-hardening and shared-contract test groups passed; all **10/10** appliance profile staging validations passed. ESP8266 and ESP32 compile jobs were **IN PROGRESS** at handover preparation and are not credited as passed.
- Push shared/hardware [#44213529806](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213529806): validation job **SUCCESS** with the same 78-test / 2-skip result and 10/10 profile staging. ESP8266 and ESP32 compile jobs were **IN PROGRESS** at handover preparation.
- Case-collision [#44213536850](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213536850): **COMPLETED SUCCESS**.
- Mandatory sandbox [#44213536824](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213536824): **FAILED CLOSED AT HOST PREFLIGHT**. Seven host-preflight tests passed; the actual unprivileged bubblewrap probe returned `bwrap: setting up uid map: Permission denied`, exit 125. Sandbox-dependent packaging regressions were not run. This is not sandbox acceptance.

Board compile jobs are firmware source compilation only, not approved OpenWrt ImageBuilder appliance images or physical hardware acceptance. No real ImageBuilder binary, signed package, hardware flash, power-cut test or device soak was performed.

### Current coordination / remaining gates

- MASTER #288: `phoenix/master-coordination@583a2053cc29825b63ead1b614192331d78fd730`, OPEN/DRAFT. Its routing manifest remains `DRAFT_REVIEW_ONLY`; the release workflow route is reimplementation-review, not copy/move authorization.
- Experiments #242: `734b89d9e7792247e8376335c3f3685500ab3f89`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) handover/build SUCCESS.
- Experiments #291: `a74b8b940fba3aa8651f1a9ee8bbf23cf112726e`; Windows run [#44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756) handover/build SUCCESS; write-privileged publisher SKIPPED. No independent submitted QA review was returned.
- COE integration #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; five PR-triggered workflows remain QUEUED with no jobs returned. No combined integration acceptance.
- No independent PHX-QA review was returned for COE #31.
- The invalid `fd00:db8:blaze::/48` remains a MASTER/CORE P0; PHX-RELEASE did not change network configuration or invent a replacement.
- Canonical private Drive registry v11 remains unavailable through the exposed Library/connector surface. No older snapshot was substituted and no private identifiers or contents were published.

**Next:** obtain independent PHX-QA review of the staging-parent regression and source fix; finish/inspect terminal board compile jobs; infrastructure owner supplies an authorized disposable, ephemeral, no-secret runner with unprivileged user namespaces for the mandatory sandbox suite; MASTER/CORE resolve durable site-scoped ULA provisioning. No merge, signing, publication, hardware flash, payment migration or customer deployment. Physical acceptance remains NOT TESTED: 150 power cuts and 30-device/24-hour soak. **PRODUCTION NO-GO.**

## 2026-11-18 UTC02 — child release PR sandbox trigger coverage

**Owner / scope:** PHX-RELEASE only; existing COE release-packager PR #31 and stacked child PR #35. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was changed.

**MASTER coordination:** the live #172 control-plane reconciliation at MASTER draft #288 head `650c6e5991ed8ba30d82dd98216316b3ae3a3780` identified child PR #35 at `61e2d8ef77e5cd3740ab9e630e5bfcc1994b7d09`, based on the old #31 head `7bdba18b86f706d7fb96831094338600e28cc9c5`, while current #31 was `20e75fc0e6fb7e7ada560a9ec41cb9695d198fa8`. The child branch had two commits ahead and seven behind, with overlapping release-owned packager/test files.

**Verified child change already present:** #35 adds a fail-closed generated-script publication correction. It creates the script non-executable (0600), writes and flushes the complete content, fsyncs the descriptor, then publishes 0755 with fchmod. A simulated partial-write regression requires the partial file to remain non-executable. Exact child-head shared CI [#44180549950](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44180549950) passed 77 packaging/tool tests with two intentional sandbox-only skips; ESP32 and ESP8266 compile jobs passed. This is CI evidence, not physical or production acceptance.

**New CI trigger defect reproduced and corrected on parent #31:**
- Test-first commit [`3db49ce1a1b1e9d8a23cf2803cb580b1c3b051bc`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3db49ce1a1b1e9d8a23cf2803cb580b1c3b051bc) added `test_workflow_triggers_for_release_child_branch`.
- Exact RED [#44222148410](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222148410): shared validation failed only at the new missing-base-branch assertion; 79 tests ran, one failed, two intentional skips. The mandatory sandbox workflow also failed at the same unit-test assertion before the real host probe; packaging regressions were skipped.
- First workflow edit [`b9fa5c9d`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b9fa5c9da2416bc944b8b91145a75343c40d1076) put the child branch in the wrong trigger section; exact validation [#44222257690](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222257690) caught the remaining push-filter assertion failure. This was an implementation-placement failure, not a product regression.
- Corrected workflow commit [`f56bdf60`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/f56bdf609632d3e096684a2d1873dd12c3cdeb02) now runs the mandatory sandbox for PRs targeting the release parent branch and pushes to the child branch. The token remains `contents: read`; no permission or sandbox fallback was added.

**Corrected parent-head CI:** shared validation [#44222357808](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222357808) passed the 79-test tools suite, shared contracts, firmware-hardening and 10/10 profile staging validation. ESP32/ESP8266 compile jobs were still running at handover authoring. Case-collision [#44222357680](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222357680) passed. Mandatory sandbox PR [#44222357646](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222357646) and push [#44222351423](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222351423) passed the host unit tests and non-root identity check, then failed closed at the real namespace probe with `bwrap: setting up uid map: Permission denied`; packaging regressions were skipped. This remains an infrastructure blocker, not sandbox acceptance.

**Next exact action:** reconcile current parent #31 into child #35 without force-pushing, preserve the child publication-safety fix, and verify PR/push sandbox workflows on the resulting exact child head. Expect the hosted-runner UID-map blocker to remain until an authorized disposable, no-secret user-namespace runner is supplied. Do not weaken the boundary or claim packaging regressions passed in the blocked sandbox job.

## 2026-11-18 UTC02 follow-up — child branch reconciled and exact-head validation

**Branch reconciliation completed without force-push.** Parent COE #31 is `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child COE #35 is now `8c13ebf627d8581f15531211c49191cc7cd76331`. The child merge commit has parents `61e2d8ef77e5cd3740ab9e630e5bfcc1994b7d09` (previous child head) and `59ed44d0b911e176f1a95b9cf5585ef811ffd31b` (current parent). Compare parent → child is **3 ahead / 0 behind**; child PR diff contains only `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py`.

**Exact reconciled child-head CI at `8c13ebf6`:**
- PR shared validation [#44222569550](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222569550): **SUCCESS**; 80 tools tests, two intentional sandbox-only skips; shared contracts, firmware-hardening, and 10/10 appliance-profile staging passed; ESP32 and ESP8266 compile/artifact-upload jobs both passed.
- Push shared validation [#44222561637](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222561637): **SUCCESS**; 80 tests, two intentional skips; both board compile/artifact-upload jobs passed.
- Case-collision [#44222569532](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222569532): **SUCCESS**.
- Mandatory sandbox PR [#44222569622](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222569622) and push [#44222561961](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222561961): host preflight unit tests **8/8 PASS**, unprivileged identity check **PASS**, real namespace probe **FAILED CLOSED** with `bwrap: setting up uid map: Permission denied`; mandatory packaging regressions were **SKIPPED**. This is not sandbox acceptance.

**Disposition:** source/test CI and board compilation are verified on this exact child SHA; mandatory sandbox execution remains infrastructure-blocked. PR #35 remains OPEN / DRAFT / UNMERGED. PHX-QA and PHX-MASTER independent review is still required. No signing, release publication, hardware flashing, payment migration or customer deployment occurred.


## 2026-11-18 UTC03 — generated wrapper rejects a replaced staging-root symlink

**Owner / scope:** PHX-RELEASE only; existing COE child draft PR #35, stacked on current parent PR #31. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source changed.

**Defect:** The generated ImageBuilder wrapper validated that STAGING_DIR was a directory, but did not verify that the path still resolved to the same real directory captured in the staging manifest. Replacing the staged rootfs path with a symlink after staging/wrapper generation therefore passed the directory check and allowed the wrapper to proceed toward Make using an operator-selected external directory.

**Test-first regression and correction**
- Test-first commit [4b4fa9ae](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4b4fa9ae6149d7afa2441bd37f4fcec34eea83de) renames the staged tree, replaces its original path with a symlink to an external operator-owned directory, and requires the generated wrapper to fail before Make. The fixture preserves an external sentinel and a Make invocation marker.
- Exact RED: [PR validation #44228438689](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44228438689) ran 81 packaging/tool tests with two intentional sandbox-only skips and failed only at the new symlink regression. The wrapper did not emit the required staged-root symlink denial and reached the post-build missing-image diagnostic instead. This is the expected source-defect reproduction, not a sandbox result.
- Source fix [e5fb3be1](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e5fb3be13c8ae0d82e943d6d71095c9a1db8223d) compares the staged path with Python realpath and rejects a symlinked path component before Make. The check is in the generated wrapper, so it is repeated when the wrapper is re-entered inside the release sandbox. No profile, network contract, ImageBuilder package list or shared subsystem was changed.

**Exact source/test HEAD:** e5fb3be13c8ae0d82e943d6d71095c9a1db8223d.
- [Shared / firmware / packaging validation #44228528489](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44228528489): **COMPLETED SUCCESS**. 81 packaging/tool tests passed with two intentional sandbox-only skips; firmware-hardening and shared-contract checks passed; all 10/10 appliance profile staging checks passed; ESP8266 and ESP32 compile plus artifact-upload jobs both passed.
- [Case-collision guard #44228528520](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44228528520): **SUCCESS**.
- [Mandatory sandbox #44228528514](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44228528514): **FAILED CLOSED AT HOST PREFLIGHT**. Host-preflight unit tests 8/8 passed and unprivileged identity checks passed; the real bubblewrap namespace probe failed with "bwrap: setting up uid map: Permission denied", exit 125. Mandatory sandbox packaging regressions were **SKIPPED**. This is not sandbox acceptance.

**Current branch relationship:** Parent #31 head/base 59ed44d0b911e176f1a95b9cf5585ef811ffd31b; child #35 head e5fb3be13c8ae0d82e943d6d71095c9a1db8223d. Exact compare: child **6 commits ahead / 0 behind**. The child base SHA equals the current parent head; this supersedes the older UTC01 audit's stale divergent #35 relationship. Both PRs remain OPEN / DRAFT / UNMERGED.

**Cross-role gates:** MASTER #288 remains OPEN/DRAFT at 650c6e5991ed8ba30d82dd98216316b3ae3a3780; OWNERSHIP_ROUTES remains DRAFT_REVIEW_ONLY. The PHX-RELEASE workflow route is reimplementation-review only. Architecture Contracts §6.9 still blocks the invalid global fd00:db8:blaze::/48: CORE/COE must define installation/first-boot ULA provisioning and durable persistence before RELEASE implements it. No shared profile or network source was changed. COE #26 remains at b382d233ff06c8791b1028bed3c617cc7b670d12 with five workflows queued and no integration acceptance.

**Provenance:** Canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json was not available through the exposed Library surface. No older registry snapshot was substituted and no private contents were copied into GitHub.

**Next:** PHX-QA independently reviews the new wrapper guard and exact source/test head; infrastructure owner supplies an authorized disposable, ephemeral, no-secret runner with unprivileged user namespaces for the mandatory sandbox suite; PHX-MASTER/CORE/COE resolve §6.9 provisioning ownership. No merge, signing, publication, hardware flash, payment migration or customer deployment. Physical acceptance remains NOT TESTED: 150 power cuts and 30-device/24-hour soak. **PRODUCTION NO-GO.**


## 2026-11-18 UTC04 — open Rental staging sources without following symlinks

**Disposition:** TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / SHARED PACKAGING + BOTH BOARD BUILDS PASS / CASE-COLLISION PASS / MANDATORY BUBBLEWRAP HOST-BLOCKED / PRODUCTION NO-GO.

**Scope:** PHX-RELEASE only, existing child draft PR #35 stacked on parent draft PR #31. The exact parent branch head is `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child source/test head is `988d2a6dd4c629b095d9d75c8cd0f0f46d15c04b`. Compare parent → child before this documentation update: **9 ahead / 0 behind**. Changed source/test paths remain only `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py`.

**Defect:** `_copy_staging_file()` first used `lstat()` to reject symlinks, then reopened the path with ordinary `open()`. A final-component replacement between those operations could turn the regular source into a symlink and cause the packager to read an operator-owned external file into the release staging tree.

**Test-first and correction**
- Regression commit [`1d0e1c54`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/1d0e1c54706112a5883a5750382fb05fe865310b) simulates replacement immediately after the regular-file `lstat`, preserving an external sentinel and requiring rejection before a staged copy is created.
- Exact RED: [shared validation #44236971833](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44236971833), job `134575337716`, **FAILED AS EXPECTED** at the new assertion: `AssertionError: ValueError not raised`. 82 tests ran, one expected failure and two intentional sandbox-only skips. Firmware-hardening and shared-contract checks passed before the packaging test failure; profile and board jobs were skipped. Case-collision [#44236971880](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44236971880) **SUCCESS**.
- Source fix [`988d2a6d`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/988d2a6dd4c629b095d9d75c8cd0f0f46d15c04b) opens with `O_NOFOLLOW` (and nonblocking mode where available), verifies the opened descriptor is a regular file, and compares device/inode with the earlier `lstat` identity before reading. Unsupported hosts fail closed. Destination writes still use the existing no-follow staging writer.

**Exact source/test-head CI at `988d2a6d`**
- Shared / firmware / packaging [#44237096331](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44237096331): **SUCCESS**. Packaging/tool suite: **82 tests, 2 intentional skips**; firmware-hardening: **18 tests PASS**; shared contracts PASS; appliance profile staging **10/10 PASS**.
- ESP32 job `134575812066`: **SUCCESS**; artifact ID `14397149892`, provider digest `sha256:a8966602e55e5a0ec24caadb10f04987bd068d36cdbf4c023e98ac36f1c43a49`.
- ESP8266 job `134575812074`: **SUCCESS**; artifact ID `14397513883`, provider digest `sha256:a1e6cf615cdaeee46e06a0e076a52713539feea7e1e5c1a35af7db5ce93be5dc`.
- Case-collision [#44237096287](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44237096287): **SUCCESS**.
- Mandatory sandbox [#44237096522](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44237096522): host preflight unit tests **8/8 PASS**, identity checks PASS, actual namespace probe **FAILED CLOSED** with `bwrap: setting up uid map: Permission denied`, exit 125. Mandatory sandbox packaging regressions were **SKIPPED**, not passed. This is infrastructure blockage, not sandbox acceptance.

Board compile artifacts are CI outputs only; their provider digests are not independent readback, approved OpenWrt ImageBuilder binaries, physical hardware evidence, or production release authorization.

**Cross-repository refresh**
- Parent #31 remains at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; its latest shared/case runs [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) and [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) **SUCCESS**; mandatory sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) **FAILED** at hosted UID-map setup.
- Child #35 remains OPEN / DRAFT / UNMERGED, stacked 9 commits ahead / 0 behind parent before this handover-only commit.
- Experiments #242 exact head `734b89d9e7792247e8376335c3f3685500ab3f89`, run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472): handover and Windows build **SUCCESS**.
- Experiments #291 exact head `a74b8b940fba3aa8651f1a9ee8bbf23cf112726e`, run [#44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756): handover/build **SUCCESS**, privileged publisher **SKIPPED**.
- COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; five PR workflows remain **QUEUED**, with no combined integration acceptance.
- MASTER #288 head `1c6c874c489474eb6b5aa1b10793e10eff547f63`; ownership routes remain `DRAFT_REVIEW_ONLY`, and the PHX-RELEASE workflow route is reimplementation-review only. No Master PR CI run returned.
- Architecture Contracts §6.9 still blocks the invalid `fd00:db8:blaze::/48` placeholder. PHX-CORE / COE integration owner must define installation-scoped RFC 4193 ULA provisioning and durable persistence before RELEASE changes the packager. No replacement prefix was invented.
- Canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the exposed Library/connector surface. An accessible 2026-11-09 checkpoint references its name/count for provenance only; it is not the registry. No older snapshot was substituted and no private contents were copied.

**Next owner actions:** PHX-QA and PHX-MASTER independently review source/test head `988d2a6d`; infrastructure owner supplies an authorized disposable, ephemeral, no-secret runner with unprivileged user namespaces for mandatory bubblewrap acceptance; PHX-CORE / COE integration owner settle §6.9 ULA provisioning; integration owner unblocks #26 workflows.

No merge, signing, publication, hardware flash, payment migration or customer deployment occurred. Physical acceptance remains NOT TESTED: 150 power cuts and 30-device/24-hour soak. **PRODUCTION NO-GO.**


## 2026-11-18 UTC05 — reject Rental source paths with symlinked parent components

**Disposition:** TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / 83 PACKAGING TESTS PASS / 10-OF-10 PROFILES PASS / ESP32 + ESP8266 PUSH BUILDS PASS / CASE GUARD PASS / MANDATORY SANDBOX HOST-BLOCKED / PRODUCTION NO-GO.

**Scope and refs:** PHX-RELEASE only, existing child draft PR #35 stacked on parent draft PR #31. Parent/base remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. Exact source/test head is `656540334b0f25cd43021a4de9b0b54d5f4cccbc`; current docs head at the time of this entry is the same source/test head. Child compare is **12 commits ahead / 0 behind** parent. Source/test paths are only `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py`.

**Defect:** `_copy_staging_file()` protected only the final filename with `O_NOFOLLOW`. A Rental source path whose parent directory was a symlink still traversed that parent and copied a file from an operator-owned external directory. Final-component protection alone did not constrain the full source path.

**Test-first and correction**
- Regression commit [`5c22338e`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5c22338e69d7860c3f32fad477ec79feb5904983) adds `test_copy_staging_file_rejects_symlinked_source_parent`. It creates an external Rental source directory, aliases it through a symlinked parent, and requires rejection before a destination file is created while preserving the external sentinel.
- Exact RED [#44242344408](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44242344408), job `134592991846`: **FAILED AS EXPECTED** at the new assertion, `AssertionError: ValueError not raised`. 83 tests ran, one failure, two intentional sandbox-only skips. Existing final-component symlink regression passed. The profile and board jobs were skipped after the packaging test failure.
- Source fix [`65654033`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/656540334b0f25cd43021a4de9b0b54d5f4cccbc) factors the descriptor-relative path walk into `_open_file_without_symlink_parents()`. It opens every parent component from filesystem root with `O_DIRECTORY | O_NOFOLLOW`, opens the final source with `O_NOFOLLOW`, retains regular-file and device/inode checks, and reuses the same helper for generated build-script creation. Unsupported hosts fail closed; no symlink or unsandboxed fallback was added.

**Exact source/test-head CI at `65654033`**
- Push shared/firmware/packaging [#44242430784](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44242430784): **COMPLETED SUCCESS**. Packaging/tool suite: **83 tests, 2 intentional skips**; firmware-hardening and shared-contract validation PASS; appliance profile staging **10/10 PASS**.
- ESP32 job `134593339262`: **SUCCESS**, compile and artifact upload completed.
- ESP8266 job `134593339421`: **SUCCESS**, compile and artifact upload completed.
- PR shared/firmware/packaging [#44242437545](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44242437545): validation **SUCCESS** (83 tests / two intentional skips, 10/10 profile staging); ESP8266 **SUCCESS**; ESP32 was **IN PROGRESS** at handover authoring and is not credited as complete here.
- Case-collision [#44242437616](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44242437616): **SUCCESS**.

**Mandatory sandbox**
- Push [#44242430710](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44242430710) and PR [#44242437575](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44242437575): **FAILED CLOSED AT HOST PREFLIGHT**. The eight sandbox-host preflight unit tests and non-root identity checks passed; actual bubblewrap namespace setup failed with `bwrap: setting up uid map: Permission denied`, exit 125. Mandatory sandbox packaging regressions were **SKIPPED**, not passed. This is hosted-runner infrastructure blockage, not a packager regression result or sandbox acceptance.

**Cross-repository refresh**
- MASTER #288 remains OPEN/DRAFT at `e95cda0ae3f08c4f1dbdfcdfa79808cc887cd7b3`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, and the PHX-RELEASE workflow route is reimplementation-review only.
- Experiments #242 remains OPEN/DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`; exact Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472): handover and build-windows **SUCCESS**.
- Experiments #291 remains OPEN/DRAFT at `a74b8b940fba3aa8651f1a9ee8bbf23cf112726e`; exact Windows run [#44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756): handover/build **SUCCESS**, write-privileged publisher **SKIPPED**.
- COE integration #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; five PR workflows remain **QUEUED**, no combined integration acceptance.
- MASTER UTC04 lineage audit identifies incompatible Stage-3 journal alternatives #39/#40/#42 (different on-flash record formats), with #41 dependent on #39; source license/redistribution rights for the Labs-origin Pisonet Universal import remain UNKNOWN. Do not select, merge, transplant or promote these candidates without MASTER/CORE/QA owner decisions.
- Architecture Contracts §6.9 still blocks `fd00:db8:blaze::/48`. PHX-CORE/MASTER/COE integration owner must define valid installation-scoped RFC 4193 ULA provisioning and durable persistence before RELEASE changes the packager. No replacement prefix was invented.
- Canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed Library surface. Search surfaced older v5-v7 snapshots only; they were not substituted. No private registry contents were copied.

**Reviews and next actions:** No submitted independent reviews were returned for #31 or #35. PHX-QA should independently review the parent-component no-follow regression and shared descriptor walker at source/test head `65654033`. Infrastructure owner must provide an authorized disposable, ephemeral, no-secret runner with unprivileged user namespaces for mandatory sandbox packaging tests. MASTER/CORE/COE must resolve §6.9 ULA provisioning and the integration journal/license lineage; COE integration owner must unblock #26 workflows.

No merge, signing, release publication, hardware flashing, payment migration or customer deployment occurred. Physical acceptance remains **NOT TESTED**: 150 power cuts and 30-device/24-hour soak. **PRODUCTION NO-GO.**


## PHX-RELEASE — 2026-11-18 UTC06 staged configuration write containment

**Disposition:** TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / PACKAGING + PROFILE VALIDATION PASS / BOARD COMPILES IN PROGRESS AT HANDOVER / CASE GUARD PASS / MANDATORY SANDBOX HOST-BLOCKED / PRODUCTION NO-GO.

A new destination-side race remained after the prior symlink hardening: `_write_staging_bytes()` checked the final file with `lstat()` and then used path-based `os.open()` with final-component `O_NOFOLLOW`. Replacing the destination parent directory with a symlink after `lstat()` redirected the write into an operator-owned external directory. Final-component protection did not secure the parent chain.

**Test-first history**
- Regression commit [`5ac689cc`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5ac689cc41784885cefc70f9c9cfe22f5d328367) adds `test_write_staging_bytes_rejects_parent_replaced_with_symlink_after_lstat`. It swaps the disposable staging parent for a symlink in the lstat/open gap and verifies the external sentinel and destination remain untouched.
- Exact RED [#44249610818](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44249610818), validation job `134616774794`: **FAILED AS EXPECTED**. 84 tests ran, the new assertion failed with `AssertionError: ValueError not raised`, and two sandbox-only tests were intentionally skipped. Board compile jobs were skipped after validation failed.
- Source correction [`aaecb633`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/aaecb633102712b471d923b5accdcaf8504809de) routes staged writes through the existing descriptor-relative `_open_file_without_symlink_parents()` helper. It opens each parent with `O_DIRECTORY | O_NOFOLLOW`, opens the final component with `O_NOFOLLOW`, uses nonblocking open flags, verifies the opened descriptor is a regular file before truncating, and fails closed when the required POSIX capabilities are absent. No fallback to path-based writes was added.

**Exact source/test-head CI at `aaecb633`**
- Shared/packaging validation [#44249718595](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44249718595): validation job `134617130042` **SUCCESS** — 84 tests, two intentional sandbox-only skips; firmware-hardening and shared-contract checks passed; all 10 appliance profiles staged successfully. ESP32 job `134617248955` and ESP8266 job `134617248962` were still **IN PROGRESS** at handover authoring and are not credited as passed.
- Case-collision [#44249718611](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44249718611): **SUCCESS**.
- Mandatory sandbox [#44249718583](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44249718583): **FAILED CLOSED AT HOST PREFLIGHT**. Host preflight 8/8 and unprivileged identity passed; actual bubblewrap namespace setup failed with `bwrap: setting up uid map: Permission denied`, exit 125. Sandbox-dependent packaging regressions were **SKIPPED**, not passed.

**Current stack and coordination**
- Child PR #35 remains OPEN/DRAFT/UNMERGED, stacked on parent #31 at base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. The exact source/test head is `aaecb633102712b471d923b5accdcaf8504809de`; this handover commit will be docs-only.
- MASTER #288 is OPEN/DRAFT at `c1500a585b07a5ecb2772bf58bf25c0e9df816e8`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, and the PHX-RELEASE route is reimplementation-review only.
- Experiments #242 `734b89d9...` exact Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) SUCCESS. Experiments #291 `a74b8b94...` exact Windows run [#44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756) SUCCESS; write-privileged publisher and signing steps remain skipped.
- COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT; five workflows remain QUEUED, no combined integration acceptance.
- Canonical private Drive registry v11 and newer corrections remain unavailable through the exposed Library/connector. Older v3-v7 snapshots were not substituted; no private contents were copied.
- Invalid `fd00:db8:blaze::/48` remains a P0 architecture blocker. PHX-MASTER/CORE/COE integration must define the installation-scoped RFC 4193 provisioning/persistence interface before RELEASE changes network UCI.

**Next:** finish inspecting the two board jobs at exact source/test head `aaecb633`; PHX-QA independently review the race and descriptor-open behavior; infrastructure owner provide the authorized disposable no-secret namespace-capable runner. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation changed. No merge, signing, publication, hardware flash, payment migration or customer deployment. Physical 150 power-cut and 30-device/24-hour soak acceptance remain NOT TESTED. **PRODUCTION NO-GO.**


## UTC06 final docs-head CI completion — 2026-11-18T06:20Z

**This addendum supersedes only the in-progress board-job observation above; it does not change the tested source/test SHA.**

- Child PR #35 docs/PR HEAD at this verification: `70593ed9c2ee6272be393b8f2b11b1ec954d86ce`.
- Exact source/test HEAD: `aaecb633102712b471d923b5accdcaf8504809de`.
- Final docs-head shared/firmware run [#44249893147](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44249893147) completed **SUCCESS**: validation job passed 84 packaging/tool tests with two intentional sandbox-only skips; firmware-hardening/shared-contract checks passed; appliance profile staging 10/10 passed; ESP8266 and ESP32 compile/artifact-upload jobs both completed **SUCCESS**.
- Final docs-head case-collision [#44249893268](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44249893268) completed **SUCCESS**.
- Final docs-head mandatory sandbox [#44249893131](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44249893131) completed **FAILURE / FAILED CLOSED**. Host preflight tests 8/8 and unprivileged identity passed; actual bubblewrap namespace setup was denied (`bwrap: setting up uid map: Permission denied`, exit 125). Mandatory sandbox packaging regressions were skipped, not passed.
- Earlier source/test-head shared run [#44249718595](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44249718595) had validation and ESP8266 success, but ESP32 was cancelled by the documentation successor. Only final docs-head run #44249893147 is credited for both board compiles.
- CI board artifacts are synthetic build outputs, not approved target firmware or physical hardware acceptance. No signing, tag, publication, merge, flash, payment migration or customer deployment occurred.
- PR remains OPEN/DRAFT/UNMERGED; independent PHX-QA and PHX-MASTER reviews are still required. Production remains NO-GO.


## UTC07 — immutable Node24 sandbox checkout pin — 2026-11-18T07:12:30Z

**Disposition:** TEST-FIRST RED REPRODUCED / WORKFLOW PIN UPDATED / EXACT-SOURCE SHARED + BOTH BOARD CI PASS / CASE-COLLISION PASS / MANDATORY SANDBOX STILL HOST-BLOCKED / DRAFT / PRODUCTION NO-GO.

This is a release-owned CI maintenance correction on the existing child PR #35. The dedicated ImageBuilder sandbox workflow still used an older immutable checkout commit whose action metadata was not Node24. The upstream immutable commit `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` was inspected directly in `actions/checkout/action.yml` at that exact commit; it declares `runs.using: node24` and its changelog identifies v7.0.1. No tag reference is used.

**Test-first history**
- Regression test commit [`667ff155`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/667ff155c68d4d44a3dbf3993722dab622aaf196) adds `test_workflow_uses_immutable_node24_checkout_action`. It asserts the exact reviewed 40-hex action pin, exact triggering PR/push SHA checkout, `persist-credentials: false`, and rejects mutable `@v*` references.
- Exact RED [#44258083959](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44258083959): shared validation failed exactly at the new assertion because the workflow still used `11bd71901bbe5b1630ceea73d27597364c9af683`; 85 tests ran with one expected failure and two intentional sandbox-only skips. Case-collision passed. The sandbox job also stopped at the failing host-preflight unit test before attempting the namespace probe; no host result is inferred from that RED run.
- Workflow correction commit [`5fe815f9`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5fe815f9e985bf2280b05fb189598826c68a7be6) changes only the checkout action pin to the verified immutable Node24 commit. Exact PR-head ref and `persist-credentials: false` are preserved.

**Exact source/test-head CI at `5fe815f9`**
- Shared/firmware validation [#44258251193](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44258251193): **SUCCESS**. Packaging/tool validation: 85 tests, two intentional sandbox-only skips; all 18 firmware-hardening/shared-contract tests passed; 10/10 appliance profiles passed; ESP32 and ESP8266 compile/artifact-upload jobs both **SUCCESS**.
- Case-collision [#44258251159](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44258251159): **SUCCESS**.
- Mandatory sandbox [#44258251152](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44258251152): **FAILED CLOSED**, not accepted. The 9 host-preflight unit tests passed, including the new Node24 pin assertion; the actual bubblewrap user-namespace probe then failed with `bwrap: setting up uid map: Permission denied`. Mandatory sandbox packaging regressions were skipped. The Node24 pin removes the old checkout runtime; it does not resolve the hosted runner's UID-map restriction.

**Current stack**
- Child PR #35 remains OPEN/DRAFT/UNMERGED, based on parent #31 at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Source/test HEAD for this task: `5fe815f9e985bf2280b05fb189598826c68a7be6`.
- This handover update is documentation-only.
- The child remains a release-owned branch; no parent #31, CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was changed.

**Next:** infrastructure owner supplies an authorized disposable, ephemeral, no-secret runner with unprivileged user namespaces; rerun mandatory sandbox regressions at the exact current PR head. PHX-QA independently reviews the sandbox boundary and new workflow assertion. Keep signing and publishing closed. No merge, real signing, release publication, hardware flashing, payment migration or customer deployment. Physical 150 power-cut and 30-device/24-hour soak acceptance remain NOT TESTED. **PRODUCTION NO-GO.**


**Documentation-head verification at `d8a27af958dd65fc61477a52a2da1d9cab0c05b1`**
- Shared/firmware [#44258725074](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44258725074): **SUCCESS**. 85 packaging/tool tests with two intentional sandbox-only skips; 18 firmware-hardening/shared-contract checks; 10/10 appliance profiles; ESP8266 and ESP32 compile/artifact-upload jobs both **SUCCESS**.
- Case-collision [#44258725104](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44258725104): **SUCCESS**.
- Mandatory sandbox [#44258724895](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44258724895): **FAILED CLOSED** after all 9 host-preflight unit tests passed, including the new action-pin regression. The actual bubblewrap UID-map probe failed with `Permission denied`; mandatory packaging regressions were skipped.
- This addendum is documentation-only; the exact source/test SHA remains `5fe815f9e985bf2280b05fb189598826c68a7be6`. CI firmware artifacts are synthetic outputs, not approved target binaries or physical acceptance.

## UTC09 — reap detached ImageBuilder sandbox process groups — 2026-11-18

**Disposition:** TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / EXACT SOURCE-TEST SHARED CI PASS / 10 OF 10 PROFILES PASS / ESP32 + ESP8266 CI COMPILE AND ARTIFACT UPLOAD PASS / CASE-COLLISION PASS / REAL BWRAP HOST PREFLIGHT STILL BLOCKED / DRAFT / PRODUCTION NO-GO.

### Defect

The runner previously returned success when the ImageBuilder shell leader exited normally without checking whether a detached descendant remained in the per-invocation sandbox process group. The timeout path attempted group termination, but a normal leader exit bypassed that cleanup. A surviving descendant could therefore continue writing inside the writable ImageBuilder bind after the wrapper had returned.

### Test-first and correction history

- Test-first regression commit [`bd953dca`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/bd953dca37a6a905e0d2c89c700bed6c21f4e453) adds two synthetic unit regressions: normal leader exit must terminate and wait for a detached child group; a group that remains after SIGKILL must fail closed.
- Expected RED [#44274660873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44274660873): packaging validation ran 87 tests and failed exactly at the two new assertions; the existing tests passed, with two intentional sandbox-only skips. ESP32/ESP8266 matrix jobs were skipped after validation failed. Case-collision [#44274671560](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44274671560) passed.
- Source correction [`79cd7480`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/79cd748029aecb536caa2e3bcca945948b8e1f25) now terminates and polls both the outer bubblewrap group and inner sandbox child group after normal completion and timeout. It waits for group disappearance within a bounded grace period and fails closed if SIGKILL cannot be confirmed or any group remains.
- Test mock adjustment [`59f88f5b`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/59f88f5bd8568220b73d061a527b518f9b67c787) models already-reaped process groups in the timeout test.
- Deterministic timeout-clock correction [`233a9add`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/233a9adde1f51e73ff5b228d59e058900430d73c) fixes an intermediate test-harness `StopIteration`; it does not change runner behavior.

### Exact source/test-head evidence

Source/test HEAD: `233a9adde1f51e73ff5b228d59e058900430d73c`.

- Push shared/firmware [#44275038491](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44275038491): **SUCCESS**. Packaging/tool suite 87 tests, two intentional sandbox-only skips; both new process-group regressions PASS; all 10 appliance profiles PASS; ESP8266 and ESP32 compile and artifact-upload jobs both PASS.
- PR shared/firmware [#44275051365](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44275051365): **SUCCESS**, same exact head; validation and both board compile/upload jobs PASS.
- PR case-collision [#44275051357](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44275051357): **SUCCESS**.
- An intermediate push run [#44274944632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44274944632) failed in the newly added test's mocked clock because its finite `side_effect` was exhausted. The test clock was made deterministic in `233a9add`; final exact-head push and PR shared runs above passed.

### Mandatory real bubblewrap boundary remains unaccepted

- Push sandbox [#44275038819](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44275038819): **FAILED CLOSED**.
- PR sandbox [#44275051408](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44275051408): **FAILED CLOSED**.
- Host-preflight unit tests: 9/9 PASS; unprivileged identity checks PASS.
- Actual bubblewrap user-namespace probe: FAIL, `bwrap: setting up uid map: Permission denied`, exit 125.
- Mandatory `PHX_REQUIRE_BWRAP=1` packaging regressions were SKIPPED, not passed. The two new regressions are synthetic unit tests in the shared CI suite; they do not establish real bubblewrap sandbox acceptance.

### Current stack and next owner action

- Child PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35) remains OPEN / DRAFT / UNMERGED, stacked on parent #31 at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Exact source/test HEAD: `233a9adde1f51e73ff5b228d59e058900430d73c`; documentation update follows as a separate commit.
- Only release-owned runner, release packaging tests and this handover are in scope. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was changed.
- Next: PHX-QA independently reviews normal-exit/timeout group cleanup; infrastructure owner provides an authorized disposable, no-secret runner with unprivileged user namespaces and reruns the mandatory sandbox tests at the latest exact head.

No merge, signing, tag, publication, firmware flash, payment migration or customer deployment occurred. CI board artifacts are synthetic build outputs, not approved target binaries or physical acceptance. **PRODUCTION NO-GO.**


## UTC10 — forward per-invocation ImageBuilder timeout — 2026-11-18

**Disposition:** TEST-FIRST RED REPRODUCED / FINAL SOURCE-TEST HEAD VERIFIED / BOTH BOARD CI BUILDS PASS / CASE-COLLISION PASS / MANDATORY REAL BWRAP HOST-BLOCKED / DRAFT / PRODUCTION NO-GO.

### Defect

The release-owned sandbox runner already accepted a bounded --timeout-seconds argument from 1–14400 seconds with a 3600-second default. The generated operator wrapper did not forward an operator-selected value, so normal wrapper invocation always used the runner default. The existing mock-wrapper test timeout was a separate test-harness limit and did not exercise this operator-facing runner argument.

### Test-first and implementation history

- Test-first assertion [4cb0709d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4cb0709de2f56bb81e7e99d538a555e696c05daa) requires the generated wrapper to forward PHX_IMAGEBUILDER_TIMEOUT_SECONDS and the runner's default.
- Expected RED, PR shared validation [#44283533005](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44283533005): **FAILED exactly at the new assertion** because the generated wrapper omitted --timeout-seconds. Packaging suite ran 87 tests with one expected failure and two intentional sandbox-only skips. Case-collision [#44283533082](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44283533082) **PASS**.
- Initial source attempt [d5cc76eb](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/d5cc76eb9bd79746aff09fd38a9d10af1fd4cff7) was **not accepted**: the first generated f-string referenced DEFAULT_BUILD_TIMEOUT_SECONDS without importing it, causing a test-time NameError in 29 tests. This implementation error is recorded, not hidden.
- Intermediate correction [7ae6e5da](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/7ae6e5da3fb97dc4a9d53382cd3b861372ed3bbf) restored a literal default.
- Final source correction [99ee1c89](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/99ee1c89a4147b77f468f1570c8b449791451ebd) imports the canonical DEFAULT_BUILD_TIMEOUT_SECONDS from the release runner and emits a quoted timeout argument using the optional operator environment value. The runner remains the authority for the 1–14400-second range. No unquoted shell input, privilege, namespace or fallback behavior was added.

### Exact source/test-head CI

Source/test HEAD: 99ee1c89a4147b77f468f1570c8b449791451ebd.

- PR shared/firmware [#44283880298](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44283880298): **SUCCESS**. Packaging/tool suite: 87 tests, two intentional sandbox-only skips; 18 firmware-hardening/shared-contract checks; 10/10 appliance profiles; ESP8266 and ESP32 compile plus artifact-upload jobs both **SUCCESS**.
- Push shared/firmware [#44283868073](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44283868073): **SUCCESS**, same validation and both board compile/upload jobs **SUCCESS**.
- PR case-collision [#44283880307](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44283880307): **SUCCESS**.
- PR mandatory sandbox [#44283879110](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44283879110) and push sandbox [#44283868013](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44283868013): **FAILED CLOSED** after host-preflight 9/9 and unprivileged identity checks passed. Actual bubblewrap namespace setup failed with “bwrap: setting up uid map: Permission denied”; mandatory packaging regressions were **SKIPPED**, not passed.

### Current stack and next owner action

- Child PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35) remains OPEN / DRAFT / UNMERGED, stacked on parent #31 at 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.
- Exact source/test HEAD: 99ee1c89a4147b77f468f1570c8b449791451ebd; this handover addendum is documentation-only.
- Only tools/package_appliance_firmware.py, tools/test_package_appliance_firmware.py, and this release handover changed for this task. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation changed.
- Next: PHX-QA independently reviews operator timeout forwarding and existing runner bounds; infrastructure owner supplies an authorized disposable, ephemeral, no-secret runner supporting unprivileged user namespaces so mandatory real bubblewrap regressions can run.

No merge, signing, tag, publication, firmware flash, payment migration or customer deployment occurred. CI board builds are synthetic compilation artifacts, not approved OpenWrt images, production binaries or physical acceptance. **PRODUCTION NO-GO.**


## UTC11 — remove privileged Bubblewrap installation from NO-GO workflow — 2026-11-18

**Disposition:** TEST-FIRST RED OBSERVED / FAIL-CLOSED WORKFLOW CORRECTION / SHARED VALIDATION PASS / ESP8266 BUILD PASS / ESP32 BUILD IN PROGRESS AT THIS HANDOVER / CASE-COLLISION PASS / SANDBOX AVAILABILITY BLOCKED / DRAFT / PRODUCTION NO-GO.

### Defect and safe correction

The mandatory ImageBuilder sandbox workflow installed Bubblewrap with sudo apt-get before checking the user-namespace boundary. That privileged runner mutation was unnecessary to determine whether the runner can execute the required sandbox and conflicts with the release boundary: a runner without the dependency must fail closed, not self-modify or acquire a fallback path.

- Test-first commit [9613fba9](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/9613fba973764b0bd42dba0441655d214c7ce101) adds a workflow guard requiring command -v bwrap, rejecting sudo apt-get and any apt-get install bootstrap.
- Expected RED shared CI [#44293811837](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44293811837) failed in Validate appliance firmware packaging & tools because the old workflow still contained the privileged install. This is the intended regression signal; board jobs were skipped after validation failed.
- Workflow correction [e412066c](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e412066c2439e1acb96668fa12b2a5a1bcd9e81d) replaces the installer with a read-only availability/version check. It does not add a download, helper, sudo use, broad UID/GID mapping, namespace fallback, signer, artifact publisher or release action.

### Current exact-head evidence

Source/test HEAD: e412066c2439e1acb96668fa12b2a5a1bcd9e81d.

- Shared/firmware [#44294024317](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294024317): packaging/tool validation **SUCCESS**; ESP8266 compile **SUCCESS**; ESP32 was **IN PROGRESS** when this handover was written and is not credited as pass here.
- Case-collision [#44294024362](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294024362): **SUCCESS**.
- Mandatory sandbox [#44294024223](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294024223): **FAILED CLOSED** at Verify bubblewrap availability (no privileged install). This hosted runner did not provide Bubblewrap. No installation, privileged fallback or mandatory packaging regression execution occurred.

### Next actions and limits

- The infrastructure owner must provide an approved disposable, ephemeral, no-secret runner with Bubblewrap and unprivileged user namespaces enabled; rerun mandatory sandbox regression at the current exact head.
- PHX-QA must independently review the no-sudo workflow guard and the exact-head run once the board matrix becomes terminal.
- PR #35 remains draft and unmerged. CI builds remain synthetic compile outputs; they are not approved target binaries or physical acceptance.

No merge, signing, tag, publication, firmware flash, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


## UTC11 follow-up — standard RELEASE-BLOCKED exit code for missing bubblewrap — 2026-11-18

**Disposition:** TEST-FIRST RED REPRODUCED / WORKFLOW CORRECTION COMMITTED / 89 PACKAGING TESTS PASS / 10-OF-10 PROFILES PASS / ESP32 + ESP8266 CI PASS / CASE-COLLISION PASS / MANDATORY BUBBLEWRAP SANDBOX STILL HOST-BLOCKED / DRAFT / PRODUCTION NO-GO.

### Defect and correction

The release-owned sandbox workflow correctly stopped when Bubblewrap was absent, but it returned shell exit code 1 rather than the runner's documented fail-closed code 125. The existing test-first regression now requires the standard RELEASE-BLOCKED exit code.

- Test-only regression commit 6d9e1d7: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6d9e1d7abab6fce29ebcf0f195290bd9c9f8cc7d adds the exit-125 assertion.
- Expected RED: PR shared/firmware run #44294942295: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294942295 failed exactly in test_workflow_requires_existing_bubblewrap_without_privileged_install: 'exit 125' not found. The packaging suite ran 89 tests, with one expected failure and two intentional sandbox-only skips. Case-collision #44294942334: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294942334 passed.
- Source correction 797ebdc6: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/797ebdc6d70f24aa7c57bbada410695ab854966e changes only the missing-Bubblewrap branch from exit 1 to exit 125, matching run_imagebuilder_sandbox.py:blocked(). The workflow still requires preinstalled Bubblewrap and does not install packages, use sudo, or fall back to unsandboxed execution.

### Exact source/test-head CI

Source/test HEAD: 797ebdc6d70f24aa7c57bbada410695ab854966e.

- PR shared/firmware #44298647518: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44298647518 — SUCCESS: 89 packaging/tool tests, two intentional sandbox-only skips; firmware hardening/shared contracts PASS; 10/10 appliance profiles PASS; ESP8266 and ESP32 compile plus artifact-upload jobs both SUCCESS.
- PR case-collision #44298647593: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44298647593 — SUCCESS.
- PR mandatory sandbox #44298647511: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44298647511 and push sandbox #44298636991: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44298636991 — FAILED CLOSED at the explicit Bubblewrap availability check because the hosted runner does not provide bwrap. The workflow emitted RELEASE-BLOCKED and exit 125 as intended. Host-preflight, namespace and mandatory sandbox packaging regressions were SKIPPED, not passed. No actual bubblewrap boundary validation is claimed.

### Current stack and next owner action

- Child PR #35: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35 remains OPEN / DRAFT / UNMERGED, stacked on parent #31 at 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.
- Source/test HEAD: 797ebdc6d70f24aa7c57bbada410695ab854966e; this handover is documentation-only.
- Scope remains six release-owned paths: sandbox workflow, packager, sandbox runner, host-preflight test, packager test, and narrow release handover. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation changed.
- Next: PHX-INFRA provides an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and unprivileged user namespaces; PHX-QA independently reviews the process-group and fail-closed runner behavior; PHX-MASTER confirms the child stack and ownership boundary.

No merge, signing, tag, publication, firmware flash, payment migration or customer deployment occurred. CI board builds are synthetic compile/artifact outputs, not approved OpenWrt images, production binaries or physical acceptance. PRODUCTION NO-GO.

## UTC12 — reject duplicate appliance isolation VLAN IDs — 2026-11-18

**Disposition:** TEST-FIRST RED REPRODUCED / RELEASE PACKAGER FIX COMMITTED / EXACT SOURCE-TEST PUSH + PR SHARED CI PASS / 10 OF 10 PROFILES PASS / ESP32 + ESP8266 CI COMPILE AND ARTIFACT UPLOAD PASS / CASE-COLLISION PASS / MANDATORY BUBBLEWRAP HOST-BLOCKED / DRAFT / PRODUCTION NO-GO.

### Defect

`generate_network_uci()` validated each `lan`, `guest`, and `vendo` VLAN as an integer in the 802.1Q range, but did not reject duplicate IDs. Duplicate IDs could make separate logical appliance interfaces resolve to the same VLAN device and defeat the profile's intended isolation. All ten current shared appliance profiles were read at the exact child branch and use distinct `lan=1`, `guest=10`, `vendo=20`; no profile JSON or shared schema was changed.

### Test-first and correction

- Test-first commit [`abcaf272`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/abcaf272d3cf5e76f5284a40f8c0ba1ceccd6540) adds negative cases for LAN/guest, LAN/vendo, and guest/vendo collisions.
- Expected RED push [#44302486375](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44302486375) and PR [#44302498387](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44302498387): packaging suite ran 90 tests; all three new duplicate-pair subtests failed exactly because the old generator raised no `ValueError`. Case-collision [#44302498309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44302498309) passed.
- Source correction [`5d79637c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5d79637c66b6cf9093d5191c1f002e057a09f50b) rejects non-distinct validated VLAN IDs before generating UCI. Existing valid profile output is unchanged. No ULA, profile schema, CORE, HARDWARE, or shared interface change was made.

### Exact source/test-head CI

Source/test HEAD: `5d79637c66b6cf9093d5191c1f002e057a09f50b`.

- Push shared/firmware [#44302570990](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44302570990): **SUCCESS**. Packaging/tool suite 90 tests, two intentional sandbox-only skips; all ten appliance profiles PASS; firmware-hardening/shared-contract validation PASS; ESP8266 and ESP32 compile plus artifact-upload jobs both **SUCCESS**.
- PR shared/firmware [#44302585314](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44302585314): **SUCCESS** at the same source/test SHA; validation and both board compile/artifact-upload jobs **SUCCESS**.
- PR case-collision [#44302585278](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44302585278): **SUCCESS**.
- Push mandatory sandbox [#44302570603](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44302570603) and PR mandatory sandbox [#44302585391](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44302585391): **FAILED CLOSED** at the explicit pre-provisioned Bubblewrap availability check because the hosted runner has no `bwrap`; workflow emitted `RELEASE-BLOCKED` and exit 125. Namespace preflight and mandatory bubblewrap packaging regressions were **SKIPPED**, not passed. This is not sandbox acceptance.

### Cross-role coordination and next actions

- PHX-MASTER architecture contract §6.9 treats the RFC 4193 /48 as durable installation/site identity, not a shared hardware-profile constant. The invalid placeholder `fd00:db8:blaze::/48` remains a separate P0. This task deliberately does not guess a replacement or alter first-boot provisioning; PHX-CORE/COE must define the provisioning interface, PHX-RELEASE owns the approved packager/first-boot implementation, and PHX-QA must independently verify it.
- PHX-QA and PHX-MASTER: independently review the duplicate-VLAN admission guard at exact source/test SHA `5d79637c...`; no submitted review is implied by CI.
- PHX-INFRA: provide an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces; rerun the mandatory sandbox regressions at the latest exact PR head.
- COE integration #26 still has five queued workflows and no combined acceptance. Parent #31 and child #35 remain draft and unmerged.

### Current stack and rollback

- Child PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35) remains OPEN / DRAFT / UNMERGED, based on parent #31 at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Source/test HEAD: `5d79637c66b6cf9093d5191c1f002e057a09f50b`; this handover addendum is documentation-only.
- Only release-owned `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, and this handover changed for UTC12.
- Rollback is limited to reverting the source and test commits together; no generated images, profiles, customer devices, payments, signatures, or external state were changed.

CI board outputs are synthetic build artifacts, not approved OpenWrt images, production binaries, or physical acceptance. No merge, signing, tag, publication, firmware flash, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


## UTC13 — reject Makefile-created ImageBuilder output-ancestor symlinks — 2026-11-18

**Disposition:** TEST-FIRST RED REPRODUCED / POST-BUILD OUTPUT-PATH GUARD COMMITTED / EXACT SOURCE-HEAD SHARED CI PASS / 10-OF-10 PROFILES PASS / ESP32 + ESP8266 COMPILE AND ARTIFACT UPLOAD PASS / CASE-COLLISION PASS / MANDATORY BUBBLEWRAP HOST-BLOCKED / DRAFT / PRODUCTION NO-GO.

### Defect

The generated wrapper rejected symlinked `bin/targets/<target>/<subtarget>` components before Makefile execution. However, if a Makefile created a previously absent ancestor (for example, `bin`) as a symlink during the build, the later `find "$IMAGE_REL_DIR"` followed that ancestor. The wrapper could then generate a release checksum manifest from files reached through the redirected path.

The regression uses a disposable ImageBuilder directory and a synthetic Makefile that creates `bin -> redirected-output`, writes a synthetic image below the redirected target path, and requires the wrapper to reject the result before writing `RELEASE_MANIFEST.sha256`. No real firmware is involved.

### Test-first history and correction

- Initial regression commit [30381f11](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/30381f11625660d5a04ac106dd518a18901ff9c5) contained a malformed synthetic Makefile recipe with literal escaped separators. Its first run [#44311869104](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44311869104) failed at the test-harness assertion because the symlink was not created. This was a test-authoring error, not counted as the defect RED.
- Test-harness correction [23837553](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/23837553f3d077206f4e5d0fb714d9f5b6bfaa76) changed the recipe to emit real newline/tab separators.
- Proper expected RED on corrected test head [#44312104147](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44312104147): **91 tests, one failure, two intentional sandbox-only skips**. The new regression failed because the wrapper returned exit 0 and admitted the redirected output. The other packaging tests passed. Case-collision [#44312104137](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44312104137) passed.
- Source correction [2975ae9a](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2975ae9af418a5d831615323cde02e81e2b8f593) rechecks each `bin/targets/<target>/<subtarget>` ancestor for a symlink **after** Makefile execution and before target-directory traversal or manifest generation. It changes only the release-owned packager; the sandbox runner, workflow, profiles, network schema and other subsystem sources are unchanged.

### Exact source/test-head CI

Source/test HEAD: `2975ae9af418a5d831615323cde02e81e2b8f593`.

- PR shared/firmware [#44312279130](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44312279130): **SUCCESS**. Packaging/tool suite **91 tests, two intentional sandbox-only skips**; firmware hardening and shared contracts **PASS**; all **10/10** appliance profile/staging checks **PASS**; ESP8266 compile and artifact upload **SUCCESS**; ESP32 compile and artifact upload **SUCCESS**.
- PR case-collision [#44312279137](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44312279137): **SUCCESS**.
- PR mandatory sandbox [#44312279208](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44312279208): **FAILED CLOSED** at the explicit pre-provisioned Bubblewrap availability check because this hosted runner has no `bwrap`; it emitted `RELEASE-BLOCKED` and exit 125. Host-preflight, namespace and mandatory bubblewrap packaging regressions were **SKIPPED**, not passed. No actual bubblewrap sandbox acceptance is claimed.

### Limits, rollback and next owner action

- The new output-ancestor regression is a synthetic/mock wrapper test in the shared CI suite. It proves the post-build path-admission guard rejects a Makefile-created symlink before manifest creation; it does **not** prove the real bubblewrap boundary, network isolation, host confidentiality or physical hardware acceptance.
- The mandatory sandbox remains blocked until PHX-INFRA supplies an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces. Do not add sudo, uidmap helpers, broad subordinate-ID mappings or an unsandboxed fallback.
- PHX-QA and PHX-MASTER independent review remains required. The current child PR #35 is still OPEN / DRAFT / UNMERGED, based exactly on parent #31 head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Rollback is limited to reverting the source correction and its regression/harness commits together. No profile, generated firmware, external file, release tag, signer, payment or customer state was changed.

No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. CI board outputs remain synthetic compile artifacts, not approved target binaries or physical acceptance. **PRODUCTION NO-GO.**


## UTC14 — pin generated wrapper bootstrap executables and verify sandbox context — 2026-11-18

**Disposition:** TEST-FIRST RED REPRODUCED / WRAPPER INTERPRETER AND HASH TOOL PINNED / SANDBOX CONTEXT VERIFIED BY SOURCE TESTS / TRUSTED BWRAP SEARCH ENFORCED / EXACT SOURCE-HEAD SHARED CI PASS / HOSTED BWRAP ABSENT / DRAFT / PRODUCTION NO-GO.

### Defect and scope

The generated ImageBuilder wrapper resolved `python3` and `sha256sum` through the caller's inherited `PATH`; the sandbox runner and host preflight also resolved `bwrap` without restricting lookup to trusted system directories. A caller could shadow bootstrap tools. Separately, environment markers plus a writable probe file were accepted as evidence of an active sandbox without validating namespace maps or mount boundaries.

This work is limited to release-owned packaging/bootstrap, sandbox runner/preflight, CI and tests. No shared interface, appliance profile, firmware source, networking contract or financial logic was changed.

### Test-first evidence

- Initial PATH-shadow/forged-context/namespace-map tests were added at [`3eadebe5`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3eadebe5bcd16987f142056bed068b8eda38408b). Expected RED: [run #44325545434](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44325545434), 95 tests, 3 failures, 1 error, 2 intentional sandbox-only skips. The failures exposed PATH-selected Python, forged sandbox markers, untrusted Bubblewrap lookup and the missing context verifier.
- Host-preflight trusted-path regression: [`4e6f5ed6`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4e6f5ed6c5c10912ccecb851e808d47f44553fe3); workflow reordered to run pure host tests before the real-host gate at [`4cc3a395`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4cc3a395901f7e7ba632916f453fb1715544e818). Expected RED: [run #44328117809](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44328117809), 97 tests, 4 failures, 1 error, 2 intentional skips; the new host-helper assertion failed because its lookup still used inherited PATH.

### Source corrections

- [`9cf5500b`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/9cf5500bb94ba68bc3cf54ded5e81f9ca16de5bd): add `--verify-context`, single-ID UID/GID map checks, read-only root and required mount checks; constrain runner Bubblewrap lookup.
- [`292fbbce`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/292fbbce718b28df66ee6cb71b0c991383d3c3b9): constrain host preflight Bubblewrap lookup.
- [`00988235`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0098823595c58130bfb0dd7fb6ada98791eedc2e): pin generated wrapper Python interpreter and SHA-256 utility; replace PATH-resolved bootstrap calls.
- Intermediate validation [run #44329073590](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44329073590) exposed an over-strict realpath check for the system `sha256sum` entry. Corrected by [`4968b753`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4968b75355bc84fc7c2cf3c9413870983fae602f), preserving trusted-directory lookup while accepting the system-managed path entry.
- [`6b855313`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6b855313e52da45222b7e96c10aad1b22116c8fb): correct literal probe-name matching.
- [`52489ff1`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/52489ff1059a6043a5291058d4903060ee69f6de), [`d6fd5c7e`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/d6fd5c7e22dd4c34e9501c3a1538c9780dba3851), [`39bb8afd`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/39bb8afd674e33f2c2648fc0e53220ab5ccd252b): restrict workflow/runner/preflight bootstrap resolution to `/usr/bin:/bin`; the wrapper resets subsequent utility PATH to trusted system directories.

### Exact source/test-head CI

Source/test HEAD: `39bb8afd674e33f2c2648fc0e53220ab5ccd252b`.

- Shared/firmware [run #44329453252](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44329453252): **SUCCESS**. Packaging suite **97 tests, 2 intentional sandbox-only skips**; firmware/shared-contract tests **18 PASS**; all **10/10** appliance profiles validated; ESP32 and ESP8266 compile and artifact-upload jobs **SUCCESS**.
- Case-collision [run #44329453498](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44329453498): **SUCCESS**.
- Mandatory sandbox [run #44329453108](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44329453108): host-preflight unit tests **12 PASS**, then **FAILED CLOSED** because Bubblewrap is not installed on the hosted runner (exit 125). Namespace and mandatory real-bubblewrap packaging tests were skipped, not passed.

### Limits, rollback and next owner action

The synthetic tests prove that PATH-shadowed bootstrap tools are not selected, forged markers do not bypass sandbox verification, and the runner rejects an untrusted namespace/mount layout. They do **not** establish real Bubblewrap execution on the hosted runner, network isolation, host confidentiality, physical hardware acceptance or production release readiness.

PHX-INFRA must provide an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces. PHX-QA and PHX-MASTER independent review remains required. Rollback is limited to reverting this release-owned source/test/workflow change set together; no external state, generated firmware, release tag, signer, payment or customer device was changed.

No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. CI board outputs are synthetic compile artifacts, not approved production binaries. **PRODUCTION NO-GO.**



## UTC15 — mask common host-data paths in the ImageBuilder sandbox — 2026-11-18

**Disposition:** TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / EXACT SOURCE-HEAD SHARED CI PASS / CASE-COLLISION PASS / HOSTED BUBBLEWRAP ABSENT / DRAFT / PRODUCTION NO-GO.

### Finding and bounded correction

The runner previously used `--ro-bind / /`. Read-only mounting prevents writes to the host root, but it does not prevent Makefile code from reading files that the invoking host user can read. In particular, host home directories, runtime paths and external mount points may contain credentials or operator data. The sandbox continues to use `--share-net`; network isolation is **not** claimed.

The release-owned runner and host preflight now request writable tmpfs overlays over these common host-data paths after the read-only root bind:

- `/home`
- `/root`
- `/run`
- `/mnt`
- `/media`
- `/srv`

The runner's context verifier requires every listed path to appear in `/proc/self/mountinfo` as a writable `tmpfs` mount before accepting the active sandbox. The host preflight mirrors the same mount arguments. This is a bounded exposure reduction, **not complete host confidentiality**: other host-readable paths remain visible under the read-only root, and networking remains shared. Continue to use only an authorized disposable, ephemeral, no-secret runner.

### Test-first evidence

- Test-only commits: [`1e7eabbd`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/1e7eabbda188a1ba02630edcda99a1104ea0e84f) and [`e9737273`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e973727325dfb54beee01e8180790d6154a161f7).
- Expected RED at test head `e973727325dfb54beee01e8180790d6154a161f7`: PR [#44333542656](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44333542656) and push [#44333530778](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44333530778) failed in the packaging/tool suite as intended. PR log: 99 tests, two intentional sandbox-only skips; the new assertions exposed (1) missing runner mount-argument helper, (2) absent host-preflight tmpfs mounts, and (3) context verifier accepting an exposed `/home` mount.
- Source corrections: [`10cfeaee`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/10cfeaeee64d9af9bc93ea489ade69831bf04964) adds the runner mount list, actual bwrap arguments and mountinfo enforcement; [`4bead9ce`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4bead9ce0590580b316ea1aac960e29d5ce42e02) mirrors the mount list in host preflight.

### Exact source/test-head CI

Source/test HEAD: `4bead9ce0590580b316ea1aac960e29d5ce42e02`.

- PR shared/firmware [#44333732485](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44333732485): **SUCCESS** — 99 packaging/tool tests with two intentional sandbox-only skips; firmware/shared-contract checks **18 PASS**; appliance profiles **10/10 PASS**; ESP32 and ESP8266 compile plus artifact-upload jobs **SUCCESS**.
- Push shared/firmware [#44333720922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44333720922): **SUCCESS** — same validation and both board compile/artifact-upload jobs **SUCCESS**.
- Case-collision [#44333732378](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44333732378): **SUCCESS**.
- Mandatory sandbox PR [#44333732558](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44333732558) and push [#44333720962](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44333720962): **FAILED CLOSED** because Bubblewrap is not installed on the hosted runner (exit 125). Host-preflight unit tests **13 PASS**; unprivileged identity, namespace probe and mandatory real-bubblewrap packaging regressions were **SKIPPED**, not passed.

### Limits, rollback and next owner action

These tests establish the requested command arguments and the source-level mountinfo rejection behavior. They do **not** establish that Bubblewrap actually mounted these paths on a real runner, that every host-readable file is hidden, that network egress is isolated, or that hardware/production acceptance occurred.

Rollback is limited to reverting the two source corrections and their two regression commits together. No profile, firmware, shared API, hardware, financial state, release tag, signer, external operator file or customer device was changed.

PHX-INFRA must provide an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces. PHX-QA and PHX-MASTER independent review remains required. No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


## UTC16 — close staging-directory symlink race — 2026-11-18

**Disposition at handover edit:** TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / EXACT-SOURCE CI PENDING / MANDATORY BUBBLEWRAP HOST-BLOCKED / DRAFT / PRODUCTION NO-GO.

### Finding

`_ensure_staging_directory()` used path-based `mkdir()` followed by `lstat()`. A directory entry could be replaced with a symlink after the stat result but before the next child `mkdir()`. The next path-based operation could then create a configuration directory through the external symlink target. This was inconsistent with the release packager's existing `dir_fd` / `O_NOFOLLOW` file-write and source-copy helpers.

### Test-first evidence

- Regression commit: [`f03fd99a`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/f03fd99a0ca857fc06f7a1aed9baaa3a4f868941).
- Exact expected RED: [PR shared run #44344908980](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44344908980), validation job `134944563025`. The new `test_ensure_staging_directory_rejects_parent_swapped_to_symlink_during_walk` failed exactly with `AssertionError: ValueError not raised`. Packaging suite: **100 tests**, two intentional sandbox-only skips, one expected failure. The test creates an operator-owned sentinel and proves the old path-based directory walk does not reject the raced symlink.
- Case-collision [#44344909114](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44344909114): **SUCCESS**.
- Mandatory sandbox [#44344908972](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44344908972): **FAILED CLOSED** because Bubblewrap is not installed on the hosted runner (exit 125). Host-preflight unit tests **13 PASS**; namespace and mandatory real-bubblewrap packaging tests **SKIPPED**, not passed.

### Source correction

- Source commit: [`2a9d2e98`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2a9d2e98f7d1fd9955ece4a237eb78b0addd9476).
- `_ensure_staging_directory()` now opens the staging root through the existing no-symlink parent-descriptor walker, creates/opens each child relative to the pinned parent descriptor, and compares the no-follow directory entry's device/inode with `fstat()` on the opened descriptor before continuing. It fails closed on symlink/non-directory entries, path replacement, or unavailable POSIX descriptor primitives.
- The generated path is still returned for existing callers; subsequent file writes continue to use the separate no-follow descriptor helper. No router profile, network contract, CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was changed.
- The first post-fix run [#44345101904](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345101904) exposed a **test-fixture error**, not a packager defect: the fixture's `mock.patch` replacement for `os.open` was not present in `os.supports_dir_fd`, so the existing capability guard correctly rejected the mocked function before the race could execute. The fixture-only correction is [`611e3bcca4d3e7a7c4c7df99bcc34aabb3c3e476`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/611e3bcca4d3e7a7c4c7df99bcc34aabb3c3e476), which adds the patched callable to the test-only capability set; production capability checks remain unchanged.

### Exact source/test-head validation

Final source/test HEAD: `611e3bcca4d3e7a7c4c7df99bcc34aabb3c3e476`.

- Shared/firmware [run #44345441736](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345441736): **SUCCESS**. Packaging/tool suite **100 tests, 2 intentional sandbox-only skips**; firmware-hardening/shared-contract checks **18 PASS**; appliance profiles **10/10 PASS**; ESP8266 and ESP32 compilation plus artifact-upload jobs **SUCCESS**.
- Case-collision [run #44345441853](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345441853): **SUCCESS**.
- Mandatory sandbox [run #44345441940](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345441940): **FAILED CLOSED** because Bubblewrap is not installed on the hosted runner (exit 125). Host-preflight unit tests **13 PASS**; unprivileged identity, namespace probe and mandatory real-bubblewrap packaging regressions were **SKIPPED**, not passed.

The shared/firmware result is synthetic CI and source-level validation only. The ESP board outputs are compile artifacts, not approved production binaries or physical acceptance. The mandatory Bubblewrap boundary remains unverified on an authorized runner.

### Cross-repository and provenance check

- MASTER #288 exact PR head: `18cd5064f0b0682bb50b8c53b145cb0fd356ea0d`; role assignment keeps PHX-RELEASE on Phoenix-specific build/signing workflows, packaging and manifests. `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`; the Experiments workflow route is reimplementation-review, not a copy/move instruction.
- Experiments #242 head `734b89d9e7792247e8376335c3f3685500ab3f89`; exact current-head Windows run #40882814472 is reported SUCCESS.
- Experiments #291 head `ed3565395bd70c4de696e49a84f0bb454efebc8b`; exact current-head Windows run #44328674893 is reported SUCCESS; publisher remains SKIPPED. The historical `CHANGE_LEDGER.md` provenance hold remains for MASTER/QA reconciliation.
- COE integration #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows remain QUEUED with no combined integration acceptance.
- COE parent #31 head/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; prior shared/firmware #44222517238 and case-collision #44222517258 passed; mandatory sandbox #44222517263 failed closed at hosted UID-map permission denial.
- The exact private Drive registry v11 was not surfaced by the available Library/connector search. Older v6/v7 snapshots were visible but were not substituted. No private Drive identifiers or contents were copied to GitHub.

### Limits and next actions

The new regression and source fix are source-level packaging hardening only. They do not prove a real Bubblewrap mount namespace, network isolation, complete host confidentiality, ImageBuilder binary reproducibility, physical hardware acceptance or production release readiness.

PHX-INFRA must provide an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces. PHX-QA and PHX-MASTER must independently review the exact source/test head. Keep PR #35 OPEN / DRAFT / UNMERGED. No merge, signing, tag, publication, hardware flash, payment migration or customer deployment. **PRODUCTION NO-GO.**

## PHX-RELEASE 2026-11-18 UTC17 — pin initial rootfs copy to staging directory descriptor

**Disposition:** TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / SOURCE-TEST SHARED CI PASS / BOARD BUILDS PARTLY PENDING / MANDATORY BUBBLEWRAP HOST-BLOCKED / DRAFT / PRODUCTION NO-GO.

### Control plane, ownership and selected defect

Live #172, cleanup-first #266, MASTER #288 ownership routes, Experiments release PRs #242/#291, COE integration #26, parent packager #31 and child #35 were re-read before source changes. #35 remains the existing release-owned child branch stacked on #31; no new branch was created. The exact child base is #31 head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.

`stage_overlay()` previously checked that the requested output parent was not a symlink, then called path-based `shutil.copytree(source_rootfs, staging_dir, symlinks=True)`. Replacing the parent with a symlink after the check but before copytree redirected the initial rootfs copy into an external operator-owned directory. A later no-follow helper rejected the path, but only after the external directory had already been created and populated.

### Test-first progression

- Initial regression commit: [a54f7a14](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a54f7a14e2e4556e8759977276126a32417094af). Its first run [#44357255948](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357255948) exposed an over-specific assertion-message mismatch: the existing later helper raised a different `ValueError` after the redirected copy. This was a test-authoring failure, not a passing regression.
- Test assertion correction: [947864db](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/947864dbc258a6bcef14768a12f1664d1f08c0b6).
- Expected RED at exact test head: shared validation [#44357449644](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357449644) and duplicate PR validation [#44357429634](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357429634) both failed at the new assertion that the external staging directory must not exist. The runner confirmed it **did** exist after the parent swap. The suite ran **101 tests**, one expected failure and two intentional sandbox-only skips. Case-collision [#44357449403](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357449403) passed.
- The two RED-head mandatory sandbox runs [#44357449505](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357449505) and [#44357429641](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357429641) failed closed because Bubblewrap was not installed; host preflight passed **13/13**, while namespace and real sandbox tests were skipped.

### Source correction and compatibility coverage

- Source fix: [462d02fb](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/462d02fb01e689556efcf5bf1019af951807b130).
- Compatibility regression: [91691a37](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/91691a377af5fa4251c0f4695dbf4c4484305f83) verifies that missing output-parent directories are still created safely.

The packager now opens or creates parent components one at a time with directory descriptors and `O_NOFOLLOW`, creates the new staging root relative to the pinned parent descriptor, and copies the rootfs through `/proc/self/fd/<staging-fd>` rather than the operator-visible path. It reopens the visible parent after the copy and compares device/inode identity, then verifies the staging entry still matches the pinned directory. On failure it removes only the staging directory whose entry still matches the descriptor it created; it does not follow or delete a replacement symlink.

The helper preserves the prior behavior of creating missing parent directories. It requires POSIX `dir_fd`/directory no-follow support and an accessible Linux `/proc/self/fd`; it fails closed if those primitives are unavailable. No firmware profile, networking/VLAN contract, shared API, financial ledger, source ownership route or other subsystem was changed.

### Exact source/test-head CI

Final source/test HEAD: `91691a377af5fa4251c0f4695dbf4c4484305f83`.

- Push shared/firmware [#44358097407](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44358097407), validation job `134991644751`: **SUCCESS**. Firmware/shared-contract checks **18 PASS**; packaging/tool suite **102 tests, 2 intentional sandbox-only skips**; appliance profiles **10/10 PASS**.
- PR shared/firmware [#44358115225](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44358115225), validation job `134991695337`: validation **SUCCESS** with the same source/test suite.
- Case-collision [#44358114424](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44358114424): **SUCCESS**.
- At handover authoring, both exact-head ESP8266 compile/artifact jobs had **SUCCESS**; the exact-head ESP32 core installation was still **IN_PROGRESS**, and ESP32 compile/upload were **PENDING**. Do not infer a final board result from the shared validation job.
- Mandatory sandbox push [#44358097367](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44358097367) and PR [#44358114284](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44358114284): **FAILED CLOSED** because Bubblewrap is not installed on the hosted runner (exit 125). Host preflight **13/13 PASS**; unprivileged identity, namespace probe and real-bubblewrap packaging regressions were **SKIPPED**, not passed.

These are hosted synthetic CI and source-level results only. ESP compile artifacts are not approved production binaries or physical hardware acceptance. No real ImageBuilder sandbox acceptance, network isolation, firmware flashing, signing or release publication is claimed.

### Cross-repository provenance and limits

- MASTER #288 current head at audit: `dacde8ba60bd47e4d549d4000a1e37b5409e4a9f`; ownership routes remain `DRAFT_REVIEW_ONLY`, and the PHX-RELEASE Experiments workflow route is reimplementation-review only. No workflow or source migration was performed.
- Experiments #242 head `734b89d9e7792247e8376335c3f3685500ab3f89`; exact Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) **SUCCESS**.
- Experiments #291 head `691ed55dbe39a79a88eac45f6eebff81cee5e628`; exact Windows run [#44353380470](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44353380470) **SUCCESS**; `publish-release` **SKIPPED**. No signer or publisher executed.
- COE integration #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows remain queued with zero jobs and no combined integration acceptance.
- COE parent #31 head/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 is still OPEN / DRAFT / UNMERGED.
- The canonical private Drive registry v11 was not available through the current Library/connector search. Only a prior metadata pointer was visible; no older registry snapshot was substituted and no private contents were copied to GitHub.

### Rollback and next owner actions

Rollback is a normal revert of source commit `462d02fb` and its regression commits `91691a37`, `947864db`, and `a54f7a14` in reverse order; no force-push is required. Keep PR #35 draft and unmerged.

PHX-INFRA must provide an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces. PHX-QA must independently review the exact source/test head and regression. PHX-MASTER must confirm ownership/interface routing; the COE integration owner must resolve the five queued #26 workflows; the registry custodian must restore authorized v11 provenance access; repository administration must independently verify protected release admission.

No PR merge, real signing, tag, release publication, hardware flash, payment migration or customer deployment occurred. Independent protected signer/freshness witness, durable financial accounting and migration, independent QA/MASTER approval, approved target binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. **PRODUCTION NO-GO.**


## PHX-RELEASE 2026-11-18 UTC18 — descriptor-safe staging permission normalization

**Disposition:** TEST-FIRST RED REPRODUCED / SOURCE FIX COMMITTED / EXACT SOURCE + BOTH BOARD CI PASS / CASE-COLLISION PASS / MANDATORY BUBBLEWRAP HOST-BLOCKED / OPEN DRAFT / PRODUCTION NO-GO.

### Control plane, ownership and current exact refs

Live #172 and cleanup-first #266 were re-read before source changes. The sole PHX-RELEASE UTC18 role-lock/checkpoint is [#172 comment 6987447368](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-6987447368); it was claimed before the regression commit. MASTER PR #288 was re-read at 1cc0d1ac45a9696349d369abff878022cad315e2; OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY. PHX-RELEASE's Experiments workflow route is reimplementation-review only. No shared interface, hardware networking, source migration or ownership route was changed.

- Experiments #242: head 734b89d9e7792247e8376335c3f3685500ab3f89; exact Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) SUCCESS. Signing steps and GitHub Release publication were SKIPPED.
- Experiments #291: head 691ed55dbe39a79a88eac45f6eebff81cee5e628; exact Windows run [#44353380470](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44353380470) SUCCESS; publish-release SKIPPED.
- COE integration #26: head b382d233ff06c8791b1028bed3c617cc7b670d12; eight exact-head workflows (five PR events, three push events) remain QUEUED with zero completed jobs. No integration acceptance exists.
- COE parent packager #31: head/base 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.
- COE child #35: branch phoenix/release-build-script-publication-safety-20261117; source/test head b8aa8dc7fec4e12694acf1314555e88c8b0e6cbf; base remains #31 head above. PR remains OPEN / DRAFT / UNMERGED.
- The canonical private Drive project registry v11 was not available in the current Library search. No older registry was substituted and no private registry contents were copied into GitHub.

### Defect reproduced

stage_overlay() normalized staging permissions with a path-based os.path.islink() check followed by path-based os.chmod(). A staged file or directory could be replaced with a symlink between those operations, causing chmod to change an external operator-owned target. A hardlink inserted before normalization could also expose an external inode to a mode change.

### Test-first progression and source correction

- Regression commit [b9ab8dc](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b9ab8dc442adb75ad8954420b3d3941221db6381) added file- and directory-symlink race tests.
- Expected RED: push [#44368864845](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44368864845), job 135029882697, and PR [#44368879189](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44368879189), job 135029936557, failed in the packaging suite. The exact two new tests failed because the injected replacement reached the old path-based chmod window. Push log: 104 tests, 2 failures, 2 intentional sandbox-only skips. This was the expected RED, not a test-fixture failure.
- Source correction [fd9e77c](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/fd9e77c4ebf1987de1839b225c587ee3f9beab6b).
- Hardlink regression [b8aa8dc](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b8aa8dc7fec4e12694acf1314555e88c8b0e6cbf) verifies that a staged executable hardlinked to an external file is atomically replaced before its mode changes; the external inode remains 0644 and both resulting inodes have link count 1.

The final implementation:
- Opens parent components without following symlinks and pins the final directory/file with O_NOFOLLOW.
- Compares the no-follow directory entry's device/inode with fstat() of the opened descriptor.
- Uses fchmod() on the pinned directory descriptor, not a path-based chmod.
- For files whose mode differs, reads the pinned regular file and atomically replaces the staging entry with a fresh private temporary inode. The temporary starts at 0600; the requested final mode is applied with fchmod() before rename/publication. This avoids changing an external hardlink's inode mode.
- Skips symlink entries and fails closed for unexpected non-regular entries or changed paths.

No firmware profile, VLAN/network contract, financial ledger, hardware source, shared API, signer, release tag or publisher was changed.

### Exact source/test-head CI

Final source/test HEAD: b8aa8dc7fec4e12694acf1314555e88c8b0e6cbf.

PR-triggered exact-head runs:
- Shared/firmware [#44369463493](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44369463493), validation job 135032153329: SUCCESS. Packaging/tool suite 105 tests, 2 intentional sandbox-only skips; firmware hardening/shared contracts 18 checks PASS; appliance profiles 10/10 PASS.
- ESP32 build job 135032299536: SUCCESS; compile and artifact upload PASS.
- ESP8266 build job 135032299570: SUCCESS; compile and artifact upload PASS.
- Case-collision [#44369463171](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44369463171): SUCCESS.

Push-triggered exact-head runs:
- Shared/firmware [#44369446947](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44369446947), validation job 135032092056: SUCCESS with the same 105 tests / 2 intentional skips, 18 checks, and 10/10 profiles.
- ESP8266 job 135032217320: SUCCESS; compile and artifact upload PASS.
- ESP32 job 135032217335: SUCCESS; compile and artifact upload PASS.

Mandatory sandbox remains blocked, not passed:
- PR [#44369463028](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44369463028), job 135031984069: host-preflight unit tests PASS; Bubblewrap availability failed because bwrap is not installed; unprivileged identity, namespace probe and mandatory Bubblewrap packaging regressions SKIPPED.
- Push [#44369446996](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44369446996), job 135031924134: same fail-closed result.
- The separate host preflight suite passed 13/13. No actual Bubblewrap sandbox acceptance is claimed.

These are hosted synthetic CI and source-level results. ESP board compile artifacts are not approved production target binaries and do not constitute physical hardware acceptance.

### Rollback, review and next owner actions

Rollback is a normal revert, without force-push, in reverse order: hardlink regression b8aa8dc, source correction fd9e77c, and symlink regressions b9ab8dc. Keep PR #35 OPEN / DRAFT / UNMERGED.

- PHX-QA: independently review exact source/test HEAD b8aa8dc7fec4e12694acf1314555e88c8b0e6cbf, especially no-follow descriptor checks and atomic mode replacement.
- PHX-INFRA: provide an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces; rerun mandatory sandbox validation at the exact candidate.
- PHX-MASTER: confirm release ownership and coordinate the integration blockers; no shared interface changed in this task.
- COE integration owner: unblock the eight queued #26 exact-head workflows and establish per-file provenance.
- Registry custodian: restore authorized read-only access to canonical private registry v11.
- Repository administrator: independently verify branch protection and required release checks.

No PR merge, production signing, tag, release publication, hardware flash, real payment migration or customer deployment occurred. Protected signer, independent freshness witness, durable accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. PRODUCTION NO-GO.


## PHX-RELEASE 2026-11-19 UTC01 — race-safe overlay size accounting

**Disposition:** TWO-DIRECTION TEST-FIRST RED REPRODUCED / FINAL SOURCE FIX COMMITTED / EXACT PR + PUSH SHARED CI PASS / ESP32 + ESP8266 COMPILE AND UPLOAD PASS / CASE-COLLISION PASS / MANDATORY BUBBLEWRAP SANDBOX BLOCKED / OPEN DRAFT / PRODUCTION NO-GO.

### Control plane, ownership and live provenance

Before source changes, PHX-RELEASE re-read #172, cleanup-first #266, MASTER draft #288 and its current `REPOSITORY_ROUTING.md` / `OWNERSHIP_ROUTES.json`, Experiments #242/#291 and COE #26/#31/#35/#44. The single UTC01 role lock is [#172 comment 6996553323](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-6996553323); this same comment is the final checkpoint and is updated in place.

- MASTER #288: current head `acebbb23276d592b3a735e9bc29b59049a27995e`; ownership manifest remains `DRAFT_REVIEW_ONLY`. The release workflow route is `reimplementation-review`, not copy authorization. No ownership manifest, shared interface, hardware-networking contract or migration route was changed.
- Experiments #242: exact head `734b89d9e7792247e8376335c3f3685500ab3f89`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) SUCCESS. Signing and GitHub Release publication were skipped.
- Experiments #291: exact head `26e138acf2fbbb8890103fa1cfe2469e8efdd6ba`; BlazePwifi build [#44432976878](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44432976878) SUCCESS. Windows run [#44432976880](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44432976880) FAILED in PISONET-owned `tests/ReleaseSigning/negative-selftest.ps1`: `$buildWorkflow` is uninitialized under StrictMode. Publisher was SKIPPED; PHX-RELEASE did not edit this path.
- COE integration #26: exact head `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows remain queued with zero completed jobs; no integration acceptance exists.
- COE release parent #31: exact head/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- COE release child #35: branch `phoenix/release-build-script-publication-safety-20261117`, base #31 above; current source/test head `5e25e4ceab7c0615bcdad8309d50739e6b255f46`; remains OPEN / DRAFT / UNMERGED.
- COE ULA child #44: exact head `582fd5d5e83e36b36546ac28534740298ba94af4`; still based on the earlier #35 head `1a5be48d2845781b0b07bad39a37f8440cea4d4f`, not rebased onto current #35. No ULA/site-networking or shared-interface decision was changed.
- Canonical private Drive project registry v11 was not returned by the Library search; no Google Drive connector was exposed in this run. Historical v4-v7 snapshots appeared but were deliberately not substituted. No private registry content was copied to GitHub.
- The branch-protection API read returned 403 to the connector; no repository settings were changed. The current MASTER control plane still reports missing protected-ref admission evidence.

### Defect and regression coverage

The old `calculate_overlay_size()` used path-based `os.walk()`, `os.path.islink()` and `os.path.getsize()`. A regular staged file could be replaced by a symlink after the path check, causing the external target to be followed and counted. Conversely, a symlink could be replaced by a regular file after classification and be silently skipped, undercounting the flash budget.

Two deterministic regressions now cover both directions:
1. Regular file replaced by symlink before the no-follow open: external target is not followed or counted; external bytes remain unchanged.
2. Symlink replaced by regular file before the no-follow open: the new staged regular file is counted, rather than being silently skipped; external target remains unchanged.

### Test-first and implementation history

- First regression [e200833](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e20083381cb4cf875088146b7345286e4de19ef8). Expected RED: PR [#44435063672](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44435063672), shared validation FAILED with the new check-to-use regression (`ValueError not raised`); 106 tests, one expected failure, two intentional sandbox-only skips.
- Initial descriptor-walk attempt [5cb89e0](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5cb89e0dbb0c1dcf928042f6f8c83dbd48565680) failed host capability detection because the hosted Python runtime did not advertise fd-based `os.scandir` support; PR [#44435203597](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44435203597) FAILED.
- The next attempt [a752b99](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a752b9956fdc797e3f52d6486a0070505d0c9263) had an indentation error; PR [#44435285512](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44435285512) FAILED before importing the packaging tests.
- Descriptor traversal switched to fd-based `os.listdir`; the first follow-up [90c3664](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/90c36645a8eafc68752979638fc694eff6cca0b1) still rejected the hosted runtime's `supports_fd` identity set; PR [#44435343057](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44435343057) FAILED at preflight.
- Removing that redundant capability-set check exposed a test-fixture issue: patching `os.open` changed its identity in `os.supports_dir_fd`. PR [#44435497827](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44435497827) FAILED at the capability preflight. Fixture correction [546e1fb](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/546e1fbe100eb2718e77d7fbd4b4783cfa3156c0) preserved the original fd capability set while injecting the race.
- The first one-direction implementation passed at that intermediate head, but a second test was added to cover symlink-to-regular replacement. Regression commit [3513e82](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3513e82583e318fb6c8b2f37bfd50bd43e88a054) produced expected RED on PR [#44436345907](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44436345907): 107 tests, one failure, two intentional skips; the old implementation skipped the replacement file before opening it.
- Initial `O_PATH` implementation [7e04a55](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/7e04a55c339958ddee33ba6b068f76275ae22b57) still compared against a pre-open path stat and rejected both replacement directions; PR [#44436424277](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44436424277) FAILED with two regression failures. Test semantics were then corrected in [e3d0923](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e3d09232722b61b7c5aedcc422c00948f9765646).
- Final source correction [5e25e4c](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5e25e4ceab7c0615bcdad8309d50739e6b255f46) opens each entry first with Linux `O_PATH|O_NOFOLLOW`, obtains metadata from `fstat()`, then verifies the directory entry still refers to that opened inode using `stat(..., dir_fd=..., follow_symlinks=False)`. Symlinks are skipped only after their own inode is pinned; regular file size comes from the opened object; directories are separately opened with `O_DIRECTORY|O_NOFOLLOW` and compared to the pinned inode. All descriptors are closed on success and failure. The function fails closed when required Linux/POSIX descriptor primitives are unavailable.

### Final exact source/test-head CI

Source/test HEAD: `5e25e4ceab7c0615bcdad8309d50739e6b255f46`.

PR-triggered:
- Shared/firmware [#44436769990](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44436769990): SUCCESS. Packager/tool suite **107 tests, two intentional sandbox-only skips**; firmware/shared-contract checks **18/18 PASS**; appliance profiles **10/10 PASS**.
- ESP32 job 135267565544: SUCCESS; compile and artifact upload PASS. Artifact ID 14488078924; artifact ZIP SHA-256 `61439eff5fd8e49f1f8449f76a37a5169155c5b2ff3fbf582a5e83b3bb5ddb04`.
- ESP8266 job 135267565362: SUCCESS; compile and artifact upload PASS. Artifact ID 14489492095; artifact ZIP SHA-256 `e2f3dd9c12714fd214347cbfbbc355c10ccab8cbc8ff0619112b582a375b3857`.
- Case-collision [#44436769921](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44436769921): SUCCESS.

Push-triggered:
- Shared/firmware [#44436760346](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44436760346): SUCCESS with the same 107 tests / two intentional skips, 18 checks and 10/10 profiles.
- ESP32 job 135267520344: SUCCESS; compile and artifact upload PASS. Artifact ID 14488603152; artifact ZIP SHA-256 `59ac9e895efccd84daaa7ff6fccc883be404bdb36c37fe0989f8725e33d50c22`.
- ESP8266 job 135267520367: SUCCESS; compile and artifact upload PASS. Artifact ID 14487804361; artifact ZIP SHA-256 `437b8e463d576ecf7ad6de357029761ccba60c70f2576889e5d453d40400d61a`.

Mandatory sandbox remains blocked, not passed:
- PR [#44436769949](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44436769949) and push [#44436760369](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44436760369): host preflight 13/13 PASS; Bubblewrap is absent; both fail closed with exit 125. Namespace/identity and actual Bubblewrap packaging regressions were SKIPPED. No unsandboxed fallback was used.

The listed SHA-256 values are **GitHub Actions artifact-ZIP digests**, not per-firmware binary checksums. PR and push ZIP digests differ (including ESP32 artifact sizes differing by six bytes); no byte-reproducible firmware claim is made. These are hosted CI compile artifacts, not approved production target binaries or physical hardware evidence. CI also emitted upstream ESP8266 `elf2bin.py` invalid-escape warnings and Node `punycode`/`url.parse` deprecation warnings; these did not fail the builds.

### Rollback, review and next owners

Rollback is by normal revert on PR #35 only, in reverse order: source correction 5e25e4c, test semantics e3d0923, initial O_PATH attempt 7e04a55, reverse-race regression 3513e82, earlier source/test iterations 90c3664 / a752b99 / 5cb89e0 / 4f97799 / 546e1fb / e200833. Do not force-push or merge.

- PHX-QA: independently review exact source/test HEAD `5e25e4ceab7c0615bcdad8309d50739e6b255f46`, especially O_PATH semantics, post-open inode check, symlink accounting and flash-budget calculation.
- PHX-INFRA: provide an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces; rerun mandatory sandbox validation at the exact candidate.
- PHX-PISONET: repair `$buildWorkflow` initialization in #291's `tests/ReleaseSigning/negative-selftest.ps1`; RELEASE did not edit this owner path.
- PHX-MASTER: reconcile current #35/#44 ancestry and keep migration/ownership routes review-only; no shared interface or hardware-networking contract changed here.
- COE integration owner: unblock the five queued #26 exact-head workflows and establish per-file source/destination provenance.
- Registry custodian: restore authorized read-only access to canonical private Drive registry v11.
- Repository administrator: verify protected branch/ruleset admission and required release checks; no repository settings were changed.

No PR merge, production signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer, independent freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. **PRODUCTION NO-GO.**


### UTC01 final documentation-head CI completion — 2026-11-19T01:33Z

This addendum supersedes the earlier in-progress documentation-head board-job observation in the PHX-RELEASE UTC01 checkpoint. It does not change the source/test SHA or upgrade any artifact to production status.

- Child PR #35 documentation/PR HEAD: `4074d37cbe5233eb982233def52e7a4b6b65d4b0`; base parent #31: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- PR shared/firmware run [#44437315555](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44437315555) completed SUCCESS: validation job `135269332332` PASS; packager/tool suite 107 tests with two intentional sandbox-only skips; firmware/shared checks 18/18 PASS; appliance profiles 10/10 PASS; ESP8266 job `135269431126` and ESP32 job `135269431312` both PASS including compile and artifact upload.
- Push shared/firmware run [#44437306358](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44437306358) completed SUCCESS; validation and both ESP board compile/artifact-upload jobs PASS.
- PR case-collision [#44437315434](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44437315434) completed SUCCESS.
- PR mandatory sandbox [#44437315442](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44437315442) FAILED CLOSED: host preflight 13/13 PASS; Bubblewrap is absent and the job exits 125. Unprivileged identity, namespace setup and mandatory sandbox packaging regressions were SKIPPED. No unsandboxed fallback was used.

These are hosted synthetic CI and compile artifacts only. Artifact ZIP digests are not per-firmware binary checksums; no byte-reproducibility, approved OpenWrt ImageBuilder target binary, physical hardware acceptance or production release is claimed. PR #35 remains OPEN / DRAFT / UNMERGED.


## PHX-RELEASE UTC03 — deterministic COE firmware toolchain pins

**Delegation:** PHX-MASTER BLAZE-COMMS/1 task `PHX-MASTER-UTC02-COE35-ESP32-TOOLCHAIN-DRIFT` (control-plane refs #172/#266/#288/#26/#35/#44/#327). Scope is release CI and its guard only; no firmware, shared interface, networking, PISONET, CORE, QA or MASTER source was changed.

**Branch/source identity at implementation:** COE PR #35 branch `phoenix/release-build-script-publication-safety-20261117`, base parent PR #31 at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; source/test head `3b83a408583091f2b2e8a7cf4ef73833f2eb9e39`. Compare against #31: 103 commits ahead / 0 behind. PR #35 remains OPEN / DRAFT / UNMERGED. The current source-side reference is Experiments PR #291 at `fe940216e9e250b5df48c633b669ef3dd34fb299`; its `.github/workflows/blazepwifi-build.yml` blob is `b10101a0ed18b361566baa40ef4319c576067390`. That source workflow pins Arduino CLI 1.6.0, ESP8266 core 3.1.2 and ESP32 core 3.3.13. Source run [#44440710888](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44440710888) passed its firmware build, v0.4 simulation and Android emulator jobs; production signing/import/publish jobs were skipped. Separate Windows run [#44440710823](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44440710823) failed in the PISONET-owned negative self-test and is not attributed to this toolchain task.

**Release-owned changes:**
- `.github/workflows/hardware-ci.yml`: pin checkout to `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1), Arduino CLI setup to `arduino/setup-arduino-cli@b3cda96fddef6af6c56b4c5efb5c47e2357935db` (signed Node24 upstream commit), and artifact upload to `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9` (v7.0.2). Checkout uses `persist-credentials: false`.
- Both board jobs request Arduino CLI `1.6.0`, verify `arduino-cli version` at runtime, install exactly `esp8266:esp8266@3.1.2` and `esp32:esp32@3.3.13`, then verify the installed package version from `arduino-cli core list` before compilation.
- Added `tools/test_release_toolchain_pins.py`: four guards check exact action identity/counts, CLI setup version and runtime guard, exact board-core pins/runtime checks, and absence of floating core-install commands.

**Test-first history (all runs are exact commit refs):**
- Initial guard commit [`08e3932`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/08e3932be45f59cb3520d58126d73e813fee28c8). Run [#44450070728](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44450070728) failed while importing the new test module because the first regex literal was over-escaped; this is a test-authoring error, not product evidence.
- Regex correction [`41053af`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/41053af51bb22c7ce244d3c05b7d589c1eb0ce2a). Run [#44450170893](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44450170893) then reproduced the intended RED: four assertions failed because the old workflow still used mutable action tags and floating Arduino board-core installs.
- Workflow correction [`398a914`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/398a914202a1f5c351a45f86ae64f84a8b8a9f24) added the exact pins and runtime checks. Run [#44450264038](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44450264038) left one test-only mismatch: the guard expected literal `Version: 1.6.0`, while the workflow correctly contains the escaped shell regex `Version: 1\\.6\\.0`.
- Final assertion correction [`3b83a408`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3b83a408583091f2b2e8a7cf4ef73833f2eb9e39) matches the workflow's literal regex.

**Exact source/test-head CI at `3b83a408583091f2b2e8a7cf4ef73833f2eb9e39`:**
- Shared/firmware run [#44450399556](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44450399556): validation job `135312614791` SUCCESS; 112 tools/packaging tests passed with two intentional sandbox-only skips; 18 shared-contract tests passed; firmware-hardening checks passed; all 10 appliance profiles staged successfully. ESP32 job `135312725263` SUCCESS (Arduino CLI 1.6.0, ESP32 core 3.3.13, compile and artifact upload pass). ESP8266 job `135312725283` SUCCESS (Arduino CLI 1.6.0, ESP8266 core 3.1.2, compile and artifact upload pass).
- Case-collision run [#44450399688](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44450399688): SUCCESS.
- Mandatory sandbox run [#44450399466](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44450399466): FAILED CLOSED at `bwrap` availability (not installed; exit 125). Host preflight passed 14/14; identity/namespace and real Bubblewrap packaging regressions were skipped, not passed. No privileged installation or unsandboxed fallback.

**Evidence limits:** This is hosted CI/toolchain-version verification and compile-artifact evidence only. The Arduino package index/archive bytes are not independently checksum-locked by this change; exact version pins do not prove byte-for-byte reproducibility. No OpenWrt ImageBuilder production image, target-router run, physical hardware acceptance, signer-positive test, release publication or customer deployment is claimed.

**Stack/control-plane reconciliation:** MASTER PR #288 remains OPEN/DRAFT at `49a508b90d01b1d314484786b5f2fb45962498cf`; `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`. Its release source route remains `.github/workflows/blazepwifi-build.yml` → COE `.github/workflows/pisowifi-ci.yml` as reimplementation-review; no route or migration manifest was changed. The UTC02 MASTER delegation above specifically authorizes this bounded COE #35 CI toolchain correction. COE #26 remains at `b382d233ff06c8791b1028bed3c617cc7b670d12` with five workflows QUEUED / zero jobs. COE #31 remains parent `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. COE #44 remains a separate older ULA child at `582fd5d5e83e36b36546ac28534740298ba94af4`, based on prior #35 head `1a5be48d2845781b0b07bad39a37f8440cea4d4f`; no rebase, force-push or merge was performed. Cleanup-first issue #266 remains OPEN and is a coordination checklist, not proof of all-role cleanup completion.

**Private provenance:** Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available in the authorized Library search; no Google Drive connector was exposed. No older registry snapshot was substituted and no private file content was copied into this repository.

**Next owners:** PHX-QA independently reviews the exact pinned toolchain/workflow and the unsigned action provenance if any future pin changes; PHX-HARDWARE owns firmware compatibility changes; PHX-INFRA provides the approved disposable Bubblewrap-capable runner; COE integration owner unblocks #26 and completes file/license/test provenance; PHX-MASTER reconciles #35/#44 stack and current control-plane refs; registry custodian restores authorized v11 access.

**Disposition:** PR #35 remains OPEN / DRAFT / UNMERGED. No merge, signing, tag, publication, hardware flashing, financial migration or customer deployment. **PRODUCTION NO-GO.**

## PHX-RELEASE UTC05 — profile input no-follow admission

**Status at source/test head `cf80b938bdc6ab06bb84a3a129b66a634222916d`: release-owned fix committed; shared validation PASS; ESP8266 PASS; ESP32 still running at this checkpoint; mandatory sandbox remains blocked.**

**Scope:** `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, this handover only. Existing COE child PR #35 remains OPEN / DRAFT / UNMERGED on `phoenix/release-build-script-publication-safety-20261117`, base parent #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was changed.

### Defect and bounded correction

`load_profile()` previously used path-based `os.path.isfile()` followed by ordinary `open()`. It followed a final profile-file symlink and a symlinked parent directory. A profile path could therefore resolve to content outside the intended regular profile file after the existence check.

- Test-first commit [`c971ffd5`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/c971ffd5a1428dcf7cd6ec021466a706477a874a) added final-file symlink and parent-directory symlink negative cases plus a regular custom-JSON-path positive control.
- Expected RED [#44464576853](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464576853): validation failed exactly at the two new symlink assertions (`ValueError not raised`); 115 tests ran, 2 intentional skips, 2 expected failures. The regular custom JSON path control passed.
- Case-collision [#44464576846](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464576846): SUCCESS.
- Source correction [`cf80b938`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/cf80b938bdc6ab06bb84a3a129b66a634222916d): preserve profile-ID and explicit custom-JSON-path behavior, open via the existing descriptor-walk helper with `O_NOFOLLOW`, reject symlinked parent components, and require the opened descriptor to identify a regular file before JSON parsing.
- Source/test-head shared run [#44464722316](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464722316): validation job `135359632933` SUCCESS; 115 packaging/tool tests PASS with 2 intentional skips; 18 shared-contract checks PASS; 10 appliance profiles PASS. Both new symlink regressions and the regular custom-path control passed. ESP8266 job `135359719732` SUCCESS. ESP32 job `135359719719` was still IN_PROGRESS at handover preparation and is not credited as passed.
- Source/test-head case-collision [#44464722413](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464722413): SUCCESS.
- Mandatory sandbox [#44464722305](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464722305): FAILED CLOSED because Bubblewrap is not installed (exit 125) after 14/14 host-preflight tests passed. Namespace setup and sandbox-dependent packaging regressions were SKIPPED, not passed. No privileged installation or unsandboxed fallback was used.

### Limits and review

This is release-input path integrity evidence from hosted CI. It does not establish ImageBuilder sandbox acceptance, real OpenWrt binaries, signing, router behavior or physical acceptance. Explicit custom JSON paths remain supported when they resolve to regular files without symlink components; symlinked profile paths are intentionally rejected.

**Next:** reconcile terminal ESP32 status and verify the final documentation-head Actions runs; PHX-QA independently review the no-follow profile loader and its input compatibility. PHX-INFRA still owns the approved disposable Bubblewrap-capable runner. Keep #35 draft/unmerged and production NO-GO.
