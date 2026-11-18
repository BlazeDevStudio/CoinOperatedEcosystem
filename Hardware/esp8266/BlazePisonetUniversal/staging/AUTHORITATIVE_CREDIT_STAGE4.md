# BLAZE PISONET INTERCON — Stage 4: Journal-authoritative wireless crediting

**Engineering status (2026-11-18): source implementation + automated integration tests; real-hardware paid-operation gate = NO-GO.**

This stage changes the previous development line from signed PING/PONG and non-operative credit models to a **one-Master / one-paired-Slave**, signed CRED/ACKN path with durable transaction ordering. Standard mode remains a local standalone Pisonet timer. The existing V1.5 hardware mapping and local remaining-time logic are preserved, rather than overwriting the sketch with the older Universal implementation.

## What is now connected

1. **Master** requires a successfully paired peer, recent signed PONG, STA connectivity, healthy dual-slot journal and no outstanding event before enabling **D7 / GPIO13** coin acceptor enable (through its external driver). Its D3/GPIO0 coin pulse input is debounced and grouped into a bounded electrical pulse burst (650 ms quiet interval, up to 20 pulses, grant <=65,535 seconds).
2. Master immediately disables coin acceptance, durably commits **one pending event ID and summed paid seconds**, then transmits authenticated `CRED` to the previously paired Slave's STA IP. No journal commit = no transmitted credit.
3. Master retains an unsettled event over restart, disconnects, lost ACK and retry. It retransmits only the **same** durable signed event ID. Another coin event cannot be accepted until a valid authenticated ACK is itself durably settled in the Master journal.
4. **Slave** rejects physical coin input. A signed `CRED` is only actionable from the selected authenticated Master while the Slave journal is healthy. Slave settles its elapsed timer in RAM, validates monotonic event order and permissible 7-day balance, then atomically commits **new paid-time balance + accepted sequence + paid-event count** in one dual-slot journal image. Only after that commit does the live timer and PWR_SW logic change and `ACKN` get sent. Duplicates receive an ACK with no additional time.
5. Slave journal is the **authoritative paid balance**. At reboot the Slave ignores the old EEPROM remaining-time copy, restores the latest valid journal balance, and **keeps the countdown paused** until the next new paid credit or an authorized manual start. It does not automatically press the physical PC power switch on ESP reboot.
6. **Slave timer checkpoints, admin add/set time, reset and expiry** update that same journal. Manual grants do not increment paid-coin receipts. The legacy EEPROM remains only a redundant configuration/UI shadow in Slave mode.
7. Failed writes, missing/corrupt/re-keyed journal slots, unknown pending events and burst overflow keep the coin gate closed. CS disable remains manually accessible to administrators, including while paid time exists.
8. The firmware disables **LittleFS auto-format before mount**. A failed mount must never erase financial history. All regular administrator requests remain authenticated; pairing/journal initialization are AP-only.

## The signed transaction sequence

```text
Master CS enabled (only when paired + online + journal healthy + no pending)
   |
   +--- D3 coin pulses -> bounded coin burst (physical acceptor)
   |
   +--- DISABLE D7 CS
   |
   +--- COMMIT Master event {ID N, seconds}; verify flash readback
   |
   +--- SEND HMAC-SHA256 CRED(N, seconds), retry N only until receipt
                                   |
                                   v
                    Slave verifies source, MAC, binding, role
                                   |
                                   v
                    COMMIT {lastAccepted=N, paidBalance+=seconds,
                            paidEventCount+1} in one journal image
                                   |
                                   v
                    Update live countdown + optional PWR_SW request
                                   |
                                   v
                           SEND signed ACKN(N)
                                   |
                                   v
                    Master COMMIT pending cleared, then D7 can reopen
```

A retransmitted `CRED(N)` whose sequence and seconds are already recorded does **not** add time again. The Slave re-ACKs instead. An ACK lost after a successful slave commit is therefore not lost money or doubled credit.

## Safety and persistence semantics

