# CORE config transaction reliability — 2026-11-03

**Repository:** `BlazeDevStudio/CoinOperatedEcosystem` (not the Phoenix source-owner PR chain).
**Scope:** `core/openwrt/rootfs/usr/lib/blazepwifi/config.sh`, local first-party refactor stacked on COE draft PR #8.
**Derived SHA-256:** `8720700298dc770aed8008b8eb4c0fa8823409122e80247ef6664e5b57a0dd13`.

## Original source identity (retained)

Upstream: `BlazeDevStudio/BlazingSystems-Experiments`, CORE draft #252,
commit `c2a7515f43aff7043b0c2274dcdc097f30d7efbb`.
Original `config.sh` blob `7bde717f02d6f1d90ca099ab29bff336824ad81f`;
original SHA-256 `4a73c0841614f841dd35df4e42f9bf1eedc3c5f8e89cb0d9a793f7ee692e20a2`.
The destination is **refactored**, not a byte-identical imported source.

## Observed failure mechanisms and bounded remedies

Previously, `bp_config_set` returned immediately after a failed `uci set`,
even though an implementation can mutate pending state before returning an
error. A failed apply attempted rollback but ignored `uci delete`, `uci set`
or `uci commit` errors. Concurrent setters were not serialized.
A return from the apply callback did not prove the UCI setting was retained.

This refactor installs a single, nonblocking `flock` lock spanning
snapshot, UCI set/commit, readback, apply, final readback and rollback.
It refuses to write when the lock cannot be acquired, when the previous
value or verified absence cannot be established, or when `flock` is missing.
Any set/commit/apply/readback failure attempts to restore the old value
(or delete an originally absent key), commits and checks the restored state.

The return statuses distinguish:

| Status | Meaning |
|---|---|
| `0` | UCI commit, apply callback, and post-apply UCI readback succeeded |
| `1` | Operation denied; previous UCI state restored and verified |
| `2` | Input rejected before mutation |
| `8` | Lock or initial snapshot unavailable; no mutation attempted |
| `9` | Restoration could not be verified; operator recovery required |

The existing developer apply hook remains a closed true/false-only test seam,
without arbitrary shell command execution. The normal installed apply path
remains unchanged when the hook is absent.

## Fault-injection acceptance and limits

`tests/core_config_contract.sh` uses a temporary, synthetic UCI database
and injected failures for write-after-mutation, commit failure, restoration
commit failure, missing original setting, failed section read and independent
file-lock contention. Existing validation and command-injection rejection
tests remain. GitHub Actions must execute the test at the exact PR head
before acceptance.

This is **not crash-atomic OpenWrt hardware evidence**. `flock` only
coordinates callers using the same lock. A live router's apply script can
partially reconfigure interfaces even if its UCI value is later rolled back.
Power-loss journaling, boot-time repair, controller protected identity and
anti-rollback, accounting migration, safe hardware admission and physical
150-cut/30-client acceptance remain NO-GO. No merges, releases, flashing,
production signing keys, paid operations, or unlicensed third-party source.
