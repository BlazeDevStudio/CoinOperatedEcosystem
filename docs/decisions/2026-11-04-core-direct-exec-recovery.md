# CORE direct executable and running-loop recovery enforcement (2026-11-04)

Repository: **BlazeDevStudio/CoinOperatedEcosystem**. Stacked on COE draft PR #11. This does not modify the original owner-controlled Phoenix development PRs or any customer hardware.

## Independent source identity

- Original first-party source: `BlazeDevStudio/BlazingSystems-Experiments`, CORE draft PR #252, commit `c2a7515f43aff7043b0c2274dcdc097f30d7efbb`.
- Original executable: `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/sbin/blazepwifi-core`.
- Original Git blob: `94c6bfa462b509587e0ea5416c0481de0cb641f0`.
- Original SHA-256: `f789066018389fb014e56c50718376bdbbc1611d173a6b004a10aa090a3b818a`.
- Local destination: `core/openwrt/rootfs/usr/sbin/blazepwifi-core`.
- Derived destination Git blob: `6d81377833a8c06bae6937343d21a30275652062`.
- Derived destination SHA-256: `5169f96f0284a59f92d0dca3b6de6fd5c4933692ec91a075072a68b03be403ec`.
- Intake state: `refactored`, production authorization `false`.

## Root cause and bounded response

COE PR #11 inserted a read-only recovery preflight in the OpenWrt `rc.common` service entrypoint. The underlying `/usr/sbin/blazepwifi-core` script can also be executed directly or be active when a pending configuration transaction appears, bypassing that one-time preflight.

The daemon now checks the **canonical** `/etc/blazepwifi/.config-transaction.pending` path before sourcing `common.sh` or attempting `bp_init_dirs`, `nft`, or account authorization. A non-real/missing/symlinked configuration directory or source library is a denial. It does not honor inherited `BP_CONFIG_PENDING_FILE` overrides. It loads the same `bp_config_recovery_status` implementation as the init-script gate.

Within the existing account-processing loop, the daemon checks the recovery state again before `sync_accounts`. If the check fails, it attempts to flush the `auth_macs` nft set and exits with status `9`. The pending marker is not removed or auto-reconciled; there is no new payment, controller admission, GPIO or UCI mutation path.

The exact source executable runs in `tests/core_direct_exec_recovery.sh` with **only** path substitutions in a disposable copy, a synthetic account, and mocked `nft`, `common.sh` and `sleep`. It tests initial denial before any network setup; inherited override, symlink and missing library/directory denials; clean initial authorization; an unresolved marker appearing during the loop; and library disappearance during the loop. Each runtime halt must return `9` and attempt to flush authorizations.

## Still unproven and strictly NO-GO

- `nft flush` is best-effort. If nft fails or an external rule independently permits traffic, **this is not proof of network fail-closed containment**. A source-level check does not eliminate races between checking the marker and individual account authorization calls.
- Other entrypoints—remote admin, update-guard, direct CGI, independent payment operations, external processes and ESP firmware—are not protected by this specific daemon change. A complete system-wide policy/authority map and runtime integration tests remain necessary.
- No actual OpenWrt boot/procd or device execution, physical marker persistence, protected cryptographic witness, power-cut tests, financial reconciliation, or user device deployment was performed.
- Real coin/relay admission, real payment paths, merges, releases, flashing and production signing keys remain prohibited. No third-party commercial source was imported.

This branch is an isolated **draft** stacked on #11. The source-integrity and source-linked CI jobs must be green on its exact head before accepting the scoped result.
