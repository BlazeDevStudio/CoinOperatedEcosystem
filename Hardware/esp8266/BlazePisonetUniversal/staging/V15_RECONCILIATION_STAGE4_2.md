# BLAZE PISONET — V1.5 ↔ INTERCON Stage 4.2 reconciliation

**Input audited:** User-supplied `BLAZE_PISONET_POWER_CS_V1_5(1).zip`, containing 21 archive members, dated 2026-11-18. Package includes a self-contained V1.5 sketch, the five-header modular V1.5 sketch, README, validation, browser preview and local host tests.

## Input verification
- Package manifest reports single-file V1.5 sketch SHA256 `e121655830706c4492ad2f3b092753ca25f0e3b1d50bed1904375f24644dec54`.
- Package manifest reports modular `BlazePisonet/BlazePisonet.ino` SHA256 `af2bc56441d3717a98c5d36d04a85fe20bf1b7d06371ce77aa2b97538943d5cb`.
- **Both SHA256 checks passed** against extracted files.
- `host-tests/run_tests.sh` passed locally: GPIO layout, D7 coin gate, D6 momentary pulse, expiry/shutdown grace, cancellation and recovery.
- The package's own `VALIDATION.md` explicitly says a **real Arduino ESP8266 compiler** and real hardware were **not** tested at the time of V1.5 packaging.

## Code reconciliation (source structure; not a claim of runtime equivalence)
Compared the modular V1.5 sketch with INTERCON Stage 4.1 source at commit `4e13a6cbee1778987e0257b28d0f0ddce413069d`.

- **65/65 original named firmware function identifiers retained**, including display setup, relay/CS handling, WAV/tone parsing, idle/welcome chimes, manual Add/Set, sales, EEPROM migration and authentication.
- **8/8 original HTTP routes represented:** `/`, `/api/status`, `/display/test`, `/display/default`, `/api/time`, `/action`, `/settings`, `/upload`; INTERCON adds separate pairing/journal APIs.
- Original V1.5 `pinSetIsUnique` rules remain: configurable **coin, Relay 1, Relay 2, display CLK and DIO**. Fixed buzzer D5/GPIO14 and fixed coin slot EN D7/GPIO13 were part of V1.5 itself. D0/GPIO16 relay cutoff, D6/GPIO12 momentary PWR_SW, D3/GPIO0 coin input and D1/D2 TM1637 remain default.
- V1.5 EEPROM CS preferences 392–399, power preferences 400–411 and one-time pin migration at 416–419 were deliberately preserved; INTERCON network and payment journal use separate LittleFS files. This comparison **does not prove installed EEPROM migration on physical boards**.
- Standard mode preserves the original local coin-to-timer workflow, sales/chimes, HTTP admin and power control (subject to safety interlocks).
- INTERCON Master is a **different role** (coin forwarding with durable pending credits); Slave uses the **journal**, not the V1.5 EEPROM timer, as paid balance authority. These are intentional behavior differences, not silent regressions.
- The Stage 4.1 Master every-boot quarantine is also intentional. It requires explicit physical reconciliation before arming the coin slot.

## New reconciled integration improvements (Stage 4.2 draft)
1. Responsive **live functional NodeMCU D-pin map inside Settings**; labels track all five editable GPIO inputs. It highlights Relay 1, PWR_SW, Coin, CLK, DIO, plus reserved fixed D5 buzzer/D7 CS. This is **not an exact physical board header footprint**; adapters and clones vary.
2. Browser-side pre-save validation mirrors the firmware collision, UART/flash, strap-pin, interrupt and fixed-reservation rules. Actual server validation remains authoritative.
3. Server rejects malformed/blank/negative or greater-than-16 pin parameters instead of silently clamping to GPIO0/16.
4. Settings are blocked while CS is actively accepting coins, pulses are queued, or the Master has an unsettled durable credit. Wiring/polarity changes also refuse nonzero stored paid balances, pending PC operations, and active coin edges.
5. Settings show when a Master/Slave journal prevents switching into a different operating role.

## Operating mode decision — NOT freely hot-swappable
- **Standard ↔ Master ↔ Slave** is selectable in the UI, but mode changes are permitted only **before** a paid-event journal is initialized, after paid time is cleared and with safe hardware/coin state. Restart/reprovision is required for coherent Master/Slave operation.
- After either journal slot exists, **role switching is deliberately blocked**. A future migration must preserve the immutable transaction history and settle pending credits on both boards; clearing filesystem or changing role/key to bypass that rule risks customer losses.
- A Master-to-Slave switch is **not** a production-ready live failover system. Multi-Slave paid credit routing remains unimplemented.

## Remaining limitations / release decision
- Stage 4.2 source builds/tests are required for each head; do not infer pass from earlier head.
- Hardware real coin pulses and power-cut-before-first-journal-commit cannot be guaranteed lossless in software.
- 650 ms burst-quiet prototype, 60 s Slave journal checkpoints, flash wear, AP/STA reliability, real relay polarity and PCB wiring still require physical acceptance.
- Relay 2 estimates PC power state without a sensor; a mistaken pulse could shutdown a running computer.
- Input V1.5's one-file example and preview are **comparison references**, not drop-in replacements for the current INTERCON modular firmware.
- **Status: DRAFT / LAB-ONLY / PAID PAYMENT NO-GO.** Do not merge or flash on live paid equipment without real hardware validation.
