NO-GO FOR SHOP INSTALL

# Experiments #31 — member/receipt crash atomicity gate

Scope: **PisoWiFi only**, draft COE PR #18. Financial writes and paid acknowledgements are NOT approved. No source repo deletion, real coins, router flashing, signed v2 authority, or auto-reconciliation.

## Verified source and failure window

- Current destination `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/member.sh` Git blob `69af39052959a1d6a349851b4fbd909a9ad53aeb` is byte-identical to pinned Experiments `6d4c9b487af4d768c4d7627654d119417fcc6e00`.
- `bp_member_transfer` computes both post-transfer balances, writes a new `members.tsv` snapshot, then records the transaction in the independent `member-events.tsv`. The revision is also mutated separately.
- `bp_member_balance_change` similarly persists a new balance before the paid receipt.
- The existing `paid-state-uncertain` marker is a valuable fail-closed quarantine. It stops subsequent payment and ACK, but does **not** make multiple files a single durable transaction. A receipt failure can leave new balances and no receipt. Removing the marker automatically would risk double credit or loss.
- The legacy financial receipt history now retains paid IDs and has a bounded fail-closed file-capacity check; this is not a protected independent replay index or a crash-atomic ledger.

## Regression prepared, NOT passed

`Pisowifi/tests/member_crash_atomicity_red.sh` (blob `39d851f8cdfa425d836620efd8680a142d858bf0`) sets up synthetic members, forces the receipt recorder to fail, then demands that neither member balance advance without a receipt. It also checks the no-ACK response, uncertainty marker, and denied retry. The expected original-code outcome is RED, as indicated by the filename.

Actually performed in this pass: `sh -n /mnt/data/member_crash_atomicity_red.sh` **PASS (one syntax check)** on a local byte-for-byte copy whose `git hash-object` equals the committed Git blob above. This **does not execute** the regression against the branch's actual `member.sh`.

Not performed: running the test with the source files from an exact full checkout; BusyBox ash; real OpenWrt; fault-injected actual fsync/rename/power cuts; concurrency/out-of-order ACK; duplicate history retention; real coin hardware; builds; or CI. No pass count is claimed for these.

The RED fixture is intentionally **not** registered in `tests/run_focus.sh`. Do not mark CI green by skipping the defect. The issue is still OPEN.


## Update 2026-11-11 — member transaction journal implemented (Issue #31 still OPEN)

`member.sh` now stages `members.tsv`, `member-events.tsv` and `member-revision`, writes a SHA-256 commit record (`member-txn.commit`) by tmp+rename (the commit point), applies the staged files, then removes the record. `bp_member_lock` runs `bp_member_txn_recover` first: a commit record rolls forward (digest-verified, idempotent); no record discards stale stage files; any mismatch fails closed and preserves the evidence. All six member mutators (`bp_member_transfer`, `bp_member_balance_change`, `bp_member_delete`, `bp_member_create`, `bp_member_patch`, `bp_member_set_password`) use it, and `rental.sh` now applies an equivalent two-file redo journal (`rental-txn.commit`) across `rental-devices.tsv` and `rental-events.tsv` for `bp_rental_apply_coin`, `bp_rental_lease_add`, `bp_rental_lease_expire` and `bp_rental_device_rename`. `paid-state-uncertain` is still pinned before each mutation and is **never auto-cleared** by failure or recovery.

Evidence (exact head `e9e1af43501840087842227c02e52f696c5e7961`):
- `tests/member_receipt_failure_atomicity.sh` (formerly the expected-RED witness) PASS.
- `tests/member_txn_journal.sh`: 10 simulated-fault cases PASS (success, receipt failure, crash after commit record, replay idempotence, crash mid-apply, tampered stage fail-closed, uncommitted stage discard, balance_change/delete, member create/patch/password, and rental coin-credit receipt failure + roll-forward recovery). Two mutation checks (no-op recovery, no digest check) were detected by the suite.
- GitHub Actions: both suites pass under POSIX sh and BusyBox ash.

Still NOT proven (gate stays NO-GO): real power-cut/flash rename+sync ordering (#34); anti-rollback witness (#43, a full-flash restore is undetected); concurrent unlocked readers can observe the brief apply window; voucher redemption (`accounts.tsv` + `vouchers.tsv`) and multi-file rental device revocation (`bp_rental_device_revoke`) remain unjournaled; independent QA review.

Correction: earlier project notes described this defect as a `members.db`/`sessions.db` split. The affected files are `members.tsv`, `member-events.tsv` and `member-revision`.

## Required implementation before moving past #31

1. Choose **one authoritative, bounded financial journal** with stable transaction IDs and full source/controller/target/payload binding. Retain deduplication independently of trimmed UI history, and fail closed at capacity.
2. Record a durable PREPARED intent with complete before/after snapshots and receipt identity **before** changing any materialized balance; commit with an explicit recovery contract. The source must prove flush/rename/directory durability on the intended filesystem, not merely claim it.
3. Replay a proven durable committed journal exactly once. An uncertain or pending marker must remain blocked until documented authorized reconciliation; never auto-clear it or re-add the same coin.
4. Execute negative fixtures for every failed write, interrupted transition, duplicate/concurrent event, stale/out-of-order ACK, source/controller/target collision, corrupted revision and exhausted storage.
5. Rerun the exact-HEAD tests, inspect build artifacts, and seek separate spare-device physical power-cut proof. No v2 paid acknowledgement or customer install.

## Additional admission blockers from the same scoped scan

All **76** file blobs listed by `SOURCE_INTAKE.json` (61 runtime, four migrated tests, 11 derived fixtures) were fetched at the draft branch and matched the manifest SHA. A limited pattern scan found the literal sentinel `CHANGE_ME` only in `openwrt/rootfs/etc/uci-defaults/99-blazepwifi` as a legacy placeholder-rejection check, **not as a configured default password**. This is not a complete credential audit. Also, the bootstrap script's random-secret helper has a predictable timestamp/PID fallback if system randomness fails; do not claim first-boot secret generation is secure until this has been replaced with a hard failure and verified end-to-end.

Other independent NO-GO gates: absent installable OpenWrt image and live apply/rollback program, protected external anti-rollback witness (#43), unsigned distribution, and spare-machine physical proof (#34).
