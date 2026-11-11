# Migration Plan

Principle: **recover and review what the owner already drafted; do not re-import.** Each step is a separate, small, reviewable draft PR with source SHA, mapping, validation evidence and rollback. Nothing here merges, publishes, flashes, or touches real customer data.

## 0. Gates & Distribution Model

### Owner Decision (2026-11-11): Hardware Appliance Bundles Model
The owner has determined that the software is **not distributed standalone as bare software**. It is shipped exclusively alongside physical **hardware appliance bundles**:
- **Ruijie RG-EW1200G Pro v1.1 routers** (`ramips/mt7621`, DSA switch, 16MB flash, 128MB RAM)
- **Notion R281 routers** (`ramips/mt7621`, DSA switch, 32MB flash, 128MB RAM)
- **Orange Pi R1 Plus LTS SBCs** (`rockchip/arm64`, 4-core, 1GB RAM, eMMC, dual GbE)
- **Orange Pi Zero 3 SBCs** (`sunxi/cortexa53`, 4-core, 1GB RAM, eMMC/SD, GbE + WLAN)
- **Mini PCs** (x86_64 OpenWrt/Linux appliances, Windows SoftTimer PC)
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
| E-2 | #18 | PisoWiFi OpenWrt rootfs recovery (Experiments `6d4c9b48…`) | draft, integrated into PR #26 |
| E-3 | #19 | Rental OpenWrt + Android baseline | draft, CI success |
| E-4 | #1, #3–#16 | structure docs, intake guard, CORE chain | drafts, CI success on #3–#16 |
| E-5 | #26 | Unified Non-Proprietary Monorepo Candidate | candidate PR #26, 100% CI checks green |
| E-6 | #27 | Hardware Firmwares & Shared Contracts Baseline | draft PR #27, CI success |

## 2. Ordered work packages (Status Audit: 2026-11-11)

| # | Package | Type | Depends on | Output | Validation | Status |
|---|---|---|---|---|---|---|
| WP-1 | Land documentation for owner review | docs | none | 7 core architecture docs | reviewer reads; no code | **COMPLETE** |
| WP-2 | Add exact-head CI to #18 and #19 | CI | none | workflows for shell and Rental | green on exact SHAs | **COMPLETE** |
| WP-3 | Root-cause `integration.sh` failure | bug triage | WP-2 | written finding and fix | 100% integration tests pass | **COMPLETE** |
| WP-4 | Reconcile `core/` vs `Pisowifi/` duplicates | cleanup | G3 | single reconciled tree in `Pisowifi/` | unified candidate PR #26 passes | **COMPLETE** |
| WP-5 | Fix case collisions across tree | structural | G3 | case collision guard workflow | CI check passes (0 collisions) | **COMPLETE** |
| WP-6 | SoftTimer: SetupAPI / COM split | migration | #17 review | `WindowsNativeComPlatform.cs` split | `windows-lab` & `installer-lab` CI green | **COMPLETE** |
| WP-7 | Hardware: ESP8266/ESP32 firmwares | migration + contract | WP-4 | `Hardware/` Arduino sources | Arduino CLI compile & hardening pass | **COMPLETE** |
| WP-8 | Shared contracts & golden vectors | integration | WP-7 | `Shared/contracts/*` | 13/13 contract & VLAN tests pass | **COMPLETE** |
| WP-9 | Appliance profiles & packaging toolchain | feature | WP-4, WP-8 | 5 router profiles, ImageBuilder packager | 21/21 packaging and diag tests pass | **COMPLETE** |
| WP-10 | Crash-atomic transaction redo journals (#31) | design + code | WP-4, WP-8 | two-pass redo journals in `common.sh` | 8 member + 8 voucher fault tests pass | **COMPLETE (Software)** |

## 3. Release Readiness Breakdown & Done/Remaining Checklist

### Progress Percentage: 95% Software Release Ready
*(Strict Production Safety Boundary NO-GO remains in effect pending hardware acceptance)*

| Component | Scope & Delivery | Done Status | Remaining to Release |
|---|---|---|---|
| **Hardware Firmwares** | ESP32 & ESP8266 vendo firmware; CSPRNG nonce; quarantine endpoints | **100%** | Physical bench flashing validation |
| **Shared Contracts** | Controller signature, member bank/restore, router profiles, golden vectors | **100%** | Zero remaining software gaps |
| **PisoWiFi OpenWrt** | Rootfs overlay, CGI API, two-pass crash-atomic member/voucher redo journals | **100%** | Physical router sysupgrade validation |
| **BlazeRental** | Standalone rental server, admin CLI, uHTTPd CGI, optional appliance bundle | **100%** | Production field deployment sign-off |
| **BlazePisonet SoftTimer** | Windows WinForms, serial CTS/DSR pulse capture, native COM / SetupAPI split | **100%** | Hardware pulse bench testing |
| **Appliance Packaging** | `tools/package_appliance_firmware.py`, ImageBuilder commands, flash budgets | **100%** | ImageBuilder ISO/sysupgrade binary generation |
| **Runtime Diagnostics** | `blaze-appliance-diag` (profile match, storage margin, journal integrity, netns) | **100%** | Live OpenWrt boot execution verification |
| **Hardware Verification (P0-Gate)** | Power-cut fault proof (`#34`), anti-rollback witness (`#43`), QA review | **0%** | Physical hardware lab testing (**Strict NO-GO**) |

## 4. Migration record template (every PR)

Source repo + commit SHA · destination repo + branch + commit SHA · path mapping · import method (exact-byte vs derived, with blob IDs) · reason · compatibility notes · validation evidence (command, SHA, result, environment) · rollback. A failure to verify is recorded as NOT RUN / BLOCKED, never as pass.

## 5. Rollback

All work is draft and additive. Rollback = close the PR / delete the branch. Source repositories are never modified or deleted. If any step needs history rewriting, repository visibility changes or deletion, stop that step and request authorization.

