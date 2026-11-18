# Blaze Pisonet Universal — legacy source intake (review only)

> **DRAFT / NOT FOR FLASHING OR PRODUCTION.** This directory preserves the existing publicly published *Blaze Pisonet Universal* ESP8266 implementation and maps its migration into the CoinOperatedEcosystem architecture. It is **not** a replacement for the owner's later BLAZE PISONET V1.5 firmware, and is **not** the existing router-linked `BlazePwifiVendo` firmware.

## Source provenance

- Original, retained unchanged: [BlazingSystems-Labs / embedded/blaze-pisonet-universal](https://github.com/BlazeDevStudio/BlazingSystems-Labs/tree/main/embedded/blaze-pisonet-universal).
- Original source file: [BLAZE_PISONET_UNIVERSAL_PUBLIC.ino](https://github.com/BlazeDevStudio/BlazingSystems-Labs/blob/main/embedded/blaze-pisonet-universal/BLAZE_PISONET_UNIVERSAL_PUBLIC.ino), Git blob `3fb15ecb9272b65500260bc7c92f05590163fa6d`.
- Immutable reference copy in this directory: [legacy/BLAZE_PISONET_UNIVERSAL_PUBLIC/BLAZE_PISONET_UNIVERSAL_PUBLIC.ino](legacy/BLAZE_PISONET_UNIVERSAL_PUBLIC/BLAZE_PISONET_UNIVERSAL_PUBLIC.ino).
- All original source remains in Labs for provenance; no deletion, force push or merge of another worker's branches.
- This import is **public-safe**, but code provenance alone does not establish safety or current feature parity.

## Existing behavior verified by inspecting source

| Concept | Existing implementation | Gaps for the requested feature |
| --- | --- | --- |
| Standard (called `ROLE_STANDALONE` in code) | Local coin input and timer | Adapt to V1.5 retained-time, GPIO/CS and PC power-button semantics |
| Master (`ROLE_MASTER`) | Local coins sent to a selected slave via UDP port 4210 | Signed/authenticated messages, event durability and acknowledgement |
| Slave (`ROLE_SLAVE`) | Remote `CREDIT` message increments local timer and sales | Only accept paired-master commands and deduplicate durably |
| STA + AP | `NET_AP` / `NET_STA`, AP fallback when STA fails | Owner requests **persistent AP+STA concurrently**, not AP only on failure |
| Discovery | `HELLO`/UDP and a node table, requests via a dedicated request button | Rate-limited LAN discovery, secure pairing, unique peer identity, configurable target selection |
| Web portal | Role/STA/AP fields and visible node monitoring | Authentication/authorization before financial and relay actions; manage over STA LAN IP |
| Pin mapping | Coin/relays/display configurable | Include CS enable and safe, verified PWR_SW pulse on owner's V1.5 hardware map |

## Critical blocker in the public reference

The existing `handleUdp()` accepts plaintext `CREDIT|...` messages without peer authentication or durable event deduplication. A token derived from `millis()` is not a secure replay identifier. The current `/relay2` route toggles the relay rather than enforcing a momentary pulse. These are **review blockers** for deployment; the imported code must not be flashed onto a paid machine or connected to a PC motherboard power-button header.

## Where maintained code belongs

- `Hardware/esp8266/BlazePisonetUniversal/` — ESP8266 **standalone timer** with optional peer Master/Slave mode. The owner's newer V1.5 source must be reconciled here in a separate reviewed step.
- `Hardware/esp8266/BlazePwifiVendo/` — existing **router-linked external coin-controller** firmware. Do not overwrite or combine raw source files.
- `Shared/contracts/pisonet-intercon/` — proposed authenticated device-to-device interoperability contract.
- `Shared/contracts/controller-signature/` — existing BlazePwifi router-controller contract; keep it intact.
- `Pisowifi/` — optional BlazePwifi **adapter** to the local timer system; router/accounting remains financially authoritative when enabled.
- `Pisonet/SoftTimer/` — standalone **Windows** PC rental timer, a different product.

See [the draft interconnection contract](../../../Shared/contracts/pisonet-intercon/PROTOCOL_DRAFT.md) and [migration notes](../../../docs/migration/BLAZE_PISONET_INTERCON_AUDIT.md).

## Build and release admission

No ESP8266-core build or hardware test of this source copy is asserted by the migration. Before turning the reference into active firmware: separately compile the exact NodeMCU target; prove boot-pin and relay safety; enforce peer cryptographic authentication and replay defense; test duplicate/dropped/reordered coins under power cuts and partitions; preserve paid balances; test AP+STA/STA-IP access, fallbacks, and safe role changes; and obtain independent QA. CI mocks do not substitute for physical coin and relay testing.

**Never expose the admin portal or UDP credit protocol directly to the public internet.** The STA IP is a LAN address unless a deliberately secured remote-access method (e.g. VPN) is deployed.
