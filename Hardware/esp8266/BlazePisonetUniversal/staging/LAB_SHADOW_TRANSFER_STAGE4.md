# BLAZE INTERCON — Stage 4 journal-only Master→Slave exchange

**Date:** 2026-11-18  
**Release status:** DRAFT / NO-GO for production paid credits.

This branch builds on the existing **Stage 3** two-slot, CRC-checked LittleFS journal, itself stacked on the Stage 2 HMAC pairing and Stage 1 AP+STA discovery. It does **not** replace the independently maintained Universal source or router-linked `BlazePwifiVendo`.

## What actually works in source

- Each device retains AP+STA, its own admin portal, paired-HMAC PING/PONG, Standalone/Standard role and configured safe GPIO mappings.
- Master and Slave roles keep the *physical coin slot disabled*, including D7 CS enable and the software coin ISR gate.
- An authenticated administrator connected to the **Master's own WPA2 AP** can use **Settings → Master-to-Slave journal transfer test** to stage 1–3600 **shadow seconds**. The Master must be paired, authenticated, have a healthy initialized journal, and have no active/saved local paid time or pending PC pulse.
- Master stages **one** event at a time via the existing `blaze_credit::stage()` and `blaze_journal::commitMasterPending()` callback. A failed or uncertain durable write means **no transmission or success response**. Its signed `CRED` message carries the persisted 64-bit event sequence and seconds. Retry uses **exactly the same** event identity every ~3 seconds while the paired peer is authenticated.
- Slave verifies signed peer identity, target, sender IP, paired session, role, healthy correct-issuer journal, counter bounds, and no live paid session. The `blaze_credit::apply()` path commits sequence + shadow balance + test-event count as **one** versioned journal snapshot; **only after commit/readback** may it send signed `ACKN`. Exact duplicate event is ACKed again without changing the balance. Missing/torn/uncertain storage never earns an ACK.
- Master accepts a signed ACK only for its **current outstanding sequence** and commits the cleared pending state. Lost ACK → Master retries old event; restarted Slave sees persisted sequence and returns duplicate ACK.
- Both journals recover independently after ESP reset. This is **actual firmware-to-firmware authenticated, acknowledged, durable shadow transfer logic**, not a browser mock.

## Explicitly NOT implemented

1. **No real paid credit application**: remote CRED does not change `remainingSeconds`, `remainingMs100`, `salesOverall`, the display, Relays 1/2, or the PC state. Slave journal `remainingUnits` is a *shadow balance* shown only in status/dashboard.
2. **No money collection by the Master**: CS D7 remains OFF for Master and Slave. No coins accepted, even if a journal is healthy.
3. **No cross-file atomic timer migration**: the legacy EEPROM saved-time record is separate; integrating the live timer requires a *single authoritative record* for sequence + remaining time + any locally earned/manual time updates and recovery checkpoints. A second write to EEPROM after journaling is not atomic.
4. **No production-grade proof of power-loss integrity** on real ESP8266 flash chips; the current LittleFS two-slot backend has a power-cut-recovery design but must undergo physical repeated fault injection.
5. **No multi-slave switching, credit transfer between customers, OpenWrt accounting integration, cash value conversion, or internet-exposed remote control.**

## Laboratory two-board procedure

**Disconnect coin acceptors and isolate motherboard PWR_SW/mains relay loads first.**

1. Flash the same Stage 4 sketch to two correctly identified NodeMCU boards (compiled with ESP8266 Arduino Core 3.1.2 and TM1637). Provision different AP/admin passwords and STA credentials; choose **Master** on A and **Slave** on B.
2. Pair via their respective AP administration pages using a random 32-byte shared key, both peer chip IDs and STA IPs. Confirm signed authenticated PING/PONG in the status cards.
3. With both legacy paid balances at zero, initialize each role's **empty journal** using Settings. Initialization is intentionally irreversible in ordinary UI; it cannot be used to erase, re-pair or repair existing event history.
4. On the Master AP, send e.g. **60 shadow seconds**. Verify Master shows `PENDING ACK` while delivery is outstanding, then clears it. Slave status should show `slaveLabSequence=1` and `slaveLabShadowSeconds=60`. Its actual paid time and sales must remain unchanged.
5. Repeat with 30 seconds. The Slave shadow sum becomes 90 seconds; live paid time remains zero. Use network isolation to drop ACK, power off the Slave after it commits, then reconnect. Master retransmits the same event and the Slave must ACK it as a duplicate with no second grant.
6. Test wrong key, wrong chip ID, malformed UDP CRED, missing STA Wi-Fi, failure to persist the alternate flash slot, role change and re-pairing attempts, and manual paid time/relay actions. All financial/unsafe paths must fail closed.
7. Preserve serial logs and exported journal slot images for a real fault-injection audit. Host tests cannot substitute for these physical tests.

## Automated checks

- `Hardware/tests/intercon_lab_transfer_test.cpp`: real OpenSSL HMAC wire frames + portable A/B journal backend simulation for lost ACK, retransmission, reboot, wrong source/target/key, corruption, torn write, unavailable storage, monotonic sequence and acknowledgement.
- Previously existing Stage 1 static coin-gate checks, Stage 2 signed-wire tests and Stage 3 journal corruption tests.
- Real `arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2` in GitHub Actions.
- The simulated journal `Flash` adapter is a **host fault-injection harness**. It is not a substitute for physical ESP8266 flash power-cut testing.

## File locations

- Runtime dispatch & dashboard: `BlazePisonetIntercon/BlazePisonetIntercon.ino`
- Authenticated transport: `BlazePisonetIntercon/InterconSecureWire.h`, `InterconPeerAuth.h`
- New staging logic: `BlazePisonetIntercon/InterconLabCredit.h`
- Durable storage: `BlazePisonetIntercon/InterconDurableJournal.h`, `InterconJournalFS.h`
- CI + host integration: `.github/workflows/intercon-stage1-ci.yml`, `Hardware/tests/intercon_lab_transfer_test.cpp`

**Safety verdict:** Suitable as a reviewed laboratory *candidate*, not for connecting to paying customers or critical PC power inputs until the hardware validation and actual paid-timer reconciliation are complete.
