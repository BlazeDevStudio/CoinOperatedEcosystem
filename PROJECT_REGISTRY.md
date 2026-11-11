# Project Phoenix — Migration Registry

This is a **destination-scoped staging registry**, not a replacement for the historical master registry. Update every row with exact source SHA and test evidence before promoting state.

| Subsystem | Destination | Candidate origin | Engineering owner | State | Release gate |
| --- | --- | --- | --- | --- | --- |
| CORE | `core/` | `BlazingSystems-Experiments:experiment/openwrt/BlazePwifi/` | PHX-CORE | STRUCTURE_CREATED | NO-GO — financial safety |
| RENTAL | `rental/` | `BlazingSystems-Experiments:experiment/openwrt/BlazePwifi/android/` | PHX-RENTAL | STRUCTURE_CREATED | NO-GO — signed lease persistence |
| PISONET | `pisonet/` | `BlazingSystems-Experiments:experiment/windows/BlazePisonet-SoftTimer/` | PHX-PISONET | STRUCTURE_CREATED | NO-GO — serial session, signing |
| CONTROLLERS | `controllers/` | `BlazingSystems-Experiments:experiment/openwrt/BlazePwifi/esp8266/, esp32/` | PHX-HARDWARE | STRUCTURE_CREATED | NO-GO — admission, relay safety |
| CONTRACTS | `contracts/` | Cross-subsystem, exact sources to be resolved | PHX-CORE + consumers | STRUCTURE_CREATED | NO-GO — contract compatibility |
| INTEGRATION | `integration-tests/` | Source-linked independent Phoenix fixtures | PHX-QA | STRUCTURE_CREATED | NO-GO — independent acceptance |

No row is SOURCE_STAGED, MIGRATED, VERIFIED or release-ready. Source repository original heads and PR discussions stay authoritative until independently reconciled.

## Known outstanding draft dependencies (observed 2026-10-28)

- Finance: [#198](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/198), [#215](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/215), [#222](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/222).
- Windows serial: [#197](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/197), [#216](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/216), [#219](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/219), [#221](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/221).
- Windows signing/build: [#217](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/217), [#218](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/218), [#223](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/223).
- Hardware: [#193](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/193), [#183](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/183).

These links are discovery references, **not** evidence that the changes are merged or passing.
