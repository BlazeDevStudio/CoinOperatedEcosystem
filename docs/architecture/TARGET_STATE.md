# Target State

Proposal derived from the verified current state (`CURRENT_STATE.md`). It is a recommendation for owner review, not an accepted decision.

## 1. Decision: monorepo for products, independent repos kept independent

**Hybrid.** `CoinOperatedEcosystem` is the home of the four coin-operated products and their shared contracts, because they already ship together (shared signature contract, member bank/restore) and the owner's draft work is already organized this way. Unrelated products stay in their own repositories (see `REPOSITORY_BOUNDARIES.md`). No dedicated SoftTimer repository exists, so SoftTimer lives here under its own directory with its own CI path filter, and may be split out later without history loss if it is imported with path history.

Products remain independently buildable, testable and releasable: each product directory has its own README, tests, CI workflow with path filters, and version.

## 2. Directory layout (case rule: **Capitalized product directories, lowercase infrastructure directories**)

```
CoinOperatedEcosystem/
├── Pisowifi/          # OpenWrt captive portal + coin vendo API   (from PR #18 and CORE chain)
│   ├── core/          #   shell services: capabilities, config transactions, accounting, nft
│   ├── openwrt/       #   rootfs overlay, init scripts, CGI, packaging (profiles live in profiles/)
│   ├── profiles/      #   router profiles (EW1200G Pro first) - VLAN/port maps are DATA, not code
│   ├── portal/ admin/ vouchers/
│   └── tests/
├── Rental/            # server/ (OpenWrt), android/, shared/, tests/   (from PR #19)
├── Pisonet/           # Windows SoftTimer; SoftTimer/ (from PR #17); integration/; docs/
├── Hardware/          # esp32/ esp8266/ protocols/ tests/
├── Shared/            # contracts/ authentication/ accounting/ schemas/  (only when a real need exists)
├── deployment/  tools/  tests/  docs/  .github/
```

Rules:
1. **One spelling per directory.** `Pisonet`, `Rental`, `Pisowifi`, `Hardware`, `Shared` are capitalized. The `pisonet/` and `rental/` lowercase directories in PR #1, and `core/` in PRs #5–#16, must be moved before any of them merge (they collide or duplicate). 
2. **CORE is not a product.** The COE-CORE chain (#3–#16) belongs under `Pisowifi/core/` because its files are the PisoWiFi OpenWrt runtime. The two lines of the same four files (see `DEPENDENCY_MAP.md` §3) must be reconciled into one before further cleanup.
3. **Proprietary material is excluded from this public repo** until the owner resolves P0-1. The directory layout does not imply that BlazePwifi source may live here.
4. **Profiles, not constants.** VLAN IDs, LAN/WAN port mappings and SSID separation are described by profile files validated by a schema. Nothing is hardcoded for EW1200G Pro; it is the first profile.
5. **Default deny.** Coin acceptance, relay actuation, financial credit and paid-ack stay disabled unless explicitly enrolled; synthetic tests never enable them.

## 3. Shared contracts (introduce only on demand)

First two candidates, both already implemented informally in two products:

1. `Shared/contracts/controller-signature` — action, id, nonce, pulses, target, signature, replay window, versioning.
2. `Shared/contracts/member-bank-restore` — event id/idempotency, sequence, ack semantics.

Each contract is a versioned schema plus **golden test vectors** consumed by each implementation's tests (shell, C#, C++). Financial authority stays in the accounting layer; device control never decides credit. A missing ack is "unknown", never "failed" and never "succeeded".

## 4. Build, CI and release

- One workflow per product with path filters, `permissions: contents: read`, pinned toolchains, exact commit recorded. Release/publish workflows are separate, manual and owner-controlled.
- Required checks per product before a PR leaves draft: static (lint, syntax, secret scan), unit/mock, and where possible OS-level (Windows build; OpenWrt rootfs in a container). Hardware acceptance is a separate documented gate.
- Provenance manifests (the existing `SOURCE_INTAKE.json` style plus `tools/source_intake_guard.py`) are kept for every import.

## 5. Status targets

| Component | Today | Next realistic status |
|---|---|---|
| Pisowifi | CLEANUP | VALIDATING after core reconciliation + CI + integration test decision |
| Rental | RECOVERING | DEVELOPING after CI and EW1200G/R281 profile decision |
| Pisonet SoftTimer | MIGRATING | VALIDATING after #17 review and Windows runtime tests |
| Hardware | RECOVERING | MIGRATING after Pisowifi core stabilizes |
| Shared | not started | contracts from the two candidates above |

All remain **NO-GO for production** until physical acceptance and the financial/anti-rollback gates are independently met.
