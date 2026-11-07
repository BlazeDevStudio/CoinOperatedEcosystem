# Blaze PisoWiFi — Development Pass 05 (2026-11-08)

**PR:** [#18](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/18), still DRAFT and unmerged. **Only `Pisowifi/**`** changed. **Source:** already-public first-party `BlazeDevStudio/BlazingSystems-Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00` (no private keys, customer configs, payments, production deployment or proprietary source migrated).

## Concrete P0/P1 code fix — UCI read ambiguity

Pre-Pass-05 code in `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/config.sh` contained:

```sh
if old="$(uci -q get "blazepwifi.main.$key" 2>/dev/null)"; then had_old=1; else old=""; had_old=0; fi
```

A transient I/O or malformed UCI failure when the old option **existed** could be mistaken for a legitimately **absent** option. On later apply or commit failure, rollback deleted rather than restored the old option.

Fix commit `8c1a8558f34adb4048103fd76804d95019adcf98` now requires a successful, nonempty `uci -q show blazepwifi.main` snapshot with a valid section entry before any mutation. If `get` fails but `show` identifies the exact option key, the operation halts with CRITICAL and error 8, preserving old state. Missing option is accepted only when section is readable and option is absent from its enumerated keys. On normal success, existing audit/change semantics remain intact. UCI CLI syntax checked against official UCI documentation; real UCI binary not tested here.

### Locally reproduced exact-file RED/GREEN

Previous exact Git source file `config.sh` hash `10aff0703073dba8f02ed0eb036b9acf16e1f0c6` and previous executable test hash `7dc8a42addde12b1caf7dbc6cc1cb50dbfb87c74` were reconstructed into a disposable local directory, then verified with `git hash-object` matching GitHub. Original nine cases: `/bin/sh` **9/9 PASS**; BusyBox `ash` **9/9 PASS**.

Expanded suite against the old source deliberately failed (exit 1 after first baseline check): **RED**. The corrected file `da6319d5136f02f3b1d474460a91ccfef62dc449` and test `9c6ca0f1a10d3faa1043ded143807915cc191eb9` were locally executed and their **actual Git hashes** matched the two committed GitHub blobs, mode `100755`. **14/14 PASS** under `/bin/sh` and **14/14 PASS** under BusyBox `ash`. New cases include failed section snapshot, missing section record, failed `get` despite existing option, truly missing option, and delete-rollback after failed apply. The failed-get case verifies original DB bytes unchanged. No real UCI configuration or router was modified.

**Important limit:** this proves exact local source/test file execution on a disposable filesystem, **not** a full exact-head checkout of all scripts, GitHub Actions, real OpenWrt, nftables kernel, service reload, or physical hardware.

## Provenance-only recovery (separate commit)

Commit `0a5ad08eab37356289a1078872db962df06724d2` copied four already-public first-party OpenWrt **dormant source files** byte-for-byte from the pinned source and preserved original modes `100644`:
- `usr/lib/blazepwifi/member_migration.sh` — `058891bf2b13b59333b4247743fcccc8741bf9b4`
- `usr/lib/blazepwifi/console_ops.sh` — `92a44fa1c7f69a81b750acf6bac4acc98c637a3b`
- `usr/lib/blazepwifi/v2_shadow.sh` — `cd6f2421dfb4c0abad86e37547db863ac5f38768`
- `usr/lib/blazepwifi/v2_maintenance_freeze.sh` — `07b8c98b70a77a90bda3a85f57fabe540aabfb2c`

These files were **not enabled, invoked, or admitted as production authority**. Their public Git blobs match the source exactly; their behavior has not been validated.

## Recovery ledger and unresolved gates

Verified original rootfs: **61** files. Recovered: **42** (36 byte-identical upstream, 6 corrected source). Still excluded: **19**, including rental-specific services, remote-update/admin and v2 migration supports. Source inventory and exact per-file hashes/modes: `Pisowifi/SOURCE_INTAKE.json`.

**Not run:** full `Pisowifi/tests/run_focus.sh` as an exact-head checkout, the four upstream integration tests, or any GitHub Actions job; destination repository has no `.github/workflows` on PR branch. Existing legacy `tests/config.sh` mock UCI does not implement the newly required `show blazepwifi.main` and must be repaired before claiming suite PASS. The runner itself was not modified in this pass.

**Still P0 NO-GO:** Financial durability (#31/#32), independent antirollback witness (#43), physical durability (#34), protected signing, secure update/migration, firewall4/netns/real packet-path verification and safe networking configuration application/rollback. The `BP_CONFIG_APPLY_HOOK` executable override is still trusted-operator only; restoring UCI on failed apply does not rollback externally modified live services. Concurrency between config snapshot/get/set is not yet serialized. No production releases, merges, keys, flashing, coin operations, or cross-project edits.

## Next gate
Repair the upstream config test's simulated `uci show` compatibility, then run its full integration suite only when all first-party dependencies are recovered and validated. Add a strict isolated UCI state transaction/concurrency regression, followed by service rollback evidence, without enabling unfinished remote, rental or payment subsystems.
