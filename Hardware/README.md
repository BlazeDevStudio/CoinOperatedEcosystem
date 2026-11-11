# Blaze Hardware — Coin Vendo Microcontroller Firmwares

This directory contains the hardened microcontroller firmwares for the **Blaze Coin Operated Ecosystem**, designed to bridge physical coin acceptors and power relays to the router controller plane.

---

## 1. Supported Hardware Platforms

| Platform | Target Board | Sketch Path | Core Version | Build FQBN |
|---|---|---|---|---|
| **ESP32** | NodeMCU-32S / ESP32 DevKit | [`esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino) | `esp32:esp32@3.3.12` | `esp32:esp32:esp32` |
| **ESP8266** | NodeMCU v2 / ESP-12E | [`esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino) | `esp8266:esp8266@3.1.2` | `esp8266:esp8266:nodemcuv2` |

---

## 2. Hardening Invariants & Security Implementation

1. **HW-P0-1 — Mutual Response Signature Verification:**
   - Both sketches track `lastSentNonce` and cryptographically verify `response_sig` emitted by the router `/cgi-bin/vendo` for `register` and `poll` actions:
     `HMAC/SHA256(key | action | id | nonce | ... | key)`
   - Unauthenticated, forged, or replayed responses are dropped fail-closed.
2. **HW-P0-2 — Uncredited Coin Dispute Quarantine:**
   - Instead of discarding uncredited coin pulses on router rejection (`"coin window expired"`, `"no active coin window"`), both sketches call `quarantinePending(reason)`, appending the uncredited coin event to `/quarantine.log` in LittleFS with timestamp, pulse count, nonce, and target.
   - Operators can inspect and clear dispute records via `/quarantine` (GET) and `/quarantine/clear` (POST) in setup AP mode.
3. **HW-P1-1 — Cryptographic Nonce Entropy:**
   - Nonces are generated from two 32-bit hardware RNG words (`esp_random()` on ESP32, `ESP.random()` on ESP8266), eliminating predictable timer dependencies (`micros()`).
4. **HW-P2-1 — Setup Portal HTML Sanitization:**
   - All dynamic input fields in the temporary setup portal are escaped via `htmlEsc()`, preventing DOM distortion or script injection via malicious SSIDs.

---

## 3. Default Pinout & Configuration

| Signal | ESP32 Default Pin | ESP8266 Default Pin | Logic Active | Description |
|---|---|---|---|---|
| **Coin Input** | GPIO 27 | GPIO 14 (D5) | Low (Pull-Up) | Pulse line from mechanical/electronic coin acceptor |
| **Insert LED** | GPIO 2 | GPIO 2 (D4) | High | Status indicator for active coin acceptance window |
| **Relay Actuation** | GPIO 26 | GPIO 12 (D6) | High | Power cut/relay switch for connected timer device |

---

## 4. Production Safety Notice

> [!IMPORTANT]
> **Production Safety Boundary:** In accordance with `AGENTS.md` and the Master Development Directive §18, hardware admission and device flashing remain **STRICT NO-GO** pending physical hardware power-cut testing (`Experiments #34`), ISR-driven edge pulse capture verification on physical coin acceptors, off-device anti-rollback witness integration, and formal QA sign-off.
