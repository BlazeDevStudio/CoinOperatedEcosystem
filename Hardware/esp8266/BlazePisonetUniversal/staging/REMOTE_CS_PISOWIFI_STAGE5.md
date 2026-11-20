# Stage 5 — fourth operating mode: Remote CS for PisoWiFi (DRAFT / NO-GO)

Source reference: [JuanFi](https://github.com/ivanalayan15/JuanFi) (Apache 2.0; consulted for architecture, NOT copied code/protocol). JuanFi implements a voucher-scoped `/topUp` → coin window → `/checkCoin` → `/useVoucher` process with MikroTik API ownership. This firmware intentionally defines a **new**, HMAC-authenticated `BLZCS1` adapter. It is **not compatible with the JuanFi HTTP endpoints**.

## User-visible roles

0. **Standard** — local coin + timer, original V1.5 settings.
1. **Master** — signed, durable ESP-to-ESP credit source.
2. **Slave** — signed, durable ESP-to-ESP paid countdown.
3. **Remote CS (PisoWiFi)** — coin-slot enable/pulse controller; **does not credit local rental time**, issue MikroTik vouchers, or decide PESO-to-minute rates. Router backend owns customer sessions, denominations, credit and internet access.

The five original configurable GPIO assignments, D0 cutoff, D6 PWR_SW, D7 CS-enable fixed, D5 buzzer fixed, TM1637 test, animations, manual time settings (disabled when role is Master/Remote), admin portal and local AP remain in the code. The old 512-byte EEPROM layout is unmodified. All existing payment journals stay separate.

## Setup (unoccupied lab hardware only)

1. Back up the existing ESP configuration. Use a **fresh device with no prior paid journal** to select role 3, or reconcile prior histories offline. Never format LittleFS to bypass a role/rekey lock. Connect to the device's own WPA2 AP; change both default AP and admin credentials.
2. Set Remote CS in Settings, enable STA and configure the shop router. Save and restart; D7 remains closed. Disconnect the physical acceptor from paying customers.
3. In INTERCON pairing, use the PisoWiFi controller's **dedicated 8-uppercase-hex identifier** (not this ESP chip ID), static **LAN IPv4** and a fresh **32-byte secret** (64 hex chars). Provision the same secret into the trusted PisoWiFi adapter; never expose it to browser clients.
4. Disable CS. Click *Initialize new Remote CS journal* once, then verify the two-slot journal status is healthy. Inspect actual coin chute and prior receipts; with no pending event, select *Confirm physical coin reconciliation (this boot)*. Enable CS separately; it stays electrically OFF until a valid signed OPEN.
5. The PisoWiFi backend sends authenticated `OPEN` for a nonzero customer session and a **5–60 second coin lease**. D7 enables only while lease valid, STA connected, journal healthy and this boot physically reconciled.
6. Coin burst (650 ms quiet time) is **committed to a separate two-slot LittleFS journal**, binding the event ID, session ID, physical pulse count and controller identity before a `POLL` can return `EVNT`. D7 stays disabled with one event awaiting ACK.
7. Backend `POLL` retrieves `EVNT`; router **durably credits the correct customer once, keyed by (device ID,event ID)**, then sends matching `ACKN` with same session, event ID and pulse count. Only then can new OPEN accept the next coin.
8. `CLOS` closes D7 for the session; it will refuse a partial denomination until its pulse quiet window settles. `POLL` is read-only and idempotent.
9. After ESP reboot the customer coin window is always CLOSED even if previously active. An unsettled journaled receipt remains available through `POLL`; a new OPEN requires separate physical inspection/reconciliation.
10. Real coin/power-cut/CS-driver/relay electrical validation, Wi-Fi loss, coin denominations, LittleFS wear and controller credit reconciliation are all **release blockers**.

## Wire protocol (controller ↔ NodeMCU)

POST to `http://<esp-sta-ip>/api/pisowifi/control` with form field `frame`, from the **preconfigured controller LAN IP** only. This endpoint does **not** use browser Basic authentication, CORS or unsigned queries; all frames have **HMAC-SHA256** with the paired 32-byte key. Both controllers should be isolated on a trusted LAN/VLAN. The HMAC authenticates but **does not encrypt** traffic. Never expose it to WAN.

Canonical UTF-8 ASCII frame:

```
BLZCS1|KIND|SOURCE8|DEST8|COMMAND16|SESSION16|EVENT16|VALUE|HMAC64
```

- `SOURCE8`, `DEST8`: uppercase eight-digit hex controller/device identity.
- `COMMAND16`, `SESSION16`, `EVENT16`: sixteen-digit uppercase hex unsigned 64-bit fields.
- `VALUE`: unsigned decimal 0–65535, without leading zeroes except `0`.
- `HMAC64`: uppercase hex HMAC-SHA256 covering the complete prefix **including the last `|`**, using the paired key.
- Incoming `OPEN`: unique strictly increasing `COMMAND16`, nonzero `SESSION16`, `EVENT16=0`, `VALUE=5..60` seconds. Commit counter to journal **before** D7 opens.
- Incoming `CLOS`: higher command, currently active `SESSION16`, event/value zero. Close physical gate; queued pulses must finish before complete.
- Incoming `POLL`: session,event,value all zero. Read-only; can safely repeat with command zero. Response `EVNT` or `EMPT`.
- Incoming `ACKN`: higher command, exact pending session/event and exact pending physical **pulse count**. Clears pending only after a durable journal write. **A packet ACK is not a voucher credit; backend must commit payment first.**
- Every successful response is also signed with the same envelope: `OKAY`, `EVNT` or `EMPT`. `EVNT` contains pending session, event and number of physical pulses. The backend must never interpret it as seconds or pesos.
- Invalid keys/identities/IPs are rejected. Replayed mutating commands are rejected without opening D7. Pending events cannot be silently dropped or replaced.

Portable diagnostic client is under `Hardware/tools/remote_cs_client.py`; it **does not** implement a PisoWiFi billing backend, and requires explicit commands so no hotspot credit can be accidentally simulated.

## Recovery and safety

- The new `RemoteCsJournal.h` uses a separate two-slot, generationed, CRC-checked, identity/key-bound LittleFS journal (`/remote-cs0` and `/remote-cs1`), with temporary write/flush/readback/rename/readback.
- Corrupt/mismatched or incomplete journal causes **NO-GO** rather than autoformat or silently resetting previous paid history.
- An existing Main/Slave journal, or a Remote CS journal, locks role switching and re-pairing; there is no migration tool yet.
- The same Stage 4.1 every-boot arm marker requires AP-only physical reconciliation before any coin acceptance; it is not an actual hardware coin sensor.
- Physical coins taken between an electrical pulse and its first completed flash commit **may be lost**. This cannot be guaranteed away with software. Operator inspection and hardware hold-up/inhibit tests are required before production.
- The 650 ms burst timing is provisional for the user's acceptor; adjust only after actual pulse-width testing.
- The interface is not a replacement for MikroTik RouterOS API or a complete PisoWiFi captive portal. Implement backend idempotent crediting and compare the controller's durable credit receipts to the ESP pulse journal **before enabling payments**.

## Remaining before a paid release

1. Build/tests on the exact NodeMCU board and inspect D0/D6/D7 under brownout, restart and Wi-Fi disconnect.
2. Integrate the backend with the site's actual PisoWiFi accounting API; support per-session and denomination policy in the router, with durable event deduplication.
3. Execute real two-device paid-session tests and router reboot/crash tests; ensure no customer credit is lost or duplicated.
4. Validate flash endurance and incomplete coin bursts. Confirm physical CS driver does not fail enabled without ESP power.

**Stage 5 is source/CI/LAB only and must stay draft/unmerged until those tests pass.**
