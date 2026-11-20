# BLAZE PISONET INTERCON — Stage 5 Arduino source

**Source-only package. Not a compiled firmware release.**

Repository: `BlazeDevStudio/CoinOperatedEcosystem`  
Branch: `feature/blaze-intercon-stage5-pisowifi-remote-cs-20261120`  
Source: `Hardware/esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/`

## Open in Arduino IDE

1. Extract this ZIP to a normal directory, keeping the **`BlazePisonetIntercon` folder** intact.
2. Open **`BlazePisonetIntercon/BlazePisonetIntercon.ino`**. All **13 companion project `.h` files** must remain alongside that exact `.ino` file.
3. In Arduino IDE, add board manager URL `https://arduino.esp8266.com/stable/package_esp8266com_index.json`, install **ESP8266 boards core version 3.1.2**, and select **NodeMCU 1.0 (ESP-12E Module)** (`esp8266:esp8266:nodemcuv2`).
4. In Library Manager, install **TM1637** (provides `TM1637Display.h`). Arduino ESP8266 core supplies `ESP8266WiFi.h`, `ESP8266WebServer.h`, `EEPROM.h`, `LittleFS.h`, and the BearSSL crypto headers. C++ `<vector>` comes with the toolchain.
5. Use **Verify/Compile** before any testing. Never flash equipment in service or holding customers' money with this development build.
6. Use `SHA256SUMS.txt` in the ZIP root to verify the source after extraction. The hashes are for source/docs, not hardware firmware authenticity.

## Included source

- `BlazePisonetIntercon.ino` — full sketch, web UI, GPIO, display, local controls and route setup.
- `SketchTypes.h` — Arduino-dependent enum/type declarations.
- `InterconDiscovery.h`, `InterconPeerAuth.h`, `InterconSecureWire.h` — roles, pairing and authenticated peer transport.
- `InterconJournalCodec.h`, `InterconFlashJournal.h`, `InterconCreditLedger.h`, `InterconPaidRuntime.h` — durable Master/Slave credit path.
- `InterconArmGuard.h`, `InterconArmGuardCodec.h` — every-boot Master/Remote CS paid-coin quarantine.
- `RemoteCsCodec.h`, `RemoteCsJournal.h`, `RemoteCsRuntime.h` — fourth PisoWiFi Remote CS mode, signed controller commands and durable pulse receipts.

## Hardware and integration limits

Modes: Standard, Master, Slave, Remote CS. Stage 5 Remote CS physically controls the coin acceptor but **does not** credit a PisoWiFi account by itself. See `Docs/REMOTE_CS_PISOWIFI_STAGE5.md` and `Docs/REMOTE_CS_BLAZEPWIFI_BRIDGE_CONTRACT.md`.

GPIO defaults: D0/GPIO16 Relay 1, D1/GPIO5 TM1637 CLK, D2/GPIO4 TM1637 DIO, D3/GPIO0 coin, D5/GPIO14 buzzer fixed, D6/GPIO12 Relay 2 (PC PWR_SW), D7/GPIO13 coin-slot enable fixed. Five GPIO assignments are configurable; changing a setting does **not** rewire hardware.

**IMPORTANT: LAB / NO-GO.** The physical coin acceptor, power interruption, MOSFET/driver, relay polarity, router backend payment bridge and durable accounting have not passed customer-install acceptance. The archive intentionally contains **no `.bin` or `.elf` files**, and does not bundle third-party toolchains or libraries. Install external Arduino dependencies through the Arduino IDE.

Original upstream architectural reference: `https://github.com/ivanalayan15/JuanFi`. The new BLAZE Remote CS wire protocol is NOT JuanFi-compatible.
