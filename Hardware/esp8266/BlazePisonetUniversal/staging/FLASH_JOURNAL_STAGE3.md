# BLAZE INTERCON Stage 3 — Dual-slot power-loss journal

**2026-11-18 · Development / QA gate: NO-GO for live paid Master-to-Slave sessions**

This milestone advances [Stage 2 authenticated PING/PONG](AUTHENTICATED_PEER_STAGE2.md) with real portable snapshot serialization and a LittleFS persistence adapter, while continuing to preserve existing standalone V1.5 behavior. It does **not** yet route coin pulses or write a remotely credited rental balance to the old timer's EEPROM record.

## Existing code and new paths

- `BlazePisonetIntercon/InterconJournalCodec.h`: 92-byte fixed little-endian journal record; version, generation, Master pending credit sequence, Slave last accepted sequence, paid credit balance and accepted event count in **one atomic snapshot**; 128-bit HMAC-derived pairing fingerprint; CRC32 corruption detection; dual-slot fail-closed recovery rules. No Arduino dependencies.
- `BlazePisonetIntercon/InterconFlashJournal.h`: two independently retained LittleFS files `/intercon-j0` and `/intercon-j1`; temporary `/intercon-jtmp`, flushed and read back before metadata rename. No live coin-processing function calls the journal commit API yet.
- `BlazePisonetIntercon.ino`: boot performs **read-only** recovery; admin dashboard shows journal status and generation. Manual, explicitly confirmed initialization on this board's own AP creates **two identical generation-1 records** only if both slots were absent, the node was paired, its role was Master/Slave, and the local session was idle with zero remaining time.
- `Hardware/tests/intercon_journal_fault_test.cpp`: portable tests for crash boundaries (before rename, after rename/before ACK), duplicate events, bad issuer, out-of-order attempts, wrong key/role, missing/corrupt slot, incompatible generations and same-generation conflicts.
- Dedicated GitHub Actions workflow runs HMAC codec, ledger rules, journal fault simulation, real ESP8266 Arduino compile and the established static contract checks.

## Crash and ACK contract

1. **Initialize** only a completely empty, paired lab station through its AP. Neither existing paid balances nor damaged/unreadable journals may be reset by this endpoint.
2. A future **Master** must first atomically commit its target-bound pending coin event before sending that event. One pending coin event at a time avoids ambiguous in-flight target changes.
3. A future **Slave** must authenticate the frame, check event sequence and issuer, and commit its new paid credit *together with* the accepted sequence and count in one durable record. Only after successful verified commit may it send `ACKN`.
4. If ACK is lost, retransmit the identical event. The Slave must answer **duplicate** without granting credit again.
5. If the write fails, the controller must **fail-stop** and reconcile storage state rather than retrying with possibly stale RAM. A power cut after rename may leave the new snapshot durable even if the caller never received success.
6. At reboot, both journal slots must be present, valid, have the same peer/key/role binding, and differ by at most one generation. The highest generation is the state of record. Identical generation-1 slots are valid for initialization; same-generation conflicting files are invalid.
7. Any partially created file, corrupted CRC, missing slot, unexpected generation gap, wrong role or changed pairing key yields `degraded`/`binding-mismatch`, **not** automatic reset. Operator reconciliation is required before paid operation.
8. Do **not** move real credits into the preexisting 5-minute-checkpointed timer until the local countdown state, power-loss restoration, manual adjustments and remote receipts share one authoritative durable balance. The old 512-byte EEPROM record and these new LittleFS journal slots cannot be independently committed as one crash-atomic transaction.

## Native artifact on-flash format

Each little-endian image occupies 92 bytes and is encoded field-by-field, not via compiler-dependent C++ struct packing:

| Offset | Bytes | Field |
|---|---:|---|
| 0 | 4 | Magic `BLZJ` |
| 4 | 2 | Schema version = 1 |
| 6 | 2 | Reserved flags = 0 |
| 8 | 8 | Monotonic journal generation |
| 16 | 4 | Owner chip ID |
| 20 | 4 | Paired chip ID |
| 24 | 16 | 128-bit HMAC-derived key fingerprint |
| 40 | 4 | Role (1 Master / 2 Slave) |
| 44 | 8 | Master last issued sequence |
| 52 | 8 | Master currently pending sequence, or zero |
| 60 | 4 | Master pending seconds, or zero |
| 64 | 8 | Slave last accepted sequence |
| 72 | 8 | Slave credited balance units (100,000 units per second) |
| 80 | 4 | Slave accepted event count |
| 84 | 4 | Slave last accepted grant seconds |
| 88 | 4 | CRC-32 over bytes 0–87 |

The fingerprint is **not** a security token; real peer authentication uses full HMAC-SHA256 over wire frames, while CRC32 detects corrupted storage.

## Lab-only initial bring-up

1. Start from the staged V1.7 code and physical hardware with the coin acceptor's payment output and motherboard `PWR_SW` disconnected. Configure separate, non-default AP and admin credentials.
2. Select Master or Slave and configure STA, then restart. Pair the two devices using Stage 2's manual AP-only key enrollment and signed challenge/response.
3. With timer inactive and remaining paid time **zero**, open the board's own AP dashboard, then click **Initialize empty journal (lab only)**. Do not use a board with existing unreconciled paid records.
4. Confirm both slots exist and the status is `healthy`, generation 1. Restart and verify the status remains healthy. Repeat with one slot deliberately damaged **on a non-revenue test board only**: status must become degraded and no reinitialization should succeed.
5. Test interrupted LittleFS writes, brownouts, empty flash, and storage-full conditions on **actual ESP8266 hardware** before enabling paid events. These conditions are simulated in native tests but are **not** proven electrically.

## Blockers before production

- **No remote credit invocation:** existing firmware intentionally ignores signed `CRED` / `ACKN` packets and holds Master/Slave coin acceptance OFF. This Stage 3 change does not make a live remote timer.
- **No unified timer ledger:** Stage 3 flash records are separate from the original local countdown and manual time/EEPROM state. Reliable paid credit needs one authoritative durable balance, not two independently persisted copies.
- **No physical power-fault validation:** host fault injection is representative of pre-/post-rename boundaries, but not verification of real LittleFS metadata, ESP brownout behavior, flash wear, coin pulse electrical timing or whole-device power sequencing.
- **Journal recovery is conservative:** if either valid file is lost, it requires human reconciliation. This favors refusing to take money over automatically guessing whether credit was accepted.
- **Admin portal over HTTP:** AP uses WPA2 but HTTP Basic credentials and pairing-key provisioning are not TLS-encrypted. Use a trusted management network; never expose TCP 80 or UDP 4210 directly to the internet.
- **Pinmap visualization remains held:** D0 cutoff, D6 momentary PWR_SW, D7 CS, D1/D2 display defaults are preserved and settings stay editable according to existing validation, but the visual NodeMCU pinout overlay is not part of Stage 3.

**Release gate: draft source and CI only. Do not flash a paid installation or treat any simulation as a real collected coin.**
