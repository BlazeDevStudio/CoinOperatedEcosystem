## PHX-RELEASE UTC14 — rollback interrupted rootfs staging copy (2026-11-22)

**Disposition:** one RELEASE-owned staging-recovery defect was reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**. This increment changes only the packager, its regression test and this handover.

### Live control plane and ownership

- Read live BLAZE-COMMS/1 control plane #172, cleanup-first issue #266, this handover, MASTER PR #288 and the requested release/integration PRs.
- MASTER #288 current head: `b7c6bb66d5603447d06fb8559c61457ee587c372`; PR remains OPEN / DRAFT / UNMERGED, all 169 changed paths under `coordination/phoenix/`. `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`; PHX-RELEASE's Experiments workflow route is `reimplementation-review`, not migration authorization.
- Experiments #242 exact head: `734b89d9e7792247e8376335c3f3685500ab3f89`, draft. Its Windows build/handover run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) passed; signing/publication remain unproven.
- Experiments #291 exact head: `42797e2f3d65c30a1070caf49c93aebec149d897`, draft with 26 mixed-owner paths (21 RELEASE / 3 CORE / 2 PISONET). Compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at handover freshness. Downstream signing/publication were skipped. RELEASE did not modify #291.
- COE integration #26 remains FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows queued / zero jobs. Parent #31/base is `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- COE child #35 branch is `phoenix/release-build-script-publication-safety-20261117`; it remains based on #31. The inherited `.github/workflows/hardware-ci.yml` path is outside this task and remains untouched.

### Confirmed defect and correction

`_copy_rootfs_to_new_staging_directory()` creates and pins a new staging directory, then copies the ImageBuilder rootfs through `/proc/self/fd/<staging_fd>`. Its rollback handler caught only `Exception`. If rootfs copying was interrupted by `KeyboardInterrupt` or `SystemExit`, the handler did not run; the partial staging directory remained and a later retry would be refused as an existing output.

The correction catches `BaseException` only around the rollback boundary. It removes the partial tree only after confirming that the operator-visible name still identifies the same pinned directory. If the directory was not pinned, was replaced, disappeared, or cleanup itself fails, it refuses path-based deletion and raises an explicit `Rootfs staging rollback could not be confirmed` error chained to the original interruption. A replacement symlink/directory is never deleted.

### Test-first lineage

