# Coin Operated Ecosystem — fail-closed OpenWrt core startup (2026-11-03)

This is a separate **CoinOperatedEcosystem** draft, based on COE PR #10. It does **not** alter Phoenix app-owner branches or customer routers.

## Original source and explicit derived identity

- First-party original: `BlazeDevStudio/BlazingSystems-Experiments`, CORE PR #252, commit `c2a7515f43aff7043b0c2274dcdc097f30d7efbb`.
- Original file: `experiment/openwrt/BlazePwifi/openwrt/rootfs/etc/init.d/blazepwifi`.
- Original Git blob `4a3d6240e700520c78acff4d3daea5b98d5df5d7`, SHA-256 `ea13be79fac39d0dee6de3aae178e7a4c69e9d998419d62d9e8a81cf55183ba2`.
- Derived file: `core/openwrt/rootfs/etc/init.d/blazepwifi`, Git blob `34aaee0da17648016ea3547cbb30c0377d6aee19`, SHA-256 `72594c9490868943aa35659e04455b8031dba225b45df0034ffe4ce8d91738c8`.
- State: `refactored`, not an identical or historically migrated original. Global `production_authorized=false`.

## Root issue and change

The original `/etc/rc.common` start_service function created a procd instance for `/usr/sbin/blazepwifi-core` when enabled, without consulting the recovery state. The COE config library from PR #10 retains a pending transaction marker across interrupted UCI changes; that marker is meaningful only when service startup also respects it.

Before `procd_open_instance`, the refactored init script requires:
1. A readable real `/etc/blazepwifi` configuration directory, with no symlink at its path.
2. A readable real `/usr/lib/blazepwifi/config.sh` (no symlink) with the `bp_config_recovery_status` function.
3. A clean recovery result for the canonical pending file `/etc/blazepwifi/.config-transaction.pending`. The init script forces that pathname and ignores inherited `BP_CONFIG_PENDING_FILE` overrides.

An unresolved marker, invalid library, or unavailable config directory returns failure *without* opening a procd instance. The init script never removes a marker, edits UCI, changes GPIO, or auto-restores a pending change.

The new `tests/core_startup_preflight.sh` runs a path-substituted copy of the **actual source init script** under a disposable simulated procd environment. It verifies success, disabled mode, pending marker preservation, symlink rejection, missing path, invalid recovery function and environment override protection.

## Scope limitations — production remains NO-GO

- The file is part of an unmerged source tree, not installed on any router; native OpenWrt rc.common/procd behavior and actual boot ordering are not tested.
- Only this CORE init entrypoint is guarded. Other init scripts, direct binary starts, remote admin, portal, network changes and ESP coin GPIO are NOT guarded by this PR.
- A journal written with `sync` is not a hardware-protected durable witness. Flash ordering, torn writes, NAND/overlay failover, 150 power cuts, and actual rollback remain unproven.
- Protected controller identity, anti-rollback, financial ledger migration, paid operation and hardware admission remain denied.
- No merge, release, real payment, signing key access, flashing or proprietary third-party code is authorized.
