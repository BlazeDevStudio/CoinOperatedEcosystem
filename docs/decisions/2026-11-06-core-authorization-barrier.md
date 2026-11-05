# COE CORE per-MAC authorization transaction barrier — 2026-11-06

## Scope and lineage

This work belongs only to the distinct `BlazeDevStudio/CoinOperatedEcosystem` repository. It is stacked on COE draft PR #14, which itself preserves the active PR #12 direct-daemon and running-loop preflights. It does not modify source-owner Phoenix PRs, merge existing draft branches, or change payment, controller or GPIO code.

Original first-party source remains `BlazeDevStudio/BlazingSystems-Experiments`, CORE draft PR #252 at commit `c2a7515f43aff7043b0c2274dcdc097f30d7efbb`; original `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/sbin/blazepwifi-core` Git blob `94c6bfa462b509587e0ea5416c0481de0cb641f0` and SHA-256 `f789066018389fb014e56c50718376bdbbc1611d173a6b004a10aa090a3b818a`. The derived, refactored `core/openwrt/rootfs/usr/sbin/blazepwifi-core` is SHA-256 `655fdbcab8bdfe6f0de3b5cab34c7c0a0586a6c2272a2e8f5c1c85282d08d4b2`; manifest `production_authorized=false`.

## Narrow race identified

PR #12 rechecks `bp_core_recovery_gate` once per account-loop iteration. However, the first check occurs **before** `sync_accounts()` obtains current time and parses an account record. A legitimate `bp_config_set` could create the pending configuration marker during that gap and the loop could subsequently authorize a MAC despite a pending transaction.

The local helper `bp_core_authorize_if_stable` now uses the existing `bp_config_lock` / `bp_config_unlock` functions and the canonical `/var/run/blazepwifi-config.lock`, overriding inherited `BP_CONFIG_LOCK_FILE` values at this daemon boundary. It holds the lock across recovery preflight, the existing `bp_authorize_mac` call, and an immediate post-grant preflight. Every positive `bp_authorize_mac` call in the accounted loop goes through this helper. The previous loop-level recovery check from PR #12 is retained.

On a missing/busy lock, failed guard, or a newly detected marker after a grant, `bp_core_stop_grants` best-effort flushes nft `auth_macs` and exits with code `9`. A test-only path substitute allows the mock process to use a disposable lock, but the deployed source contains a fixed lock path.

## Executable test and acceptance scope

Existing source-linked `tests/core_direct_exec_recovery.sh` is extended, without introducing a parallel model, to exercise the actual derived CORE daemon with synthetic `common.sh`, nft, UCI state and timer/lock fixtures. The added cases are:

1. After loop-wide check but before the MAC grant, mock `bp_time_sane` plants a pending marker. No account authorization is allowed and a flush is attempted.
2. While the mock `bp_authorize_mac` runs, it plants a marker *without respecting the lock*. The post-grant check detects it, attempts a flush and stops with code 9. The test intentionally allows one transient mock grant, demonstrating a remaining out-of-band writer risk.
3. Another process holds the canonical config lock. The daemon refuses to grant, attempts the flush and returns 9.

Existing start/loop/missing-library and pinned five-component tests remain. The CI result on the **exact latest PR head** is required before any acceptance.

## Critical limits and production NO-GO

- `flock` coordinates **only processes using this exact lock**; other code or a malicious/uncoordinated process can still change a marker or nft state. The code does not make nft + marker + UCI one kernel-atomic transaction.
- The upstream `bp_authorize_mac` function masks nft command failures with `|| true`. A returned success is **not** evidence that the firewall permitted/denied traffic correctly. The flush on denial is also best-effort.
- A timer between clean check and next iteration can retain previously authorized entries; immediate revocation requires stronger, independently verified service-level authority fencing, not just a periodic shell loop.
- A real OpenWrt overlay/filesystem power-cut persistence witness, cold-boot probes, protected signer/anti-rollback, reversible financial migration, 150-cut/30-client hardware soak, and real payment/controller admission remain unproven.

No production deployment, merge, release, flashing, commercial third-party source copying, live credentials, financial state, or customer hardware actions are permitted. This is an isolated draft with synthetic tests only.
