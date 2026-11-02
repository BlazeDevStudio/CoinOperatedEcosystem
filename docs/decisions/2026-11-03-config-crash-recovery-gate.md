# CORE interrupted configuration change — read-only restart gate (2026-11-03)

## Identity and scope

- Repository: `BlazeDevStudio/CoinOperatedEcosystem`, separate from existing Phoenix owner source PRs.
- Draft parent: COE PR #9, `ecosystem/config-transaction-failclosed-20261103`.
- Only runtime source changed: `core/openwrt/rootfs/usr/lib/blazepwifi/config.sh`.
- Original first-party source: `BlazeDevStudio/BlazingSystems-Experiments` CORE PR #252 at `c2a7515f43aff7043b0c2274dcdc097f30d7efbb`, Git blob `7bde717f02d6f1d90ca099ab29bff336824ad81f`, SHA-256 `4a73c0841614f841dd35df4e42f9bf1eedc3c5f8e89cb0d9a793f7ee692e20a2`.
- Derived destination SHA-256: `1f802c26090eeff2263066b39783b5ce73ffa9fdb241607455fb8be27f6b2def`; record remains `refactored`, with unchanged source lineage.
- Production authorization remains `false`.

## Failure model and change

Prior synthetic tests covered process-lifetime config failures but did not distinguish a completed transaction from a killed process between `uci commit`, network apply and final verification. `flock` does not survive restart as a recovery witness.

Before *any* UCI mutation, the helper now creates a fresh, mode-600 pending marker under `/etc/blazepwifi/.config-transaction.pending` (override permitted for isolated tests) using a temporary file, rename and OS `sync`. A pre-existing marker or symlink is a **DENY**: `bp_config_set` returns `9`, and it will not apply or overwrite new settings. Success only clears the marker after UCI commit, apply and final UCI readback. A verified rollback also clears it; uncertain state retains it when possible.

`bp_config_recovery_status` is a **read-only reconciliation interface**: a new process can detect an unresolved marker, report operator recovery required, and refuse state promotion. The file contains only a fixed version marker and validated config key. It is never sourced or evaluated. It deliberately does **not** auto-restore an old UCI value or admit coins. The marker does not confer signature, custody or protected reboot freshness.

## Executed regression scope required

`tests/core_config_contract.sh` tests clean marker clearance after success and rollback; a second shell process simulates a restart and detects a leftover marker before a write; both before-UCI and after-UCI-commit cuts require refusal; a blocked writer cannot change UCI; missing journal directory and symlinked marker are rejected; after explicit synthetic operator repair, clean writes may resume. Preexisting partial-set/commit/rollback, lock contention and injection cases remain.

## Critical limitations: still NO-GO

- A `sync` return is **not** proof that underlying flash persisted the marker before UCI. Dirty writeback, filesystem reorder and flash loss still need independent cold-reboot/power-cut testing.
- Marker deletion followed by a failed `sync` can leave no durable pending evidence. Do not claim crash consistency until transactional persistence or hardware witness is independently validated.
- `bp_config_recovery_status` is a callable library check; **there is no installed OpenWrt boot service or pre-network activation wiring in this draft**. Real boot-time enforcement is not implemented.
- UCI config and applied network interfaces can disagree following a partial `apply-config.sh` failure. This draft does not repair physical VLANs, router forwarding, GPIO or money.
- No production privileges, signed controller identity, anti-rollback witness, real paid balances, physical flasher, 150-cut acceptance or 30-device soak are proven.

Operator reconciliation must occur with service disabled and exact device/source verification. Never remove a real pending marker just to silence a warning.

No merges, customer changes, firmware flashing, releases, live keys, or unlicensed external source copied.
