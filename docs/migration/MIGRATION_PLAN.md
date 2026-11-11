# Migration Plan

Principle: **recover and review what the owner already drafted; do not re-import.** Each step is a separate, small, reviewable draft PR with source SHA, mapping, validation evidence and rollback. Nothing here merges, publishes, flashes, or touches real customer data.

## 0. Gates & Distribution Model

### Owner Decision (2026-11-11): Hardware Appliance Bundles Model
The owner has determined that the software is **not distributed standalone as bare software**. It is shipped exclusively alongside physical **hardware appliance bundles**:
- **Ruijie RG-EW1200G Pro v1.1 routers**
- **Orange Pi single-board computers (OPi Zero 3, OPi One, OPi PC, OPi PC2, etc.)**
- **Mini PCs (Windows SoftTimer PC, x86_64 OpenWrt/Linux appliances)**
- **Commercial routers and embedded IoT platforms**

Consequently, **Gate G1 (P0-1 Privacy/Licensing Conflict) and Gate G2 are RESOLVED & REMOVED**. All components (PisoWiFi, Rental, Pisonet SoftTimer, Hardware firmware, and Shared contracts) are unified in this monorepo as turnkey appliance firmware and companion software for these hardware bundles.

| Gate | Status | Resolution |
|---|---|---|
| G1 — Governance & Privacy Licensing (P0-1) | **RESOLVED / REMOVED** | Software is shipped bundled with hardware appliances (EW1200G Pro, OPi, Mini PC, routers); not distributed standalone. |
| G2 — Approved private repository | **RESOLVED** | Unified monorepo architecture for all hardware bundle components in `CoinOperatedEcosystem`. |
| G3 — Case/layout decision (`TARGET_STATE.md` §2) | **RESOLVED** | Unified capitalized convention (`Hardware`, `Pisonet`, `Rental`, `Shared`, `Pisowifi`). Case collisions eliminated (PR #1, PR #25). |
| G4 — Drive registry access | DEFERRED | Artifact archiving and binary mirror connector access when available; does not block appliance integration. |


## 1. Already-existing migrations (do not redo)

| ID | PR | Subject | State |
|---|---|---|---|
| E-1 | #17 | SoftTimer baseline (Experiments #255 stack @ `21b06553…`) | draft, CI success ×2 |
| E-2 | #18 | PisoWiFi OpenWrt rootfs recovery (Experiments `6d4c9b48…`) | draft, **no CI**, `integration.sh` fails, RED crash-atomicity test fails |
| E-3 | #19 | Rental OpenWrt + Android baseline | draft, **no CI**, 21/22 tests pass here (1 needs `busybox`) |
| E-4 | #1, #3–#16 | structure docs, intake guard, CORE chain | drafts, CI success on #3–#16 |

## 2. Ordered work packages

| # | Package | Type | Depends on | Output | Validation |
|---|---|---|---|---|---|
| WP-1 | Land this documentation PR for owner review | docs | none | the 7 docs in this PR | reviewer reads; no code |
| WP-2 | **Add exact-head CI to #18 and #19** (shellcheck/`sh -n`, `run_focus.sh`, Rental unittest with BusyBox installed, secret scan). Include an explicit decision on `integration.sh`: either fix the fixture/product root cause or move it to a documented KNOWN-FAIL list; do not delete it | CI | none (can run now) | workflow files on separate small PRs against #18/#19 heads | green/red recorded on the exact SHA |
| WP-3 | Root-cause `integration.sh` failure (P1-5): run it against both the original `6d4c9b48` and #18 with an `nft` mock that implements the membership read-back | bug triage | WP-2 | written finding with SHAs | reproducible command |
| WP-4 | Reconcile `core/` vs `Pisowifi/` duplicates (P1-3): diff the four overlapping files, record which fixes exist in which line | cleanup | G3 | single reconciled tree in `Pisowifi/` | existing tests from both lines pass on the merged tree |
| WP-5 | Fix case collisions in #1 (move `pisonet/`, `rental/` content to the capitalized spelling or drop the placeholders) | structural | G3 | updated #1 | `git ls-tree` case-collision check, added as a CI guard |
| WP-6 | SoftTimer: review #17 against Experiments chain M1–M4 below; **only** import missing pieces | migration | #17 review | one PR per increment | Windows CI build + source-linked synthetic tests; no hardware claims |
| WP-7 | Hardware: inventory ESP8266/ESP32 sources and the DENY-only CORE auth PRs (#252/#254); define the vendo protocol spec with test vectors | migration + contract | WP-4 | `Hardware/protocols/` + vectors | vector tests in shell and C#/C++ host builds |
| WP-8 | Shared contracts: controller signature and member bank/restore, with golden vectors consumed by PisoWiFi, SoftTimer, firmware | integration | WP-7 | `Shared/contracts/*` | each implementation passes the same vectors |
| WP-9 | EW1200G Pro profile + netns-based VLAN/profile tests (no hardware claims) | feature | WP-4 | `Pisowifi/profiles/` | namespace test results; physical compatibility **NOT claimed** |
| WP-10 | Financial invariants (#31): design and regression tests before code | design | WP-4, WP-8 | invariant spec + tests | RED test turns green only via a real fix. **Status 2026-11-11:** candidate fix on Draft PR #24 (journaled commit); CI green; NOT accepted — power-cut proof (#34), witness (#43) and QA review outstanding |

## 3. SoftTimer increments still to review (Experiments, linear chain)

Compare against #17 before importing anything; skip what #17 already contains.

| ID | Source ref (Experiments) | SHA (12) | Content | Action |
|---|---|---|---|---|
| M1 | `blazepwifi-v0.6.0-audit-foundation` | `7a32197276a2` | V2 ack verifier, V2 tests | check whether #17 includes (it contains `V2MemberServerAckVerifier.cs`) |
| M2 | `phoenix/pisonet-cts-session-atomic-v2-20261029` | `0496482a22c2` | CTS session pulse safety | diff vs #17 |
| M3 | `phoenix/pisonet-native-com-interface-20261030` | `d01fd1642c10` | native COM (#255) | #17 contains `NativeComInterfaceTransport.cs` and related; verify equivalence |
| M4 | `qa/pisonet-setupapi-hygiene-20261108` / `…validation-20261111` | `8f476ef05893` / `32028de8ebef` | SetupAPI/Win32 split (`WindowsNativeComPlatform.cs`) | **not in #17's file list** (#17 has no `WindowsNativeComPlatform.cs`); candidate import |
| — | `feature/pisonet-optional-diskless-addon-20261107` (closed #273) | `a14e8b1e0ac1` | diskless | reference only, never wholesale |

## 4. Migration record template (every PR)

Source repo + commit SHA · destination repo + branch + commit SHA · path mapping · import method (exact-byte vs derived, with blob IDs) · reason · compatibility notes · validation evidence (command, SHA, result, environment) · rollback. A failure to verify is recorded as NOT RUN / BLOCKED, never as pass.

## 5. Rollback

All work is draft and additive. Rollback = close the PR / delete the branch. Source repositories are never modified or deleted. If any step needs history rewriting, repository visibility changes or deletion, stop that step and request authorization.
