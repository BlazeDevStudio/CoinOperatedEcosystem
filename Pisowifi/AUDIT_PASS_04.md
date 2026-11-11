# Blaze PisoWiFi — Development Pass 04 (2026-11-08)

**GitHub:** `BlazeDevStudio/CoinOperatedEcosystem`, exclusive `Pisowifi/**`. Draft PR #18, open/unmerged.
**Verified source:** `BlazeDevStudio/BlazingSystems-Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00`, `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/config.sh`.
**Exact original source blob:** `7bde717f02d6f1d90ca099ab29bff336824ad81f` (4266 bytes), matched locally before editing.
**Exact committed fixed blob:** `10aff0703073dba8f02ed0eb036b9acf16e1f0c6` (4853 bytes).
**Focused executable regression blob:** `7dc8a42addde12b1caf7dbc6cc1cb50dbfb87c74`.

## Reproduced source-level defects
- Original `bp_config_set` masked both UCI restore and restore-commit errors (`|| true`) and returned ordinary failure 1 even when the new config remained active. New fault-injection test fails at the fourth scenario under the original blob (expected distinct failure return 8 and CRITICAL reporting).
- Original optional `BP_CONFIG_APPLY_HOOK` used `sh -c "$BP_CONFIG_APPLY_HOOK"` and therefore interpreted shell control operators. A string such as `false; touch <temp>/injected` could execute the second statement and return success. Fixed hook validates a single executable token and calls the program directly; the normal fixed absolute production path stays unchanged.

## Source cleanup
- `bp_config_restore` now runs in a subshell and checks UCI set/delete and commit outcomes. It returns error 8 on an unverified restore and does not silently continue.
- `bp_config_set` now returns explicit 8 + `CRITICAL: UCI rollback failed ...` when a failed commit or apply cannot be restored; ordinary failed operation with a confirmed restored value remains 1; invalid configuration remains 2; successful commit and apply remains 0.
- No false `config_change` audit event is emitted on failures; no config data, tokens, keys or pricing fixtures changed.
- `BP_CONFIG_APPLY_HOOK` is still a **trusted test/operator executable override**; anyone who controls that environment variable can request an arbitrary executable. This fix only stops *shell-string interpretation*, not execution by a privileged operator. Do not expose the override to untrusted client input.

## Verification
**Actual fixed config.sh blob** `10aff0703073dba8f02ed0eb036b9acf16e1f0c6` executed via:
- `sh Pisowifi/tests/config_faults.sh` — **9/9 PASS**;
- `busybox ash Pisowifi/tests/config_faults.sh` — **9/9 PASS**;
- `sh -n` and `busybox ash -n` syntax checks — PASS.

The fault-injection scenarios: normal set+audit, apply rollback success, commit rollback success, failed restore-set CRITICAL 8, failed restore-delete CRITICAL 8, rejected injected shell operator without side effect, valid single executable hook, invalid numeric validation, and persistent UCI commit failure CRITICAL 8. All operations were on a disposable fake UCI db under `mktemp`; no router configuration changed.

Previously established local extracted-function nfts tests (10+6), older nft tests (5+4), and capabilities tests (7) were re-run PASS in their existing separate mock-source labs. **These are NOT exact-head full checkout tests**, so do not claim CI coverage for those suites. `Pisowifi/tests/run_focus.sh` is a convenience dispatcher for six focused script files, but the full dispatcher on one exact-head checkout has **not** been executed in GitHub Actions.

## Release gates / unresolved risks
- The recovered OpenWrt rootfs is still **38 of 61 original files**, now **32 byte-identical and 6 derived**, with 23 missing (includes rental, remote/update/migration dependencies). The four original integration suites remain unexecuted.
- A committed UCI rollback does not undo partial live service changes (uhttpd/firewall) made by an apply script. Actual service-level transactional rollback remains unsupported and MUST NOT be claimed.
- No protected quarantine marker for uncertain config, no storage I/O/power loss proof, no actual UCI executable, no ImageBuilder, no real kernel nft/netns, no firewall4 integration, and no physical router verification.
- Financial integrity #31/#32, rollback witness #43 and physical durability #34 remain P0 NO-GO. No deployment, merge, release, paid operation, key processing or router flash.
- All changes restricted to `Pisowifi/**`. Do not edit Phoenix CORE, Pisonet, Android, independent ESP, or standalone Rental.

## Next gate
Execute six focused test scripts as a single exact-source checkout on a disposable runner, then review the UCI `get` error distinction (absent option vs I/O) and live service apply/rollback semantics. Audit remaining OpenWrt-only dependencies and run real nft namespace tests before considering appliance build. Maintain strict no-merge/no-release.
