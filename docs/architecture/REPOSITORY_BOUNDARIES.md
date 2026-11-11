# Repository Boundaries

Recommendation derived from `SOURCE_PROVENANCE.md`. Visibility changes, repository creation and any deletion require owner authorization and are **not** performed by this document.

## 1. What belongs where

| Repository | Visibility today | Boundary |
|---|---|---|
| `CoinOperatedEcosystem` | PUBLIC | PisoWiFi, Rental, Pisonet SoftTimer, Hardware firmware, Shared contracts, deployment, product docs. Only material the owner confirms may be public |
| `BlazingSystems-Experiments` | PUBLIC | **Historical reference only.** Not a permanent production source. Never delete or force-push; keep branches and PRs as provenance. Stop adding production work here |
| `BlazingSystems-Labs` | PUBLIC | Hardware lab / public-safe derivatives (`blaze-pisonet-timer-public`). Hardware product code migrates only via reviewed PR |
| `BlazingSystems-Archives` | PUBLIC | Historical notes. Leave as is |
| `Forked-Projects` | PUBLIC | Third-party-derived NRSuite ports; respect upstream licenses/attribution. Reference only |
| `BlazingSystems`, `-Projects` | PUBLIC | Portfolio and policy docs. Fix stale owner URLs in a docs-only PR |
| `BlazeMCU`, `BlazeMCUstudio`, `BlazeMessenger`, `AndroidDevel`, `B-Secure`, `Blaze-Ultimate-Optimizer`, `BlazeFM`, `BlazeNetMonitor`, `BlazeUnifiedElSim`, `BlazeExeCute`, `EasyMode`, `ThreadHarbor`, `BlazeWeb`, `BlazeDevStudio.github.io`, `samdenty-esp32-port`, `BCR-Repository` | PUBLIC | **Out of scope.** Different products. Do not merge into the Ecosystem because they share an owner |
| **Private restricted repository** | does not exist | **Needed** before any proprietary BlazePwifi code, signing assets, private configs or sensitive audit records are written anywhere. Must be created and approved by the owner |

## 2. Product boundaries inside the monorepo

- **Pisowifi** ↔ **Rental:** independent. No source imports either direction. Optional interoperability only through a versioned contract in `Shared/contracts`.
- **Pisonet SoftTimer:** core paid-session and lock operation must not require Pisowifi, Rental, Phoenix control plane or the diskless manager. Pisowifi integration is an optional adapter. Diskless manager stays a separate add-on that is never loaded into the financial timer process.
- **Hardware firmware:** may speak the Pisowifi vendo contract; coin/relay disabled by default; ESP8266 and ESP32 kept as separate implementations with a shared protocol spec.
- **Phoenix / MCU Studio / other Blaze products:** excluded.

## 3. Dependency direction

`Shared/contracts` ← {Pisowifi, Rental, Pisonet, Hardware}. Products never import each other's source. CI enforces it with a dependency-direction check (planned, `tools/`).

## 4. Open boundary decisions for the owner

1. **P0-1:** is BlazePwifi proprietary (directive) or MIT/public (current repo state)? This decides whether #18 may stay on a public repo.
2. Whether SoftTimer is public. The existing `Pisonet/README.md` designates it public; confirm.
3. Whether `core/` (#5–#16) is folded into `Pisowifi/` (recommended) or kept separate.
4. Whether the Experiments branches that continue to receive new production work (e.g. `phoenix/pisonet-*`) should stop and move here after review.