- **Exactly-once logged grant, conditional on successful Master journaling:** once an event is durable at Master, a lost UDP packet or ACK can be retried. Once a Slave event is durably committed, that exact sequence cannot grant again after a reboot. Host tests simulate these boundaries.
- **Power loss before first journal commit remains unresolved:** neither software nor a 650 ms pulse burst collector can know that a physical coin fell into the acceptor moments before the ESP lost power. A properly designed acceptance-inhibit circuit, supply hold-up, or other hardware proof is essential for production operation. An operator alert does not itself reimburse a customer.
- **Power-loss timer accuracy:** Slave balance is checkpointed every **60 seconds** during countdown. A sudden power cut may restore up to approximately 60 seconds of previously spent session time. Credit grants, admin changes and expiry are journaled immediately. A reliable RTC/UPS or a more durable timebase is required for strict offline wall-clock accuracy.
- **Flash endurance:** minute-level journal commits, frequent coins and manual admin operations create flash write load. Hardware soak and wear characterization are mandatory. Failed writes should stop credit acceptance, not erase records.
- **One peer only:** this build supports exactly one paired Master/Slave relationship. Discovery can see other devices, but it is not a secure multi-target switchboard or BlazePwifi router payment adapter.
- **No silent journal reset:** an existing corrupt/mismatched journal requires a deliberate reconciliation process; the dashboard cannot delete it or re-pair across it.
- **Physical PC state is estimated:** D6 / GPIO12 momentarily connects the motherboard PWR_SW relay and does not measure the PC. Sudden non-ESP resets may make that assumption wrong; no hardware sensor was added.
- **Network admin is still HTTP:** WPA2 LAN access and HTTP Basic alone do not justify public WAN exposure. Never port-forward the admin interface or the peer UDP credit port.

## Defaults retained

| Function | NodeMCU label | GPIO |
| --- | --- | --- |
| Relay 1 — cutoff | D0 | 16 |
| Relay 2 — PWR_SW pulse | D6 | 12 |
| CS enable output via external driver | D7 | 13 |
| TM1637 CLK (SCL-labelled pin) | D1 | 5 |
| TM1637 DIO (SDA-labelled pin) | D2 | 4 |
| Buzzer | D5 | 14 |
| Coin pulse input (boot sensitive) | D3 | 0 |

Default labels have not replaced the existing configurable GPIO settings. The previously requested visual pinout overlay is still intentionally deferred.

## Verification and runbook

Automated tests:
- `Hardware/tests/intercon_secure_wire_test.cpp` — real HMAC test vector, malicious packets, identities and bounds.
- `Hardware/tests/intercon_credit_ledger_test.cpp` — monotonic event and commit callback invariants.
- `Hardware/tests/intercon_journal_fault_test.cpp` — corrupt/partial flash, pre-/post-rename faults, duplicates and crash recovery.
- `Hardware/tests/intercon_stage4_end_to_end_test.cpp` — signed Master CRED, same-image Slave receipt+time commit, ACK loss, restart, journal checkpoints, manual time grant, expiry and corrupted slot lockdown.
- `Hardware/tests/test_intercon_stage1_contract.py` — actual source integration invariants including Master gate, Slave authority, manual-time durability, no-autoformat and relay pin defaults.
- `.github/workflows/intercon-stage1-ci.yml` — actual Arduino CLI ESP8266 core 3.1.2 / NodeMCU V2 compilation plus native tests.

Physical verification is **not** represented by those tests. Before field use on the actual custom PCB, perform:
1. Confirm coin acceptor external CS driver polarity, boot-state inhibition and pulse width/gap across all accepted coin denominations (not all acceptors send one pulse per coin).
2. Load two devices on the same Wi-Fi router and verify AP+STA concurrent access, pairing, signed status, reconnect, client isolation behavior and transaction resend.
3. Physically interrupt power at each coin edge and journal-rename boundary; inspect whether any accepted physical coin loses credit and build hardware hold-up/disable measures as required.
4. Inject storage-full, corrupted/rolled-back records, repeated packet, lost ACK, router failure, replayed PONG and power loss while a Slave countdown or manual grant is active.
5. Verify relay polarity, D6 momentary PWR_SW behavior, shutdown grace, no unexpected pulses at power-up, and whether Relay 1 really switches mains.
6. Perform long-running flash wear and heap/stack/watchdog tests on the exact NodeMCU flash layout; external BlazePwifi accounting integration requires its own signed adapter and reconciliation.

## Release decision

**The software integration milestone is implemented and reviewable, but it must remain a draft / NO-GO build for unattended paid coin operation until those physical tests pass.** It would be misleading to call it production-safe based only on simulator and CI results.
