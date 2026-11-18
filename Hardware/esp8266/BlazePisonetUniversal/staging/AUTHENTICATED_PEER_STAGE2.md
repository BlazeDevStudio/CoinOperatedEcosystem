# BLAZE INTERCON — Stage 2 Authenticated Peer Link (V1.7 engineering)

**Status:** DRAFT / NO-GO for live Master-to-Slave coin credit. This stage proves that manually enrolled ESP8266s can authenticate each other and that future credit events have an independently tested fail-closed transaction model. It does **not** enable remote sales, relay or power actions.

## Baseline and preservation

- Stacked on CoinOperatedEcosystem draft [PR #36](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/36), itself derived from the maintained integration PR #26. A different INTERCON V1.6 discovery branch is being maintained in parallel; no files on that branch were replaced.
- Uses the **actual V1.5 standalone timer** as the staging sketch; preserves D0/GPIO16 cutoff, D6/GPIO12 momentary PWR_SW, D7/GPIO13 coin-slot-enable, D1/GPIO5 CLK, D2/GPIO4 DIO, D5/GPIO14 buzzer, and D3/GPIO0 coin input.
- Existing paid-time and sales EEPROM records, standby countdown, AP+STA, and admin workflow are not replaced. The older Universal source remains in `legacy/` for provenance.

## New implementation

1. **Bounded HMAC-SHA256 packet codec**: `InterconSecureWire.h`. Uses the installed ESP8266 Arduino core's BearSSL implementation and OpenSSL in native tests; no homegrown hashing. Fixed, upper-case, exact 8-hex-digit chip identifiers and 32-bit event parts; exact HMAC over the canonical prefix; constant-work tag comparison; strict length/numeric/parser validation.
2. **Explicit pairing**: `InterconPeerAuth.h` persists one chosen peer's 8-hex chip ID, STA IPv4 address and shared 256-bit secret in its own checksummed LittleFS file. Saving is denied during a paid session. Pairing cannot be provisioned while the known default AP or admin password remains in use.
3. **Admin workflow**: On each ESP's **own local WPA2 AP**, open the Settings pairing section. The device shows its chip ID. Set the peer's chip ID, router STA IP and the same 64-hex-digit shared key on both boards. A controller can generate the fresh key locally through an admin-protected AP-only endpoint. The persisted key is never returned in status JSON.
4. **Network proof-of-possession**: Each configured Master or Slave periodically sends a fresh signed PING. The paired peer returns a signed PONG carrying exactly that challenge. The requester shows **Authenticated** only after receiving a matching, timely response from the configured peer address, with the expected peer chip ID and valid MAC. Replayed PONGs from old challenges do not establish a new connection. Standard role performs no authenticated peer traffic.
5. **Closed financial path**: Signed `CRED` / `ACKN` messages may be recognized by the standalone parser but the running firmware **ignores them**. Neither Master nor Slave can accept local coins in Stage 2. `writeCsEnable()` is gated by `interconLocalCoinsAllowed()`, and the coin ISR path cannot add paid time for those roles.
6. **Future credit durability contract**: `InterconCreditLedger.h` models one outstanding Master event, persisted monotonic sequences, fail-closed receiver acceptance, duplicate ACK handling, target/issuer checks, max balance and crash-safe commit ordering. This is **portable test code only**, not a claim that ESP8266 LittleFS/EEPROM currently implement the necessary atomic commit.

### Wire v2 envelope

```text
BLZ2|PING|SSSSSSSS|TTTTTTTT|HHHHHHHH|LLLLLLLL|0|HMAC_SHA256_HEX64
BLZ2|PONG|SSSSSSSS|TTTTTTTT|HHHHHHHH|LLLLLLLL|0|HMAC_SHA256_HEX64
```

The 64-character MAC is HMAC-SHA256 of the bytes up to and including the delimiter directly before the MAC. `SSSSSSSS` and `TTTTTTTT` are 8-character uppercase hexadecimal chip IDs; `HHHHHHHH` / `LLLLLLLL` identify the challenge or future persistent event sequence. For Stage 2 only PING/PONG are actionable.

**Known test vector:** key = bytes `00 01 ... 1F`, prefix = `BLZ2|PING|AABBCCDD|11223344|01234567|89ABCDEF|0|`; expected HMAC = `C05C7E4E2A7597346B8F75BEFBE05B0BA22351E5CC84247FDC72163507F915BD`.

## Pairing two disconnected lab boards

1. With **coin acceptor output disconnected** and PC relay loads isolated, configure two controllers with different roles (Master, Slave), two unique AP/admin passwords and STA credentials on a trusted non-client-isolated Wi-Fi LAN. Both must see their own STA LAN IP and each other in discovery.
2. Connect directly to Board A's local AP. In Settings, generate a pairing key and copy it safely. Enter Board B's chip ID and router STA IP. Save. Verify that key is not echoed in normal status.
3. Connect directly to Board B's local AP. Enter Board A's chip ID and STA IP, and paste **the same key**. Save.
4. After STA connects on both boards, within a few heartbeat cycles each should show its configured peer as **Authenticated**. Change one key or peer ID: authentication must fail. Drop Wi-Fi, restart either board, or replay an old signed PONG: authentication must not become current without a fresh challenge.
5. Confirm that sending a packet whose type is `CRED` does **not** change rental time, sales, Relay 1, Relay 2 or CS. Neither Master nor Slave should physically enable the coin slot.

## Validation

- `Hardware/tests/intercon_secure_wire_test.cpp`: build with `g++ -std=c++17 -O2 -Wall -Wextra -Werror ... -lcrypto`. Known HMAC vector, peer identity mismatch, tampered signature, malformed/truncated packets and signed credit envelope parsed but not applied.
- `Hardware/tests/intercon_credit_ledger_test.cpp`: portable simulated sender/receiver persistence with lost ACK, resend, duplicate credit, reboot, out-of-order, bad issuer, failed commit and overflow.
- `.github/workflows/intercon-stage1-ci.yml`: native host tests **and** actual ESP8266 NodeMCU compile using Arduino core 3.1.2 and TM1637.
- Existing Hardware/Shared CI and case-collision checks are unchanged; no published signed binaries or physical acceptance results are claimed.

## Hard blockers for real paid events

- A durable Master pending-event journal must persist each accepted physical coin pulse before trying to send it; a sudden power cut between a coin edge and journal commit **cannot be made lossless by software alone** without appropriate hardware/power-loss design.
- A Slave's accepted event sequence, remaining time and counters must become atomically durable in the **same** record/transaction before ACK. Writing an event marker to LittleFS and separately calling `EEPROM.commit()` is **not atomic** and can lose or duplicate credits.
- Replayed/old/out-of-order events must not be accepted after a power cut, backup restore, role change or peer re-pairing. Balance snapshots must be reconciled with countdown checkpoints and manual admin adjustments before restoring credits.
- Pairing uses admin HTTP over WPA2 and stores a secret in flash; this is **not** secure against physical flash extraction or a hostile LAN with captured administrator traffic. External internet exposure is prohibited. A dedicated management VLAN and stronger provisioning are needed for production.
- Multi-node actual coin/relay tests, negative network tests, power-cut injection, and security review are still required.

**Release decision: NO-GO** for paid multi-unit operation, even when the Arduino build and host tests are green.