- Regression test commit [`9975711d`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/9975711daaba6a48292c9829275de2250e824b0d) added deterministic partial-copy interruption cases for both `KeyboardInterrupt` and `SystemExit`.
- Expected RED: shared workflow [#45032763075](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45032763075), job `137239762353`: **185 tests ran, 2 failures / 2 intentional skips**. Both new cases failed because the partial staging destination still existed after interruption. This was a product-defect reproduction, not a fixture/setup failure.
- Source correction [`cea8ec21`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/cea8ec21197f20084bcecc626a23447b9c106353) adds interruption-safe, identity-pinned rollback and explicit failure reporting.

### Exact-source Actions at `cea8ec21`

- PR shared/firmware [#45033026495](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45033026495), validation job `137240591702`: packaging/tool suite **185 PASS / 2 intentional skips**; firmware hardening, shared contracts and manifest durability marker **PASS**. The next all-profile admission **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority is undefined. ESP32/ESP8266 compile jobs were **SKIPPED**; overall workflow **FAILURE**, not green.
- PR sandbox [#45033026468](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45033026468), job `137240591615`: host-preflight suite **33/33 PASS**; Bubblewrap is absent, exit 125. Namespace verification and mandatory sandbox packaging regressions were **SKIPPED**, not passed.
- PR case-collision [#45033026523](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45033026523): **PASS**.

These are hosted synthetic CI results. No real Bubblewrap namespace, ImageBuilder build, firmware artifact, approved target binary or physical hardware test was produced.

### Remaining blockers and next owners

1. PHX-QA independently reviews source/test SHA `cea8ec21`, especially BaseException rollback and replacement-path preservation.
2. PHX-INFRA supplies an authorized disposable no-secret runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces.
3. PHX-CORE / PHX-MASTER establish approved site-scoped RFC 4193 ULA /48 authority; no synthetic prefix is substituted.
4. PHX-MASTER reconciles its control-plane PR-head index and resolves inherited `hardware-ci.yml` ownership with HARDWARE; RELEASE does not edit that workflow.
5. Registry custodian restores authorized provenance-only access to canonical private Drive registry v11. No older registry snapshot is substituted.

#35 independent submitted reviews remain zero at the start of this increment. Cleanup-first #266 remains OPEN / 0 of 7 tracks complete. No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.

---

## PHX-RELEASE UTC21 — reject hard-linked firmware output admission (2026-11-19)

**Disposition:** one release-owned packaging admission defect reproduced test-first and fixed on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Control plane, ownership and exact heads

- Read the live BLAZE-COMMS/1 control plane #172, cleanup-first issue #266, the owner's `06_RELEASE_ENGINEERING(1).txt`, and MASTER PR #288.
- MASTER #288 exact head: `e0e499b4fd8f1e6ae3b15c7a22e3fa12559daf10`; route manifest blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`. PHX-RELEASE owns Phoenix-specific build/signing workflow files, packaging and manifests, not every workflow or other roles' runtime source.
- Experiments #242 remains `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 exact head `3bffd9d14de42abf2c2f6079632e0348127ad025`. #291 has 16 changed paths including CORE/PISONET-owned files; its latest commit changes only CORE handover paths. RELEASE did not edit or append to that mixed-owner branch.
- COE #26 exact head `b382d233ff06c8791b1028bed3c617cc7b670d12`; parent #31 exact head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; active release child #35 branch `phoenix/release-build-script-publication-safety-20261117`.
- COE #35 base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; source/test head `6f007699a513e46d6d45bfca6693d91c02c03b5e`; docs head follows this entry.
- COE #44 ULA installer draft remains separate at `582fd5d5e83e36b36546ac28534740298ba94af4`, based on older #35 head `1a5be48d2845781b0b07bad39a37f8440cea4d4f`. It was not rebased or modified; ULA provisioning is a shared hardware/networking contract requiring CORE/MASTER approval.

### Confirmed defect and correction

The generated ImageBuilder wrapper already rejected stale firmware images, symlink entries, empty images and symlinked output ancestors. It still admitted a regular `.bin` or `.img.gz` file with `st_nlink > 1`. A Makefile could hard-link a cached file outside `bin/targets/<target>/<subtarget>` into the expected output tree; the existing `find -type f` checksum scan then wrote a release manifest for the aliased payload.

New test `test_generated_wrapper_denies_hardlinked_firmware_output` creates a cache file inside the disposable ImageBuilder tree, hard-links it into the target output directory, asserts identical inode / link count 2, preserves the cache bytes, and requires no `RELEASE_MANIFEST.sha256`.

- Test-first commit: [`8cd598ce`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8cd598ce48c299ecdf4195e05b115718fa29fe7d).
- Expected RED: [PR validation #44617273391](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617273391), job `135889225770`: 118 tests, 2 skips, exactly one failure in the new test. The wrapper returned 0 and wrote `RELEASE_MANIFEST.sha256` for `hardlinked.bin`; the new assertion correctly exposed the admission gap.
- Source correction: [`6f007699`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6f007699a513e46d6d45bfca6693d91c02c03b5e). The wrapper now rejects firmware candidates with `find ... -links +1` before empty-file validation and checksum-manifest creation.

### Exact-source Actions at `6f007699`

- PR [hardware/shared validation #44617526950](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617526950), validation job `135890107114`: packaging/tool suite **118 tests PASS, 2 intentional skips**. The next all-profile staging step **FAILED BY DESIGN**: all 10 profiles were rejected because the approved site-scoped RFC 4193 ULA /48 authority remains unset. ESP8266 and ESP32 compile jobs were skipped. Overall workflow is **FAILURE**, not green.
- Push [hardware/shared validation #44617513890](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617513890), validation job `135890063056`: same exact-source result — 118 tests PASS / 2 skips; 10/10 profiles fail closed at the missing ULA authority; board compile jobs skipped.
- PR [ImageBuilder sandbox #44617527410](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617527410) and push [#44617513983](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617513983): host preflight **14/14 PASS**; Bubblewrap is not installed (exit 125); namespace checks and mandatory sandbox packaging regressions were skipped. No privileged install or unsandboxed fallback was used.
- Case-collision guard [#44617527377](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617527377): **PASS**.

No firmware artifact was produced. No profile was admitted, no board compilation was run, and no signing or publication occurred.

### Remaining blockers and next owners

1. PHX-CORE / COE integration: define the durable site-scoped ULA authority and approved source; do not substitute the synthetic test prefix.
2. PHX-MASTER: approve the ULA provisioning interface and decide how the older-base #44 draft is reconciled with current #35.
3. PHX-QA: independently review the hard-link admission regression and exact source SHA.
4. PHX-INFRA: provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged user namespaces.
5. PHX-RELEASE: continue from the docs head after this entry; do not repeat the hard-link test/fix.

The canonical private Drive project registry v11 was not available through the authorized Library search surface; no older snapshot was substituted and no private contents were copied to GitHub.

No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was modified. No PR was merged, no release was tagged/published, and no signing, hardware flashing, payment migration or customer deployment occurred. Physical 150-power-cut and 30-device/24-hour acceptance remain **NOT TESTED**. **PRODUCTION NO-GO**.

---

## PHX-RELEASE UTC18 — preserve the unconfigured production site-ULA default

**Disposition:** one release-owned regression guard added on the existing COE #35 draft branch. No production prefix, network configuration, profile schema, ImageBuilder behavior, or shared interface was changed. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Control plane and exact ownership

- BLAZE-COMMS/1 control plane #172 remains FULL (7 roles); cleanup-first issue #266 was reread. No assignment or ownership route was changed.
- MASTER PR #288 head at inspection: `3b910343ea25ac93ecb417c3ea29cb2d09c84f00`. `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`; PHX-RELEASE's workflow route remains reimplementation-review only.
- COE PR #35 branch: `phoenix/release-build-script-publication-safety-20261117`; parent #31/base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Exact source/test commit: `6bd286daa3f62bde48b37d5807a23bd960f03ae5`. Test file blob after the change: `174ea7133b1a8672db7c8fe66a57a6465692faba`.
- Experiments #242 remains `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 current head at inspection: `a17f270ef5560e4fada4e9ef7ca4ea5ed03fbf28`. COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`.

### Regression guard

The packager intentionally leaves `APPROVED_SITE_ULA_PREFIX = None` until CORE/COE establish a durable site-prefix authority and MASTER approves the provisioning contract. The existing test class normally patches a synthetic `fd12:3456:789a::/48` fixture so profile-generation tests can exercise UCI output.

New test `test_production_default_site_ula_remains_unconfigured_and_fails_closed` temporarily stops that fixture, asserts the actual module default is still `None`, and verifies `generate_network_uci()` raises the approved-site-prefix error. The fixture is restarted in `finally`. The synthetic prefix remains test-only and is not an assigned or deployable site prefix.

Commit: [`6bd286d`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6bd286daa3f62bde48b37d5807a23bd960f03ae5).

### Exact-source Actions at `6bd286d`

- Shared/firmware [#44585692690](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44585692690): job `135777868782` **FAILED BY DESIGN AT PROFILE ADMISSION**. The packager/tool suite ran **117 tests: PASS, 2 intentional skips**. `validate_all_profiles.py` then rejected all 10 appliance profiles because no approved site-scoped RFC 4193 ULA /48 is configured. ESP32 and ESP8266 compile jobs were skipped after profile admission failed. No appliance firmware artifact was produced.
- Case-collision [#44585692646](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44585692646): **SUCCESS**.
- Mandatory ImageBuilder sandbox [#44585692890](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44585692890): **FAILED CLOSED** with exit 125 because Bubblewrap is not installed on the hosted runner. Host-preflight unit suite **14/14 PASS**; namespace execution and sandbox-dependent packaging regressions were skipped, not passed. No privileged or unsandboxed fallback was used.

The shared run is not an overall success: the 117 unit tests passed, but the required all-profile admission gate correctly blocked every profile.

### Other live release and integration CI

- Experiments #291 BlazePwifi run [#44581603752](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44581603752): **SUCCESS**. ESP32 compatibility [#44581603620](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44581603620): **SUCCESS** for cores 3.3.13 and 4.0.0. Windows run [#44581603605](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44581603605): **FAILURE** in PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is uninitialized; exact .NET SDK 8.0.425 and package-parity checks passed, Windows build/publisher did not pass. No PISONET file was changed.
- COE #26 exact head `b382d233ff06c8791b1028bed3c617cc7b670d12`: five workflows remain QUEUED with zero executed jobs; no integrated acceptance.
- COE parent #31 exact head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 remains stacked on it. The ULA site authority and actual Bubblewrap-capable runner remain separate blockers.
- Canonical private Drive project registry v11 was not available through the authorized Library search/connector surface in this activation. No older snapshot was substituted; no private identifiers or contents were copied into GitHub.

### Next owners and limits

1. PHX-CORE / COE integration owner: define the durable site-scoped ULA authority and exact provisioning source; preserve same-site sharing, distinct-site separation, and persistence across reboot/upgrade/backup/restore.
2. PHX-MASTER: approve the shared provisioning interface before any profile schema or CLI input is introduced.
3. PHX-QA: independently review the default-unset regression and later verify site-prefix vectors and persistence.
4. PHX-INFRA: provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged user namespaces.
5. PHX-PISONET: repair the uninitialized `$buildWorkflow` in its own negative self-test; RELEASE does not edit it.

No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was changed. No workflow migration, merge, signing, tag, publication, hardware flashing, payment migration or customer deployment occurred. Hosted CI is synthetic evidence only. Approved production binaries, protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, 150 physical power cuts and 30-device/24-hour soak remain unproven. **PRODUCTION NO-GO.**

---

## PHX-RELEASE UTC14 — site ULA packager fail-closed admission (2026-11-19)

**Disposition:** release-owned guard implemented test-first; unit suite PASS; all-profile packaging deliberately BLOCKED until PHX-CORE/COE select and supply an approved site-scoped prefix. PR #35 remains OPEN / DRAFT / UNMERGED / PRODUCTION NO-GO.

### Authority and exact source

- MASTER coordination PR #288 current head at inspection: `37fd3ed542e9b4924d5a0a0c7ece976c9c23f227`; `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`. Release workflow migration remains `reimplementation-review`; this task did not migrate or modify workflows.
- MASTER Architecture Contracts §6.45 at head `37fd3ed542e9b4924d5a0a0c7ece976c9c23f227`, blob `0dc116bdcaea3f49a4884f75dc9cba71913b3cd8`, explicitly requires packagers to fail closed until an approved site-scoped RFC 4193 ULA /48 is supplied. Prefix authority is undecided.
- COE child PR #35 branch `phoenix/release-build-script-publication-safety-20261117`, base parent #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Exact source/test head: `90ce4200b66ce0b55f40feaab42cc7b53fad1f2d`. Packager blob `f17b653f79ffd80177453dc98842983bcd37a116`; test blob `1dbccc8ed276d29feaaf6fefc707915bb8ca2900`.

### Defect and bounded correction

The packager emitted the invalid literal `fd00:db8:blaze::/48` without validation. It is not a valid IPv6 prefix. The release-owned correction:

- Removes the vendor literal and leaves `APPROVED_SITE_ULA_PREFIX = None` intentionally.
- Validates a supplied value with strict `ipaddress.IPv6Network` parsing, requires a /48 inside `fd00::/8`, and rejects multicast, link-local, global-unicast and unspecified addresses.
- Refuses to generate network UCI when no approved site prefix is configured.
- Does not invent a prefix, add a profile/CLI field, select a provisioning authority, alter UCI/VLAN/bridge behavior, or change CORE/COE/HARDWARE networking interfaces.
- Existing unit tests use `fd12:3456:789a::/48` only as a synthetic test fixture. It is not an assigned site prefix and must never be used for deployment.

### Test-first history

- Test-only commit [`16d9c23b`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/16d9c23b7ef8683ca7caca96f3a91ffcf667ad92).
- Expected RED: [push run #44542358476](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44542358476), packaging/tool suite ran 116 tests, 10 expected failures, 2 intentional skips. The new guard failed because the old generator neither rejected missing/invalid prefixes nor emitted the test-supplied prefix. The run is a regression reproduction, not a pass.
- Source correction [`8ea5c927`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8ea5c9276b6096fd99198f549ac0baf98801bfd4).
- Test-vector correction [`90ce4200`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/90ce4200b66ce0b55f40feaab42cc7b53fad1f2d) keeps negatives aligned with §6.45 (missing, malformed, non-/48, non-ULA classes, and host bits); no extra restriction on otherwise syntactically valid Global ID values was invented.

### Exact-source Actions at `90ce4200`

- Push shared validation [#44542912289](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44542912289): **OVERALL FAILURE BY DESIGN AT PROFILE ADMISSION**. Firmware-hardening checks PASS; shared-contract suite 18/18 PASS; packager/tool suite **116 tests PASS, 2 intentional skips**. The subsequent `validate_all_profiles.py` step rejected all 10 profiles with `An approved site-scoped RFC 4193 ULA /48 is required`. ESP32 and ESP8266 jobs were skipped because profile validation failed. No appliance staging or firmware artifact was produced.
- PR shared validation [#44542927405](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44542927405): same exact-head result; unit suites pass, all-profile staging fails closed, board jobs skipped.
- Case-collision guard [#44542927518](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44542927518): **SUCCESS**.
- Mandatory sandbox push [#44542912278](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44542912278) and PR [#44542927374](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44542927374): **FAILED CLOSED** because `bwrap` is not installed (exit 125). Host preflight 14/14 PASS; identity/namespace and sandbox-dependent packaging regressions SKIPPED, not passed. No privileged or unsandboxed fallback.

### Cross-repository state and next owners

- Experiments #291 exact head `4e3d954a89835fff54463d456c278eeb5f70b056`: ESP32 core compatibility run [#44538815283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44538815283) PASS on both 3.3.13 and 4.0.0; BlazePwifi build [#44538815114](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44538815114) SUCCESS; Windows run [#44538815094](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44538815094) FAILS at PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is unset; Windows build/publisher do not pass.
- Experiments #242 remains at `734b89d9e7792247e8376335c3f3685500ab3f89`; historical exact-head Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) passed handover/build; signing and publication were skipped.
- COE #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; eight workflows (five PR, three push) remain queued with no jobs returned.
- COE parent #31 remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; its previous sandbox runs failed at unprivileged UID-map setup. Child #35's current sandbox failure is specifically missing pre-provisioned Bubblewrap.
- Canonical private Drive registry v11 was not available through the authorized Library surface; no older snapshot was substituted and no private content copied to GitHub.

**Next actionable owner tasks:**
1. PHX-CORE + COE integration owner choose and document the durable site-prefix authority and exact approved-prefix supply mechanism; preserve same-site sharing, distinct-site separation, and persistence across reboot/upgrade/backup/restore.
2. PHX-MASTER approve the shared interface/contract before any profile schema or CLI input is introduced.
3. PHX-QA independently verify valid/invalid prefix vectors, same-site sharing, distinct-site separation, persistence/restore, and authority-unavailable denial.
4. PHX-INFRA provide an authorized disposable runner with pre-provisioned Bubblewrap and unprivileged namespace support.
5. PHX-RELEASE rerun exact-head packager/profile validation only after the approved prefix mechanism exists; do not bypass the fail-closed admission.

No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was modified. No merge, signing, tagging, publication, hardware flashing, payment migration or customer deployment occurred. Physical 150 power cuts and 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO.**

---

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

**Status at source/test head `cf80b938bdc6ab06bb84a3a129b66a634222916d`: release-owned fix committed; shared validation, ESP32 and ESP8266 all completed PASS; mandatory sandbox remains blocked.**

**Scope:** `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, this handover only. Existing COE child PR #35 remains OPEN / DRAFT / UNMERGED on `phoenix/release-build-script-publication-safety-20261117`, base parent #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was changed.

### Defect and bounded correction

`load_profile()` previously used path-based `os.path.isfile()` followed by ordinary `open()`. It followed a final profile-file symlink and a symlinked parent directory. A profile path could therefore resolve to content outside the intended regular profile file after the existence check.

- Test-first commit [`c971ffd5`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/c971ffd5a1428dcf7cd6ec021466a706477a874a) added final-file symlink and parent-directory symlink negative cases plus a regular custom-JSON-path positive control.
- Expected RED [#44464576853](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464576853): validation failed exactly at the two new symlink assertions (`ValueError not raised`); 115 tests ran, 2 intentional skips, 2 expected failures. The regular custom JSON path control passed.
- Case-collision [#44464576846](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464576846): SUCCESS.
- Source correction [`cf80b938`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/cf80b938bdc6ab06bb84a3a129b66a634222916d): preserve profile-ID and explicit custom-JSON-path behavior, open via the existing descriptor-walk helper with `O_NOFOLLOW`, reject symlinked parent components, and require the opened descriptor to identify a regular file before JSON parsing.
- Source/test-head shared run [#44464722316](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464722316): validation job `135359632933` SUCCESS; 115 packaging/tool tests PASS with 2 intentional skips; 18 shared-contract checks PASS; 10 appliance profiles PASS. Both new symlink regressions and the regular custom-path control passed. ESP8266 job `135359719732` SUCCESS; ESP32 job `135359719719` subsequently completed SUCCESS.
- Source/test-head case-collision [#44464722413](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464722413): SUCCESS.
- Mandatory sandbox [#44464722305](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44464722305): FAILED CLOSED because Bubblewrap is not installed (exit 125) after 14/14 host-preflight tests passed. Namespace setup and sandbox-dependent packaging regressions were SKIPPED, not passed. No privileged installation or unsandboxed fallback was used.

### Limits and review

This is release-input path integrity evidence from hosted CI. It does not establish ImageBuilder sandbox acceptance, real OpenWrt binaries, signing, router behavior or physical acceptance. Explicit custom JSON paths remain supported when they resolve to regular files without symlink components; symlinked profile paths are intentionally rejected.

**Next:** reconcile terminal ESP32 status and verify the final documentation-head Actions runs; PHX-QA independently review the no-follow profile loader and its input compatibility. PHX-INFRA still owns the approved disposable Bubblewrap-capable runner. Keep #35 draft/unmerged and production NO-GO.

### UTC05 terminal documentation-head verification

The earlier in-progress observation above is superseded by these terminal results; source/test SHA and implementation did not change.

- Documentation head `cad128e466cec4f85a5f54475b5589a43be6d373`: [shared/firmware run #44465017354](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465017354) completed with all three jobs SUCCESS. Validation job `135360596076` passed 115 packaging/tool tests (2 intentional skips), 18 shared-contract checks and 10/10 profile staging; ESP8266 job `135360681427` and ESP32 job `135360681558` both completed compile and artifact upload successfully.
- Documentation-head case-collision [#44465017348](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465017348): SUCCESS.
- Documentation-head mandatory sandbox [#44465017311](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465017311): FAILED CLOSED with `RELEASE-BLOCKED: bubblewrap is not installed on this runner`, exit 125. Host preflight 14/14 PASS; identity/namespace and sandbox packaging regressions were SKIPPED, not passed.

No real ImageBuilder sandbox execution or production image was produced.


## PHX-RELEASE UTC21 — Atomic checksum-manifest publication

**Scope:** Release-packager child draft PR #35, based on release-packager parent PR #31 at 59ed44d0b911e176f1a95b9cf5585ef811ffd31b. No merge or publication.

### Defect and correction

The generated ImageBuilder wrapper previously redirected sort output directly to RELEASE_MANIFEST.sha256. If sort emitted partial output and then failed, the wrapper exited nonzero but left a partial file at the final manifest path.

The wrapper now:
- writes sorted output to RELEASE_MANIFEST.sha256.sorted.tmp;
- refuses a pre-existing temporary sorted manifest;
- creates the final manifest only after successful sorting, using a same-directory no-overwrite hard link;
- leaves a failed temporary file for diagnosis and refuses an unsafe retry until the operator uses a clean ImageBuilder workspace.

A synthetic failing sort regression writes PARTIAL-CHECKSUM and exits 42. It proves the final manifest is absent on failure.

The regression also exposed a runner-status defect: _communicate_with_timeout previously treated any normal stderr containing RELEASE-BLOCKED: as a sandbox cleanup failure. It now recognizes only process-group cleanup diagnostics. This preserves ordinary fail-closed wrapper exit status while retaining the detached-process-group kill checks.

### Source and test commits

- Test-first manifest regression: 9655317f21d318b205c5200feb5017a442374831
- Atomic manifest publication: 28df88c2053af77a42b8023bf8888d59ac78e9df
- Runner diagnostic-classification regression: 5f1c9a5ff5f54a8e539ca41e469c90a222c594f5
- Cleanup-diagnostic classification fix: e1f5a57ba76cb0032ecf3250ae5204e9bb30d72c

### Exact-source CI evidence

- Expected RED, test-only head 9655317f: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44818832035. test_generated_wrapper_does_not_publish_partial_manifest_when_sort_fails failed because the partial final manifest existed.
- Intermediate implementation run https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44818972955: new manifest regression passed; an existing final-manifest symlink assertion needed to be updated for the new hard-link refusal diagnostic.
- Runner-classifier RED, test-only head 5f1c9a5: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819549527. The new test proved ordinary RELEASE-BLOCKED stderr was incorrectly classified as cleanup failure.
- Final source head e1f5a57: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819619526. Packaging/tools suite: 120 tests passed, 2 skipped. Both new regressions and the existing final-manifest symlink test passed.
- PR exact-head validation: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819630196. Overall workflow failed later at all-profile staging because an approved site-scoped RFC 4193 ULA /48 is not defined. This is a MASTER/network-authority blocker, not a packaging-test failure.
- Mandatory sandbox: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819629850. Host preflight passed; Bubblewrap was unavailable in trusted system directories, so identity mapping, namespace preflight and sandboxed packaging were skipped. No unsandboxed fallback was used.
- Case-collision guard: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819630026 — PASS.

### Evidence boundary and next owners

All packaging regression execution above is hosted CI with synthetic ImageBuilder output and a fake sort; it is not a real firmware build, hardware test, production binary, or release acceptance.

Next actions:
1. PHX-INFRA: provide an approved runner with Bubblewrap available in a trusted system directory and unprivileged user namespaces enabled.
2. PHX-MASTER / network authority owner: define and approve the site-scoped ULA /48 contract before all-profile staging can pass.
3. PHX-QA: independently review the manifest publication and runner cleanup-classification changes.
4. PHX-MASTER: reconcile child PR #35 with parent #31 and the integration route; keep both drafts unmerged pending review.



### UTC21 docs-head follow-up

The intermediate source-head run [#44819173752](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819173752) failed the packaging suite because the runner treated the wrapper's ordinary RELEASE-BLOCKED final-manifest collision diagnostic as a process-group cleanup failure (return code 124). The new partial-manifest regression itself passed. This was the second defect fixed by the cleanup-marker classifier change.

The test-only runner-classifier RED [#44819549527](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819549527) reproduced that false classification. After the fix, the source-head packaging suite [#44819619526](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819619526) passed 120 tests with 2 skipped.

The handover commit then triggered current docs-head checks:
- PR validation [#44819874655](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819874655): packaging/tools tests PASS (120 passed, 2 skipped); all-profile staging FAIL because the approved site-scoped ULA /48 is missing.
- Mandatory sandbox [#44819875058](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819875058): host preflight PASS; Bubblewrap availability FAIL; unprivileged identity, namespace and sandboxed packaging steps SKIPPED.
- Case-collision guard [#44819874610](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44819874610): PASS.

No real ImageBuilder build was run. The only passing packaging evidence is the synthetic CI regression suite; all-profile firmware staging and the mandatory sandbox remain blocked.


## PHX-RELEASE UTC04 — persist generated build-script execute mode (2026-11-21)

**Disposition:** one release-owned durability defect reproduced test-first and fixed on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Defect and bounded correction

`generate_build_script()` wrote and flushed the generated script, called `fsync()`, and only then applied mode `0755` with `fchmod()`. The file contents were synced, but the executable-mode metadata change had no subsequent sync. A crash after the function returned could therefore leave the script non-executable after recovery even though generation had reported success.

A new regression records the filesystem call order and requires `fsync → fchmod(0755) → fsync`. The release-owned generator now performs a second `fsync()` after `fchmod()`, persisting the executable-mode metadata through the same open descriptor. Existing exclusive-create and no-symlink-parent behavior is unchanged.

### Exact branch and commits

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`
- Parent #31/base SHA: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`
- Child #35 branch: `phoenix/release-build-script-publication-safety-20261117`
- Test-first commit: [`3e245d37`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3e245d37ee4bd9ed263544774d3499a3fea56861)
- Source correction: [`be4ad529`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/be4ad529d9117fad07a52a189a7d7468ecf80683)
- Current PR before this handover update: [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35) at `be4ad529d9117fad07a52a189a7d7468ecf80683`

Only `tools/test_package_appliance_firmware.py`, `tools/package_appliance_firmware.py`, and this release-owned handover changed in this task. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation or shared interface was changed.

### Exact-source CI

- Expected RED at test-only commit: [push run #44864992108](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44864992108). Packaging suite ran 121 tests, with exactly the new test failing: observed calls were `['fsync', 'fchmod']`, missing the post-chmod sync. Two pre-existing tests were intentionally skipped.
- Exact source/test push run [#44865035316](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44865035316): packaging/tool suite **121 tests PASS, 2 intentional skips**. The subsequent all-profile admission step **FAILED CLOSED** for all 10 profiles because approved site-scoped RFC 4193 ULA /48 authority is still undefined. ESP32 and ESP8266 jobs were skipped because validation failed at profile admission. Overall workflow is **FAILURE**, not green.
- Exact PR validation [#44865040773](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44865040773): same 121-test PASS / 2 skips, followed by the same missing-site-ULA admission failure; both board compile jobs SKIPPED.
- Mandatory sandbox [#44865040768](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44865040768): host preflight **14/14 PASS**, then failed closed because Bubblewrap is not installed on the hosted runner (exit 125). Namespace execution and sandbox-dependent packaging tests were SKIPPED, not passed. No privileged install or unsandboxed fallback.
- Case-collision guard [#44865040796](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44865040796): **SUCCESS**.

### Evidence limits and next owners

The new regression and source correction are hosted CI evidence for filesystem call ordering only. They do not establish a real ImageBuilder run, production image, protected signer, or physical acceptance. This change persists the file's executable-mode metadata; it does not claim directory-entry crash-consistency or power-cut acceptance.

1. PHX-QA: independently review the exact test/source commits and failure-mode coverage.
2. PHX-INFRA: provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged namespaces; do not bypass the mandatory sandbox.
3. PHX-CORE / COE integration owner: supply the approved site-scoped ULA authority and persistence contract; RELEASE will not invent or replace the prefix.
4. PHX-MASTER: reconcile #35 with parent #31 and the frozen #26 integration route; the ownership manifest remains `DRAFT_REVIEW_ONLY`.
5. Registry custodian: restore authorized access to private Drive registry v11; no older snapshot was substituted.

No real OpenWrt ImageBuilder appliance image, signer-positive result, hardware flash, payment migration, or customer deployment occurred. The 150 physical power-cut test and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO**.

## PHX-RELEASE UTC05 — persist generated build-script directory entry (2026-11-21)

**Disposition:** one release-owned crash-durability defect reproduced test-first and corrected on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Defect and correction

The generated ImageBuilder wrapper was created with `O_CREAT | O_EXCL` through a no-follow parent-directory walk. The file bytes and executable mode were fsynced, but `_open_file_without_symlink_parents()` closed the parent directory descriptor immediately after `openat()`. The generator therefore never fsynced the parent directory entry. After a crash, the newly created script name could be lost even though generation had returned success.

The RELEASE-owned helper now retains both the new file descriptor and its already-verified parent directory descriptor. Publication order is:

1. Write and flush complete script bytes.
2. `fsync(file_fd)` for content.
3. `fsync(parent_directory_fd)` while the new file is still mode `0600`.
4. `fchmod(file_fd, 0755)`.
5. `fsync(file_fd)` to persist executable inode metadata.
6. Close the retained parent directory descriptor.

If parent-directory sync fails, the function raises before granting execute permission. No path is reopened by name for the directory sync; the descriptor came from the existing component-by-component `O_DIRECTORY | O_NOFOLLOW` walk. Existing exclusive-create and no-overwrite behavior remains.

### Exact branch and commits

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`
- Parent #31/base SHA: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`
- Child #35 branch: `phoenix/release-build-script-publication-safety-20261117`
- Test-first regression: [`4802cd26`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4802cd264c564ae2b5fbd0327647ac1412dc3f1f)
- Source correction: [`eb858d2e`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/eb858d2eae39c639310682e05bd1109c26ab4e32)
- Existing file-mode assertion adjusted to distinguish file and directory fsync events: [`609fe214`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/609fe214867f88be82b2e9e46b5642c074b1389c)
- Current source/test PR head before this handover update: `609fe214867f88be82b2e9e46b5642c074b1389c`.

Only `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, and this RELEASE-owned handover changed for this task. No CORE, RENTAL, PISONET, HARDWARE, QA, MASTER or shared interface implementation changed.

### Exact-source CI

- Expected RED at test-only head [#44870390309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870390309): the new regression failed exactly because observed events were file `fsync → fchmod → fsync` and the required parent-directory `fsync` was absent. The packaging suite ran 122 tests, with one expected failure and two intentional skips. Case-collision [#44870390301](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870390301): PASS.
- Intermediate source head [#44870504597](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870504597): packaging suite failed only because the pre-existing file-mode test counted the newly added directory fsync as an extra file fsync. The new parent-directory regression itself passed. The test-only correction at `609fe214` now classifies descriptors by `fstat()` mode and keeps the two assertions independent.
- Final source/test PR validation [#44870585855](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870585855) and push validation [#44870582419](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870582419): packaging/tools suite **122 PASS / 2 intentional skips**. Both the new directory-entry ordering regression and the existing executable-mode regression passed. Overall validation then **FAILED CLOSED** at all-profile staging: all 10 profiles require approved site-scoped RFC 4193 ULA /48 authority, which is not defined. ESP32/ESP8266 compile jobs were skipped after admission failed; no board build is claimed.
- Exact-head case-collision [#44870585740](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870585740): PASS.
- Mandatory sandbox PR [#44870585766](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870585766) and push [#44870582449](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870582449): **FAILED CLOSED** because `bwrap` is not installed (exit 125). Host preflight 14/14 PASS; unprivileged identity, namespace probe and sandbox-dependent packaging tests were SKIPPED, not passed. No privileged install or unsandboxed fallback.

### Evidence boundary and next owners

This is hosted CI evidence for filesystem call ordering and descriptor-based durability sequencing. It is not a real OpenWrt ImageBuilder build, production appliance image, physical power-cut test or hardware acceptance. No firmware was signed or published.

1. PHX-QA: independently review the exact test/source sequence at `609fe214`, including the fail-before-chmod behavior when parent-directory fsync fails.
2. PHX-INFRA: provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged namespaces; mandatory sandbox remains closed until then.
3. PHX-CORE / PHX-MASTER / COE integration owner: supply and approve the site-scoped ULA /48 authority and persistence contract; RELEASE will not invent or substitute a prefix.
4. PHX-MASTER: reconcile child #35 with parent #31 and frozen integration #26; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY` and the RELEASE workflow route remains reimplementation-review only.
5. Registry custodian: restore authorized access to canonical private Drive registry v11. This activation's exact-title Library search returned older v3-v7 snapshots only; none was substituted.

No real ImageBuilder sandbox execution, approved production binary, signer-positive result, hardware flash, payment migration or customer deployment occurred. The 150 physical power-cut test and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO**.


## PHX-RELEASE UTC06 — make checksum-manifest publication crash-durable (2026-11-21)

**Disposition:** one release-owned manifest durability defect reproduced test-first and corrected on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Defect and bounded correction

The generated ImageBuilder wrapper already sorted checksums into a temporary file and published the final `RELEASE_MANIFEST.sha256` through a same-directory no-overwrite hard link. It then removed the sorted and unsorted temporary names without synchronizing the final manifest inode or its parent directory. Atomic publication prevented partial overwrite, but a crash could still lose the final manifest data or published directory entry after the wrapper reported success.

The wrapper now performs a descriptor-based finalization step immediately after the hard link succeeds:

1. Open the ImageBuilder directory with `O_DIRECTORY | O_NOFOLLOW`.
2. Open the final manifest with `O_WRONLY | O_NOFOLLOW` relative to that pinned directory descriptor.
3. Verify the final file is regular, the sorted temporary name is the same inode, the final inode has the expected two links, and the unsorted temporary input is a separate single-link regular file.
4. `fsync(final_manifest_fd)` to persist checksum bytes and inode metadata.
5. `fsync(directory_fd)` to persist the final published name before cleanup.
6. Unlink the two temporary names relative to the pinned directory descriptor.
7. `fsync(directory_fd)` again to persist cleanup.

Any open/stat/fsync/unlink failure emits `RELEASE-BLOCKED: checksum manifest durability finalization failed` and exits nonzero. A file- or directory-sync failure occurs before temporary cleanup, so the temporary evidence is retained. The existing atomic no-overwrite hard-link publication remains unchanged.

### Exact branch and commits

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`
- Child PR #35 branch: `phoenix/release-build-script-publication-safety-20261117`
- Parent PR #31/base SHA: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`
- Test-first commit: [`ea08e48b`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/ea08e48b66be4d8d912fa42797fd707dd98d2e17)
- Source correction: [`3f4028ae`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3f4028aec38f922e197fa25bd54bf31cdd4c31cd)
- Source/test head before this handover update: `3f4028aec38f922e197fa25bd54bf31cdd4c31cd`.

Only `tools/package_appliance_firmware.py`, `tools/test_package_appliance_firmware.py`, and this RELEASE-owned handover changed for this task. No CORE, RENTAL, PISONET, HARDWARE, QA, MASTER or shared interface implementation changed.

### Exact-source CI

- Expected RED at test-only head [#44875832118](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44875832118): packaging suite ran **124 tests / 2 intentional skips**; both new manifest-durability tests failed because the generated wrapper did not yet contain the required finalization block. The failures were expected and isolated to the new assertions. The overall validation run failed at the packaging test step; profile admission and board compiles were not reached.
- Exact source/test PR validation [#44876039985](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44876039985): packaging/tool suite **124 PASS / 2 intentional skips**. Both new tests passed, including actual file/directory fsync call-order verification and the fail-closed/no-cleanup behavior when the first durability sync fails. The subsequent all-profile staging gate **FAILED CLOSED** for all 10 profiles because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP32 and ESP8266 compile jobs were SKIPPED; no board build or firmware artifact is claimed.
- Exact-head case-collision guard [#44876039980](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44876039980): **PASS**.
- Mandatory sandbox [#44876040106](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44876040106): host preflight **14/14 PASS**, then Bubblewrap availability **FAILED CLOSED**, exit 125. Unprivileged identity, namespace probe and sandbox-dependent packaging tests were SKIPPED, not passed. No privileged install or unsandboxed fallback.

### Evidence boundary and next owners

The new tests execute the generated manifest-finalization Python block in hosted CI and verify file fsync → directory fsync → temporary cleanup → directory fsync ordering. This is filesystem-call-order CI evidence, not a physical power-cut test or proof of storage-controller durability. The actual ImageBuilder sandbox remains unexecuted because Bubblewrap is unavailable; no appliance image was produced.

1. PHX-QA: independently review the exact test/source commits and the fail-closed behavior for file/directory fsync failures.
2. PHX-INFRA: provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged namespaces; the mandatory sandbox must remain closed until then.
3. PHX-CORE / PHX-MASTER / COE integration owner: supply and approve the site-scoped ULA /48 authority and persistence contract; RELEASE will not invent or substitute a prefix.
4. PHX-MASTER: reconcile child #35 with parent #31 and frozen integration #26; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY` and the RELEASE workflow route remains reimplementation-review only.
5. Registry custodian: restore authorized access to canonical private Drive registry v11. The exact-title authorized Library search returned older v3-v7 snapshots only; none was substituted.

No real ImageBuilder sandbox execution, approved production binary, signer-positive result, hardware flash, payment migration or customer deployment occurred. The 150 physical power-cut test and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO**.


---

## PHX-RELEASE UTC07 — cover pre-cleanup directory fsync failure (2026-11-21)

**Disposition:** added the missing release-owned negative regression requested by MASTER. This is a coverage completion, not a claim that the existing implementation was defective. COE #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Review request and exact branch

- MASTER review request: [COE #35 comment #7058864355](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35#issuecomment-7058864355).
- Repository: `BlazeDevStudio/CoinOperatedEcosystem`.
- Child branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Starting PR/docs head: `93bab4c97e2a487a3223dc209c5be8fbbc609b5c`.
- Test-only commit: [`d5a2d727`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/d5a2d727727d7019cf3b4ad60503a4fb821d69d1).
- Current source/test head: `d5a2d727727d7019cf3b4ad60503a4fb821d69d1`.

### Added regression

New test: `test_generated_wrapper_keeps_temporary_manifests_when_precleanup_directory_sync_fails` in `tools/test_package_appliance_firmware.py`.

The test executes the generated manifest-finalization block against disposable files and injects an `OSError` on the second `os.fsync` call. It allows the manifest-file fsync to succeed, then fails the pre-cleanup directory fsync. It asserts:

1. The observed fsync sequence is exactly `file`, then `directory`.
2. The wrapper exits with `RELEASE-BLOCKED: checksum manifest durability finalization failed`.
3. The final manifest, sorted temporary hard-link name and unsorted temporary input all remain.
4. The final and sorted names still identify the same inode with link count 2.

No packager source behavior, profile, workflow, shared interface or other subsystem path changed in this task.

### Exact-source Actions at `d5a2d727727d7019cf3b4ad60503a4fb821d69d1`

- PR shared/firmware [#44879798619](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879798619): packaging/tool test step **PASS**, **125 tests PASS** and log marker `PHX-MANIFEST-DURABILITY-PASS`. The subsequent all-profile admission step **FAILED CLOSED** for all 10 profiles because approved site-scoped RFC 4193 ULA /48 authority is still absent. ESP8266 and ESP32 compile jobs were **SKIPPED**; no board artifact is claimed.
- Push shared/firmware [#44879793109](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879793109): same 125-test packaging step **PASS**, then the same 10-profile ULA admission failure; board compile jobs **SKIPPED**.
- Case-collision guard [#44879798675](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879798675): **PASS**.
- Mandatory ImageBuilder sandbox [#44879798653](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879798653): host preflight **14/14 PASS**, then Bubblewrap availability **FAILED CLOSED**, exit 125. Unprivileged identity, namespace probe and mandatory sandbox packaging tests were **SKIPPED**, not passed. No privileged install or unsandboxed fallback.

This task is a test-only coverage extension; no expected-RED run was appropriate because the current source already contains the fail-closed behavior. The test now guards against regression if the pre-cleanup directory fsync is removed or moved after temporary cleanup.

### Next owners and evidence boundary

1. PHX-QA: independently review exact test commit `d5a2d727727d7019cf3b4ad60503a4fb821d69d1` and the failure injection/retained-name assertions.
2. PHX-INFRA: provide the authorized disposable, no-secret runner with pre-provisioned Bubblewrap and working unprivileged namespaces.
3. PHX-CORE / PHX-MASTER / COE integration owner: approve the site-scoped ULA /48 authority and persistence contract; RELEASE will not invent a prefix.
4. PHX-MASTER: reconcile #35/#31/#26 ownership and route status; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`.
5. Registry custodian: restore authorized access to canonical private Drive registry v11; older snapshots were not substituted.

The new test is hosted-CI failure injection, not a physical power-cut test or proof of storage-controller durability. No real ImageBuilder sandbox execution, approved production binary, signer-positive result, hardware flash, payment migration or customer deployment occurred. The 150 physical power-cut test and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO**.


---

## PHX-RELEASE UTC11 — reject symlinked Bubblewrap executables (2026-11-21)

**Disposition:** a release-owned trust-path validation gap was reproduced test-first and corrected in both the sandbox host preflight and the runtime sandbox runner. COE #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Defect and bounded correction

Both tools/check_imagebuilder_sandbox_host.py and tools/run_imagebuilder_sandbox.py restricted Bubblewrap lookup to /usr/bin:/bin and checked that the resolved path's parent directory was trusted. They then used os.path.isfile(), which follows the final symlink. A symlink named /usr/bin/bwrap could therefore pass the lexical trusted-directory check while redirecting execution to a target outside the trusted directory.

Both checks now use os.lstat() and require the final directory entry itself to be a regular file before checking execute access. A symlink, FIFO, directory or other non-regular final entry is rejected. This does not pin the Bubblewrap binary's contents or claim protection against privileged mutation of trusted system directories; it closes the final-component symlink-following gap.

### Exact branch and commits

- Repository: BlazeDevStudio/CoinOperatedEcosystem.
- Child PR #35 branch: phoenix/release-build-script-publication-safety-20261117.
- Parent PR #31 / base SHA: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.
- Starting docs/source head: d28271a35776543bf558c90e3a117957829ee61c.
- Test-first commit: [bf2220e3](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/bf2220e390795510e9e51515913405c39436cfa7).
- Source correction: [847e3558](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/847e355845d9043667d6ccaa8e160b8e64b67352).
- Source/test HEAD at this handover update: 847e355845d9043667d6ccaa8e160b8e64b67352.
- Only two release-owned source files and two release-owned test files changed for this task; this handover is the fifth changed file. No workflow, shared interface, profile, firmware application, or other role-owned source was changed.

### Regression tests

- test_probe_rejects_symlinked_bubblewrap_in_trusted_directory creates a temporary executable symlink and verifies host preflight rejects it even when its lexical parent is represented as /usr/bin.
- test_runner_rejects_symlinked_bubblewrap_in_trusted_directory exercises the runtime runner's trusted-directory predicate against the same symlink case.

### Exact-source RED at test-only commit bf2220e390795510e9e51515913405c39436cfa7

- PR shared/firmware [#44898395744](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44898395744): 127 tests ran; exactly the two new symlink tests failed; two intentional skips. Firmware-hardening and shared-contract steps passed; profile admission and board compiles were not reached.
- PR sandbox [#44898395675](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44898395675): host preflight ran 15 tests and failed only at the new symlink test. Bubblewrap availability, namespace and packaging steps were skipped after that failure.
- Case-collision [#44898395665](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44898395665): PASS.

### Exact-source results at source/test commit 847e355845d9043667d6ccaa8e160b8e64b67352

- PR shared/firmware [#44898517084](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44898517084): packaging/tool suite 127 PASS / 2 intentional skips; the following all-profile admission gate FAILED CLOSED for all 10 profiles because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266 and ESP32 compile jobs were SKIPPED.
- Push shared/firmware [#44898511763](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44898511763): same 127 PASS / 2 skips, then the same ten-profile ULA admission failure; board compile jobs skipped.
- PR sandbox [#44898517081](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44898517081): host preflight 15/15 PASS, then Bubblewrap availability FAILED CLOSED because bwrap is not installed (exit 125). Unprivileged identity, namespace probe and mandatory sandbox packaging tests were skipped, not passed.
- Push sandbox [#44898511806](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44898511806): same 15/15 host preflight PASS, then missing Bubblewrap exit 125; later sandbox steps skipped.
- Case-collision [#44898517082](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44898517082): PASS.

The two symlink regressions pass in both the 15-test host preflight and 127-test packaging/tool suite. The overall workflows are not green because separate required gates remain blocked. No actual Bubblewrap namespace or ImageBuilder execution occurred in these runs.

### Live ownership and cross-repository state

- MASTER PR #288 exact head at inspection: 940fe4f1ec3816dd2ac60468303b0454835d496c. coordination/phoenix/OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY; the RELEASE route from .github/workflows/blazepwifi-build.yml to .github/workflows/pisowifi-ci.yml remains reimplementation-review. No workflow migration is authorized.
- Experiments #242 exact head: 734b89d9e7792247e8376335c3f3685500ab3f89.
- Experiments #291 exact docs/head: 42797e2f3d65c30a1070caf49c93aebec149d897; source/test: 1851f1d06648beed70695528f2799d57154a69237. Compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed 3/3. Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at CORE-owned PROJECT_HANDOVER.md freshness; downstream signing/publication and Windows build/publisher were skipped. The 26-path #291 diff remains mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); RELEASE did not edit those inherited paths.
- COE integration #26 exact head: b382d233ff06c8791b1028bed3c617cc7b670d12, frozen with five workflows queued / zero jobs.
- COE parent #31 exact head/base for #35: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.
- COE child #35 source/test head: 847e355845d9043667d6ccaa8e160b8e64b67352; PR remains OPEN / DRAFT / UNMERGED.
- Cleanup-first issue #266 remains OPEN, 0/7 checked. This scoped release fix does not complete the seven-role cleanup inventory.
- The #172 embedded control-plane body still contains an older #291 head (bcb71b4c...). The live PR API and MASTER UTC10 audit confirm 42797e2f.... MASTER should reconcile its own index; RELEASE did not edit coordination-owned files.

### Remaining owner actions and evidence boundary

1. PHX-QA: independently review the exact symlink rejection tests and source correction at 847e3558.
2. PHX-INFRA: provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged namespaces; no privileged install or unsandboxed fallback.
3. PHX-CORE / PHX-MASTER / COE integration owner: establish approved site-scoped ULA /48 authority and persistence contract before profile admission can proceed.
4. PHX-MASTER: reconcile the stale #172 PR-head index and preserve the draft-only reimplementation-review route.
5. Registry custodian: restore authorized access to canonical private Drive registry v11. The exact-title Library search surfaced older v3-v7 snapshots only; none was substituted. No Google Drive connector was exposed in this activation.

This is hosted-CI path-validation evidence using synthetic symlink fixtures, not a real host Bubblewrap execution, real ImageBuilder build, signed production binary, physical power-cut test or hardware acceptance. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was modified. No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. The 150 physical power-cut test and 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO**.



---

## PHX-RELEASE UTC12 — require unprivileged Bubblewrap executable mode (2026-11-21)

**Disposition:** release-owned trust-boundary hardening implemented test-first and verified by exact-source host CI. COE #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Finding and bounded correction

The UTC11 checks rejected a final-component symlink but still accepted a regular executable with setuid/setgid bits or group/world write permission. That is inconsistent with MASTER's approved unprivileged single-ID user-namespace trial. Upstream Bubblewrap guidance says the unprivileged executable must not be setuid root and is normally mode 0755: https://github.com/flatpak/flatpak/wiki/User-namespace-requirements

Both the host preflight and runtime runner now require a regular executable whose mode has none of `S_ISUID`, `S_ISGID`, `S_IWGRP`, or `S_IWOTH`. Ordinary executable mode 0755 remains accepted. This is a mode-bit check only: it does not pin the Bubblewrap binary's contents, prove root ownership, or protect against privileged mutation of trusted system directories.

### Exact branch and commits

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`.
- Child PR #35 branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base SHA: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Starting PR/docs head: `24ca7f7000fb8626e3e517935dd6ec6f375d0998`.
- Test-only commits: [1cf4e8c9](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/1cf4e8c961fd4ba1c575f362de8a6491e9e4d75a) and [fb1925d1](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/fb1925d1c3396f3a67bf73087c521f37c8d46adf).
- Source corrections: [b0258542](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b025854203226da566963de6d4127a74442e4f30) and [e1934fcb](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e1934fcb42f493ac0929490884045d54ad3a035e).
- Source/test head: `e1934fcb42f493ac0929490884045d54ad3a035e`.
- Changed paths for this task: `tools/check_imagebuilder_sandbox_host.py`, `tools/run_imagebuilder_sandbox.py`, `tools/test_imagebuilder_sandbox_host.py`, `tools/test_package_appliance_firmware.py`, and this handover. All are RELEASE-owned.

### Test-first and exact-source evidence

- Expected RED at test head `fb1925d1`: shared/firmware [#44903035579](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903035579), job `136842751529`, ran 133 tests with 8 expected new mode-rejection failures and 2 intentional skips; sandbox [#44903035615](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903035615), job `136842751430`, ran 18 host tests with 4 expected new mode-rejection failures; case-collision [#44903035593](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903035593) PASS.
- Exact source/test head `e1934fcb`: shared/firmware [#44903089459](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903089459), job `136842912538`, packaging/tool suite **133 PASS / 2 intentional skips**, then all ten profile admissions **FAILED CLOSED** because approved site-scoped RFC 4193 ULA /48 authority is still absent; ESP32/ESP8266 compiles SKIPPED.
- Exact source/test head sandbox [#44903089472](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903089472), job `136842912634`: host preflight **18/18 PASS**, then Bubblewrap availability FAILED CLOSED (not installed, exit 125). Namespace probe and mandatory sandbox packaging regressions were skipped, not passed.
- Exact source/test head case-collision [#44903089470](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903089470): PASS.

### Evidence boundary / next owners

The mode-bit regressions are synthetic filesystem metadata tests. No real Bubblewrap executable was present on the hosted runner, so no namespace setup or ImageBuilder execution occurred. PHX-INFRA must provide the authorized disposable runner with non-setuid Bubblewrap and working unprivileged user namespaces. PHX-CORE/MASTER/COE integration must provide the approved site-scoped ULA /48 authority. PHX-QA should independently review both exact source/test commits. No other subsystem source, shared interface, profile or firmware was changed.

No merge, signing, tagging, publication, hardware flash, payment migration or customer deployment occurred. Physical 150 power-cut and 30-device/24-hour soak evidence remains NOT TESTED. **PRODUCTION NO-GO**.

---

## PHX-RELEASE UTC13 — reject duplicate JSON object keys in custom router profiles (2026-11-21)

**Disposition:** a release-owned profile-input ambiguity was reproduced test-first and corrected in the existing COE #35 child draft. The parser now rejects duplicate keys at every JSON object depth rather than silently accepting the last value. PR remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Finding and bounded correction

`load_profile()` accepts operator-supplied custom JSON paths and previously called Python's default `json.load()`. The default decoder silently keeps the last value when a JSON object repeats a key. This permits ambiguous top-level profile identity or nested networking/VLAN fields to be interpreted differently by other JSON consumers.

The release-owned loader now passes `_reject_duplicate_json_object_keys` as `object_pairs_hook`. It checks each parsed object and raises `ValueError` naming the duplicate key. Because the hook is applied recursively by the JSON decoder, both top-level and nested duplicates are rejected. Valid profile-ID and custom-JSON-path behavior is unchanged. No checked-in profile, ULA authority, network policy, firmware source or shared interface was changed.

### Exact branch and commits

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`.
- Child PR #35: [release build-script publication safety](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35).
- Branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base SHA: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Starting docs/source head: `9d6fa64113243981efcc4b5c7af098a5c4bb94c8`.
- Test-only regression commit: [`1d209291`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/1d2092917c781cb0f1c6f7ab41beede893070cdb).
- Source correction commit: [`a143068f`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a143068f0eaf8a61ce05502ccfdf544b447fafbb).
- Changed source/test paths: `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py`. This handover is the only documentation path changed for this task.

### Test-first RED at `1d2092917c781cb0f1c6f7ab41beede893070cdb`

- Shared validation [run #44908015281](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44908015281), job `136857647930`: **134 tests ran; exactly the two new duplicate-key subcases failed** (top-level `profile_id` and nested `lan`); two intentional skips. The packaging test step failed before profile admission and board compilation.
- Sandbox [run #44908015276](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44908015276), job `136857647956`: host preflight **18/18 PASS**, then Bubblewrap availability **FAILED CLOSED**, exit 125 because Bubblewrap is not installed. Namespace and mandatory ImageBuilder packaging tests were not run.

### Exact source/test results at `a143068f0eaf8a61ce05502ccfdf544b447fafbb`

- Shared validation [run #44908078965](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44908078965), job `136857838021`: **134 tests PASS / 2 intentional skips**, marker `PHX-MANIFEST-DURABILITY-PASS`; subsequent all-profile admission **FAILED CLOSED** for all 10 profiles because approved site-scoped RFC 4193 ULA /48 authority is absent. ESP8266 and ESP32 compile jobs were **SKIPPED**.
- Mandatory sandbox [run #44908079206](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44908079206), job `136857838801`: host preflight **18/18 PASS**, then Bubblewrap availability **FAILED CLOSED**, exit 125. No namespace setup or ImageBuilder execution occurred.
- Case-collision guard [run #44908078969](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44908078969): **PASS**.

The new parser regression is synthetic custom-profile input coverage. It does not provide appliance build, ImageBuilder sandbox, firmware, hardware, financial or production evidence.

### Next owner actions and release boundary

1. **PHX-QA:** independently review source/test commits `1d209291` and `a143068f`, including nested duplicate-key rejection.
2. **PHX-CORE / PHX-MASTER:** approve the site-scoped ULA /48 authority and persistence contract; RELEASE will not invent or substitute a prefix.
3. **PHX-INFRA:** provide the authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged user namespaces.
4. **PHX-MASTER:** refresh the stale PR-head references in #172 and reconcile the #35/#31/#26 ownership routes; the route manifest remains `DRAFT_REVIEW_ONLY`.
5. **Registry custodian:** restore authorized access to canonical private Drive registry v11. Older Library snapshots were not substituted and no private registry contents were copied to GitHub.

No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. The 150 physical power-cut test and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO**.


---

## PHX-RELEASE UTC14 — test ImageBuilder sandbox process-group timeout cleanup (2026-11-21)

**Disposition:** five deterministic host-unit tests were added to cover the existing runner's process-group timeout and cleanup behavior. The runner implementation was already present; this is a previously untested release-owned control path, not a newly discovered runtime defect. COE #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Finding and bounded coverage

`tools/run_imagebuilder_sandbox.py` already:
- bounds ImageBuilder execution with `--timeout-seconds` (default 3600; maximum 14400);
- sends SIGTERM then SIGKILL to both the outer Bubblewrap process group and the child `--new-session` group;
- waits for both groups to disappear before accepting completion;
- preserves partial output and cleanup diagnostics on timeout; and
- distinguishes ordinary wrapper `RELEASE-BLOCKED` output from process-group cleanup failure.

The existing sandbox host suite did not import the runtime runner or exercise these paths. Five tests were added to `tools/test_imagebuilder_sandbox_host.py`:
1. timeout escalation order and both outer/child process groups;
2. cleanup of a detached child group after a successful wrapper leader exit;
3. partial stdout/stderr and cleanup diagnostic preservation;
4. ordinary profile `RELEASE-BLOCKED` output not being misclassified as cleanup failure; and
5. fail-closed classification when the child process group cannot be reaped.

These are deterministic mock-based unit tests. They verify the runner's signaling decisions and cleanup-result classification; they do **not** spawn real detached OS processes, exercise a real Bubblewrap namespace, or establish that the hosted runner can run ImageBuilder.

### Exact branch and commits

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`.
- Child PR #35 branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base SHA: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Starting source/docs head: `f2bd3e13a2c42d8bc7155060aee84c2b97e9cb6f`.
- Test commit: [`a5d49742`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a5d49742de476c8e5b0159ba1f7ad59dd50751b5).
- Source/test head for this task: `a5d49742de476c8e5b0159ba1f7ad59dd50751b5`.
- New test-file blob: `3dce8da77c1c11bad9f815e6e780b7adaa2b79f2`.
- Only `tools/test_imagebuilder_sandbox_host.py` changed in the test commit. No runtime source, profile, workflow, firmware, shared interface or other role-owned path changed.

### Exact-source CI at test head `a5d49742`

- Sandbox PR run [#44912978248](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44912978248), job `136872511929`: host preflight **23/23 PASS**, including all five new runner tests. The following Bubblewrap availability step **FAILED CLOSED** because Bubblewrap is not installed on this runner (exit 125). Unprivileged identity, namespace probe and mandatory ImageBuilder packaging steps were **SKIPPED**, not passed.
- Shared/firmware PR run [#44912978205](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44912978205), job `136872511532`: firmware/syntax, shared-contract/profile checks and packaging/tools steps **PASS**. Packaging/tools executed **139 tests PASS / 2 intentional skips**, with `PHX-MANIFEST-DURABILITY-PASS`. The subsequent all-profile admission step **FAILED CLOSED** for all 10 profiles because approved site-scoped RFC 4193 ULA /48 authority is still undefined. ESP8266 and ESP32 compile jobs were **SKIPPED**.
- Case-collision PR run [#44912978201](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44912978201), job `136872511437`: **PASS**.

No expected-RED run is claimed: the task adds coverage for already-implemented behavior and does not claim a runtime defect or source correction.

### Live ownership and cross-repository state

- MASTER PR #288 exact head: `2fdad5acb3dfa8e9c170721b87fd5524061eb577`; base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. `coordination/phoenix/OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`; the RELEASE workflow route remains `reimplementation-review`. No migration is authorized.
- Experiments #242 exact head: `734b89d9e7792247e8376335c3f3685500ab3f89`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) is **SUCCESS** (scoped CI only).
- Experiments #291 exact head: `42797e2f3d65c30a1070caf49c93aebec149d897`; ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) **PASS 3/3** for its pinned source. Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) **FAIL** at the CORE-owned `PROJECT_HANDOVER.md` freshness gate; downstream signing/publication and Windows build/publisher were skipped. The 26-path diff remains mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); no inherited paths were changed.
- COE integration #26 exact head: `b382d233ff06c8791b1028bed3c617cc7b670d12`; **FROZEN**, five workflows queued / zero jobs.
- COE parent #31 exact head/base for #35: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. Its earlier sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) installed Bubblewrap 0.9.0 but failed the unprivileged namespace probe with `bwrap: setting up uid map: Permission denied` (exit 125); this is runner capability failure, not a successful sandbox build.
- Cleanup-first #266 remains OPEN / 0/7 checked. This scoped RELEASE test addition does not complete the seven-role cleanup inventory.
- Canonical private Drive registry v11 and newer corrections were not surfaced by the authorized Library search. Older snapshots were not substituted; no private registry content or identifiers were copied to GitHub.

### Next owner actions and evidence boundary

1. **PHX-QA:** independently review test commit `a5d49742` and confirm the timeout/cleanup assertions are adequate for the runner contract.
2. **PHX-INFRA:** provide the authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces. Do not install privileged dependencies or fall back to unsandboxed packaging.
3. **PHX-CORE / PHX-MASTER / network authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** reconcile stale #172 embedded PR-head references and keep the #35/#31/#26 ownership route draft-only.
5. **Registry custodian:** restore authorized access to canonical private Drive registry v11.

This activation provides mock-based host-unit CI evidence only. No real Bubblewrap namespace, ImageBuilder build, approved target binary, signing, physical power-cut test or hardware acceptance is established. The 150 physical power-cut test and 30-device/24-hour soak remain **NOT TESTED**. No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. **PRODUCTION NO-GO**.


---

## PHX-RELEASE UTC15 — real POSIX detached-process-group cleanup (2026-11-21)

**Disposition:** one additional release-owned host regression now exercises the existing ImageBuilder cleanup helper against real detached OS process groups. This extends the UTC14 mock coverage; it does not claim a Bubblewrap namespace or ImageBuilder build. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Scope and behavior exercised

Added `test_real_detached_process_groups_are_terminated_and_reaped` to `tools/test_imagebuilder_sandbox_host.py`.

The test is POSIX-only and launches:
- an outer process in its own session/process group; and
- a detached child in a second session/process group.

Both deliberately ignore SIGTERM. The test waits for the child to install that handler, then calls the existing `_terminate_process_groups()` helper with both real process-group IDs. It verifies SIGTERM grace expires, SIGKILL terminates both groups, the outer process is reaped, the child group disappears, and no cleanup diagnostic is returned. A `finally` cleanup path attempts to terminate both groups if an assertion fails.

Only the release-owned host test file changed in the source/test commit. No runtime runner implementation, Bubblewrap configuration, profile, firmware, workflow, shared interface or other role-owned path changed.

### Exact branch and commit

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`.
- Child PR #35 branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base SHA: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Starting docs/source head: `a533ec7b3f8080eb7f3780ba59d4bb411906f503`.
- Initial real-process test commit: [`4c1fb136`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4c1fb136eb1d5fa9cad0780b861028e27d95a21b).
- Test-harness cleanup-finally hardening follow-up: [`496c374c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/496c374cd0ae4fd630be51a0ea507d8d6139229b); the cleanup retry flag is now set only after all assertions pass, so a failed assertion still enters the final cleanup path.
- Final source/test SHA: `496c374cd0ae4fd630be51a0ea507d8d6139229b`.
- Final test-file blob: `39b04c9cb32cb028036b438791e463079cfffed5`.
- Source scope: `tools/test_imagebuilder_sandbox_host.py` only.

### Exact-source Actions at final source/test head `496c374c`

- Sandbox PR [#44918411114](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44918411114), job `136888905997`: host preflight **24/24 PASS**, including the real detached-process test (2.158 seconds). Bubblewrap availability then **FAILED CLOSED** because Bubblewrap is not installed (exit 125). Unprivileged identity, namespace probe and mandatory ImageBuilder packaging steps were **SKIPPED**, not passed.
- Shared/firmware PR [#44918411159](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44918411159), validation job `136888906304`: firmware syntax and shared-contract checks **PASS**; packaging/tool suite **140 tests PASS / 2 intentional skips**, with `PHX-MANIFEST-DURABILITY-PASS`. All ten appliance profiles then **FAILED CLOSED** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266 and ESP32 compile jobs were **SKIPPED**.
- Case-collision PR [#44918411168](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44918411168), job `136888905928`: **PASS**.

No expected-RED run is claimed: the new test covers existing cleanup behavior and does not claim a newly discovered runtime defect. The real POSIX process-group test is hosted Linux CI evidence only; it is not real Bubblewrap namespace, ImageBuilder, hardware or production evidence.

### Live ownership and cross-repository references

- MASTER PR #288 exact head at this activation: `d02335240eb8cdc7f7e671beb53f721ffd13247c`; base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. Ownership routes blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`; PHX-RELEASE workflow route remains `reimplementation-review`. No migration is authorized.
- Experiments #242 exact head: `734b89d9e7792247e8376335c3f3685500ab3f89`; its Windows CI [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) is scoped SUCCESS only.
- Experiments #291 exact head: `42797e2f3d65c30a1070caf49c93aebec149d897`; ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) is 3/3 PASS for its pinned source. Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) fail at the CORE-owned `PROJECT_HANDOVER.md` freshness gate; downstream signing/publication and Windows build/publisher were skipped. Its 26-path diff remains mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); no inherited path was changed here.
- COE integration #26 exact head: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT / FROZEN with five queued workflows and zero executed jobs.
- COE parent #31 exact head/base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. Its earlier Bubblewrap experiment [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) installed Bubblewrap 0.9.0 but failed the unprivileged UID-map setup with `Permission denied`; no namespace acceptance.
- Cleanup-first #266 remains OPEN / 0/7 checked. This bounded test does not complete the seven-role cleanup inventory.
- Canonical private Drive registry v11 and newer corrections were not surfaced by the authorized Library search. Older snapshots were not substituted and no private registry content/identifiers were copied to GitHub.

### Next owner actions and evidence boundary

1. **PHX-QA:** independently review the real-process test addition `4c1fb136` and cleanup-finally follow-up `496c374c`, especially the detached-session setup, readiness handshake, SIGTERM-ignore condition, process-group disappearance assertions and failure-path cleanup.
2. **PHX-INFRA:** provide the authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces. Do not install privileged dependencies or use an unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site network authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** reconcile the stale embedded PR-head index in #172 and retain the draft-only #35/#31/#26 ownership route.
5. **Registry custodian:** restore authorized access to canonical private Drive registry v11.

No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. Approved production binaries, protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.


## PHX-RELEASE UTC16 — real successful-leader exit with detached child cleanup (2026-11-21)

### Scope and coverage gap

The existing mock test `test_successful_leader_exit_still_kills_detached_child_group` asserted SIGTERM/SIGKILL call ordering, while the UTC15 real-process test called `_terminate_process_groups()` with the outer leader still running. The success path in `_communicate_with_timeout()`—outer leader exits successfully while a detached child session remains—therefore lacked a real POSIX process regression.

Added a POSIX-only test that starts an outer process group and a detached child process group. The child installs a SIGTERM-ignore handler and publishes readiness; the outer leader prints its child PGID and exits 0. The test passes the already-exited leader and live detached child PGID to `_communicate_with_timeout()`, then verifies successful leader status/output, no cleanup diagnostic, and disappearance of the detached child group. A `finally` path attempts cleanup if any assertion fails.

This is test-coverage work for existing runtime behavior; it does not claim a newly discovered runtime defect and changes no production runner code.

### Exact branch and commits

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`.
- Child PR #35: [release-packager draft](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), OPEN / DRAFT / UNMERGED.
- Branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Initial test attempt: [`4631ff85`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4631ff85119e5253bd3c01e9b444bc5ae332db68). Its file-only PID handshake failed to publish the child PGID before the test deadline.
- Test-harness correction: [`662b8a45`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/662b8a45dc0b8d21af07353f90cc264a5aaad8fe). The outer helper now publishes the PGID on stdout as well as a cleanup fallback file; the parent waits for the child readiness marker before invoking the success-path cleanup.
- Final source/test SHA: `662b8a45dc0b8d21af07353f90cc264a5aaad8fe`.
- Source/test blob: `573fbc6ffc30f3cf25029e8ee1f190b6289a370a`.
- Source scope: `tools/test_imagebuilder_sandbox_host.py` only.

### Exact-source Actions

**Initial test attempt at `4631ff85` — failure recorded, not hidden**
- Shared/push [#44923293233](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44923293233): 141 tests ran, one new PID-handshake failure, two intentional skips; downstream profile admission did not pass.
- Sandbox/PR [#44923293259](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44923293259): 24/25 host tests passed; the new test failed at the PID-file readiness assertion.
- Case-collision [#44923293256](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44923293256): PASS.

**Corrected source/test head `662b8a45`**
- Sandbox/PR [#44923651180](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44923651180): host suite **25/25 PASS**, including the real successful-leader/detached-child case; next environment gate **FAILED CLOSED** because Bubblewrap is not installed (exit 125). Namespace and ImageBuilder packaging steps were skipped, not passed.
- Sandbox/push [#44923646922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44923646922): same source-head sandbox workflow; runner availability remains blocked.
- Shared/PR [#44923651213](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44923651213) and shared/push [#44923646953](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44923646953): packaging/tool suite **141 PASS / 2 intentional skips**; subsequent all-profile admission **FAILED CLOSED 10/10** because approved site-scoped RFC 4193 ULA /48 authority is unset; ESP8266/ESP32 compilation jobs skipped.
- Case-collision/PR [#44923651243](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44923651243): PASS.

The POSIX process test is hosted Linux CI evidence only. It is not Bubblewrap namespace acceptance, real OpenWrt ImageBuilder output, router/ESP hardware testing or production acceptance.

### Live ownership and blockers

- MASTER PR #288 live head at this activation: `7b4688dc989f17707f722f85f739b2b31c962eb9`; route manifest blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`. RELEASE workflow route remains `reimplementation-review`; no migration is authorized.
- Experiments #242: `734b89d9e7792247e8376335c3f3685500ab3f89`; scoped Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) PASS.
- Experiments #291: `42797e2f3d65c30a1070caf49c93aebec149d897`; ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) PASS; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) fail at the CORE-owned `PROJECT_HANDOVER.md` freshness gate. The 26-path diff remains mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); no inherited path was changed.
- COE #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows queued / zero jobs.
- COE #31 base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; earlier Bubblewrap 0.9.0 trial [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) failed unprivileged UID-map setup with `Permission denied`.
- COE #35 current test head: `662b8a45dc0b8d21af07353f90cc264a5aaad8fe`; no independent PR review had been submitted at the last review-list read.
- #266 remains OPEN / 0/7 checked. This bounded test does not complete the seven-role cleanup.
- The embedded PHX-RELEASE row in #172 is stale and still lists #35 as `7b9706d8...`; live PR API is authoritative. PHX-MASTER owns the control-plane index correction.
- Canonical private Drive registry v11 and newer corrections were not surfaced through the authorized Library search. No older snapshot was substituted; no private contents/identifiers were copied to GitHub.

### Next owner actions and release boundary

1. **PHX-QA:** independently review test commits `4631ff85` and `662b8a45`, with emphasis on the stdout readiness handshake, detached child session, successful outer exit and cleanup-on-assertion-failure path.
2. **PHX-INFRA:** provide the authorized disposable no-secret runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces. No privileged install or unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site network authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** refresh the stale #172 PR-head index and retain the draft-only #35/#31/#26 route.
5. **Registry custodian:** restore authorized access to canonical private Drive registry v11.

No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC17 — real timeout escalation with detached child process-group coverage (2026-11-21)

**Disposition:** one release-owned POSIX host-test coverage task was added to the existing COE child draft. The existing runtime implementation was not changed; no new runtime defect is claimed. PR #35 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO**.

### Scope and behavior exercised

Added `test_real_timeout_escalates_and_reaps_outer_and_detached_child_groups` to `tools/test_imagebuilder_sandbox_host.py`.

The test launches a real outer process in its own session and a detached child in a second session. Both ignore SIGTERM. The outer process publishes the child PGID, waits until the child has installed its handler, writes/flushed a partial-output marker, and then blocks. The parent invokes the existing `_communicate_with_timeout()` with a short timeout and the child PGID. The test verifies:
- the timeout path is actually taken;
- the partial stdout is retained;
- SIGTERM grace expires and SIGKILL escalation completes;
- the outer leader is reaped and both process groups disappear;
- no cleanup diagnostic is returned; and
- assertion failures still enter the final cleanup path.

The test uses file readiness markers rather than mixing a manual pipe `readline()` with `communicate()`, because the earlier pipe-read attempt consumed/buffered the partial output before `communicate()` could return it. It is POSIX hosted-Linux process evidence only, not Bubblewrap namespace or ImageBuilder execution.

### Exact branch, commits and test-authoring history

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`.
- Child PR #35: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35 — OPEN / DRAFT / UNMERGED.
- Branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Initial test attempt: [3a4f66b4](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3a4f66b4fdfcf37f2fe5325db12bd76d2b2c89eb); its generated helper script used an incorrectly escaped line separator and the outer process exited before publishing the child PGID.
- Pipe-read revision: [0d4c8181](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0d4c818111e13d353875398fd83af8284045b9f7); it corrected the generated line separator, but manually reading the PGID from stdout caused the text wrapper to buffer the following partial-output line. The timeout path ran, but the test's partial-output assertion failed.
- File-marker revision: [e17721a5](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e17721a57de50f1d9480a4047417d7bf2d082230); it removed mixed pipe reads but retained an incorrectly escaped generated line separator, so the outer helper again exited before publishing the PGID.
- Final corrected source/test commit: [93506568](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/935065687d45848edf1c1cbc02bb76b6c2d5addf).
- Final source/test blob: `f087c7e15a4ace3de6f7cb3a8ad68c5e8a13ee8b`.
- Only source/test path changed: `tools/test_imagebuilder_sandbox_host.py`.

### Exact-source Actions at final source/test SHA `93506568`

- Sandbox PR [#44929347357](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929347357), job `136922343319`: **26/26 host tests PASS**, including the new real-timeout process-group regression. The following Bubblewrap availability step **FAILED CLOSED** because Bubblewrap is not installed on the runner (exit 125); namespace and mandatory sandbox packaging steps were **SKIPPED**, not passed.
- Shared/firmware PR [#44929347397](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929347397), validation job `136922343689`: firmware syntax, shared contracts and packaging/tool suite **PASS**; **142 tests PASS / 2 intentional skips** and `PHX-MANIFEST-DURABILITY-PASS`. The subsequent appliance profile admission **FAILED CLOSED 10/10** because approved site-scoped RFC 4193 ULA /48 authority is absent. ESP8266/ESP32 compile jobs were **SKIPPED**.
- Case-collision guard [#44929347361](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929347361): **PASS**.

### Failed attempts retained in the record

- Initial source head `3a4f66b4`: sandbox [#44929154159](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929154159) host suite failed at the empty child-PGID line; shared [#44929154178](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929154178) ran 142 tests with the same one new failure; case-collision [#44929154175](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929154175) passed.
- Pipe-read source head `0d4c8181`: sandbox [#44929197704](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929197704) and shared [#44929197725](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929197725) failed only at the new partial-output assertion; case-collision [#44929197710](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929197710) passed.
- File-marker source head `e17721a5`: sandbox [#44929316136](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929316136) and shared [#44929316076](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929316076) failed at the empty child-PGID line due the remaining escape error; case-collision [#44929316083](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44929316083) passed.

No expected-RED run is claimed; this was coverage of existing behavior, not a newly discovered runtime defect.

### Live ownership and integration references refreshed

- MASTER PR #288: `8cc44fdf748fb7ba2ab44e665b0556c836be6351`, OPEN / DRAFT. `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`; PHX-RELEASE workflow route remains `reimplementation-review`. No migration is authorized.
- Experiments PR #242: `734b89d9e7792247e8376335c3f3685500ab3f89`, OPEN / DRAFT. Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) succeeded; signed executables and GitHub Release publication steps were skipped.
- Experiments PR #291: `42797e2f3d65c30a1070caf49c93aebec149d897`, OPEN / DRAFT. ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) succeeded. Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) failed at the CORE-owned mandatory `PROJECT_HANDOVER.md` freshness gate; target/platform build jobs observed succeeded, while downstream simulations/update/signing/publication were skipped. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at the same shared handover freshness gate; Windows build and publish were skipped. The 26-path diff remains mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); no inherited path was changed.
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT / FROZEN; five workflows remain queued with zero jobs.
- COE parent PR #31: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`, OPEN / DRAFT. Its prior Bubblewrap 0.9.0 attempt [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) installed Bubblewrap but failed unprivileged UID-map setup with `Permission denied`.
- COE child PR #35 before the task: `c39905cd18af13b3938c00af803e243cb03b8edc`; final source/test head: `935065687d45848edf1c1cbc02bb76b6c2d5addf`. PR remains OPEN / DRAFT / UNMERGED.
- Cleanup-first #266 remains OPEN / 0 of 7 checked. This bounded test does not complete the broader cleanup inventory.
- Canonical private Drive registry v11 and newer corrections were not surfaced through authorized Library search; only older v3-v7 snapshots were found and none was substituted. No private registry contents or identifiers were copied to GitHub.

### Next owner actions and release boundary

1. **PHX-QA:** independently review source/test SHA `935065687d45848edf1c1cbc02bb76b6c2d5addf`, especially real timeout, SIGTERM-ignore, SIGKILL escalation, output retention and both process-group disappearance.
2. **PHX-INFRA:** supply the authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces; no privileged install or unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site network authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** reconcile stale #172 PR-head pins and preserve the draft-only #35/#31/#26 ownership route.
5. **Registry custodian:** restore authorized access to canonical private Drive registry v11.

No runner source, profile, network policy, workflow, shared interface or firmware was changed in this task. No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.


## PHX-RELEASE UTC18 — root-owned Bubblewrap executable and canonical parent admission (2026-11-21)

**Disposition:** a release-owned sandbox trust-boundary gap was reproduced test-first and fixed on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED. The host and runtime trust checks now require a root-owned regular Bubblewrap executable under a canonical, root-owned, non-group/world-writable /usr/bin or /bin directory chain. **PRODUCTION NO-GO**.

### Defect boundary and correction

Before this task, both the host preflight and runtime runner checked the final Bubblewrap path's regular-file type, executable mode, setuid/setgid bits and group/world-write bits, but did not establish the canonical parent-directory provenance or require the executable inode to be root-owned. A path that appeared under /usr/bin or /bin could therefore be accepted without proving that the parent resolved to the trusted system directory or that the executable owner was root.

The correction is limited to the RELEASE-owned host preflight and runtime trust checks:

- Resolve the candidate's parent directory with realpath() and accept only canonical /usr/bin or /bin.
- Walk every canonical directory component from / to the trusted directory using lstat; require each to be a real directory owned by UID 0 and not group/world writable.
- Require the final Bubblewrap inode to be a regular file owned by UID 0, executable, and free of setuid/setgid and group/world-write bits.
- Preserve the legitimate merged-usr alias /bin -> /usr/bin when it resolves to the trusted canonical directory.
- Keep the existing unprivileged single-ID namespace, no-sudo/no-subordinate-ID and fail-closed behavior unchanged.

No privileged dependency installation, namespace fallback, workflow migration, profile change, network policy, firmware change or shared interface change was made.

### Exact branch and commits

- Repository: BlazeDevStudio/CoinOperatedEcosystem.
- Child PR #35: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35 — OPEN / DRAFT / UNMERGED.
- Branch: phoenix/release-build-script-publication-safety-20261117.
- Parent PR #31 / base: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.
- Test-first commit: [b81053a9](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b81053a96c1d01212874105226ca5aece4a417b4).
- Source correction: [a10cf724](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a10cf724f1e0488ba23a5fad357257124a563732).
- Final source/test SHA: a10cf724f1e0488ba23a5fad357257124a563732.
- Source/test paths:
  - tools/check_imagebuilder_sandbox_host.py
  - tools/run_imagebuilder_sandbox.py
  - tools/test_imagebuilder_sandbox_host.py
  - tools/test_package_appliance_firmware.py

### Test-first RED at b81053a9

- Sandbox PR [#44934730538](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934730538), job 136938774783: **30 host tests, 4 expected failures**. The new failures were non-root-owned executable, untrusted parent redirect, group/world-writable parent and non-root-owned parent. The Bubblewrap availability and later namespace/package steps did not run because the host suite failed.
- Sandbox push [#44934725590](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934725590): same exact-source host RED.
- Shared PR [#44934730519](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934730519), job 136938774523: packaging/tool suite **150 tests, 8 expected failures, 2 intentional skips**. The eight failures are the same four negative conditions exercised by both the host-preflight and runtime trust helpers. Profile admission and board compilation did not pass.
- Shared push [#44934725613](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934725613): same exact-source shared RED.
- Case-collision PR [#44934730523](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934730523): PASS.

### Exact-source GREEN at a10cf724

- Sandbox PR [#44934840976](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934840976), job 136939109494: **30/30 host-preflight tests PASS**. The next Bubblewrap availability gate **FAILED CLOSED** because Bubblewrap is not installed on the hosted runner (exit 125). Unprivileged identity verification, namespace preflight and mandatory Bubblewrap packaging regressions were **SKIPPED**, not passed.
- Sandbox push [#44934835045](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934835045): same exact-source result.
- Shared PR [#44934840959](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934840959), job 136939109617: firmware syntax and shared-contract checks **PASS**; packaging/tool suite **150 tests PASS / 2 intentional skips**. The next all-profile admission step **FAILED CLOSED** for all ten appliance profiles because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266 and ESP32 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Shared push [#44934835054](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934835054): same exact-source shared result.
- Case-collision PR [#44934840899](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44934840899): PASS.

These results are hosted CI evidence. The trust predicate tests are synthetic metadata fixtures; the POSIX runner was not executed with a real Bubblewrap binary on this runner. No real namespace or ImageBuilder package was produced.

### Live ownership and integration state refreshed

- MASTER PR #288 exact head at initial ownership-route inspection: 0fd192b09da50c33b9c49aac43982fc629c55706; MASTER later advanced its draft to live head ce12ad9b838a6deca89176c8b2086bde0a0a410d during this activation. Ownership route manifest blob e4db324315a1b3543fec17a148fbf960170fcb29 remains DRAFT_REVIEW_ONLY; RELEASE workflow route remains reimplementation-review.
- Experiments RELEASE #242 exact head: 734b89d9e7792247e8376335c3f3685500ab3f89.
- Experiments RELEASE #291 exact head: 42797e2f3d65c30a1070caf49c93aebec149d897. Its current Windows failure is in PISONET-owned negative-selftest.ps1; its Full build is blocked at inherited CORE handover freshness. No CORE or PISONET path was edited.
- COE integration #26 exact head: b382d233ff06c8791b1028bed3c617cc7b670d12; five workflows remain queued with zero executed jobs.
- COE parent #31 exact head/base: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.
- COE child #35 exact source/test head: a10cf724f1e0488ba23a5fad357257124a563732; documentation head 732ba66626d267b9b85c80b251722a3f710f2972 was also checked by the exact PR Actions below.
- Cleanup-first #266 remains OPEN, 0/7 checked. This bounded release task does not complete the broader seven-role cleanup.
- The authorized Library search surfaced only provenance metadata referencing canonical private registry v11; the actual file and newer corrections were not surfaced. The checkpoint was used only to establish provenance; no private registry contents, Drive identifiers or links were copied to GitHub, and no older registry snapshot was substituted.
- The embedded PR-head index in #172 remains stale relative to live PR metadata; PHX-MASTER owns that coordination correction. RELEASE did not edit the control-plane body.

### Next owner actions and release boundary

1. **PHX-QA:** independently review test/source SHA a10cf724, especially root ownership, canonical parent resolution, writable ancestor rejection and merged-usr /bin alias behavior.
2. **PHX-INFRA:** provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces; no privileged install or unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** reconcile stale PR-head references embedded in #172 and preserve the draft-only #35/#31/#26 ownership route.
5. **Registry custodian:** restore authorized access to canonical private registry v11 and its newer corrections.

No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was modified. No workflow migration, merge, signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.


### PHX-RELEASE UTC18 post-handover exact-head reconciliation

The documentation-head SHA 732ba66626d267b9b85c80b251722a3f710f2972 was verified after the handover commit:

- Sandbox PR [#44935047125](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44935047125), job 136939727734: **30/30 host-preflight tests PASS**. Bubblewrap availability then **FAILED CLOSED** because the runner has no Bubblewrap executable (exit 125); identity, namespace and mandatory sandbox packaging steps were **SKIPPED**.
- Shared PR [#44935047159](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44935047159), job 136939728096: host preflight **18 tests PASS**; packaging/tool suite **150 tests PASS / 2 intentional skips**; firmware syntax and shared contracts **PASS**. All ten appliance profile admissions then **FAILED CLOSED** for missing approved site-scoped RFC 4193 ULA /48 authority. ESP8266/ESP32 compile jobs were **SKIPPED**. Overall workflow remains **FAILURE**, not green.
- Case-collision PR [#44935047185](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44935047185): **PASS**.

After the initial ownership-route inspection, MASTER advanced PR #288 to ce12ad9b838a6deca89176c8b2086bde0a0a410d and posted its UTC18 checkpoint on #172. The canonical route manifest blob remains e4db324315a1b3543fec17a148fbf960170fcb29 / DRAFT_REVIEW_ONLY. The #172 issue body still carries older embedded heads for #288, #291 and #35; PHX-MASTER owns that index correction. RELEASE did not edit the control-plane body or MASTER files.

The private registry v11 check remains provenance-only: authorized Library search surfaced a checkpoint reference, not the canonical private file or its newer corrections. No private file name, Drive ID, URL or contents were copied into this repository.



## PHX-RELEASE UTC19 — pin checksum utility bytes before manifest use (2026-11-21)

**Disposition:** one release-owned manifest-integrity hardening was reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO**.

### Finding and correction

The generated ImageBuilder wrapper pinned the Python interpreter and sandbox-runner SHA-256 values, but only pinned the checksum utility by absolute path plus existence/executable checks. If the system-managed `sha256sum` path entry changed after wrapper generation, the replacement could be invoked to verify the interpreter/runner and to produce the firmware manifest. This left the checksum implementation itself outside the wrapper's generation-time identity.

The wrapper now:
- Resolves `sha256sum` only through the existing trusted `/usr/bin:/bin` lookup, preserving the system-managed path entry used by supported hosts.
- Opens the selected executable during wrapper generation and records its SHA-256 digest as `SHA256SUM_SHA256`.
- Uses the pinned Python interpreter to hash the current executable bytes before invoking `sha256sum` for any later verification or firmware manifest generation.
- Rejects a changed, missing, non-regular or non-executable checksum utility before Makefile execution or manifest creation.
- Retains the existing deterministic target-relative manifest, C-locale sorting, no-overwrite publication and crash-durability checks.

The test generates a wrapper, substitutes a disposable checksum-tool fixture and its expected digest, mutates that tool after generation, then verifies the wrapper blocks before invoking the tool or Makefile. This is a synthetic regression fixture; it is not a real firmware build.

### Exact branch and commits

- Repository: BlazeDevStudio/CoinOperatedEcosystem.
- Child PR #35: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35 — OPEN / DRAFT / UNMERGED.
- Branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Test-first commit: [9feb7baf](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/9feb7bafe8502a363cf07846a162330abb4a9bed).
- Test-fixture correction commits: [5493e52d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5493e52d86153c28ebbd270faea56591c390ec60) and [2803bbe6](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2803bbe63d9de5739a7d7faaa7e13a51ec67436c). These corrected generated-script newline/tab escaping before the expected-RED CI run.
- Expected-RED test head: `2803bbe63d9de5739a7d7faaa7e13a51ec67436c`.
- First source attempt: [79ba6b51](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/79ba6b51bf1b50823c4290c4381e60ffd69500a5). It over-resolved a system-managed checksum path alias and failed CI; it is superseded by the corrected source commit.
- Corrected source/test head: [47a4fcd8](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/47a4fcd8b3ce47ec70a9a763f7eb92fb165b5bcd).
- Changed source/test paths: `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py`; this handover is the only documentation path changed for the task.

### Test-first RED and retained failed attempt

- Test-first PR shared validation [#44940893796](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44940893796), exact head `2803bbe6`: **151 tests, one expected new failure, two intentional skips**. The new test failed because the generated wrapper did not yet contain `SHA256SUM_SHA256`. The host preflight suite passed; the mandatory sandbox workflow separately failed closed because Bubblewrap was unavailable; case-collision guard passed.
- First source attempt [#44941052472](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44941052472), exact head `79ba6b51`: **151 tests, 39 errors, one failure, two skips**. The attempt incorrectly required the resolved checksum utility target to remain under the literal trusted directory and used `O_NOFOLLOW`; the hosted runner exposed a system-managed path alias outside that lexical directory. This attempt is superseded and not counted as a pass. Its sandbox host suite passed 30 tests before Bubblewrap availability failed; case-collision passed.

### Corrected exact-source Actions at `47a4fcd8`

- Shared/firmware PR [#44941141089](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44941141089), validation job `136958398738`: firmware syntax and shared-contract checks **PASS**; packaging/tool suite **151 tests PASS / 2 intentional skips**; `PHX-MANIFEST-DURABILITY-PASS`. The subsequent all-profile admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266 and ESP32 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Sandbox PR [#44941141050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44941141050), job `136958398285`: host preflight **30/30 PASS**; Bubblewrap availability **FAILED CLOSED** because the hosted runner does not have Bubblewrap installed (exit 125). Namespace execution and mandatory sandbox/ImageBuilder regressions were **SKIPPED**, not passed.
- Case-collision guard [#44941144872](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44941144872): **PASS**.

The new regression itself passed at `47a4fcd8`: `test_generated_wrapper_rejects_checksum_utility_changed_after_generation ... ok`. The 151-test result is source-level hosted CI evidence. No actual Bubblewrap namespace or ImageBuilder firmware artifact was produced.

### Live ownership and integration state

- MASTER PR #288 remains a draft ownership-routing review. Its route manifest remains `DRAFT_REVIEW_ONLY`; the PHX-RELEASE workflow route is `reimplementation-review`. No migration or ownership promotion is authorized.
- Experiments #242 remains a draft; its Windows workflow result is CI evidence only, with signing/publication skipped.
- Experiments #291 remains a mixed-owner draft (21 RELEASE / 3 CORE / 2 PISONET paths). Its ESP32 compatibility matrix passed; its Full build remains blocked at CORE-owned handover freshness; its Windows workflow remains blocked at the shared freshness gate. No CORE or PISONET path was edited.
- COE integration #26 remains frozen with five queued workflows and zero executed jobs.
- COE parent #31 remains the unchanged base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 remains unmerged.
- Cleanup-first #266 remains OPEN / 0 of 7 checked; this task does not complete the wider cleanup.
- Canonical private Drive registry v11 was not surfaced through authorized Library search; no older snapshot was substituted and no private contents, identifiers or links were copied to GitHub.

### Next owner actions and release boundary

1. **PHX-QA:** independently review exact source/test SHA `47a4fcd8b3ce47ec70a9a763f7eb92fb165b5bcd`, especially checksum-tool replacement between wrapper generation and execution.
2. **PHX-INFRA:** provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces.
3. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** reconcile stale #172 embedded PR-head references and preserve the draft-only ownership routes.
5. **Registry custodian:** restore authorized access to canonical private registry v11.

No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was modified. No merge, signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.


## PHX-RELEASE UTC20 — centralize duplicated Bubblewrap trust policy (2026-11-21)

**Disposition:** one behavior-preserving, release-owned cleanup was committed on the existing COE #35 child draft. The host preflight and runtime runner now delegate their identical trusted-directory/executable predicate to one shared helper. PR #35 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO**.

### Finding and bounded correction

The release host preflight (`tools/check_imagebuilder_sandbox_host.py`) and runtime runner (`tools/run_imagebuilder_sandbox.py`) independently implemented the same Bubblewrap trust rules:

- every canonical `/usr/bin` or `/bin` directory component must be root-owned and not group/world writable;
- the executable's parent is resolved while the final component is checked with `lstat`;
- the executable must be a regular root-owned file;
- setuid/setgid and group/world-writable executable bits are rejected;
- executable permission is required;
- the merged-usr `/bin` alias remains accepted when its canonical parent resolves to `/usr/bin`.

Duplicated security predicates can drift. The new release-owned `tools/imagebuilder_bwrap_trust.py` contains the shared `is_trusted_system_directory` and `is_trusted_executable` functions. The preflight and runtime modules retain their existing private wrapper functions for compatibility, but delegate to the shared predicate. No trust rule was relaxed or broadened.

A new parity regression proves both host preflight and runtime wrappers consult the same shared functions. Existing negative cases for untrusted parents, non-root ownership, writable directories, set-ID bits, symlinked executables and the supported merged-usr alias remain in place. This is a code-structure cleanup, not a newly discovered runtime bypass or a real Bubblewrap execution.

### Exact branch and commits

- Repository: BlazeDevStudio/CoinOperatedEcosystem.
- Child PR #35: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35 — OPEN / DRAFT / UNMERGED.
- Branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Test-first commit: [`aec5ba37`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/aec5ba37289ecdcb5633f62ab3cab3e767056ac4).
- Shared helper and delegation: [`d8d051fc`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/d8d051fc14263ed097d94b6f343aad30af30ec08).
- Import-only cleanup: [`cda3b52c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/cda3b52c040aa04e4bfca222bd1737881787a146).
- Exact source/test SHA: `d8d051fc14263ed097d94b6f343aad30af30ec08`.
- Exact source after import cleanup: `cda3b52c040aa04e4bfca222bd1737881787a146`.
- Changed paths: `tools/imagebuilder_bwrap_trust.py`, `tools/check_imagebuilder_sandbox_host.py`, `tools/run_imagebuilder_sandbox.py`, `tools/test_imagebuilder_sandbox_host.py`; this handover is the only documentation path changed for the task.
- No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER path was changed.

### Test-first RED

- Sandbox PR [#44945866910](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44945866910), exact test-only SHA `aec5ba37`: host preflight suite **31 tests, one expected error**. The new parity regression failed because `imagebuilder_bwrap_trust` did not yet exist; all other host preflight and process-cleanup tests passed.
- Shared/firmware PR [#44945866855](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44945866855), same exact test-only SHA: tool suite **152 tests, one expected error, two intentional skips**. Firmware syntax and shared-contract checks passed; the packaging/tool step failed only at the new missing-helper import. All-profile admission and board compilation were skipped after the test failure.
- Case-collision guard [#44945866917](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44945866917): **PASS**.

The expected RED is retained; it is not counted as a passing test.

### Corrected exact-source Actions at `cda3b52c`

- Shared/firmware PR [#44946117563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44946117563), exact head `cda3b52c`: firmware syntax and shared contracts **PASS**; packaging/tool suite **152 tests PASS / 2 intentional skips**; `PHX-MANIFEST-DURABILITY-PASS`. The next all-profile admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266 and ESP32 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Sandbox PR [#44946117667](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44946117667), exact head `cda3b52c`: host preflight **31/31 PASS**. Bubblewrap availability **FAILED CLOSED** because the hosted runner does not have Bubblewrap installed (exit 125); unprivileged identity, namespace preflight and mandatory sandbox/ImageBuilder regressions were **SKIPPED**, not passed.
- Case-collision guard [#44946117568](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44946117568): **PASS**.

The same source-level outcomes were observed on the push runs [shared #44946113976](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44946113976) and [sandbox #44946114020](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44946114020). These are hosted CI results. No real Bubblewrap namespace or ImageBuilder firmware artifact was produced.

### Live ownership, handovers and integration snapshot

- MASTER PR #288 live head: `46cbcd0eac6312d029fd8904e20d362db7dca7db`. Its `coordination/phoenix/OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`; the PHX-RELEASE workflow route remains `reimplementation-review`. No migration or ownership promotion is authorized.
- Experiments RELEASE #242 live head: `734b89d9e7792247e8376335c3f3685500ab3f89`. Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) is completed success. Signing and publication remain unproven/skipped. Its inherited BlazePwifi project handover was read but is not a RELEASE-owned target for this task.
- Experiments RELEASE #291 live head: `42797e2f3d65c30a1070caf49c93aebec149d897`; its `.github/PHX_RELEASE_HANDOVER.md` was read. Compatibility matrix [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) **PASS**. Full build [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) **FAIL** at the CORE-owned handover freshness gate. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) **FAIL** at the shared freshness gate; Windows build and publisher skipped. Its 26-path PR remains mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); no path in #291 was modified.
- COE integration #26 remains frozen at `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows are queued with zero executed jobs.
- COE parent #31 remains the unchanged base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 now has source/test head `d8d051fc` and documentation head `cda3b52c`.
- Cleanup-first #266 remains OPEN, 0/7 checked. This bounded RELEASE cleanup does not complete the wider seven-role cleanup.
- Issue #172's embedded PR-head index remains stale relative to the live #288/#291/#35 heads; PHX-MASTER owns that index correction. RELEASE did not edit the control-plane body.
- Authorized Library search did not surface the canonical private Drive registry v11 file or its newer corrections. Historical registry snapshots were not substituted; no private file contents, Drive identifiers or links were copied to GitHub.

### Next owner actions and release boundary

1. **PHX-QA:** independently review the shared helper and parity regression at exact source/test SHA `d8d051fc14263ed097d94b6f343aad30af30ec08`; no independent review is recorded by RELEASE.
2. **PHX-INFRA:** provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces; no privileged install or unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** reconcile stale #172 PR-head references and preserve the draft-only ownership routes.
5. **Registry custodian:** restore authorized access to canonical private registry v11.

No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.


## PHX-RELEASE UTC21 — build-script executable-mode fsync rollback (2026-11-21)

**Disposition:** one test-first, RELEASE-owned failure-path hardening increment on existing COE child PR #35. PR #35 remains OPEN / DRAFT / UNMERGED. Strict NO Codex. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was modified.

### Finding and bounded correction

`generate_build_script()` writes the complete wrapper, fsyncs the file, fsyncs the parent directory while the new file is still mode 0600, changes the mode to 0755, and fsyncs the executable inode metadata. The success ordering was already tested, but the failure path for that final post-chmod fsync was not.

A test-first regression now simulates failure of that final fsync and requires the generator to:
- attempt a rollback to mode 0600;
- fsync the non-executable mode;
- propagate an OSError rather than report publication success;
- leave the complete wrapper available for diagnosis but non-executable when rollback succeeds.

The source now performs that rollback before propagating the final-mode sync failure. If the rollback chmod or its fsync also fails, the error explicitly states that non-executable rollback could not be confirmed; no stronger guarantee is claimed. Normal successful publication remains unchanged.

### Exact branch and commits

- Repository: BlazeDevStudio/CoinOperatedEcosystem.
- Child PR #35: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35 — OPEN / DRAFT / UNMERGED.
- Branch: `phoenix/release-build-script-publication-safety-20261117`.
- Parent PR #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Test-first RED: [`bd5ef2c7`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/bd5ef2c7e3221e718a787f9b673fcdad68862786).
- Source/test correction: [`0aa7ff85`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0aa7ff85f1a20786b142ab7dc85aa009be68cb1d).
- Exact source/test SHA: `0aa7ff85f1a20786b142ab7dc85aa009be68cb1d`.
- Changed source/test paths: `tools/test_package_appliance_firmware.py`, `tools/package_appliance_firmware.py`.
- This handover is the only documentation path changed for the UTC21 increment.

### Test-first RED at exact test-only SHA `bd5ef2c7`

- Shared/firmware PR [#44950843058](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44950843058): firmware hardening and shared contracts passed; packaging suite ran **153 tests with one expected failure and two intentional skips**. The new test failed because the final-mode fsync error was propagated without a rollback fsync; observed events were `file, directory, file` instead of the required `file, directory, file, file`. All other packaging tests passed. The subsequent all-profile admission and board compilation were skipped after the packaging failure.
- Sandbox PR [#44950843110](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44950843110): host preflight **31/31 PASS**; Bubblewrap availability **FAILED CLOSED** because `bwrap` is absent (exit 125). Namespace and mandatory sandbox/ImageBuilder tests were skipped.
- Case-collision guard [#44950843077](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44950843077): **PASS**.

### Corrected source/test Actions at `0aa7ff85`

- Shared/firmware PR [#44950919161](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44950919161): firmware hardening and shared contracts **PASS**; packaging/tool suite **153 tests PASS / 2 intentional skips**, including the new rollback regression. The next all-profile admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266 and ESP32 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Sandbox PR [#44950919168](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44950919168): host preflight **31/31 PASS**; Bubblewrap availability **FAILED CLOSED** because `bwrap` is absent (exit 125); unprivileged identity, namespace preflight and mandatory sandbox/ImageBuilder regressions were **SKIPPED**, not passed.
- Case-collision guard [#44950919221](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44950919221): **PASS**.

These are hosted CI results. No real Bubblewrap namespace execution, ImageBuilder firmware artifact, target hardware test or production binary was produced.

### Live ownership and integration snapshot

- MASTER PR #288 live head: `60ad84bbd20e20b44d7fdc53c612695308278ab3`. Ownership manifest blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`; the RELEASE workflow route `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml` remains `reimplementation-review`. No migration or ownership promotion is authorized.
- Experiments RELEASE #242 live head: `734b89d9e7792247e8376335c3f3685500ab3f89`. Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) completed success; signing and publication remain unproven/skipped. No separate RELEASE handover file is present in #242's changed-file list; its PR description and workflow record were inspected.
- Experiments RELEASE #291 live head: `42797e2f3d65c30a1070caf49c93aebec149d897`; `.github/PHX_RELEASE_HANDOVER.md` was read. Exact-source compatibility matrix [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) **PASS, 3/3 jobs**. Full build [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) **FAIL** at the CORE-owned `PROJECT_HANDOVER.md` freshness gate; all 14 ESP8266/ESP32/Android/OpenWrt target jobs completed success, but downstream simulations, candidate gate, signing and publication were skipped. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) **FAIL** at the same CORE-owned handover freshness gate; Windows build and publisher were skipped. Its 26 accumulated paths remain mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); no path in #291 was modified.
- COE integration #26 remains frozen at `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows remain queued with zero executed jobs.
- COE parent #31 remains OPEN / DRAFT at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 now has source/test head `0aa7ff85f1a20786b142ab7dc85aa009be68cb1d`.
- Cleanup-first #266 remains OPEN, 0/7 checked. This bounded RELEASE increment does not complete the seven-role cleanup.
- Issue #172's embedded PR-head index remains stale relative to live #288/#291/#35 heads; PHX-MASTER owns that index correction. RELEASE did not edit the control-plane body.
- Authorized Library search did not surface the canonical private Drive registry v11 file or newer corrections. Historical snapshots were not substituted; no private contents, Drive identifiers or links were copied to GitHub.

### Next owner actions and release boundary

1. **PHX-QA:** independently review exact source/test SHA `0aa7ff85f1a20786b142ab7dc85aa009be68cb1d`, including the rollback-success and rollback-failure reporting boundary.
2. **PHX-INFRA:** provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces; no privileged install or unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** reconcile stale #172 PR-head references and preserve the draft-only ownership routes.
5. **Registry custodian:** restore authorized access to canonical private registry v11.

No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.


## PHX-RELEASE UTC22 — centralize ImageBuilder private-host mount policy (2026-11-21)

**Disposition:** one RELEASE-owned, behavior-preserving cleanup completed on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**. Strict NO Codex. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was modified.

### Finding and bounded change

The host preflight (tools/check_imagebuilder_sandbox_host.py) and runtime (tools/run_imagebuilder_sandbox.py) independently defined the same private-host mask list and duplicated the argument builder. Both currently used /home, /root, /run, /mnt, /media, and /srv, but future drift could let preflight validate a different mount boundary from the actual build.

The shared RELEASE-owned helper tools/imagebuilder_bwrap_trust.py now owns:
- the immutable PRIVATE_HOST_PATHS tuple;
- private_host_mount_args(), which emits the canonical ordered --tmpfs <path> arguments.

Both preflight and runtime import the same tuple and function. Their command construction still consumes the same arguments in the same order; no mount, network, UID/GID, timeout or sandbox behavior was changed.

A regression requires both modules to expose the same function object and the same path tuple object, and checks that the host probe command contains the complete expected ordered mask. This prevents the two security-sensitive entry points from silently drifting apart.

### Test-first and correction history

- Test-first commit: [0fe87b21](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0fe87b21ba2809c2d2d177398474236a9deffb2f). The new parity test failed as intended because preflight and runtime still owned separate helper functions. Push shared run [#44955866268](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44955866268): **154 tests, one expected failure, two intentional skips**. Push sandbox [#44955866285](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44955866285): host preflight **31/31 PASS**, then Bubblewrap unavailable / exit 125; namespace and mandatory packaging steps skipped. Case-collision PR [#44955870576](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44955870576): PASS.
- First source attempt: [ae66c912](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/ae66c912d7f264abe7c1733929f2e01d12e03bad). It centralized the helper but initially removed the runner module's PRIVATE_HOST_PATHS export, causing an existing context-verification test to raise NameError. This implementation failure was retained and corrected; it is not counted as a pass. Push shared [#44955932083](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44955932083): **154 tests, one error, two intentional skips**. Push sandbox [#44955932093](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44955932093): host tests **31/31 PASS**, then Bubblewrap unavailable / exit 125.
- Corrected source/test commit: [660491c6](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/660491c638ae42d70a70bd501cf445dc7e8fb437). Both modules now import the shared path tuple and function; the regression also asserts tuple identity. Only four RELEASE-owned source/test paths changed:
  - tools/imagebuilder_bwrap_trust.py
  - tools/run_imagebuilder_sandbox.py
  - tools/check_imagebuilder_sandbox_host.py
  - tools/test_package_appliance_firmware.py

### Exact-source Actions at 660491c6

- PR shared/firmware validation [#44956003561](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44956003561), job 137004165148: firmware syntax and shared-contract tests **PASS**; packaging/tool suite **154 tests PASS / 2 intentional skips**, including the new parity regression; PHX-MANIFEST-DURABILITY-PASS. The following ten-profile staging/admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority is not defined. ESP8266 and ESP32 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Push shared/firmware [#44955997258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44955997258): same source/test head and the same profile-admission gate; no board compilation credited.
- PR ImageBuilder sandbox [#44956003470](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44956003470), job 137004165028: host preflight **31/31 PASS**; Bubblewrap availability **FAILED CLOSED** because bwrap is absent (exit 125); unprivileged identity, namespace preflight and mandatory sandbox packaging regressions were **SKIPPED**, not passed.
- Push ImageBuilder sandbox [#44955997243](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44955997243): same host-test and Bubblewrap boundary.
- PR case-collision guard [#44956003397](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44956003397): **PASS**.

These are hosted CI results. The new parity regression uses Python test fixtures. No actual Bubblewrap namespace execution, ImageBuilder firmware artifact, target hardware test or production binary was produced.

### Live ownership and integration snapshot

- MASTER PR #288 live head: 6acb97c2a3649d449a35b12815943f571b17c83d, base Experiments main f4e8a891aed8af86d5fd315d28750a0ac3a7372b. OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY; the RELEASE workflow route .github/workflows/blazepwifi-build.yml → .github/workflows/pisowifi-ci.yml remains reimplementation-review. No migration, copy or ownership promotion is authorized.
- Experiments RELEASE #242 live head: 734b89d9e7792247e8376335c3f3685500ab3f89. Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) completed SUCCESS: handover and Windows build jobs passed; signing and publication steps were skipped.
- Experiments RELEASE #291 live head: 42797e2f3d65c30a1070caf49c93aebec149d897, branch phoenix/release-publisher-isolation-20261115, 26 accumulated mixed-owner paths (21 RELEASE / 3 CORE / 2 PISONET). Compatibility matrix [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed 3/3 jobs. Full build [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) failed at the CORE-owned handover freshness gate; dependent validation/build/release steps were skipped. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at the same freshness gate; Windows build and publisher were skipped. PHX-RELEASE did not edit the mixed-owner PR.
- COE integration #26 remains OPEN / DRAFT / FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12; five workflows remain QUEUED with zero executed jobs.
- COE parent #31 remains OPEN / DRAFT at 59ed44d0b911e176f1a95b9cf5585ef811ffd31b, based on #26. Its last exact-head shared validation [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) and case-collision [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) passed; sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) failed closed because Bubblewrap is unavailable.
- COE child #35 remains OPEN / DRAFT / UNMERGED on phoenix/release-build-script-publication-safety-20261117, base #31 59ed44d0b911e176f1a95b9cf5585ef811ffd31b; exact source/test head is 660491c638ae42d70a70bd501cf445dc7e8fb437.
- Cleanup-first #266 remains OPEN, **0/7** tracks checked. This bounded RELEASE increment is not completion of the seven-role cleanup.
- Issue #172's embedded PR-head index remains stale relative to live owner PR heads; PHX-MASTER owns that index correction. RELEASE did not edit the control-plane body.
- Canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections remain inaccessible through the authorized Library/connector surface. Historical checkpoint metadata is provenance only; no older snapshot was substituted and no private contents or identifiers were copied to GitHub.

### Next owner actions and release boundary

1. **PHX-QA:** independently review the exact source/test SHA 660491c638ae42d70a70bd501cf445dc7e8fb437, especially that preflight and runtime use the same immutable path tuple and function.
2. **PHX-INFRA:** provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces; no privileged install or unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix.
4. **PHX-MASTER:** reconcile stale #172 PR-head references and preserve the draft-only ownership routes.
5. **Registry custodian:** restore authorized access to canonical private registry v11.

No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.


## PHX-RELEASE UTC23 — deterministic ESP firmware artifact manifests and checksums (2026-11-21)

**Disposition:** one RELEASE-owned artifact-provenance feature was added to the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**. Strict NO Codex. No firmware sketch, shared API, network profile, ULA authority, CORE, RENTAL, PISONET, HARDWARE implementation, QA or MASTER source was changed.

### Scope and output contract

The existing `.github/workflows/hardware-ci.yml` uploaded ESP8266 and ESP32 build directories without a source-bound manifest or a portable checksum list. The two existing board jobs now run a RELEASE-owned manifest writer after compilation and before the existing artifact upload:

- `tools/write_firmware_artifact_manifest.py`
- `artifact-manifest.json`, schema `phoenix/firmware-artifact/v1`
- `SHA256SUMS`, covering every payload file plus `artifact-manifest.json`

Each manifest records repository, checked-out Git SHA, GitHub event SHA (which must match the checked-out SHA), PR head/base SHAs when present, product, board, FQBN, Arduino CLI version, board-core ID/version, and sorted relative file paths with byte sizes and SHA-256 digests. The JSON and checksum text are deterministic for identical inputs; no wall-clock timestamp is embedded.

The writer fails closed on missing/empty `.bin` payloads, unsafe relative paths, symlinked/non-regular/hard-linked files or directories, pre-existing output names, invalid provenance fields, source/event SHA mismatch, and incomplete directory enumeration. Manifest and checksum outputs are created exclusively (no overwrite), file-synced, then the directory is synced. The existing upload steps remain in place and include both files automatically through their existing directory paths.

The manifest schema is local to this RELEASE artifact boundary; no MASTER/shared interface or COE migration contract was changed.

### Test-first, corrections and exact commits

- Test-first commit [18bddcf2](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/18bddcf2958d2e97efc7b2dab051685e3f52bf35) added the missing-module and workflow-contract regressions before the writer existed. Exact PR run [#44960978732](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44960978732), job 137019489806, failed at the packaging test step with the expected `ModuleNotFoundError: write_firmware_artifact_manifest`. The sandbox run [#44960978721](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44960978721) independently failed closed because Bubblewrap was absent; it is not part of the expected test RED.
- Initial writer commit [6e93c356](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6e93c356b42a4bb97fd37d937d2e3c2d4f015ff0) added the deterministic payload builder and no-overwrite writer. Its exact-source shared run [#44961036034](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44961036034), job 137019668125, exposed two test-stage issues: the empty-`.bin` assertion regex did not match the diagnostic, and the workflow wiring was not yet present. These were test-contract/integration gaps, not firmware defects.
- Test assertion correction [84637bd9](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/84637bd9fafddb19d10200d56b9917fa7cd67137) aligned the expected diagnostic. Workflow integration [d5032eec](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/d5032eec4c0637fede6edf57123eda3bab5130d8) added the ESP8266/ESP32 manifest steps with exact FQBN/core pins and source/event/PR identity.
- A further test-first commit [a7e1be59](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a7e1be599d438e82ea8b62acae8ffa3de2782958) injected an artifact-directory enumeration error. Exact run [#44961216021](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44961216021), job 137020218310, logged the expected failure because `os.walk` had no `onerror` callback; that workflow run was later cancelled by the superseding source push, so it is recorded as an expected test RED, not a completed green/red workflow.
- Source correction [6ecbbd98](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6ecbbd980fbb594b805a6bde53905eb3320ee3eb) makes directory enumeration fail closed. CLI coverage [ce57bce1](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/ce57bce198ce0f3f5e901f386d54964e722ee321) exercises the exact argparse entry point and verifies both output files and provenance markers.

### Exact final-head GitHub Actions

Final PR/source-test HEAD: `ce57bce198ce0f3f5e901f386d54964e722ee321`.

- PR shared/firmware run [#44961307523](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44961307523), job 137020493399: firmware syntax and shared-contract checks **PASS**; packaging/tool suite **165 tests PASS / 2 intentional skips**, including deterministic output, source/event SHA binding, symlink/hardlink rejection, empty/missing binary rejection, incomplete-walk rejection, CLI execution and both workflow wiring contracts. `PHX-MANIFEST-DURABILITY-PASS` was emitted. The following ten-profile staging/admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266 and ESP32 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Push shared/firmware run [#44961312084](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44961312084), job 137020506867: same final source head and same 165-test/profile-gate result.
- Final-head case-collision guard [#44961312140](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44961312140): **PASS**.
- Final-head sandbox run [#44961312088](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44961312088), job 137020506966: host preflight **31/31 PASS**, then Bubblewrap availability **FAILED CLOSED** because `bwrap` is not installed (exit 125); namespace and mandatory sandbox packaging regressions were **SKIPPED**, not passed.

**Artifact evidence boundary:** the new writer and CLI were exercised against disposable synthetic files in hosted CI. The real ESP8266/ESP32 build jobs were skipped by the existing all-profile ULA admission gate, so no actual board binary, uploaded firmware artifact, or generated production manifest was produced in this activation. No target compile or hardware acceptance is claimed.

### Live ownership and integration snapshot

- MASTER PR #288 live API head: `e2a6934cd2dba8e7c3df6a972cf0a6a3d6c255d2`, base Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, OPEN / DRAFT, 160 changed paths. `coordination/phoenix/OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`; PHX-MASTER target is null and the RELEASE route `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml` remains `reimplementation-review`. No migration or ownership promotion is authorized.
- Experiments RELEASE #242 live head `734b89d9e7792247e8376335c3f3685500ab3f89`, base `6d4c9b487af4d768c4d7627654d119417fcc6e00`. Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) completed SUCCESS; signing and publication were skipped.
- Experiments RELEASE #291 live head `42797e2f3d65c30a1070caf49c93aebec149d897`, base #242 `734b89d9e7792247e8376335c3f3685500ab3f89`, 26 accumulated mixed-owner paths (21 RELEASE / 3 CORE / 2 PISONET). ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed 3/3. Full build [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) failed at the CORE-owned handover freshness gate; all 14 target/Android build jobs completed successfully, while dependent simulations/candidate/signing/publication stages were skipped. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at the shared handover freshness gate before the Windows build and publisher; those stages were skipped. RELEASE did not edit this mixed-owner PR.
- COE integration #26 remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`, base COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; five workflows remain QUEUED with zero executed jobs.
- COE parent #31 remains OPEN / DRAFT at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`, based on #26. Shared validation [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) and case-collision [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) passed. Sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) installed Bubblewrap and passed host/identity checks, then failed closed at unprivileged UID-map setup (`Permission denied`, exit 125); mandatory sandbox packaging tests were skipped.
- COE child #35 remains OPEN / DRAFT / UNMERGED on `phoenix/release-build-script-publication-safety-20261117`, base #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; final head `ce57bce198ce0f3f5e901f386d54964e722ee321`. Its 12 changed paths are confined to `.github/workflows/` and `tools/` release CI/packaging/test/handover paths; no firmware sketch or shared interface was changed.
- Related ULA provisioning candidate COE #44 is a separate OPEN / DRAFT PHX-RELEASE branch `phoenix/release-ula-installation-identity-20261118`, head `582fd5d5e83e36b36546ac28534740298ba94af4`, based on old #35 SHA `1a5be48d2845781b0b07bad39a37f8440cea4d4f`. Its five changed paths are release packaging/tests/workflow/handover only. Exact-head shared run [#44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309) succeeded: 109 packaging tests / 2 intentional skips, 18 hardening/shared checks, 10/10 profiles, ESP8266 and ESP32 compile/upload; case guard [#44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296) passed. Sandbox [#44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) failed closed because Bubblewrap is absent (exit 125). The ULA branch generates a per-installation prefix but explicitly does not prove MASTER §6.9 same-site multi-appliance prefix sharing. Compare current #35 `ce57bce198ce0f3f5e901f386d54964e722ee321` to #44 `582fd5d5e83e36b36546ac28534740298ba94af4`: DIVERGED, #44 15 commits ahead / current #35 110 commits ahead from merge base `1a5be48d2845781b0b07bad39a37f8440cea4d4f`. No cherry-pick, rebase, merge or ownership promotion was performed; retain #44 as a separate draft pending PHX-MASTER / PHX-CORE / COE integration decision.
- Cleanup-first #266 remains OPEN, **0/7** tracks checked. This bounded RELEASE task is not completion of the seven-role cleanup.
- Issue #172's embedded PR-head index is stale: it still lists older #288/#291/#35 heads than the live PR API values above. PHX-MASTER owns the control-plane index correction; RELEASE did not edit the issue body.
- The exact private registry search surfaced older v3–v7 provenance files but did not surface canonical private Drive registry v11 or newer corrections. No older registry was substituted; no private file contents or identifiers were copied to GitHub.

### Next owner actions and release boundary

1. **PHX-QA:** independently review exact source/test head `ce57bce198ce0f3f5e901f386d54964e722ee321`, especially source/event SHA equality, manifest path safety, checksum coverage and no-overwrite behavior.
2. **PHX-INFRA:** provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces; no privileged install or unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 and persistence contract; RELEASE will not invent a prefix or bypass profile admission.
4. **PHX-MASTER:** reconcile stale #172 PR-head references while preserving draft-only ownership routes.
5. **Registry custodian:** restore authorized access to canonical private registry v11.

No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.

## PHX-RELEASE UTC00 — durable rollback for firmware artifact manifest/checksum publication (2026-11-22)

**Disposition:** one RELEASE-owned failure-path defect reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Exact branch and commits

- Repository: BlazeDevStudio/CoinOperatedEcosystem.
- PR: [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`.
- Parent #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Test-first regression commit: [`beab4441`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/beab44413c5c5f5e022e53ea18aff843a21d5573).
- Corrected source/test commit: [`1c9ee385`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/1c9ee3858a07ce6b1853d75576c042b521cfcd50).
- Scope: `tools/test_firmware_artifact_manifest.py`, `tools/write_firmware_artifact_manifest.py`, and this handover only. No firmware sketch, shared interface, ULA/network policy, or other-role source changed.

### Failure reproduced and correction

The writer published `artifact-manifest.json` and `SHA256SUMS`, then fsynced the directory. If the second file creation or the final directory fsync failed, it removed already-created output names but did not fsync the directory after rollback. Cleanup unlink errors were also silently ignored. A crash could therefore leave a partial pair or an unconfirmed rollback while the CLI reported failure.

Three test-first regressions were added:

1. A failure creating `SHA256SUMS` after the manifest exists must remove the manifest and fsync the directory after removal.
2. A failed final directory fsync must remove both published names and perform a second directory fsync after rollback.
3. If rollback unlink fails, the writer must explicitly report that rollback could not be confirmed rather than silently re-raising only the original publication error.

The source correction opens the artifact directory for durable publication before creating outputs, rejects missing `O_DIRECTORY` support before writing, syncs each file, syncs the directory after successful pair publication, and syncs again after rollback. Partial-file cleanup also attempts a directory sync. Any failed removal or rollback sync is surfaced as `ManifestError` with an explicit “rollback could not be confirmed” diagnostic. Existing no-overwrite behavior and manifest/checksum format are unchanged.

### Test-first and exact-source Actions

**Test-only commit `beab4441` — expected RED**

- Shared/firmware [#44966151617](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44966151617), job `137035515848`: **168 tests executed; 2 failed and 1 errored**, exactly the three new rollback regressions. The two failures observed no directory fsync after rollback; the error showed the injected unlink denial was swallowed and the original `FileExistsError` escaped instead of a rollback-specific error. Profile staging and board builds were skipped after the test step failed.
- Sandbox [#44966151822](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44966151822), job `137035516816`: host preflight **31/31 PASS**, then Bubblewrap missing / exit 125; namespace and mandatory sandbox packaging steps SKIPPED.
- Case-collision [#44966151579](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44966151579): **PASS**.

**Corrected source/test commit `1c9ee385`**

- Shared/firmware [#44966235503](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44966235503), job `137035782564`: **168 tests PASS / 2 intentional skips**; firmware syntax, shared contracts, packaging/tool tests and manifest durability marker PASS. The following all-profile admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP32 and ESP8266 compile jobs were SKIPPED. Overall workflow is **FAILURE**, not green.
- Sandbox [#44966235511](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44966235511), job `137035782579`: host preflight **31/31 PASS**, then Bubblewrap absent / exit 125. Identity, namespace and mandatory sandbox packaging steps SKIPPED.
- Case-collision [#44966235508](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44966235508): **PASS**.

These are hosted synthetic CI results. No actual ESP32/ESP8266 artifact was built; both board compile jobs were skipped by the existing profile-admission gate. No real Bubblewrap namespace or ImageBuilder execution was performed.

### Current blockers and next owners

1. **PHX-CORE / site ULA authority / PHX-MASTER:** define and approve the durable site-scoped RFC 4193 ULA /48 source and same-site multi-appliance provisioning contract. RELEASE must not invent a prefix or bypass profile admission.
2. **PHX-INFRA:** provide an authorized disposable runner with Bubblewrap preinstalled and working unprivileged user namespaces. No privileged installation or unsandboxed fallback.
3. **PHX-QA:** independently review the rollback failure-injection tests and exact source/test SHA `1c9ee3858a07ce6b1853d75576c042b521cfcd50`.
4. **PHX-MASTER:** refresh stale control-plane PR-head pins and reconcile release ownership routes. No migration or ownership promotion was performed.
5. **Registry custodian:** canonical private Drive project registry v11 and newer corrections remain unavailable through the authorized Library surface. Older v3–v7 provenance snapshots were not substituted; no private content or identifiers were copied to GitHub.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.

---



## PHX-RELEASE UTC01 — pin manifest publication to the scanned artifact directory (2026-11-22)

**Disposition:** one RELEASE-owned artifact-integrity race reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Exact branch and commits

- Repository: BlazeDevStudio/CoinOperatedEcosystem.
- PR: [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`.
- Parent #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Test-first regression / expected RED: [`bc7550fc`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/bc7550fcc2c4920687017c2503407d77a6c1569a).
- Corrected source/test SHA: [`94fffa03`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/94fffa0343f2481a3098e96885e6b9cd15f8d671).
- Final handover is this documentation commit; no workflow, firmware sketch, board profile, shared interface, or other-role source was changed in this increment.

### Defect reproduced and correction

The manifest writer previously scanned artifact files by path, then opened the artifact directory by path only after the scan. A deterministic race replaced the scanned directory with a different real directory after payload enumeration but before publication. The old writer returned success and placed `artifact-manifest.json` and `SHA256SUMS` into the replacement directory, even though the recorded payload hashes came from the displaced original directory.

The test-first regression renames the scanned artifact directory and installs a separate empty directory at the original path after the payload scan. The original writer did not reject the identity change.

The correction:
- Opens the artifact directory with `O_DIRECTORY | O_NOFOLLOW` before scanning.
- Compares the path's `lstat` identity with the pinned descriptor's `fstat` identity after scanning and again after publication.
- Requires the path to remain a real, non-symlink directory resolving to itself.
- Creates and removes output names relative to the pinned directory descriptor (`dir_fd`), so a later pathname replacement cannot redirect publication or rollback into a different directory.
- Rolls back a just-published pair and syncs the pinned directory if the post-publication identity check fails.

The manifest schema, source/event SHA binding, payload inventory, SHA256SUMS format, no-overwrite behavior, and board workflow interfaces are unchanged.

### Test-first and exact-source Actions

**Test-only commit `bc7550fc` — expected RED**
- Push shared/firmware [#44970909570](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44970909570), job `137050262247`: **169 tests executed; exactly one failure** in the new directory-replacement regression; two intentional skips. The failure was `ManifestError not raised`, confirming that the old writer accepted the replaced directory. Profile staging and board compilation were skipped after the packaging test step failed.
- PR shared/firmware [#44970912621](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44970912621): same expected test-first failure at the same SHA.
- Case-collision [#44970912622](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44970912622): **PASS**.
- Sandbox [#44970912611](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44970912611): host preflight **31/31 PASS**, then Bubblewrap absent / exit 125; namespace and mandatory sandbox packaging tests **SKIPPED**.

**Corrected source/test head `94fffa03`**
- Push shared/firmware [#44971075013](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44971075013), job `137050761696`: **169 packaging/tool tests PASS / 2 intentional skips**; firmware syntax, shared contracts and manifest durability marker PASS. The following all-profile admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority is undefined. ESP32/ESP8266 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- PR shared/firmware [#44971080205](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44971080205), job `137050778865`: same **169 PASS / 2 skips**, followed by the same ten-profile ULA admission failure; both board compile jobs **SKIPPED**.
- Sandbox PR [#44971080214](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44971080214), job `137050778975`: host preflight **31/31 PASS**, then Bubblewrap absent / exit 125; unprivileged namespace and mandatory sandbox packaging steps **SKIPPED**.
- Case-collision [#44971080228](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44971080228): **PASS**.

These are hosted CI and deterministic filesystem fault-injection results. No real OpenWrt ImageBuilder package, production firmware, target-device run, hardware flash, or physical acceptance is established.

### Live cross-repository ownership and blockers

- MASTER #288: `f4e375ffca2bd0a17160d1fd41ead7c50274cdab`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY` at blob `e4db324315a1b3543fec17a148fbf960170fcb29`; RELEASE route remains `reimplementation-review`.
- RELEASE #242: `734b89d9e7792247e8376335c3f3685500ab3f89`; Windows [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) succeeded, while signing and publication remain skipped.
- RELEASE #291: `42797e2f3d65c30a1070caf49c93aebec149d897`; ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed 3/3; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at the CORE-owned handover freshness gate. The 26-path branch remains mixed-owner; RELEASE did not modify it.
- COE integration #26 remains frozen at `b382d233ff06c8791b1028bed3c617cc7b670d12`, with five workflows queued and zero jobs.
- COE parent #31 remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 remains OPEN / DRAFT / UNMERGED at source/test SHA `94fffa03`.
- Cleanup-first #266 remains OPEN, 0/7 tracks checked.
- Canonical private Drive registry v11 and newer corrections were not surfaced through authorized Library access. Older snapshots were not substituted; no private contents or identifiers were copied to GitHub.

### Accumulated child-PR ownership hold

The live COE #35 changed-file list also includes `.github/workflows/hardware-ci.yml` (83 additions / 9 deletions), which is not part of parent #31's changed-file list. The current MASTER `OWNERSHIP_ROUTES.json` lists the RELEASE workflow route as `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml`; it does not list `hardware-ci.yml`. The current role assignment says RELEASE owns its release workflow/package paths, and the route manifest remains DRAFT_REVIEW_ONLY. **This UTC01 activation did not modify `hardware-ci.yml`**; no further edit, revert, migration or merge of that file is authorized by this task. PHX-HARDWARE and PHX-MASTER must explicitly confirm ownership and review the inherited manifest-integration changes before any merge decision. The current UTC01 source/test change is limited to the two RELEASE manifest writer/test files.

### Next owner actions

1. **PHX-QA:** independently review exact source/test SHA `94fffa0343f2481a3098e96885e6b9cd15f8d671`, especially directory identity pinning, dir-fd output creation/rollback, and both pre/post-publication identity checks.
2. **PHX-CORE / site authority / PHX-MASTER:** define and approve the site-scoped RFC 4193 ULA /48 and same-site multi-appliance contract; RELEASE will not invent a prefix or bypass admission.
3. **PHX-INFRA:** provide an authorized disposable, ephemeral, no-secret Bubblewrap runner with working unprivileged namespaces.
4. **PHX-MASTER:** refresh stale #172 PR-head references and retain the DRAFT_REVIEW_ONLY ownership route.
5. **Registry custodian:** restore authorized access to canonical private registry v11.

No merge, real-key signing, tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.

---


## PHX-RELEASE UTC02 — pin nested artifact traversal to directory descriptors (2026-11-22)

**Disposition:** one RELEASE-owned firmware-manifest traversal race was reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**. Strict NO Codex.

### Exact branch and commits

- Repository: BlazeDevStudio/CoinOperatedEcosystem.
- PR: [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`.
- Parent #31 / base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Test-first race regression: [`96a1fe34`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/96a1fe341e955e68a07c3501866798988c145521).
- First descriptor-traversal implementation attempt: [`8c6e49b2`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8c6e49b22398e9b565416992c6d3e0ed8c34ac74) — failed three test cases; superseded, not treated as green.
- Corrected source/test SHA: [`b2ddc03c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b2ddc03c9ea2e48a4353564c5683147e4d409553).
- Scope: `tools/write_firmware_artifact_manifest.py`, `tools/test_firmware_artifact_manifest.py`, and this handover only. No workflow, firmware sketch, board profile, shared interface, network policy, or other-role runtime source changed in this increment.

### Defect reproduced and correction

The previous scanner used `os.walk(root)`, checked nested directory entries by pathname, then opened payload files by pathname with `O_NOFOLLOW`. That flag protects only the final file component; a parent directory component can still be replaced by a symlink between the directory check and payload open.

The deterministic regression creates `nested/extra.bin`, then at the file-open boundary renames `nested` outside the artifact root and replaces `nested` with a symlink to the displaced directory. The old scanner followed the parent symlink, opened the same inode, passed its before/after file identity comparison, and returned a manifest entry for a payload no longer contained by the artifact tree. The test requires a `ManifestError` and fails against the prior source with `ManifestError not raised`.

The correction uses descriptor-relative traversal:

- Open and pin the artifact root; pass the same root descriptor from publication into payload scanning.
- Enumerate each directory through its pinned descriptor.
- Inspect entries with `os.stat(..., dir_fd=..., follow_symlinks=False)`.
- Open child directories relative to their pinned parent with `O_DIRECTORY | O_NOFOLLOW`, compare the opened inode with the pre-open entry, recurse through the child descriptor, and revalidate the parent entry after traversal.
- Open payload files relative to the pinned directory descriptor with `O_NOFOLLOW`, compare file identity and link count, and revalidate the directory entry after hashing.
- Fail closed when POSIX directory-descriptor flags are unavailable or descriptor-relative operations fail.

The manifest schema, source/event SHA binding, sorted relative paths, payload sizes and hashes, SHA256SUMS format, exclusive no-overwrite publication, durable rollback, and board workflow interfaces are unchanged. The existing root-directory identity checks remain in place.

The prior unreadable-walk regression now injects a descriptor-listing error. Existing symlinked-file, symlinked-directory, hard-link, incomplete-enumeration, root-replacement, deterministic-output and rollback tests remain in the suite.

### Test-first and exact-source Actions

**Test-only commit `96a1fe34` — expected RED**

- Push shared/firmware [#44975708250](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44975708250), job `137065018668`: **170 tests executed; exactly one failure** in `test_writer_rejects_nested_directory_replaced_with_symlink_before_file_open`, with `ManifestError not raised`. Two intentional skips. Firmware syntax and shared-contract checks passed before the packaging test step; profile admission and board builds were skipped after the expected test failure.
- PR shared/firmware [#44975712400](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44975712400): same test-first failure at the same test-only head.
- Case-collision [#44975712291](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44975712291): **PASS**.
- Sandbox [#44975712368](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44975712368): host preflight **31/31 PASS**, then Bubblewrap unavailable / exit 125; namespace and mandatory sandbox packaging steps **SKIPPED**.

**First implementation attempt `8c6e49b2` — failed validation, corrected immediately**

- Push shared/firmware [#44975911302](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44975911302), job `137065664668`: **170 tests executed; 3 failed**. The descriptor-support probe compared monkeypatched OS functions by identity, preventing the injected directory-scan and race paths from reaching their intended assertions; the generic symlink diagnostic also did not satisfy the existing symlinked-file assertion. This was an implementation/test-harness integration failure, not a passing run. The next commit removed the brittle function-identity probe, retained runtime fail-closed handling for unsupported descriptor operations, and made the symlink diagnostic satisfy both file and directory rejection contracts.

**Corrected source/test head `b2ddc03c`**

- Push shared/firmware [#44976106605](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44976106605), job `137066297818`: **170 tests PASS / 2 intentional skips**; firmware syntax, shared contracts and manifest durability marker PASS. The following ten-profile admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266 and ESP32 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- PR shared/firmware [#44976110414](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44976110414), job `137066309756`: same exact-source result — **170 PASS / 2 skips**, followed by the ten-profile ULA admission failure; both board compile jobs **SKIPPED**.
- PR ImageBuilder sandbox [#44976110521](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44976110521), job `137066309409`: host preflight **31/31 PASS**, then Bubblewrap unavailable / exit 125; unprivileged identity, namespace and mandatory sandbox packaging steps **SKIPPED**.
- Case-collision [#44976110381](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44976110381), job `137066309178`: **PASS**.

These are hosted synthetic filesystem race and unit-test results. No real ESP32/ESP8266 artifact was built at this head, because profile admission failed before the board jobs. No Bubblewrap namespace or ImageBuilder execution occurred.

### Live ownership, integration and provenance snapshot

- MASTER PR #288 live head: `b2a9c028314ad7eb269bdf9145ce7c1b1c612a9b`. `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`; the RELEASE route is `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml`, kind `reimplementation-review`. It does not authorize the inherited `.github/workflows/hardware-ci.yml` path in COE #35. No route or ownership change was made.
- Experiments RELEASE #242 live head: `734b89d9e7792247e8376335c3f3685500ab3f89`. Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) completed SUCCESS; build, parity and negative signing controls passed, but actual Authenticode signing steps and GitHub Release publication were skipped.
- Experiments RELEASE #291 live head: `42797e2f3d65c30a1070caf49c93aebec149d897`. ESP32 compatibility PR run [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed the provenance suite and both ESP32 core 3.3.13 / 4.0.0 jobs. Full run [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) failed at the mandatory handover-freshness gate; 14/14 target/platform build jobs passed, while simulations, update bundle, signing and publication were skipped. Windows run [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at the shared handover gate before Windows build/publisher; those jobs were skipped. The 26-path branch remains mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); RELEASE did not edit it.
- COE integration #26 live head: `b382d233ff06c8791b1028bed3c617cc7b670d12`; eight existing workflow runs (five PR and three push) remain QUEUED, with no jobs executed.
- COE parent #31 live head/base for child #35: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. Shared run [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) passed validation and both ESP board build/upload jobs; case-collision [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) passed. Sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) failed at unprivileged UID-map setup (`Permission denied`); mandatory sandbox packaging regressions were skipped.
- COE child #35 remains OPEN / DRAFT / UNMERGED. The source/test head for this increment is `b2ddc03c9ea2e48a4353564c5683147e4d409553`; this handover commit will be the docs head. The accumulated 12-path PR still includes inherited `.github/workflows/hardware-ci.yml` (83 additions / 9 deletions), outside the current MASTER RELEASE route. This activation did not modify that workflow; PHX-HARDWARE and PHX-MASTER must explicitly confirm ownership and review the inherited changes before any merge decision.
- Cleanup-first #266 remains OPEN, **0/7** tracks checked. Issue #172's embedded PR-head index remains stale against live PR API heads; PHX-MASTER owns that correction.
- Canonical private Drive project registry v11 and newer corrections were not surfaced through the authorized Library listing/search. Older v3–v7 snapshots were not substituted; no private file contents or identifiers were copied to GitHub.

### Next owner actions and release boundary

1. **PHX-QA:** independently review exact source/test SHA `b2ddc03c9ea2e48a4353564c5683147e4d409553`, focusing on dir_fd traversal, nested-directory replacement, symlink/hard-link rejection, file identity checks and deterministic manifests.
2. **PHX-CORE / site authority / PHX-MASTER:** define and approve the site-scoped RFC 4193 ULA /48 and same-site multi-appliance provisioning contract; RELEASE must not invent a prefix or bypass profile admission.
3. **PHX-INFRA:** provide an authorized disposable runner with pre-provisioned Bubblewrap and working unprivileged single-ID namespaces; no privileged installation or unsandboxed fallback.
4. **PHX-HARDWARE / PHX-MASTER:** resolve ownership and review the inherited `.github/workflows/hardware-ci.yml` changes before any merge decision.
5. **PHX-MASTER:** refresh stale #172 PR-head references while retaining `DRAFT_REVIEW_ONLY` ownership routes.
6. **Registry custodian:** restore authorized access to canonical private registry v11.

No merge, real-key signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.

---


## UTC02 post-audit MASTER index reconciliation — read-only ownership finding

After the main UTC02 handover was written, the live MASTER PR #288 files were re-read at head `b2a9c028314ad7eb269bdf9145ce7c1b1c612a9b`:

- `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` still says `DRAFT_REVIEW_ONLY`; PHX-RELEASE remains limited to `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml`, kind `reimplementation-review`.
- MASTER `ROLE_ASSIGNMENTS.md` blob `69d360458c54eaff4dc6474777ae3675632e5385` does not contain the live COE #35 head `391663cfca336a78a09d23492363fdee554be074`; its latest RELEASE row still pins the older #35 head `048c6d2f11ef9635c93f22caa3258a25e819a644`.
- MASTER `INTEGRATION_MATRIX.md` blob `b5dbbe7386799851eb2b0f40973048bb4a77b0cd` likewise contains older COE #35 pins (latest inspected row `0d6b9edce4caff16df64c15fedbd11e4640dfdde`), not the live head `391663cf`.

This is a stale coordination/index finding only. PHX-RELEASE did not modify MASTER files, change the ownership route, or infer migration authority. PHX-MASTER owns refreshing its own role assignment, integration matrix and #172 exact-head index before using them for merge/release decisions. The inherited `.github/workflows/hardware-ci.yml` path remains outside the published RELEASE route and requires PHX-HARDWARE/PHX-MASTER review.
---

## PHX-RELEASE UTC03 — reject in-place payload mutation during artifact hashing (2026-11-22)

**Disposition:** one release-owned manifest-integrity defect reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

### Defect and correction

The descriptor-relative scanner already pinned the payload inode, rejected symlinks/hard links, compared the directory entry before/after reading, and verified that the number of bytes read equaled the initial file size. It did not take a second descriptor metadata snapshot after the read loop. A same-inode, same-size in-place rewrite during hashing could therefore leave the pathname and size checks unchanged while the manifest represented bytes read before the rewrite rather than the file's final contents.

The regression uses a payload larger than the 1 MiB read chunk, mutates the already-read first chunk in place without changing file length, and requires the writer to reject the file before either output manifest is published.

The correction compares the opened descriptor's post-read snapshot against its pre-read snapshot: device, inode, mode, link count, size, nanosecond mtime and nanosecond ctime. It then compares the directory entry against that finished descriptor snapshot before recording the digest. The manifest schema, checksum format, source/event SHA binding, descriptor-relative traversal and publication/rollback behavior are unchanged.

### Test-first and implementation history

- Test-first regression: [commit 3a05f6a5](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3a05f6a5aaf83886edb2ec417b61669b226d56ce).
- Expected RED: [PR validation #44979605926](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979605926) — 171 tests executed, 1 expected failure (ManifestError not raised), 2 intentional skips. The mutation completed with the same inode and file length and was incorrectly accepted by the pre-fix scanner.
- First source attempt: [commit 4b8bf24d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/4b8bf24dca4a8ccac96e7272ea4e08e411ea4a57). It accidentally replaced the complete writer with a partial line-range response. Exact PR run [#44979674178](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979674178) failed at import with IndentationError: unexpected indent; the push run was also failed. This was an implementation error, not a passing result.
- Recovery and corrected source/test: [commit cafb202c](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/cafb202cfc7b779c1df929b3388bc31f392bcbdf). The complete 511-line pre-fix writer was restored from the immediately preceding test-only commit, then the 19-line stability check was applied to the full file (530 lines total).

### Exact-source CI at cafb202c

- Push shared validation [#44979728564](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979728564): **171 packaging/tool tests PASS / 2 intentional skips**; manifest durability marker PASS. The subsequent 10-profile admission step **FAILED CLOSED** because approved site-scoped RFC 4193 ULA /48 authority is missing; ESP32 and ESP8266 compilation jobs were **SKIPPED**.
- PR shared validation [#44979732651](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979732651): same exact-source result — **171 PASS / 2 skips**, then 10/10 appliance profiles failed closed for missing approved site ULA authority; board compilation jobs **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Case-collision [#44979732640](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979732640): **PASS**.
- Mandatory ImageBuilder sandbox [#44979732649](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979732649): host preflight **31/31 PASS**, then Bubblewrap was not installed / exit 125; namespace and mandatory sandbox packaging execution **SKIPPED**.

These are hosted synthetic filesystem/unit-test results. No real ESP32/ESP8266 firmware artifact or OpenWrt ImageBuilder binary was produced at this head. No physical hardware acceptance is implied.

### Live ownership and integration boundary

- COE #35 branch: phoenix/release-build-script-publication-safety-20261117; parent #31/base: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b; source/test SHA: cafb202cfc7b779c1df929b3388bc31f392bcbdf.
- This activation changed only tools/test_firmware_artifact_manifest.py, tools/write_firmware_artifact_manifest.py, and this RELEASE handover. The inherited .github/workflows/hardware-ci.yml path remains in the accumulated PR diff and outside MASTER's current PHX-RELEASE reimplementation-review route; it was not edited in this activation. PHX-HARDWARE/PHX-MASTER ownership review remains required.
- MASTER #288 routes remain DRAFT_REVIEW_ONLY; no migration or route promotion.
- Experiments #242 remains a separate future SoftTimer signing draft; #291 remains a separate Windows publisher-isolation draft with mixed inherited ownership. No changes were made to either.
- COE #26 remains FROZEN with five PR workflows queued / zero jobs. Parent #31's shared and board builds passed on its recorded head; its mandatory sandbox failed at unprivileged UID-map setup (Permission denied), exit 125.
- Cleanup-first #266 remains OPEN, 0/7 tracks complete.
- Canonical private Drive project registry v11 and newer corrections remain unavailable through the exposed Library/connector surface; no older snapshot was substituted and no private content was copied to GitHub.

### Next owner actions

1. PHX-QA independently reviews the post-read metadata snapshot check and the same-size in-place mutation regression at cafb202c.
2. PHX-CORE / PHX-MASTER / site authority defines the approved site-scoped ULA /48 before profile admission can pass; RELEASE must not invent or substitute a prefix.
3. PHX-INFRA supplies an authorized disposable no-secret runner with Bubblewrap and working unprivileged namespaces; no privileged install or unsandboxed fallback.
4. PHX-HARDWARE / PHX-MASTER resolve the inherited hardware-ci.yml ownership before any merge decision.
5. Registry custodian restores authorized access to canonical private registry v11.

No merge, signing with real keys, tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC04 — close build-script descriptor when stream construction fails (2026-11-22)

**Disposition:** one release-owned resource-lifecycle defect reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

### Finding and correction

`generate_build_script()` creates the destination with `O_EXCL` at mode `0600` and retains both the raw script descriptor and parent-directory descriptor. The normal `with os.fdopen(...)` path transfers ownership of the script descriptor to the returned stream. If `os.fdopen()` raises before returning that stream, the existing outer `finally` closes the parent-directory descriptor but leaves the raw script descriptor open.

The new regression injects an `os.fdopen()` construction error after exclusive creation, captures both descriptors, and requires both to be closed while the on-disk partial file remains non-executable at `0600`.

The correction now catches the stream-construction exception only to close the still-raw script descriptor, treats `EBADF` as already closed, reports any other close failure without hiding the original exception, and re-raises. It catches `BaseException` solely to guarantee cleanup on interruption as well as ordinary errors. The parent-directory descriptor remains covered by the existing outer `finally`. No script content, execution mode ordering, path policy or publication semantics changed.

### Test-first history

- Initial regression attempt: [`3ae3de32`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/3ae3de3263b0e99450889cbab3a3afaec1bf05ba). This test harness attempt failed before reaching the intended assertion because it monkeypatched `os.open` and thereby invalidated the production `os.supports_dir_fd` capability probe. Shared run [#44984130019](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44984130019) is recorded as a harness failure, not expected RED.
- Corrected test-only commit: [`035fb42f`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/035fb42ff11f90fff002c04252d005fea60e2f33). It captures the two descriptors by wrapping the existing private create helper, leaving OS capability probes untouched.
- Expected RED: shared run [#44984177747](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44984177747), job `137091020489`: **172 tests, one expected failure** because `os.fstat(script_fd)` still succeeded after `fdopen()` raised; two intentional skips. The other descriptor was already closed by the existing `finally`.
- Sandbox run [#44984177733](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44984177733): host preflight **31/31 PASS**, then Bubblewrap missing / exit 125; namespace and mandatory sandbox packaging steps skipped. Case-collision [#44984177720](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44984177720): **PASS**.
- Source fix: [`2d914d8c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/2d914d8ccb51fb5b162d35516d4ce92a7a0754fa).
- Cleanup widened to `BaseException` before re-raising: final exact source/test SHA [`0a204374`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0a204374472d1990c8b1bdd412bfd4eb1f4abc59).

### Exact-source CI at `0a204374`

- Shared/firmware run [#44984347418](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44984347418), job `137091533698`: firmware syntax and shared contracts **PASS**; packaging/tool suite **172 PASS / 2 intentional skips**; `PHX-MANIFEST-DURABILITY-PASS`. The subsequent ten-profile admission step **FAILED CLOSED** for missing approved site-scoped RFC 4193 ULA /48 authority; ESP32 and ESP8266 compile jobs **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Mandatory sandbox run [#44984347424](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44984347424), job `137091533507`: host preflight **31/31 PASS**, then Bubblewrap unavailable / exit 125; namespace and mandatory sandbox packaging steps **SKIPPED**.
- Case-collision guard [#44984347427](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44984347427): **PASS**.

These are hosted synthetic filesystem/unit-test results. No ESP32/ESP8266 binary or OpenWrt ImageBuilder output was produced at this source head.

### Exact branch and cross-repository boundary

- COE [PR #35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`, parent #31/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- This increment changes only `tools/test_package_appliance_firmware.py` and `tools/package_appliance_firmware.py`; this handover is the third path for the UTC04 record. The accumulated 12-path PR still includes inherited `.github/workflows/hardware-ci.yml`, outside MASTER's RELEASE `reimplementation-review` route; PHX-HARDWARE / PHX-MASTER must resolve it. No hardware workflow was edited.
- MASTER [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) head `33deb02a55f4f1a3d9ea22cb96b4329dd9489626`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`. RELEASE route remains `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml`, kind `reimplementation-review`.
- Experiments RELEASE #242 remains `734b89d9e7792247e8376335c3f3685500ab3f89`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) passed build/handover, with signing and publication skipped.
- Experiments RELEASE #291 remains `42797e2f3d65c30a1070caf49c93aebec149d897`, mixed-owner (21 RELEASE / 3 CORE / 2 PISONET). Full run [#44748671313](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44748671313) completed target and simulation/update-bundle jobs successfully; signing/publication skipped. Windows run [#44748671225](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44748671225) failed in inherited PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is unset; Windows build and publisher were skipped. Compatibility run [#44748671213](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44748671213) passed both ESP32 core matrix jobs. RELEASE did not edit #291.
- COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; five PR workflows remain QUEUED with no jobs executed.
- Parent #31 remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`: shared validation and both board compile/upload jobs passed; case-collision passed; mandatory sandbox failed at unprivileged UID-map setup (`Permission denied`, exit 125).
- Cleanup-first #266 remains OPEN; seven-role checklist remains **0/7 complete**.
- Canonical private Drive registry v11 was not found in the authorized Library metadata listing (1,422 entries paged) or exact-name search. No historical registry was substituted; no private content was copied.

### Next owner actions and release boundary

1. **PHX-QA:** independently review the `fdopen()` failure regression and raw-descriptor cleanup at exact source/test SHA `0a204374`.
2. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 and same-site provisioning contract; RELEASE must not invent a prefix.
3. **PHX-INFRA:** provide an authorized disposable runner with Bubblewrap and working unprivileged namespaces; no privileged install or unsandboxed fallback.
4. **PHX-HARDWARE / PHX-MASTER:** resolve inherited `hardware-ci.yml` ownership before any merge decision.
5. **PHX-MASTER:** reconcile the live PR-head index; retain `DRAFT_REVIEW_ONLY` ownership routes.
6. **Registry custodian:** restore authorized access to canonical private registry v11.

No merge, real-key signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC05 — reject source mutation during Rental staging copy (2026-11-22)

**Disposition:** one RELEASE-owned packaging-copy integrity defect reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Finding and bounded correction

`_copy_staging_file()` already rejected non-regular source files, symlinked parent components, and a final-file inode replacement between `lstat()` and descriptor open. It did not verify that the opened Rental source remained unchanged while its bytes were read. A same-inode, same-size in-place rewrite during `read()` could therefore be accepted and staged without a stable source snapshot.

The new regression wraps only the source descriptor's reader, reads the original bytes, then rewrites the same inode with different same-length bytes before the copy routine accepts the read. It requires a fail-closed error and no staged destination file.

The source now snapshots descriptor identity and metadata before reading, then compares device, inode, mode, link count, size, nanosecond mtime and ctime after reading; it also verifies the byte count against the original size. Any difference rejects the source before `_write_staging_bytes()` publishes it. No RENTAL-owned source file or behavior was changed.

### Test-first and source commits

- Test-first commit: [`a1e1258a`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/a1e1258a3999ad44e5a59bb4751b4394458cd4b7).
- Expected RED, PR shared [#44988567691](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988567691), job `137104421153`: **173 tests, one expected failure** at `test_copy_staging_file_rejects_source_modified_during_read` (`ValueError not raised`); two intentional skips. Push shared [#44988562987](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988562987) is the corresponding push validation.
- Test-only case-collision [#44988567650](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988567650): **PASS**. Test-only sandbox [#44988567684](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988567684): host preflight **31/31 PASS**, Bubblewrap absent / exit 125; namespace and mandatory sandbox packaging tests **SKIPPED**.
- Source correction: [`99d97538`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/99d97538e1990d22ab8fc81262cded8ddcc13ce4).

### Exact-source CI at `99d97538`

- PR shared/firmware [#44988666568](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988666568): firmware hardening and shared contracts **PASS**; packaging/tool suite **173 PASS / 2 intentional skips**. The next profile-admission step **FAILED CLOSED** for all 10 appliance profiles because approved site-scoped RFC 4193 ULA /48 authority remains undefined; ESP32/ESP8266 compile jobs **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Push shared/firmware [#44988663175](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988663175): same exact-source test and profile-admission result.
- PR mandatory sandbox [#44988666263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988666263) and push [#44988663285](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988663285): host preflight **31/31 PASS**, then Bubblewrap missing / exit 125; namespace and mandatory sandbox packaging regressions **SKIPPED**, not passed. No privileged install or unsandboxed fallback.
- PR case-collision guard [#44988666560](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44988666560): **PASS**.

These are hosted synthetic filesystem/unit-test results. No OpenWrt ImageBuilder output or approved board firmware binary was produced at this source head.

### Branch, ownership and blockers

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`; PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`, parent #31/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Source/test SHA: `99d97538e1990d22ab8fc81262cded8ddcc13ce4`. This task changed only `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py`; this handover is the third path for this checkpoint.
- MASTER #288 head at inspection: `76d3af43d864d4528aabfb24128ae9981ef48f2f`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`. RELEASE's source workflow route remains `reimplementation-review`.
- Experiments #242 remains `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 remains `42797e2f3d65c30a1070caf49c93aebec149d897` and its accumulated 26 paths remain mixed-owner (21 RELEASE / 3 CORE / 2 PISONET). RELEASE did not edit either branch.
- COE #26 remains frozen at `b382d233ff06c8791b1028bed3c617cc7b670d12`; parent #31 remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- The accumulated #35 diff still contains inherited `.github/workflows/hardware-ci.yml` outside MASTER's current RELEASE route. PHX-HARDWARE / PHX-MASTER must resolve that ownership before integration; this activation did not edit it.
- Cleanup-first #266 remains OPEN, 0/7 tracks complete. Canonical private Drive registry v11 was not surfaced through authorized Library search; historical snapshots were not substituted and no private contents were copied.

### Next owner actions

1. **PHX-QA:** independently review the source/test SHA `99d97538` and same-inode mutation regression.
2. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 and same-site distribution contract; RELEASE must not invent a prefix.
3. **PHX-INFRA:** provide an authorized disposable no-secret runner with Bubblewrap and working unprivileged namespaces.
4. **PHX-HARDWARE / PHX-MASTER:** resolve inherited `hardware-ci.yml` ownership before any merge decision.
5. **Registry custodian:** restore authorized access to canonical private registry v11.

No merge, signing with real keys, tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC06 — interrupt-safe firmware manifest rollback (2026-11-22)

**Disposition:** one RELEASE-owned artifact-publication failure-path defect reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Finding and bounded correction

The release artifact writer already creates each manifest output exclusively, writes and flushes it, fsyncs the file, and removes partial output on ordinary exceptions. Both cleanup scopes caught `Exception` only:

- `_write_new_file()` could leave a partial manifest file if a Python-level interruption such as `KeyboardInterrupt` or `SystemExit` occurred after exclusive creation.
- `write_artifact_manifest()` could leave the first `RELEASE_MANIFEST.json` published if interruption occurred while creating the second `SHA256SUMS` output, because the pair rollback also bypassed `BaseException`.

The RELEASE-owned correction catches `BaseException` only around these cleanup scopes, closes any still-owned descriptor, removes the partial file, directory-syncs the rollback when a directory descriptor is available, removes the first manifest if pair publication is interrupted, then re-raises the original interruption. No manifest schema, checksum line format, provenance fields, signing policy or publication order changed.

### Test-first and source history

- Test-only regression commit [`607b4aa0`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/607b4aa0a7b731f682cb3842f306be1d6293c7f4) added two KeyboardInterrupt cases: partial-file cleanup after file fsync interruption, and pair rollback when checksum publication is interrupted after the first manifest exists.
- Expected RED, PR shared [#44993606069](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993606069), job `137119812376`, and push shared [#44993602571](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993602571), job `137119801598`: **175 tests, exactly two new failures, two intentional skips**. The first left the partial output and skipped its directory-sync cleanup; the second left the first manifest after the checksum interruption. This is the expected pre-fix regression result.
- Source correction [`0b91d7ef`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0b91d7efe50181d280bf21943e97261917448cf0) changes only the two cleanup exception boundaries to `BaseException` and clarifies their docstrings.
- Intermediate source/test run PR shared [#44993738996](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993738996), job `137120209566`, and push shared [#44993734935](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993734935): **175 tests, one test-assertion failure, two intentional skips**. The partial-file regression passed and the manifest-pair rollback itself succeeded; the test incorrectly expected a separate directory fsync after the first file (the writer intentionally syncs the pair once after both files, or syncs the rollback after interruption). This was a test expectation mismatch, not a remaining source failure.
- Test expectation correction [`6e331be4`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6e331be4234f43012d8a0b9e83eb0d1d753356ec) asserts the first manifest exists at the interruption point and expects the single rollback directory sync. This is the final source/test HEAD.

### Exact-source Actions at `6e331be4`

- PR shared/firmware [#44993881155](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993881155), validation job `137120651901`: **175 packaging/tool tests PASS / 2 intentional skips**, `PHX-MANIFEST-DURABILITY-PASS`; subsequent all-profile admission **FAILED CLOSED 10/10** because no approved site-scoped RFC 4193 ULA /48 authority is configured; ESP32 and ESP8266 compile jobs **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Push shared/firmware [#44993877301](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993877301), validation job `137120638698`: same exact-source result — **175 PASS / 2 skips**, then 10/10 profiles fail closed; board compile jobs skipped.
- PR ImageBuilder sandbox [#44993881085](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993881085), job `137120651557`: host preflight **31/31 PASS**; Bubblewrap is absent, exit 125; namespace and mandatory sandbox packaging regressions **SKIPPED**, not passed.
- PR case-collision [#44993881098](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993881098), job `137120651482`: **PASS**.

These are hosted synthetic filesystem/unit-test results. No production firmware image or OpenWrt ImageBuilder binary was produced at this source head. The hosted sandbox never reached namespace execution.

### Branch, ownership and cross-repository reconciliation

- COE PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`; parent PR #31/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Final source/test SHA: `6e331be4234f43012d8a0b9e83eb0d1d753356ec`; this handover is the documentation successor.
- This UTC06 task changes only `tools/write_firmware_artifact_manifest.py`, `tools/test_firmware_artifact_manifest.py`, and this handover. The accumulated #35 diff still includes inherited `.github/workflows/hardware-ci.yml`, outside MASTER's current RELEASE route; no Hardware workflow was edited. PHX-HARDWARE / PHX-MASTER must resolve that ownership before integration.
- MASTER PR [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) current head at audit: `737af73dbc4d3ab3786b6f6b0b251106a5d1c7c3`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`. PHX-RELEASE's only listed Experiments migration route remains `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml`, `reimplementation-review`. No workflow migration or route promotion occurred.
- Experiments RELEASE #242 exact head `734b89d9e7792247e8376335c3f3685500ab3f89`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) passed handover/build and synthetic packaging steps. Authenticode signing and GitHub Release publication were **SKIPPED**.
- Experiments RELEASE #291 exact head `42797e2f3d65c30a1070caf49c93aebec149d897`, based on #242 `734b89d9...`; its 26 changed paths remain mixed-owner (21 RELEASE / 3 CORE / 2 PISONET). Compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed provenance/toolchain tests and both ESP32 core compile/reproducibility legs. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at the mandatory handover freshness gate; build and publisher skipped. Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) failed at the inherited freshness gate; production signing/publication and downstream acceptance remained skipped. RELEASE did not edit #291 or PISONET-owned self-tests.
- COE integration #26 exact head `b382d233ff06c8791b1028bed3c617cc7b670d12`, base main `a6513ab4412b4c014eee2863e45cbe32d06cb243`: five PR workflows remain **QUEUED**, zero jobs returned.
- COE parent #31 exact head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`: shared/firmware [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) passed validation, 10/10 profile staging, ESP32 and ESP8266 compile/artifact upload; case-collision [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) passed. Mandatory sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) failed at unprivileged namespace preflight after Bubblewrap installation and host tests; mandatory sandbox packaging regressions were skipped. This is not production acceptance.
- Cleanup-first #266 remains OPEN, **0/7 tracks complete**. Canonical private Drive registry v11 was not surfaced through the authorized Library/connector; no older snapshot was substituted and no private content was copied.

### Next owner actions and limits

1. **PHX-QA:** independently review the two KeyboardInterrupt regressions and exact source/test SHA `6e331be4`.
2. **PHX-INFRA:** provide an authorized disposable no-secret Bubblewrap-capable runner with working unprivileged user namespaces; no privileged install or unsandboxed fallback.
3. **PHX-CORE / PHX-MASTER / site authority:** define approved site-scoped ULA /48 authority before all-profile admission can pass; RELEASE must not invent a prefix.
4. **PHX-HARDWARE / PHX-MASTER:** resolve inherited `hardware-ci.yml` ownership before any integration decision.
5. **PHX-MASTER:** refresh the #172 current PR-head index; its previous #35 pointer is stale relative to this exact branch head.
6. **Registry custodian:** restore authorized provenance-only access to canonical registry v11.

No merge, real-key signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC06 final exact-head reconciliation — 2026-11-22T06:39Z

This is a documentation-only CI readback after the interrupt-safe manifest rollback source/test correction. It does not change the implementation or test files.

### Source/test identity and evidence

- Test-first RED: [607b4aa0](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/607b4aa0a7b731f682cb3842f306be1d6293c7f4). Exact expected RED [#44993606069](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993606069): 175 tests, exactly two interruption regressions failed, two intentional skips.
- Source correction: [0b91d7ef](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0b91d7efe50181d280bf21943e97261917448cf0).
- Intermediate test expectation run [#44993738996](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993738996): 175 tests, one test-assertion mismatch, two intentional skips. This was not counted as a passing run.
- Corrected source/test HEAD: [6e331be4](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6e331be4234f43012d8a0b9e83eb0d1d753356ec).
- Exact source/test shared PR run [#44993881155](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993881155) and push run [#44993877301](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993877301): 175 packaging/tool tests PASS, two intentional skips, and `PHX-MANIFEST-DURABILITY-PASS`; then all 10 appliance profiles FAILED CLOSED because approved site-scoped RFC 4193 ULA /48 authority is absent. ESP32/ESP8266 compile jobs were SKIPPED. Overall shared workflows are FAILURE, not green.
- Exact source/test sandbox [#44993881085](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993881085): 31/31 host-preflight tests PASS; Bubblewrap absent, exit 125; namespace and mandatory sandbox packaging regressions SKIPPED.
- Exact source/test case-collision [#44993881098](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44993881098): PASS.

### Final documentation-head readback

- Prior documentation HEAD: `ef59449081bf3699641c7b713a915132b626f142`.
- Current source/test remains `6e331be4234f43012d8a0b9e83eb0d1d753356ec`; this addendum changes only `tools/RELEASE_PACKAGER_HANDOVER.md`.
- Docs-head shared [#44994227248](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44994227248): 175 tests PASS / two intentional skips, manifest durability marker PASS; all 10 profiles fail closed for missing approved site ULA /48; board compile jobs SKIPPED; overall workflow FAILURE.
- Docs-head sandbox [#44994227245](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44994227245): 31/31 host-preflight tests PASS; Bubblewrap absent, exit 125; namespace and mandatory sandbox packaging regressions SKIPPED.
- Docs-head case-collision [#44994227271](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44994227271): PASS.

### Current coordination pins

- COE PR #35 remains OPEN / DRAFT / UNMERGED on `phoenix/release-build-script-publication-safety-20261117`, parent #31/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- MASTER PR #288 was read at `737af73dbc4d3ab3786b6f6b0b251106a5d1c7c3`; its `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`. The PHX-RELEASE route is `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml`, `reimplementation-review`.
- Control-plane #172 body still carries a stale COE #35 head pointer `7b9706d8...`; MASTER should refresh the role index from live PR metadata. No MASTER file was edited.
- Canonical private Drive registry v11 was not found in the full Library metadata scan (1,396 entries); only historical registry snapshots v1 and v3–v7 surfaced. None was substituted as v11 and no private contents or identifiers were copied.

Hosted CI is synthetic evidence only. No approved production firmware or ImageBuilder binary was produced. No real Bubblewrap namespace execution occurred. No signing, merge, publication, hardware flash, payment migration, or customer deployment occurred. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC07 — trigger sandbox validation for shared trust-policy changes (2026-11-22)

**Disposition:** one release-owned CI trigger-coverage defect reproduced test-first and corrected on the existing COE #35 draft branch. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Finding and bounded correction

The dedicated `.github/workflows/release-imagebuilder-sandbox.yml` imports and exercises the shared `tools/imagebuilder_bwrap_trust.py` policy through both the host preflight and runtime sandbox runner. Its `pull_request.paths` and `push.paths` filters listed the consumer/test files but omitted that shared policy module. A trust-policy-only edit could therefore bypass the dedicated sandbox regression workflow even though the generic `tools/**` suite might still run.

The correction adds the helper path to both event filters and adds a host test that asserts both filters retain it. No sandbox implementation, trust decision, network behavior, shared interface, firmware profile, or Hardware workflow was changed.

### Test-first and source commits

- Test-only commit: [`8a6f5086`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8a6f508612a7b96427c4c5f1c27eb976e2a7061b).
- Expected RED, PR sandbox [#44997601471](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997601471), job `137131904898`, and push sandbox [#44997596918](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997596918), job `137131891308`: **32 tests, exactly the new trigger-coverage assertion failed**. The PR event exposed the missing pull-request path; the push event exposed the missing push path.
- Corresponding shared PR [#44997601475](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997601475) and push [#44997596899](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997596899) also failed at that same new test during generic tools discovery. ESP32/ESP8266 dependent jobs were skipped. Case-collision [#44997601436](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997601436) passed.
- First workflow correction [`c699d096`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/c699d096c3ab60a604d48116d9efaa82229d22fd) added the helper to the pull-request path filter. PR sandbox [#44997645270](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997645270) then passed all 32 host tests and reached the Bubblewrap gate; push sandbox [#44997640146](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997640146) correctly retained the failing push-filter regression. This intermediate commit is not the final fix.
- Second workflow correction and exact source/test HEAD: [`c926780f`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/c926780fa51783de1246b943dd7c6ae995a48a04), which adds the helper to the push path filter as well.

### Exact-source Actions at `c926780f`

- PR sandbox [#44997695867](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997695867), job `137132188928`, and push sandbox [#44997691265](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997691265), job `137132175268`: **32/32 host tests PASS**, including the new two-event trigger assertion. The next required gate **FAILED CLOSED** because Bubblewrap is not installed on the hosted runner (exit 125). Unprivileged namespace and mandatory real-Bubblewrap packaging regressions were not run.
- Shared/firmware PR [#44997695854](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997695854), job `137132188878`: **176 tests PASS / 2 intentional skips**, then all 10 appliance profiles **FAILED CLOSED** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP32 and ESP8266 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Case-collision [#44997695980](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44997695980): **PASS**.

These are hosted synthetic CI results. No actual Bubblewrap namespace execution, OpenWrt ImageBuilder artifact, approved production binary, or physical hardware acceptance is established.

### Branch, ownership and coordination

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`; PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`.
- Parent #31/base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Source/test HEAD: `c926780fa51783de1246b943dd7c6ae995a48a04`.
- This task changes only `.github/workflows/release-imagebuilder-sandbox.yml` and `tools/test_imagebuilder_sandbox_host.py`; this section is the narrow handover update.
- The accumulated #35 diff still includes inherited `.github/workflows/hardware-ci.yml` outside the current RELEASE route. It was not modified; PHX-HARDWARE / PHX-MASTER must resolve ownership before integration.
- MASTER #288 `737af73dbc4d3ab3786b6f6b0b251106a5d1c7c3` remains OPEN / DRAFT; `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`. RELEASE's Experiments route remains reimplementation-review only.
- Experiments #242 remains `734b89d9e7792247e8376335c3f3685500ab3f89`; its Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) passed, but signing/publication are not established.
- Experiments #291 remains `42797e2f3d65c30a1070caf49c93aebec149d897`, mixed-owner (21 RELEASE / 3 CORE / 2 PISONET): compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) failed at CORE-owned handover freshness; Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at PISONET-owned `negative-selftest.ps1`. RELEASE made no changes to #291.
- COE integration #26 remains frozen at `b382d233ff06c8791b1028bed3c617cc7b670d12`, with five workflows queued and zero jobs executed.
- Cleanup-first #266 remains OPEN, 0/7 tracks complete. Canonical private Drive registry v11 was not found in the authorized Library search results; older snapshots were not substituted and no private content was copied.

### Next owner actions and limits

1. **PHX-INFRA:** provide an authorized disposable, ephemeral, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces; rerun the mandatory sandbox regressions.
2. **PHX-CORE / PHX-MASTER / site authority:** define the approved site-scoped ULA /48 authority; do not substitute a synthetic test prefix.
3. **PHX-QA:** independently review the exact source/test SHA `c926780f` and its trigger-coverage regression.
4. **PHX-HARDWARE / PHX-MASTER:** resolve inherited `hardware-ci.yml` ownership before any integration decision.
5. **PHX-MASTER:** refresh the stale #172 PR-head index from current PR API values.
6. **Registry custodian:** restore authorized provenance-only access to canonical private registry v11.

No merge, signing with real keys, release tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC08 — host preflight descendant timeout cleanup (2026-11-22)

**Disposition:** one RELEASE-owned preflight process-lifecycle defect reproduced test-first and corrected on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

### Finding and bounded correction

`tools/check_imagebuilder_sandbox_host.py::check_host()` previously used `subprocess.run(timeout=...)`. That timeout only guarantees termination/waiting for the direct process; a descendant that survives the leader and retains captured output pipes can remain alive after the preflight reports timeout. The runtime build runner already has tested process-group cleanup, but the separate host-preflight path did not use it.

The correction:
- starts the preflight with `subprocess.Popen(..., start_new_session=True)`;
- reuses the existing RELEASE runner `_terminate_process_groups()` helper on timeout and after normal completion, so surviving members of the preflight's own process group are terminated;
- retains partial stdout/stderr in timeout diagnostics;
- fails closed when process-group cleanup reports an unconfirmed survivor or signal failure;
- keeps the existing timeout result and no-privileged-fallback policy.

The new host regression launches a disposable fake preflight executable with a SIGTERM-ignoring child that records its PID. It verifies the timeout path returns and the child is no longer running. This is synthetic host-process evidence only; it does not execute Bubblewrap or ImageBuilder.

### Test-first / source commits

- Initial test-only commit: [`27c071b0`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/27c071b076f2867407bdf21fb078d12a3c255324). PR sandbox [#45002407940](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45002407940) failed with a test-harness placement error (`AttributeError: helper_or_skip` because the new method was initially inserted in the wrong test class). No source code changed in this commit.
- Corrected test-only commit: [`7c1b2891`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/7c1b2891f2deaca0cdb1dd19c3727ed3253fde93). Exact PR sandbox RED [#45002520083](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45002520083), job `137146938394`: 33 tests, with the new regression failing because the preflight timeout left its descendant process running. The required Bubblewrap/namespace/packaging steps were skipped after the host suite failed.
- Source correction / exact source-test SHA: [`30ee7a67`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/30ee7a67e745026b4aecde8e0936030576eee64f). Only `tools/check_imagebuilder_sandbox_host.py` changed in this source commit.

### Exact-source Actions at `30ee7a67`

- Sandbox PR [#45002788265](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45002788265) and push [#45002784616](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45002784616): host preflight suite **33/33 PASS**. The next required Bubblewrap availability gate **FAILED CLOSED** because Bubblewrap is not installed on the hosted runner. Unprivileged identity, namespace preflight and mandatory Bubblewrap packaging regressions were **SKIPPED**, not passed.
- Shared/firmware PR [#45002788122](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45002788122) and push [#45002784622](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45002784622): firmware hardening/syntax and shared-contract validation **PASS**; packaging/tool suite **177 PASS / 2 intentional skips**. End-to-end profile admission **FAILED CLOSED 10/10** because approved site-scoped RFC 4193 ULA /48 authority is absent. ESP32 and ESP8266 compile jobs were **SKIPPED**. Overall workflow conclusion is **FAILURE**, not green.
- Case-collision guard [#45002788120](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45002788120): **PASS**.

### Branch, ownership and cross-repository state

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`; PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`.
- Parent #31/base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- At source/test SHA `30ee7a67`, only the two RELEASE-owned paths `tools/check_imagebuilder_sandbox_host.py` and `tools/test_imagebuilder_sandbox_host.py` changed during this increment; this section is the narrow handover update.
- Inherited `.github/workflows/hardware-ci.yml` remains in the accumulated child diff outside the current RELEASE route; PHX-RELEASE did not edit it. PHX-HARDWARE / PHX-MASTER must resolve ownership before integration.
- MASTER #288 remains OPEN / DRAFT at `737af73dbc4d3ab3786b6f6b0b251106a5d1c7c3`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`.
- RELEASE #242 remains OPEN / DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`.
- RELEASE #291 remains OPEN / DRAFT at `42797e2f3d65c30a1070caf49c93aebec149d897`, with mixed CORE/PISONET ownership in its accumulated diff; no #291 files were changed.
- #266 remains OPEN; the seven-role cleanup checklist is incomplete. Canonical private Drive registry v11 was not found in the authorized Library search; older snapshots/checkpoints were not substituted, and no private contents or identifiers were copied.

### Next owner actions and limits

1. **PHX-INFRA:** provide the authorized disposable no-secret runner with Bubblewrap preinstalled and working unprivileged user namespaces; rerun mandatory sandbox packaging regressions.
2. **PHX-CORE / PHX-MASTER / site-prefix authority:** define and approve the site-scoped ULA /48; do not substitute a synthetic prefix.
3. **PHX-QA:** independently review exact source/test SHA `30ee7a67` and the preflight descendant cleanup regression.
4. **PHX-HARDWARE / PHX-MASTER:** resolve inherited `hardware-ci.yml` ownership before integration.
5. **PHX-MASTER:** refresh stale #172 branch-head references from live PR metadata.
6. **Registry custodian:** restore authorized provenance-only access to canonical private registry v11.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC09 — reject artifact-directory membership changes during manifest scan (2026-11-22)

**Disposition:** one RELEASE-owned firmware-manifest integrity defect reproduced test-first and corrected on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Finding and bounded correction

`tools/write_firmware_artifact_manifest.py::_scan_artifact_directory_fd()` enumerated a directory once with `os.listdir(directory_fd)`, then hashed only the returned names. It pinned individual file identity and nested directory identity, but did not compare directory-entry metadata around the full traversal. A file created after the listing snapshot but before traversal completion could therefore be omitted from both `artifact-manifest.json` and `SHA256SUMS` without an error.

The RELEASE-owned correction records a descriptor `fstat` snapshot before enumeration and after each directory's full traversal. It compares device, inode, mode, link count, size, `mtime_ns` and `ctime_ns`; nested-directory metadata is rechecked after recursion. A detected membership/metadata change raises `ManifestError` and prevents manifest publication. This is mutation detection during traversal, not an atomic filesystem snapshot; the build output tree must remain quiescent, and concurrent writes after the final verification are not represented as impossible.

### Test-first progression

- Test-only regression: [`bd77b529`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/bd77b529e489d7e6bc6fdc3813f5ec8c20657df7).
- Expected RED: PR shared validation [#45007053469](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007053469), job `137160862834`: 178 tests, the new `test_rejects_directory_entry_added_after_descriptor_listing_snapshot` failed because the baseline did not raise `ManifestError`; packaging/tool validation failed and board compilation was skipped. This is the intended regression reproduction, not a pass.
- Source correction: [`5cac4dcc`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5cac4dccd541df9200b3a3f564a77eddf9053546) adds descriptor-relative directory metadata snapshots and nested-directory rechecks.
- Intermediate source-head run [#45007119342](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007119342) confirmed the new regression passed but failed one pre-existing nested-directory test's diagnostic regex; it expected the older wording and did not accept the new `artifact directory changed while scanning` message.
- Test assertion compatibility correction / final source-test anchor: [`7b1282c2`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/7b1282c2aeb689c3eb59e3eed8db10ad24785369). The existing assertion now accepts the new fail-closed diagnostic without weakening the behavior check.

### Exact-source GitHub Actions at `7b1282c2`

- PR shared/firmware [#45007216238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007216238), job `137161350889`: packaging/tool suite **178 tests PASS / 2 intentional skips**, including the new directory-membership regression; firmware-hardening and shared-contract steps PASS. The next all-profile admission step **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority is not defined. ESP32 and ESP8266 compile jobs were **SKIPPED**. Overall workflow is **FAILURE**, not green.
- Push shared/firmware [#45007212403](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007212403), job `137161339852`: same exact-source result — 178 tests PASS / 2 skips; all-profile admission failed closed; board compiles skipped.
- PR ImageBuilder sandbox [#45007216218](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007216218), job `137161351059`: host preflight **33/33 PASS**. The next mandatory gate **FAILED CLOSED** because Bubblewrap is not installed (exit 125); namespace checks and sandbox-dependent packaging tests were **SKIPPED**, not passed.
- PR case-collision [#45007216224](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45007216224): **PASS**.

These are hosted synthetic CI results. No actual Bubblewrap namespace, OpenWrt ImageBuilder appliance image, approved production binary, signer, hardware flash or physical acceptance is established.

### Exact branch and cross-repository state

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`; PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`.
- Parent #31/base: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Source/test anchor: `7b1282c2aeb689c3eb59e3eed8db10ad24785369`; this section is the narrow handover update.
- Only RELEASE-owned paths changed during this task: `tools/write_firmware_artifact_manifest.py`, `tools/test_firmware_artifact_manifest.py`, and this handover. No workflow, firmware, profile, network, shared interface or other role-owned source changed.
- MASTER #288 live head: `737af73dbc4d3ab3786b6f6b0b251106a5d1c7c3`; ownership manifest blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`. RELEASE's Experiments route `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml` remains `reimplementation-review`; no copy/migration authority.
- Experiments #242 live head `734b89d9e7792247e8376335c3f3685500ab3f89`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) handover/build PASS. Signing/publication are not established.
- Experiments #291 live head `42797e2f3d65c30a1070caf49c93aebec149d897`, base #242; its accumulated 26 paths remain mixed-owner (21 RELEASE / 3 CORE / 2 PISONET). Compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) PASS; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) fails at the CORE-owned project-handover freshness gate after target build jobs pass; downstream simulation/sign/publish jobs are skipped. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) fails at the same shared handover freshness gate; Windows build/publisher are skipped. No #291 path was changed.
- COE integration #26 remains frozen at `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows are QUEUED with zero jobs executed.
- COE parent #31 remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; shared validation [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) and case-collision [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) PASS; mandatory sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) fails at unprivileged namespace UID-map setup. This parent result is not #35 exact-head acceptance.
- #172's embedded PR-head index is stale relative to the live PR API; MASTER should refresh its own control-plane body from current refs. Cleanup-first #266 remains OPEN, 0/7 tracks complete.
- Canonical private Drive registry v11 was not found in authorized Library title search; only older v3–v7 snapshots were surfaced. No older snapshot was substituted and no private contents or identifiers were copied to GitHub.

### Next owner actions and limits

1. **PHX-QA:** independently review exact source/test SHA `7b1282c2` and the deterministic directory-membership regression.
2. **PHX-INFRA:** provide an authorized disposable, ephemeral, no-secret runner with Bubblewrap and working unprivileged user namespaces; rerun mandatory sandbox packaging tests.
3. **PHX-CORE / PHX-MASTER / site-prefix authority:** define the approved durable site-scoped ULA /48 source; do not substitute a synthetic test prefix.
4. **PHX-MASTER:** refresh stale #172 PR-head references and preserve the review-only RELEASE ownership route.
5. **Registry custodian:** restore authorized provenance-only access to canonical private registry v11.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC10 — rollback cleanup interruptions (2026-11-22T10Z)

One bounded RELEASE-owned manifest-publication defect was reproduced test-first and corrected on this existing draft branch. This does **not** establish that rollback can always remove files when the filesystem itself refuses/intercepts cleanup; it ensures cleanup interruptions are recorded, remaining cleanup operations are still attempted, directory durability is attempted, and the operation fails closed rather than letting a second KeyboardInterrupt/SystemExit abort the rollback loop silently.

### Defect and correction

The existing writer already caught `BaseException` around the primary partial-file write and manifest-pair publication. However, nested rollback operations caught only `OSError`. A `KeyboardInterrupt` or `SystemExit` raised by descriptor close, unlink, or directory fsync during rollback could escape the cleanup scope before the remaining rollback work and its durability attempt.

The correction changes only those rollback cleanup handlers to catch `BaseException`, records the exception type and message, continues with remaining cleanup operations, and raises the existing `ManifestError` when rollback cannot be confirmed, chained from the original write/publication failure. No retry is claimed for an unlink that itself was interrupted; the residual file is explicitly reported as an unconfirmed rollback.

### Test-first progression

- Test-only regression commit: [`5d556ff5`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/5d556ff5aba1ca31f3aa734a0bae1e55854af569).
- Expected RED: shared/packaging [run #45013797904](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45013797904), job `137181652312`. The first new test reproduced an uncaught `KeyboardInterrupt` from partial-output unlink; the job exited 130. The second new regression was not reached because the uncaught interrupt aborted the unittest process. This is an expected baseline failure, not a pass.
- Test-only case-collision [run #45013797895](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45013797895): PASS.
- Test-only sandbox [run #45013797886](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45013797886): host preflight 33/33 PASS; Bubblewrap unavailable, exit 125; namespace and mandatory sandbox packaging tests SKIPPED.
- Source correction: [`c1771e51`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/c1771e5139ec9b70804d44fd96498ee188a58deb), limited to rollback exception handling in `tools/write_firmware_artifact_manifest.py`.

### Exact source/test-head Actions at `c1771e51`

- Shared/firmware [run #45013908817](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45013908817), job `137181997913`: **180 tests PASS / 2 intentional skips**; `PHX-MANIFEST-DURABILITY-PASS`. Firmware hardening and shared contracts PASS. All ten appliance profiles then **FAILED CLOSED** because approved site-scoped RFC 4193 ULA /48 authority remains undefined; ESP32/ESP8266 compile jobs SKIPPED. Overall workflow FAILURE, not green.
- Mandatory sandbox [run #45013908869](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45013908869), job `137181998308`: host preflight **33/33 PASS**; Bubblewrap missing, exit 125; unprivileged identity, namespace probe and mandatory sandbox packaging regressions SKIPPED.
- Case-collision [run #45013908859](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45013908859): PASS.

These are hosted synthetic tests. No real Bubblewrap namespace or ImageBuilder execution occurred.

### Exact branch / coordination state

- PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch `phoenix/release-build-script-publication-safety-20261117`, parent #31/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- Test-only commit: `5d556ff5aba1ca31f3aa734a0bae1e55854af569`.
- Source/test commit: `c1771e5139ec9b70804d44fd96498ee188a58deb`.
- This increment changes only `tools/test_firmware_artifact_manifest.py`, `tools/write_firmware_artifact_manifest.py`, and this RELEASE handover.
- The accumulated PR diff still includes inherited `.github/workflows/hardware-ci.yml`; it was not changed and remains outside the current RELEASE ownership route.
- MASTER #288 current PR API head: `844337af4c6c7ff1833fa9a68414d3eba1b14005`; `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`; RELEASE's Experiments workflow route remains `reimplementation-review`.
- Experiments #242 current head `734b89d9e7792247e8376335c3f3685500ab3f89`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) SUCCESS.
- Experiments #291 current PR API head `42797e2f3d65c30a1070caf49c93aebec149d897` (the #172 body has a stale embedded head). Compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) SUCCESS; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) FAILURE at CORE-owned project-handover freshness after target builds; Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) FAILURE at PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is unset. Signing/publishing skipped; no #291 paths changed.
- COE #26 current head `b382d233ff06c8791b1028bed3c617cc7b670d12`; five PR workflows remain QUEUED with zero jobs executed.
- COE #31 current head/base candidate `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; prior parent shared/case runs #44222517238/#44222517258 PASS; mandatory sandbox #44222517263 FAILED at unprivileged namespace UID-map setup. Those are #31 parent runs, not #35 exact-head acceptance.
- PR #35 remains OPEN / DRAFT / UNMERGED. Independent PR reviews: 0; review threads: 0.
- Control-plane #172 body still contains stale embedded PR-head references; MASTER should reconcile its own index. Cleanup-first #266 remains OPEN with all seven role checkboxes unchecked.
- Canonical private Drive registry v11 was not found in authorized Library search; no older snapshot was substituted and no private contents were copied to GitHub.

### Next actions / release limits

1. PHX-QA independently reviews exact source/test SHA `c1771e51` and the two cleanup-interruption regressions.
2. PHX-INFRA supplies an authorized disposable, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces.
3. PHX-CORE / PHX-MASTER define approved site-scoped RFC 4193 ULA /48 authority; no synthetic prefix substitution.
4. PHX-MASTER refreshes stale #172 PR-head references and preserves the review-only ownership route.
5. Registry custodian restores authorized provenance-only access to canonical private registry v11.

No merge, real-key signing, tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC11 — reject router-profile mutation during read (2026-11-22)

**Disposition:** one RELEASE-owned profile-input integrity defect was reproduced test-first and corrected on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source/interface was changed.

### Finding and bounded correction

`load_profile()` opened a custom router-profile file through no-follow directory descriptors and verified that the opened object was regular, but then returned `json.load()` without checking whether the opened inode changed while its bytes were being read. A same-inode, same-size rewrite after the initial `fstat()` could therefore be accepted as the profile content.

The correction reads the pinned descriptor as bytes, captures a second `fstat()`, and rejects when device, inode, mode, link count, size, nanosecond mtime, nanosecond ctime, or bytes-read length differs from the initial descriptor snapshot. Only after the stability check does it decode UTF-8 and run `json.loads()` with the existing recursive duplicate-key rejection hook. The bytes are parsed from the already-read immutable buffer. This is a read-stability check, not an atomic filesystem snapshot; callers must still keep release input trees quiescent.

### Test-first lineage and retained harness corrections

- Initial test commit [`b1cb8423`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b1cb84231c34addbd0d2565ad59ec80c9ddc321e) contained a literal backslash-n fixture typo; [run #45016415535](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45016415535) failed at JSON decoding, so this was **not** counted as the expected RED.
- Fixture correction [`f424da2e`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/f424da2e9cbdb544c5b54465379d6416a8a60bb2) produced the intended RED: [run #45016520903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45016520903), **181 tests, one expected failure** — baseline returned the rewritten same-inode profile instead of raising `ValueError`.
- Source correction [`e3b7300c`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/e3b7300c286859aae41ff03f5ba54737da3a7ab2) changed profile reading to binary mode and added the post-read identity/length check. Its first run [#45016606866](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45016606866) still failed because the test injector was looking for text mode `r`, so it did not mutate the now-binary `rb` stream. This was a test-harness mismatch, not counted as a source pass.
- Harness correction [`0ee31b93`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/0ee31b93aedcf939602402056b1777a603b818e2) targets `rb`; the final source/test suite then passed.

### Exact source/test-head Actions at `0ee31b93`

- Shared/firmware PR [#45016717731](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45016717731): firmware hardening and shared-contract checks **PASS**; packaging/tool suite **181 tests PASS / 2 intentional skips**; `PHX-MANIFEST-DURABILITY-PASS`. The following all-profile staging gate **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP8266/ESP32 compile jobs were skipped. Overall workflow **FAILURE**, not green.
- Shared/firmware push [#45016714666](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45016714666): same exact-source result — **181 PASS / 2 skips**, followed by the same ULA admission failure.
- Sandbox PR [#45016717777](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45016717777) and push [#45016714688](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45016714688): host-preflight suite **33/33 PASS**; Bubblewrap availability then **FAILED CLOSED** because `bwrap` is absent (exit 125). Namespace identity/preflight and mandatory sandbox packaging tests were skipped, not passed.
- Case-collision guard [#45016717743](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45016717743): **PASS**.

These are hosted synthetic CI results. No Bubblewrap namespace, real ImageBuilder execution, OpenWrt firmware artifact, target binary, physical hardware test or production release was performed.

### Live ownership and next actions

- Child PR #35 remains stacked on parent #31/base `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; the current source/test head at this entry is `0ee31b93aedcf939602402056b1777a603b818e2`.
- MASTER #288 ownership routes remain `DRAFT_REVIEW_ONLY`; no migration or route promotion is authorized.
- Experiments #242 remains a draft with its historical Windows CI success; signing/publication remain unproven.
- Experiments #291 remains a mixed-owner draft (21 RELEASE / 3 CORE / 2 PISONET); its latest compatibility success does not clear the failed Full/Windows gates. No #291 path was changed.
- COE integration #26 remains frozen at `b382d233ff06c8791b1028bed3c617cc7b670d12`; five workflows remain queued with zero executed jobs.
- Cleanup-first #266 remains OPEN, 0/7 checked.
- Authorized Library search did not surface canonical private Drive registry v11; historical v3–v7 snapshots were not substituted and no private contents/identifiers were copied.

**Next owners:** PHX-QA independently reviews source/test head `0ee31b93`; PHX-INFRA supplies a disposable no-secret Bubblewrap-capable runner with unprivileged user namespaces; PHX-CORE/MASTER define approved site ULA /48 authority; MASTER refreshes its own stale control-plane head index; registry custodian restores canonical v11 access.

No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO**.


## PHX-RELEASE UTC12 — reject staging-tree mutation during overlay size scan (2026-11-22)

**Disposition:** one RELEASE-owned overlay-size integrity defect was reproduced test-first and corrected on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source/interface was changed.

### Finding and bounded correction

\`calculate_overlay_size()\` previously took one \`os.listdir(directory_fd)\` snapshot per staging directory, then walked the returned names through pinned no-follow descriptors. A file added after the listing snapshot could be omitted from the overlay byte budget. The staging root could also be renamed/replaced after its scan without a final check that the path still referred to the pinned root directory.

The corrected walk keeps each directory descriptor open on an explicit depth-first stack until its descendants have been scanned. At directory exit it:
- re-lists the pinned directory and compares the entry-name set with the original listing;
- re-stats every observed entry relative to the pinned directory and compares its device/inode/type/link/owner/group/size/mtime/ctime snapshot;
- verifies the pinned directory identity and mode; and
- revalidates the staging-root name through its still-pinned parent descriptor before closing the root.

This catches additions/removals and same-name object replacement after an entry was measured, while preserving the existing behavior for deliberate symlink-to-file and file-to-symlink replacement races that occur before the entry is opened. It is a mutation-detection check, not an atomic filesystem snapshot; staging inputs must still remain quiescent during packaging.

### Test-first lineage and intermediate corrections

- Test-only regression commit [\`9dc01bef\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/9dc01bef5e0ad05095a2f00a4af9e9b72a5c612b) added:
  - \`test_calculate_overlay_size_rejects_directory_entry_added_after_listing_snapshot\`;
  - \`test_calculate_overlay_size_rejects_staging_root_replaced_after_scan\`.
- Expected RED: shared run [#45022713756](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45022713756), job \`137208921111\`: **183 tests, two new expected failures, two intentional skips**. Both new tests reproduced \`ValueError not raised\`. Case-collision [#45022713642](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45022713642) passed; sandbox remained blocked by missing Bubblewrap.
- Initial descriptor-walk implementation [\`7ff88d18\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/7ff88d1839b75846caeba910620a64961a55828b) correctly detected the added entry, but its broad directory metadata comparison incorrectly rejected two existing same-name symlink replacement regressions and classified root replacement as a generic directory mutation. Exact PR shared run [#45023409307](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45023409307): 183 tests, two errors and one failure, two intentional skips.
- Root descriptor ownership transfer [\`1936849f\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/1936849fe15125efe129af7dc45f37d0b1c46d5f) prevented a double-close path when root-frame initialization failed, but did not clear the false-positive mutation checks. Exact PR shared run [#45023466616](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45023466616): the two symlink replacement tests errored and the root-specific diagnostic assertion failed. These are retained as failed intermediate attempts, not passes.
- Final source correction [\`7bbf7c40\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/7bbf7c40ab09fd839faaaa3b5a14fec818e9a23b) uses entry-name-set plus per-entry metadata revalidation and checks root path identity before the root directory snapshot comparison.

### Exact source/test-head Actions at \`7bbf7c40\`

- Shared/firmware PR [#45023691331](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45023691331), job \`137211939007\`: **181 PASS / 2 intentional skips (183 tests total)**; \`PHX-MANIFEST-DURABILITY-PASS\`; firmware hardening/shared contracts and packaging/tool tests PASS. The subsequent all-profile gate **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority remains undefined. ESP32/ESP8266 compile jobs were skipped. Overall workflow **FAILURE**, not green.
- Shared/firmware push [#45023687241](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45023687241): same exact-source result — **181 PASS / 2 skips (183 tests total)**, followed by the same ULA admission failure.
- Sandbox PR [#45023691322](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45023691322) and push [#45023687258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45023687258): host-preflight suite **33/33 PASS**; Bubblewrap availability then **FAILED CLOSED** because \`bwrap\` is absent (exit 125). Unprivileged namespace verification and mandatory sandbox packaging tests were skipped, not passed.
- Case-collision guard [#45023691325](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45023691325): **PASS**.

These are hosted synthetic CI results. No Bubblewrap namespace, real ImageBuilder execution, OpenWrt firmware artifact, target binary, physical hardware test or production release was performed.

### Exact branch / live ownership snapshot

- Child PR [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35), branch \`phoenix/release-build-script-publication-safety-20261117\`, parent #31/base \`59ed44d0b911e176f1a95b9cf5585ef811ffd31b\`.
- Source/test head at this entry: \`7bbf7c40ab09fd839faaaa3b5a14fec818e9a23b\`. This increment changes only \`tools/test_package_appliance_firmware.py\` (test-first commit) and \`tools/package_appliance_firmware.py\` (source corrections); this handover is the only documentation path.
- MASTER #288 current head \`a65d96161319740d4a54f62b5637bf7d65fb8a7f\`; \`OWNERSHIP_ROUTES.json\` remains \`DRAFT_REVIEW_ONLY\`. RELEASE's Experiments route \`.github/workflows/blazepwifi-build.yml\` → \`.github/workflows/pisowifi-ci.yml\` remains \`reimplementation-review\`, not copy/migration authorization.
- Experiments #242 current head \`734b89d9e7792247e8376335c3f3685500ab3f89\`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) completed SUCCESS, but Authenticode signing and release publication steps were skipped.
- Experiments #291 current head \`42797e2f3d65c30a1070caf49c93aebec149d897\`; compatibility run [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) SUCCESS. Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) failed at the CORE-owned mandatory handover freshness gate after target build jobs succeeded; downstream simulations/signing/publication were skipped. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at the shared handover freshness gate; Windows build/publisher were skipped. The 26 accumulated paths remain mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); no #291 path changed.
- COE integration #26 current head \`b382d233ff06c8791b1028bed3c617cc7b670d12\`; five distinct workflow types remain QUEUED with zero executed jobs. Its boundary/provenance documents identify the Experiments source as historical and #26 as a draft candidate, not completed byte-identity migration.
- COE parent #31 current head \`59ed44d0b911e176f1a95b9cf5585ef811ffd31b\`; parent shared/case runs #44222517238/#44222517258 passed, while mandatory sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) failed at unprivileged namespace preflight. Those are parent #31 results, not #35 exact-head acceptance.
- #35 remains OPEN / DRAFT / UNMERGED; independent submitted reviews: 0; review threads: 0.
- Cleanup-first #266 remains OPEN with all seven role tracks unchecked.
- Authorized Library inventory contains registry snapshots v3–v7 only; canonical private Drive registry v11 was not surfaced. No historical snapshot was substituted and no private registry contents/identifiers were copied to GitHub.

### Next owner actions / release limits

1. PHX-QA independently reviews source/test head \`7bbf7c40\`, including directory-entry identity revalidation and both mutation regressions.
2. PHX-INFRA supplies an authorized disposable no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces.
3. PHX-CORE / PHX-MASTER define and approve site-scoped RFC 4193 ULA /48 authority; no synthetic prefix substitution.
4. PHX-MASTER refreshes stale #172 PR-head references and resolves the inherited \`hardware-ci.yml\` ownership collision without RELEASE editing HARDWARE source.
5. Registry custodian restores authorized provenance-only access to canonical private registry v11.

No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC13 — close parent-directory descriptor when build-script creation is interrupted (2026-11-22)

**Disposition:** one RELEASE-owned descriptor-leak defect was reproduced test-first and corrected on the existing COE #35 child draft. PR #35 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**. This increment changes only the packager, its regression test and this handover.

### Finding and bounded correction

\`_open_new_file_without_symlink_parents()\` pins the output parent directory before the exclusive \`os.open(..., dir_fd=directory_fd)\` that creates the generated build script. If that final open is interrupted by \`KeyboardInterrupt\` or \`SystemExit\`, the old \`except Exception\` did not run. The helper then propagated the interruption without closing the parent descriptor, and the caller never received the descriptor pair needed to close it.

The helper now catches \`BaseException\` only around that final creation attempt, closes the pinned parent descriptor, treats \`EBADF\` as already closed, and reports a close failure without hiding the original open/interruption error. Script contents, exclusive creation, 0600-before-write / 0755-after-durable-write ordering, path checks and publication semantics are unchanged.

### Test-first lineage and fixture correction

- Initial test-only commit [\`81201891\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/8120189124ec299da2d6703296c6a4097e780471) attempted to intercept \`os.open\` before the POSIX dir_fd capability check. That replaced the function identity in \`os.supports_dir_fd\`, so the test fixture failed before reaching the target open. Push [#45026681025](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026681025) and PR [#45026685150](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026685150) recorded two fixture errors; **not product-defect evidence**.
- Corrected test-only commit [\`80c2897c\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/80c2897c669de04e6bc3077f4573f6b8fc7a24ba) obtains the real parent descriptor first, then intercepts only the final dir_fd-relative create call. Expected RED: push [#45026832892](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026832892) and PR [#45026838274](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026838274) each reproduced two failures (KeyboardInterrupt and SystemExit leave the parent descriptor open); 184 tests, two expected failures, two intentional skips.
- Source correction [\`13c63abd\`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/13c63abd33663630049fefc8442020b27bbb91d4) closes the descriptor for both interruption classes.

### Exact source/test-head Actions at \`13c63abd\`

- PR shared/firmware [#45026969797](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026969797) and push [#45026964680](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026964680): packaging/tool suite **184 PASS / 2 intentional skips**; firmware-hardening and shared-contract checks **PASS**; \`PHX-MANIFEST-DURABILITY-PASS\`. The following all-profile admission **FAILED CLOSED for all 10 profiles** because approved site-scoped RFC 4193 ULA /48 authority is undefined. ESP32/ESP8266 compile jobs were **SKIPPED**; overall shared workflow **FAILURE**, not green.
- PR sandbox [#45026969814](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026969814) and push [#45026964758](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026964758): host-preflight tests **33/33 PASS**, then Bubblewrap availability **FAILED CLOSED** because \`bwrap\` is absent (exit 125). Namespace verification and mandatory sandbox packaging regressions were **SKIPPED**, not passed.
- PR case-collision [#45026969795](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45026969795): **PASS**.

These are hosted synthetic CI results. No real Bubblewrap namespace, ImageBuilder firmware, approved target binary, physical hardware test or production package was produced.

### Live ownership / integration snapshot

- COE child PR #35 branch \`phoenix/release-build-script-publication-safety-20261117\`, source/test head \`13c63abd33663630049fefc8442020b27bbb91d4\`, parent #31/base \`59ed44d0b911e176f1a95b9cf5585ef811ffd31b\`. This correction is documentation-only; source/test paths are unchanged.
- MASTER #288 live head \`a65d96161319740d4a54f62b5637bf7d65fb8a7f\`; ownership routes remain \`DRAFT_REVIEW_ONLY\`. RELEASE's Experiments workflow route remains \`reimplementation-review\`, not migration authorization.
- Experiments #242 remains \`734b89d9e7792247e8376335c3f3685500ab3f89\`; Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) succeeded, but Authenticode signing and publication were skipped.
- Experiments #291 remains \`42797e2f3d65c30a1070caf49c93aebec149d897\`; compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) passed (provenance suite and both ESP32 core compatibility jobs). Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) had the ESP32, ESP8266 and 11 OpenWrt image jobs pass, but its validate job failed at CORE-owned handover freshness because source/workflow changes were newer than \`experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md\`; downstream simulation/signing/publication jobs were skipped. Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) failed at the shared handover freshness gate and identified \`.github/workflows/blazepisonet-softtimer-release.yml\` as changed; build-windows and publish-release were skipped. The stale #172 \`$buildWorkflow\` note is not current-head evidence. The 26-path diff remains mixed-owner (21 RELEASE / 3 CORE / 2 PISONET); RELEASE did not edit #291.
- COE integration #26 remains \`b382d233ff06c8791b1028bed3c617cc7b670d12\`, with five queued workflow types and zero executed jobs. Parent #31 remains \`59ed44d0b911e176f1a95b9cf5585ef811ffd31b\`.
- #266 remains OPEN with seven cleanup tracks unchecked. The canonical private Drive registry v11 was not surfaced through authorized Library search; only older v3–v7 snapshots appeared and none was substituted.
- #172's embedded #35/#291 refs are stale relative to the live PR heads. MASTER should reconcile its own index. The existing #35 diff also contains an inherited \`.github/workflows/hardware-ci.yml\` change (83 additions / 9 deletions from the #31 base); RELEASE did not modify that file in this increment. MASTER must resolve HARDWARE ownership before any integration. Independent #35 QA/Master review remains absent.

### Next owner actions / release limits

1. PHX-QA independently reviews source/test head \`13c63abd\`, especially BaseException cleanup and descriptor-close failure reporting.
2. PHX-INFRA provides an authorized disposable, ephemeral, no-secret Bubblewrap runner with working unprivileged user namespaces.
3. PHX-CORE / PHX-MASTER approve durable site-scoped ULA /48 authority; no synthetic prefix is substituted.
4. PHX-MASTER reconciles stale #172 refs and the inherited \`hardware-ci.yml\` ownership collision without RELEASE editing HARDWARE source.
5. Registry custodian restores authorized provenance-only access to canonical private v11.

No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and the 30-device/24-hour soak remain unproven or NOT TESTED. **PRODUCTION NO-GO.**
