# BLAZE PISONET INTERCON V1.6 — AP+STA / read-only peer discovery

**Engineering preview, NOT for flashing into a paid installation.** This is an incremental migration of the existing **V1.5** coin timer. It is **not** the older Blaze Pisonet Universal runtime and it is **not** the router-linked BlazePwifiVendo firmware.

## Implemented here

- Preserves the V1.5 timekeeper, coin interrupt handling, paid balance and sales EEPROM record, TM1637 animations, buzzer, manual time controls, CS D7/GPIO13, Relay 1 D0/GPIO16, and isolated momentary Relay 2 D6/GPIO12 for PWR_SW.
- Wi-Fi startup uses `WIFI_AP_STA`: the original local AP remains available, and the configured STA joins an existing local Wi-Fi router asynchronously. The web page is served on both IPs (subject to local network topology and firewall/client isolation).
- Portal Settings now include Standard / Master / Slave role, station name and numeric ID, STA SSID/password and STA enable checkbox.
- Roles and STA credentials are saved in a separately checksummed LittleFS file (`/intercon.cfg`, rollback `/intercon.bak`) without changing legacy EEPROM layouts.
- Passive UDP local-LAN discovery: version-1 `BLAZE1|HELLO|chip|node|role|name` announcements on port 4210, with a bounded 12-peer table and 30-second expiry. The administrator can see detected peers, their role and STA IP.
- **No financial commands are accepted over UDP.** This version ignores `CREDIT`, `GRANT`, `REQ` and any unrecognized packet. Discovery peers are **untrusted**, not paired.
- The original **Standard** role runs a normal local coin timer. **Master** and **Slave** are configuration/discovery *preview* roles; their coin-slot hardware-enable is intentionally **OFF** until signed, journaled credit delivery exists. The dashboard explains this lock and refuses CS enable in those modes.
- If LittleFS config is missing, a fresh install uses Standard. If an existing config is corrupted or LittleFS mounting fails, coin input is disabled rather than silently switching a previously configured Master or Slave into Standalone.

## Not yet implemented

- Secure pairing, stable coin event identifiers, HMAC signatures, durable source+destination pending-event logs, duplicate-safe ACK/replay handling, and automatic Master-to-Slave paid credit.
- Master selection of a slave or managed insertion windows.
- OpenWrt BlazePwifi accounting adapter.
- Signed, authenticated remote power / CS actions.
- Configurable visual board pinout (separately held by owner for later GPIO milestone).
- Public WAN access. **STA IP is a router-assigned local/LAN IP**, not a public internet-facing interface.

## Build

Copy `BLAZE_PISONET_INTERCON_V1_6.ino` and `InterconPeerParser.h` into the same Arduino sketch directory named `BLAZE_PISONET_INTERCON_V1_6`. ESP8266 Arduino Core and the **TM1637Display** library are required. Set board to `NodeMCU 1.0 (ESP-12E Module)` or the exact matching ESP8266 hardware. Don't flash a live paid installation without lab compile/hardware testing and rollback.

## Safe lab acceptance steps

1. With the coin acceptor and both relay loads disconnected, boot Standard mode and confirm original AP portal at its local IP.
2. Enter separate STA SSID/WPA password, enable STA, save and use **Restart (idle only)**. Check both the AP IP and router-assigned STA IP access the login page.
3. Configure two boards with unique IDs and names on the **same non-isolated LAN**. Check each discovers the other within 30 seconds and entries expire when one is disconnected.
4. Check physical coin CS is off in Master and Slave preview modes even when the stored dashboard CS preference is ON. Confirm no remote credit can alter a timer.
5. Return to Standard; revalidate original coin/timer/relay behavior only on a safely isolated test rig. Do not attach the PWR_SW relay until polarity and momentary pulse behavior have been physically verified.
6. Test STA loss and reconnect while AP remains reachable and existing paid countdown keeps running.

## Engineering caveats

- AP and STA on ESP8266 share one radio and channel: the AP can change channel when the station joins a router. Client discovery generally will not work across client-isolated SSIDs, separate LANs, or routers filtering broadcast; manual IP/pairing fallback is planned.
- The peer-list discovery payload has **no authentication**. It is status telemetry only, not evidence of ownership and never authorizes a paid or hardware action.
- Existing HTTP Basic admin credentials are not transport-encrypted; keep the STA network on a trusted management VLAN. Don't forward TCP 80 or UDP 4210 to the internet.
- Five-minute balance checkpointing, no physical PC state sense, and the original V1.5 hardware risks remain. This version doesn't change those limits.
- Neither an Arduino ESP8266 toolchain compile nor an actual hardware flash is attested by host-only checks unless GitHub CI confirms it separately.