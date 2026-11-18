# Blaze Pisonet Universal / INTERCON — source audit and migration

Audit date: **2026-11-18**. This is a reviewable **nonproduction migration**, not a merge or functional upgrade. No firmware is modified in the legacy reference, no unrelated repositories are renamed, and no source is deleted from Labs or Experiments.

## What was searched

The connected `BlazeDevStudio` account exposed **23 repositories**. Repository names were classified, and the relevant default-branch trees, active integration PRs, and branch-anchored firmware were inspected. This was a *targeted source and branch audit*, **not** a claim to have read every historical commit in every repository.

### Verified source locations

| Source / link | Role | Disposition |
| --- | --- | --- |
| [Labs: Blaze Pisonet Universal](https://github.com/BlazeDevStudio/BlazingSystems-Labs/tree/main/embedded/blaze-pisonet-universal) | Existing active ESP8266 Standalone/Master/Slave engineering build (about 2,600 lines) | Preserve in Labs; copy publicly published source byte-for-byte to an isolated `Hardware/esp8266/BlazePisonetUniversal/legacy/` folder |
| [Labs: Blaze Pisonet Timer Public](https://github.com/BlazeDevStudio/BlazingSystems-Labs/tree/main/embedded/blaze-pisonet-timer-public) | Earlier public-safe standalone timer | Leave as historical lab, do not use as canonical update |
| [Experiments: BlazePwifi ESP8266 Vendo](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/tree/main/experiment/openwrt/BlazePwifi/esp8266) | Existing router-linked signed coin-controller implementation | Historical provenance; avoid replacing it with universal timer |
| [COE: integration PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) | Unmerged candidate with `Hardware/`, `Shared/`, `Pisowifi/`, `Rental/`, `Pisonet/` | This migration branch is stacked directly on its pinned head `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| [COE: Hardware + Shared PR #27](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/27) | Signed Vendo migration and schema/golden vectors | Keep its controller-signature contract unchanged |
| [COE: Pisonet ESP8266 PR #34](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/34) | Earlier separate BLAZE PISONET V1.3 idle animation sketch | Distinct draft lineage. Do not silently replace or merge with the universal legacy build |
| Locally delivered BLAZE PISONET V1.5 | Recent timer/PWR_SW/CS design in another conversation artifact | **Not verified in GitHub**. Requires exact-source comparison before active firmware is reconciled |
| [COE: dependency map](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/integration/ecosystem-nonproprietary-candidate-20261111/docs/architecture/DEPENDENCY_MAP.md) | Product boundaries and integration edges | Follow product separation: Shared contracts do not import product implementation |

### Code findings (public Universal firmware)

1. Roles **already exist** as `ROLE_STANDALONE`, `ROLE_MASTER`, `ROLE_SLAVE`; rename the *operator-facing* Standalone label to **Standard**, not the persisted enum values without migration.
2. The existing `NET_STA` branch uses `WiFi.mode(WIFI_STA)`, with `WIFI_AP` only as fallback. This does **not** preserve a simultaneous always-on AP as requested.
3. `handleUdp()` uses plaintext `HELLO`, `REQ`, `GRANT`, `CREDIT`, `DONE` and `SALE` messages on UDP port 4210. It neither authenticates peer commands nor journals/ACKs a remote paid event. `lastCreditToken` in RAM, derived from `millis()`, is not a durable deduplication scheme.
4. Master increments its own sales when coin pulses arrive; Slave independently increments sales on CREDIT. Consolidated reporting must avoid counting the same coin twice.
5. The existing `/relay2` route **toggles** a relay and `setRelays(true)` holds both relays energized for paid sessions. This is incompatible with using Relay 2 as a motherboard `PWR_SW` **momentary pulse**.
6. Portal power and settings handlers shown in `setup()` have no explicit admin authentication. Before accepting STA/LAN remote requests, enforce authentication, CSRF protections, and POST-only state changes.
7. `pinSetIsUnique` checks coin/relay/buzzer/display assignments but not the Slave request-pin/coin-slot-enable mapping, so new GPIO collisions require additional validation.
8. Uptime-derived day/month sales buckets are not reliable wall-clock accounting. Paid-time and outage recovery need reconciliation with the current V1.5 implementation.
9. Current `Hardware/esp8266/BlazePwifiVendo` implements configured STA, temporary setup AP, signed target-bound OpenWrt registration/poll/coin path and quarantined rejected coin events. It should remain a separate implementation until an explicit, reviewed adapter is designed.

## Correct destination and promotion sequence

1. **This PR:** preserve the Lab Universal source under `Hardware/esp8266/BlazePisonetUniversal/legacy/`; publish a proposed role/peer protocol in `Shared/contracts/pisonet-intercon/`; no runtime changes, no commercial operation.
2. **Next code migration:** reconcile the newer owner-tested BLAZE PISONET V1.5 local timer with Universal's role/network logic using diff, preserving watchdog, coin pulse, EEPROM layout, CS D7, Relay 1 D0, Relay 2 D6 momentary pulse and TM1637 CLK D1/DIO D2. Do not copy legacy `setRelays()` into current firmware.
3. **Secure protocol implementation:** implement versioned pairing, HMAC signatures, stable event IDs, durable master+slave journals, receipts, power-cut recovery and fail-closed CS disable on uncertainty. Add test vectors to `Shared/contracts/pisonet-intercon/`.
4. **BlazePwifi adapter:** integrate through existing signed `controller-signature` Vendo contract without using a peer as financial authority when the router owns accounting. Separate standalone coin-to-time accounting from router-managed balances.
5. **Test and release:** real NodeMCU build, WPA2 AP+STA under STA loss and channel changes, authenticated portal LAN access, replay/power-cut/partition tests, physical coin/relay checks. Independent QA review before any merge/deployment.

## Unsupported assumptions / what we did not do

- No assertion that the legacy remote-credit path is safe.
- No compilation, physical flashing, payment acceptance test, or merge into `main`.
- No move or deletion of any Labs/Experiments source or maintenance branches.
- No guarantee that each peer can discover another across routers, client-isolated SSIDs or the public internet.
- No "WAN IP" remote access on the public Internet; access over the router-assigned local STA IP is intended. External administration, if wanted, requires secure VPN-mediated networking and additional admission controls.
