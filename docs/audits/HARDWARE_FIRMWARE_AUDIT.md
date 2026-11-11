# Blaze Hardware Firmware Audit (ESP32 & ESP8266 Controllers)

**Date:** 2026-11-11  
**Status:** Static & protocol-boundary audit complete — **NO-GO for production / physical flashing** (`Experiments #34`)

## 1. Audited Firmware Sources & Exact Provenance

| Component | Repository | Path | Blob SHA | Lines | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BlazePwifiVendo32 (ESP32)** | `BlazeDevStudio/BlazingSystems-Experiments` | `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` | `117c6e937e8f12f3890ace2ae23b3a23ff1c3df0` | 304 | Wi-Fi coin-acceptor & relay controller for Blaze PisoWiFi (`/cgi-bin/vendo`) |
| **BlazePwifiVendo (ESP8266)** | `BlazeDevStudio/BlazingSystems-Experiments` | `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` | `bfb94920eb0a189ca01d52e5443954fa133f5423` | 369 | ESP8266 Wi-Fi coin-acceptor & relay controller for Blaze PisoWiFi (`/cgi-bin/vendo`) |
| **Blaze Pisonet Timer (Public)** | `BlazeDevStudio/BlazingSystems-Labs` | `embedded/blaze-pisonet-timer-public/Blaze_Pisonet_Timer_PUBLIC.ino` | `main@5d8e4f1` | standalone | Standalone coin-operated hardware timer |
| **Blaze Pisonet Universal** | `BlazeDevStudio/BlazingSystems-Labs` | `embedded/blaze-pisonet-universal/BLAZE_PISONET_UNIVERSAL_PUBLIC.ino` | `main@5d8e4f1` | standalone | Universal standalone coin timer |

> [!IMPORTANT]
> In accordance with `Pisowifi/SOURCE_INTAKE.json` and the P0-1 privacy/licensing gate, `BlazePwifiVendo32.ino` and `BlazePwifiVendo.ino` have **not** been copied into `CoinOperatedEcosystem` pending owner resolution of P0-1.

---

## 2. Confirmed Defects in ESP32 / ESP8266 Vendo Firmware

### `HW-P0-1` — Unauthenticated Router HTTP Responses & Premature `clearPending()` Coin Loss
- **Locations:**
  - `BlazePwifiVendo32.ino` lines `192–200`, `277–280`, `293–300`
  - `BlazePwifiVendo.ino` lines `229–238`, `321–323`, `350–361`
- **Mechanism:**
  1. Requests to `http://<server>:4455/cgi-bin/vendo` are signed via `signedBody()` (`SHA256(key|action|id|nonce|pulses|target|key)`), matching `bp_vendo_sig_expected()` in `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/common.sh`.
  2. However, the firmware **never verifies a signature or nonce on the HTTP response** for `register`, `poll`, or `coin`.
  3. On `coin` submission, both sketches execute:
     ```cpp
     if (r.indexOf("\"ok\":true") >= 0 ||
         r.indexOf("coin window expired") >= 0 || r.indexOf("coin target mismatch") >= 0 ||
         r.indexOf("no active coin window") >= 0 || r.indexOf("another vendo selected") >= 0) {
       clearPending(); applyOutputs();
     }
     ```
- **Impact (P0 Financial Integrity & Security):**
  - **Physical coin loss on window expiry race:** If a customer drops a coin as the active window expires (`expires <= now`), the router returns `{"ok":false,"error":"coin window expired"}` without crediting any account, and the ESP immediately calls `clearPending()`, deleting `/pending.dat` from `LittleFS` and destroying the uncredited coin event.
  - **Forged response spoofing:** Because traffic is plain HTTP on LAN port `4455` and responses carry no MAC/signature on `poll` or `coin`, a spoofed LAN reply containing `"ok":true` or `"no active coin window"` wipes `/pending.dat` or injects arbitrary GPIO pin remapping via `applyRemoteConfig(r)`.

### `HW-P0-2` — Blocking HTTP Calls During Polling Loop Cause Missed Coin Pulses
- **Locations:**
  - `BlazePwifiVendo32.ino` lines `192–200`, `277–291`
  - `BlazePwifiVendo.ino` lines `229–238`, `321–342`
- **Mechanism:**
  - Coin pulses are detected by polling `digitalRead(runCoinPin)` inside `loop()` rather than via a hardware edge interrupt (`attachInterrupt` with `IRAM_ATTR`).
  - Every `1500 ms`, `loop()` calls `post("poll")`, which performs a synchronous TCP connect + HTTP POST with a `3500 ms` timeout (`h.setTimeout(3500)`).
- **Impact (P0 Financial Integrity):**
  - Standard multi-coin acceptors emit pulses `20–100 ms` wide. Any pulse arriving while `post("poll")` blocks on Wi-Fi congestion or router load is missed or fails debounce, under-counting multi-pulse coins.

### `HW-P1-1` — Non-Constant-Time Nonce Entropy Half on ESP8266 (`micros()`)
- **Location:** `BlazePwifiVendo.ino` lines `66–69`
- **Mechanism:**
  - `freshNonce()` on ESP8266 uses `uint32_t a=ESP.random(), c=micros(); sprintf(b,"%08lx%08lx", a, c);`, whereas ESP32 uses two `esp_random()` words. Half of the 64-bit nonce on ESP8266 is the predictable microsecond timer.

### `HW-P2-1` — Unescaped HTML Attributes in Setup Portal (`/`)
- **Locations:**
  - `BlazePwifiVendo32.ino` lines `225–234`
  - `BlazePwifiVendo.ino` lines `265–271`
