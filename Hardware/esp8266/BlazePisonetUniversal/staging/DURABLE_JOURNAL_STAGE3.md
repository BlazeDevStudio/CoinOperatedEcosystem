# BLAZE INTERCON Stage 3 — Durable Master/Slave Flash Journal

**Release status: DRAFT / NO-GO for coin forwarding.** This stage adds a real flash-backed transaction journal to the V1.5-derived firmware, compiles it for NodeMCU ESP8266, and tests crash/retry behavior independently. It does not connect paid Master/Slave events to the live timer.

## Repository lineage and scope

- Based on draft [PR #38](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/38) (authenticated HMAC peer handshake), stacked on draft PR #36 (V1.5-derived INTERCON AP+STA discovery).
- The independently maintained INTERCON V1.6 branch / PR #37 was **not edited**; this new work lives on a separate reviewable branch.
- The locally owned Standard Pisonet timer's saved-time, relay, CS, pin configuration and sales EEPROM layouts are unchanged.
- No remote `CRED`, `ACKN`, relay, time or CS actions are accepted. **Master and Slave physical coin acceptance stays disabled**.

## Actual implemented code

- `InterconDurableJournal.h`: portable 64-byte explicitly little-endian, CRC32-checked record containing a version, journal role, generation number, authorized issuer, last accepted/issued event number, remaining time, accepted event count, last credit duration, and one pending Master event.
- Dual alternating A/B records: always write the inactive slot. On valid writes, the new higher generation becomes authoritative. A failed/uncertain write locks further operations until reboot and reconciliation. A damaged slot produces `DEGRADED_LOCKED` rather than silently abandoning unknown financial events.
- `InterconJournalFS.h`: actual ESP8266 LittleFS backend. Write `.tmp`, flush/close, read back and verify before replacing the **inactive** destination; keep the active valid record untouched. After restart, choose the highest valid generation, not the last RAM state.
- Master transaction transitions require a **single pending event**, strictly increasing issued sequence, and explicit clearing only of that same pending sequence. Slave transactions must advance by exactly one event, apply exactly its paid duration, and increase the count once. Timer checkpoint transitions may only **reduce** the existing journal balance and cannot forge credit.
- Storage is separate from the existing 512-byte EEPROM state: `/bicj-master-a`, `/bicj-master-b`, `/bicj-slave-a`, `/bicj-slave-b`, with temporary files isolated by role. There is no destructive migration of legacy saved time or sales.
- `/api/status` exposes **journal health** but not pairing secrets. In Settings an administrator can initialize a **previously empty** role-specific journal on the device's own WPA2 AP, with confirmed zero paid time, valid pairing and nondefault AP/admin credentials. It never resets an existing, degraded or corrupted journal.

## Recovery policy

| Observed slots | Behavior |
| --- | --- |
| Both absent | `NOT_INITIALIZED`; explicit admin setup required |
| Valid A only, or valid B only | `READY` |
| Two valid records with increasing generation | `READY`; recover latest |
| One valid, one corrupt or torn | `DEGRADED_LOCKED`; require reconciliation |
| Both corrupt or conflicting same-generation records | `CORRUPT_LOCKED` |
| Read or filesystem error | `IO_ERROR_LOCKED` |
| Write returned error after data may have committed | `UNCERTAIN_LOCKED`; do not ACK or grant again |
| Role-kind mismatch | `WRONG_ROLE_LOCKED` |

**Exactly-once must be qualified**: this scheme can provide duplicate-safe ledger transitions and retry reconciliation only if the event and balance are saved in the *same* authoritative record and every payment acknowledgement follows a verified durable commit. The existing V1.5 timer's EEPROM and the new LittleFS record are not a single transaction. No claim of exactly-once live financial behavior is made yet.

## Automated verification

`Hardware/tests/intercon_durable_journal_test.cpp` runs using portable host GCC with deliberate fault injection:
- Initial provisioning, A/B alternating writes, highest generation on reboot.
- Replaying the same credited event after ACK loss returns duplicate, without extending the time twice.
- A completed write followed by an I/O error locks runtime; after reboot the new generation wins, and retransmission does not credit again.
- A torn inactive slot creates a locked degraded journal rather than false success.
- CRC damage, two corrupt slots, wrong role and unreadable filesystem are denied.
- Master pending event survives reboot and prevents accepting a second unacknowledged physical coin event.
- Direct unbilled balance increases, issuer mutation, invalid event changes and illegal settlement are rejected.

The CI workflow runs these tests alongside Stage 2 HMAC known-answer tests, static contract checks, and **real Arduino CLI compilation** with `esp8266:esp8266:nodemcuv2`, core 3.1.2, TM1637 library.

## Required before **paid** Master-to-Slave operation

1. Integrate the ledger as the **single authoritative time + event + sales checkpoint**. The current V1.5 EEPROM countdown and separate LittleFS journal would otherwise disagree after power loss; never simply call `addCoinTime()` after persisting the journal and hope both commits survive.
2. Create a Master coin intake window bound to **one selected paired Slave**. Persist physical pulse + recipient + monotonic sequence BEFORE transmission; keep CS disabled if the journal is full, uncertain, or network ACK is unresolved. Budget ESP8266 flash endurance and consider a power-loss hold-up circuit if coin pulses must be preserved across sudden supply loss.
3. Implement versioned signed `CRED`, `ACKN`, and `STATUS` operations with duplicate-safe delivery. Bind each event to explicit recipient and paired key epoch, not only source chip ID; no replay after key rotation or stale/foreign pairing.
4. Reconcile manual time grants, paused-after-reboot semantics, local countdown checkpoints, sales counters and power-button pulse state into the same storage lifecycle; add migrations for existing paid sessions.
5. Physically test two or more NodeMCU boards under RF loss, deliberate simultaneous supply cuts at every flash-write boundary, coin pulse bounce, full flash, corrupted storage, relay glitches and exact electrical CS polarity. A host test or successful compile does not establish these hardware properties.
6. Independently review the HTTP Basic admin/STA security boundary and pairing onboarding before deployment.

**NO-GO until all of the above are validated.** The new admin initialization button only prepares a **zero-credit** ledger. It does not enable a Master or Slave to accept coins.

## Testing on an isolated pair of devices

With the coin acceptors and motherboard PWR_SW contacts disconnected, flash *only* a lab board after confirming its exact ESP8266 board compatibility. Join each AP, change both default AP/admin credentials, configure and verify STA, pair the two boards, choose Master and Slave roles, and use the journal initialization button on each with zero paid time. The dashboard must show `READY`; a filesystem failure must show a locked status. Sending a remote `CRED` must leave time, sales, both relays and physical CS unchanged. Record every boot serial log and use a separate test supply for power-interruption testing.
