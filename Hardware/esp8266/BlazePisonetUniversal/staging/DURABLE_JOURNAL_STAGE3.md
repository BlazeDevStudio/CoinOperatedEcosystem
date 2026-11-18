# BLAZE PISONET INTERCON V1.8 — Durable Transaction Snapshot (Stage 3)

**Release status: DRAFT / NO-GO for live paid Master→Slave transfers.** Existing standalone timer functionality remains. This milestone implements a real embedded LittleFS journal and runs real fault-injection tests, but it deliberately does **not** connect that journal to live time/sales or allow remote coin intake.

## Relationship to maintained firmware

This stage is stacked on [V1.7 authenticated peer PR #38](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/38), stacked on [Universal migration/staging PR #36](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/36). All original Labs, BlazePwifiVendo, and parallel INTERCON V1.6 source remains untouched. This is the existing V1.5 ESP8266 hardware/timer with Stage 1 discovery, Stage 2 authenticated PING/PONG, and a Stage 3 storage engine.

## Design and implementation

### Dual-slot LittleFS storage

- `InterconDurableJournal.h`: a hardware-independent, deterministic 76-byte record format with magic, version, role, generation, local and paired chip IDs, Master's pending event, Slave's credit sequence, canonical remaining-time units and paid-event count. Each record includes CRC32 for accidental corruption detection (authentication still comes separately from HMAC-SHA256).
- `InterconLittleFSJournal.h`: actual ESP8266 LittleFS adapter for `/blaze-pay-A.bin` and `/blaze-pay-B.bin`. New snapshots overwrite **only** the inactive slot, then flush/close, reread, and verify byte-for-byte before the in-memory state advances.
- On reboot the journal validates the **entire** record and identity. If either present slot is corrupt or a committed-generation slot disappears, recovery returns **CORRUPT / LOCKED** rather than silently reverting to an earlier paid balance.
- Two valid snapshots must have consecutive generations. The latest valid generation wins. A single generation-1 snapshot is permitted during explicit initialization; a single later-generation snapshot is not accepted.
- An IO uncertainty (a write reports failure even if bytes may have reached flash) locks the current controller instance. Reboot recovers a complete new snapshot if both images are consistent or locks on any torn image. It never automatically erases storage or generates a new journal.
- `Journal::applySlave()` persists the new remote credit sequence **and** the new balance in the **same 76-byte image** before returning `Applied`. Retransmission of the same event is `Duplicate`. If the durable commit does not verify, it returns `NotDurable`.
- `Journal::stageMaster()` persists exactly one outstanding physical coin event before any send; another event is denied until `settleMaster()` durably acknowledges the previous sequence.
- `Journal::checkpointRemaining()` persists decreasing remaining time using the same record and sequence, avoiding an independent dedupe journal that might diverge from a separately written balance.

### Firmware integration boundary

- The real sketch compiles both journal modules and **reads journal health at startup** when the board is paired and in Master/Slave mode. The existing dashboard reports `Healthy`, `Missing — not initialized`, `Corrupt — locked`, `Wrong peer/role — locked`, or `Storage error — locked`.
- The firmware **does not automatically initialize** missing journals, migrate EEPROM balances, apply received CRED packets, issue money acknowledgments, or enable Master/Slave physical CS. There is no operator web endpoint for journal initialization, nor any path from `interconSecureReceived()` to `applySlave()`.
- The original V1.5 EEPROM balance is still the operational timer. The journal's read-only status must not be interpreted as a synchronized paid balance. The value `Healthy` means the on-disk experimental journal is internally consistent, **not** that live paid time and remote transactions are integrated.
- Standard retains local coin input and timer. Master and Slave remain **coin-locked** until the following canonical-timer and transaction wiring milestones pass tests.

## Failure-injection validation

`Hardware/tests/intercon_durable_journal_test.cpp` uses the actual portable journal against an in-memory two-slot flash surrogate. It tests:

1. Fresh initialization requires **both** slots to be absent (and is explicitly separate from live firmware).
2. Accepted credit survives reboot; a duplicate after retransmission does not add time.
3. Signed-issuer binding, out-of-order sequences, conflicting last-sequence amount and overflow denial.
4. Progress of paid-time countdown is checkpointed without changing the last accepted coin ID.
5. Every truncated inactive-slot write prefix (0–75 of 76 bytes) yields fail-closed recovery, not old-balance fallback.
6. A full write that physically reaches flash but reports IO failure recovers the newest committed record and still deduplicates retry.
7. A corrupted slot, disappearing post-genesis slot, wrong peer, or generation gap causes lock.
8. Master unacknowledged event and settlement survive reboot; stale acknowledgments cannot clear pending coins.
9. No automatic resetting/reinitializing of a corrupt or previously used journal.

CI runs the native fault-injection test, earlier native HMAC/parser and ledger tests, static no-credit-gate assertions, and the **real** NodeMCU ESP8266 Arduino compilation.

## What is still required before real payments

1. **Single canonical balance**: migrate the current live EEPROM paid timer to journal-authoritative paid-time accounting, including manual grants, periodic countdown checkpoints, sales treatment and reset semantics. Do not permit two writable "authoritative" balances. Design a guarded, one-time migration with independent backups and rollback.
2. **Master real coin delivery**: record physical coin edge/value and selected Slave target before sending; enforce one active target and fail-closed CS, recover uncertain pulses, and confirm the coin acceptor's electrical pulse format.
3. **Slave ACK and recovery**: only paired, HMAC-signed, correctly targeted CRED events may reach the transaction engine; ACK only after durable credit and relay state updates, with duplicate-proof receipts and reboot reconciliation. A lost ACK must never grant time twice.
4. **Key/identity lifecycle**: binding to chip IDs alone is insufficient across pairing-secret rotations, factory reset or restored flash image. Add a monotonic enrollment epoch and operator-controlled balance/transaction reconciliation before any re-pair or reinitialize.
5. **Storage durability and wear**: a LittleFS `flush()`/close and verified reread is not a substitute for actual brownout testing, robust external power design and endurance assessment. The dual-slot design is conservative but cannot prove atomicity against every physical flash failure mode.
6. **Node topology**: multi-target Master selection and per-Slave journals require a separate per-peer namespace with distinct durable windows, not a single global pending item.
7. **Hardware qualification**: boot-time relay polarity, D0 cutoff behavior, D6 isolated PWR_SW pulse, D7 CS driver, TM1637 D1/D2, simulated repeated outages, lost packets and Wi-Fi client isolation on real ESP8266 boards.

**No flashable production release is authorized by successful CI alone.** Preserve all previous paid balances and existing maintained upstream branches. Do not enable CS on Master/Slave until the complete chain is physically verified.