- **Mechanism:**
  - `cfg.ssid`, `cfg.server`, and `cfg.id` are concatenated directly into single-quoted HTML `<input value='...'>` attributes without escaping `'`, `<`, `>`, or `&`. An SSID containing `'` breaks the setup form DOM.

---

## 3. Required Remediation Plan (Prior to Any Hardware Admission)

1. **Authenticated Router Responses (`poll` / `coin` / `register`):**
   - Extend `/cgi-bin/vendo` `poll`, `register`, and `coin` JSON responses to include `response_sig = HMAC/SHA256(key|action|id|nonce|ok|...)` (matching the pattern already used by `member_snapshot`, `member_auth`, and `member_bank` in `/cgi-bin/vendo` lines `76–89`).
   - Require `BlazePwifiVendo32` and `BlazePwifiVendo` to verify `response_sig` before applying remote config or clearing `/pending.dat`.
2. **Quarantine Rejected/Expired Coin Events Instead of Deleting Them:**
   - Do not call `clearPending()` on `"coin window expired"` / `"no active coin window"`; transition the controller into a held/quarantined state or report an uncredited-coin dispute event to the router so operator reconciliation can credit or refund the coin.
3. **ISR-Driven Coin Pulse Capture:**
   - Replace main-loop `digitalRead(runCoinPin)` polling with an `IRAM_ATTR` GPIO interrupt handler using atomic pulse-edge timestamps, decoupling physical pulse capture from `HTTPClient` network latency.

---

## 4. Status Addendum — 2026-11-11 (`Experiments PR #283`)

Client-side remediation candidates for `HW-P0-1`, `HW-P0-2`, `HW-P1-1`, and `HW-P2-1` have been implemented and verified on branch `cleanup/esp-firmware-hardening-and-quarantine-20261111` under **Draft PR #283** in `BlazeDevStudio/BlazingSystems-Experiments`:

1. **HW-P0-1 (Response Signature Verification):** `BlazePwifiVendo32.ino` and `BlazePwifiVendo.ino` now capture `lastSentNonce` and cryptographically verify `response_sig` for `register` and `poll` against `hexDigest(key|action|id|nonce|...)` matching the server-side signatures emitted by OpenWrt `/cgi-bin/vendo` (PR #24). Unauthenticated or mismatched replies are ignored.
2. **HW-P0-2 (Uncredited Coin Quarantine):** When the router returns a coin rejection (`"coin window expired"`, `"no active coin window"`, etc.), both sketches now invoke `quarantinePending(reason)`, appending the uncredited coin event to `/quarantine.log` in LittleFS with timestamp, pulses, nonce, and target for operator reconciliation, before clearing the active queue.
3. **HW-P1-1 (ESP8266 Nonce Entropy):** In `BlazePwifiVendo.ino`, `freshNonce()` replaced predictable `micros()` with two 32-bit hardware RNG words from `ESP.random()`.
4. **HW-P2-1 (Setup Form HTML Escaping):** Added `htmlEsc()` escaping `&`, `'`, `"`, `<`, and `>` for `cfg.ssid`, `cfg.server`, and `cfg.id` inputs in the temporary setup portal.
5. **Automated Verification:** Added `experiment/openwrt/BlazePwifi/tests/v05_firmware_hardening_test.sh` asserting all four properties and verifying syntax/brace balance.
6. **Setup Portal Quarantine Log Inspection:** Added `/quarantine` (GET) and `/quarantine/clear` (POST) endpoints in `setupPortal()` on both ESP32 and ESP8266, allowing operators to inspect and clear the uncredited coin log directly from the setup browser interface.
7. **Arduino CLI CI Matrix Verification:** Corrected an extra closing brace in `BlazePwifiVendo32.ino` loop(); both ESP32 (`esp32:esp32@3.3.12`) and ESP8266 (`esp8266:esp8266@3.1.2`) Arduino CLI compile jobs and test suites pass 100% green in CI run `43042410732` and upload their binary release artifacts (`BlazePwifi-esp32-firmware` and `BlazePwifi-esp8266-firmware`).

> [!IMPORTANT]
> Hardware admission remains **STRICT NO-GO** pending physical hardware power-cut testing (`Experiments #34`), ISR-driven edge pulse capture verification on physical coin acceptors, anti-rollback witness integration, and formal QA review.
## 5. Status Addendum — 2026-11-11 (`CoinOperatedEcosystem PR #27`)

The hardened ESP32 and ESP8266 firmwares and inter-product contracts have been migrated directly into `CoinOperatedEcosystem` under **Draft PR #27** (`feature/hardware-firmware-and-shared-contracts-20261111`):
1. **Repository Layout:** Housed under `Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` and `Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`, alongside `Hardware/tests/test_firmware_hardening.sh` and pinout documentation in `Hardware/README.md`.
2. **Shared Contracts:** Established `Shared/contracts/controller-signature/` and `Shared/contracts/member-bank-restore/` containing JSON Schemas and golden test vectors for inter-product protocol compliance, validated by `Shared/tests/test_shared_contracts.py`.
3. **Reproducible Hardware CI:** Added `.github/workflows/hardware-ci.yml` running contract validation and compiling both sketches through Arduino CLI (`esp8266:esp8266:nodemcuv2` and `esp32:esp32:esp32`). Verified 100% PASS in CI run `43050741196` with binary artifacts uploaded.
4. **Candidate Integration:** Merged into Candidate PR #26 on branch `integration/ecosystem-nonproprietary-candidate-20261111`. Production hardware flashing remains strictly NO-GO.
