# Blaze PisoWiFi — Development Pass 03 (2026-11-08)

**Repository:** `BlazeDevStudio/CoinOperatedEcosystem` (public).
**Exclusive directory:** `Pisowifi/**`.
**Review:** [draft PR #18](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/18), unmerged.
**Source baseline:** `BlazeDevStudio/BlazingSystems-Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00`, `experiment/openwrt/BlazePwifi/`.

## Defect reproduced (P0)

The original `common.sh` `bp_authorize_mac` and `bp_deauthorize_mac` swallowed `nft` failures with `|| true`. Original `blazepwifi-core:sync_accounts` also masked failed unsynchronized-clock `nft flush` and did not check individual authorization results. Running the original helper logic through a disposable fake-nft harness reproduced RED: an absent MAC's grant returned success when `nft add` failed.

## Stage C — cleanup and stabilization commits

- `7b666b8351760857708c1db83d8920c5259fd3a3`: first-party `common.sh` now validates MAC addresses; requires membership readback after add; handles already-present grants and already-absent revocations as idempotent **only** on verifiable set state; fails on unreadable set or remaining MAC. `blazepwifi-core` now returns error 9 and attempts to flush all authorization after failed account synchronization, including failed clock-unsafe revocation. Main loop explicitly exits on `sync_accounts` error. Source-linked `tests/nft_membership_failclosed.sh` added.
- `18d109a13118a6112378b9c84185410ca21d2c16`: `bp_bind_device` propagates failed old-MAC revocation or new-MAC admission, attempts global MAC flush and returns error rather than success. Customer `cgi-bin/api` `connect/pause/resume/disconnect` reject a false `ok:true` when kernel access is unverified; response warns when account write may already have committed. Adds `tests/nft_account_binding_guard.sh` (actual common function execution with stubbed account writes, five failure-response source checks).

**Strict scope:** existing account balances, formats, voucher algorithm, paid journal code, original origin, and all other project directories remain unchanged. No new payment or network features.

## Verification performed and limits

1. Local shell excerpt reproducer against original grant helper: **RED** (failure returned success).
2. Local shell harness using the corrected helper + core function logic with fake `nft`: **10 PASS**, including add/get/list/delete failures, idempotent states, invalid MAC, unsynced time and core error propagation.
3. Local rebind/account boundary harness using corrected function logic with stubbed account writes and fake `nft`: **6 PASS** (five dynamic binding/flush cases and five static CGI error-response source checks grouped into sixth check).
4. Both committed test files' exact Git blob SHA values match locally tested script bytes: `9f27d228b3b6a8677902e26d9d91a689b4c60ec8` and `a7ee6a2ce2459c02ce7f83eef05f4b384092ad09`. The local source harness used source-equivalent extracted functions, **NOT** full committed source checkout or target hardware. Do not call this an exact-head full suite run.
5. Exact PR branch GitHub Actions: **0 runs, NO JOB IDs**. No full OpenWrt builds, actual nft kernel transactions, firewall4 reload, paid credit, power loss, router or captive-client acceptance.

## Remaining blockers

- **P0:** Kernel set readback is not packet-path verification. Concurrency/TOCTOU, out-of-band nft writers, firewall4 reload, missing nft table, failed global flush and non-atomic external policy all remain risks. A failed global flush can leave paid members authorized; CRITICAL logs are not proof of revocation.
- **P0:** Financial durability/antirollback (#31/#32/#43), physical endurance (#34), protected signing, migration and voucher/payment consistency remain unproven.
- **P0:** 23/61 upstream rootfs files are not recovered. Destination remains an incomplete and non-deployable OpenWrt appliance.
- **P1:** Original `config.sh` shell-string apply hook, UCI transaction rollback, and additional CGI endpoints must be audited separately for authorization and state-race correctness.
- **P1:** Entire original `tests/{portal,config,integration,security}.sh` were preserved but cannot be called green; their runtime/build dependencies and physical evidence remain outstanding.

## Next engineering gate

Run `sh Pisowifi/tests/nft_membership_failclosed.sh` and `sh Pisowifi/tests/nft_account_binding_guard.sh` against the **exact GitHub HEAD** in an isolated Linux checkout with fake nft; repair any mismatch before source admission. Next conduct a real nft network-namespace packet-path check on a test Linux kernel or runner (not a router), and audit the unrecovered first-party OpenWrt dependencies with independent source provenance. No merge, release, real keys, paid activity, customer-state edits or physical acceptance.
