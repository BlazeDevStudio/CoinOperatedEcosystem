# Current State — Blaze Coin Operated Ecosystem

**Audit date:** 2026-11-11 (UTC) · **Basis:** live GitHub state read with an authenticated `gh` session as `BlazeDevStudio`. Every SHA below was read from the remote at audit time. Anything not listed as *verified* is *not verified*.

## 1. Headline facts

1. `CoinOperatedEcosystem` `main` (`a6513ab4412b4c014eee2863e45cbe32d06cb243`) contains **only** `README.md` and `Pisonet/README.md`. **All real work lives in 18 open, unmerged draft PRs** (stacked), so the repository's default branch is not a usable baseline.
2. **No standalone SoftTimer repository exists** under `BlazeDevStudio`. Every SoftTimer copy is in `BlazingSystems-Experiments` (branches) or in draft PR #17 here.
3. `BlazingSystems-Experiments` `main` (`f4e8a891…`) is **not** the current implementation of BlazePwifi. Its own `PROJECT_HANDOVER.md` routes to branch `blazepwifi-v0.6.0-audit-foundation`. `main` has diverged from that branch (it is not an ancestor; `main` is 22 commits behind and the branch is 1874 commits ahead of their merge base `8af76924`).
4. All 23 repositories under `BlazeDevStudio` are **PUBLIC**. There is **no private repository** for restricted material.
5. The owner directive classifies BlazePwifi as proprietary, but the public sources ship it under an MIT `LICENSE` and describe it as "open-source". See audit finding **P0-1**.
6. The owner-private Drive registry files named in the repo policy (`BLAZE_PROJECT_REGISTRY`, `BLAZE_ARTIFACT_MANIFEST`, `BLAZE_SYNC_LEDGER`) could **not** be read in this session (no Drive connector). Status: **BLOCKED**.

## 2. Products and their real state

| Product | Language / platform | Source of truth today | Open work here | Status | Production |
|---|---|---|---|---|---|
| **Blaze PisoWiFi** (OpenWrt captive portal, vouchers, sessions, coin vendo API) | POSIX sh/BusyBox CGI, uhttpd, UCI, nftables | Historical: Experiments `blazepwifi-v0.6.0-audit-foundation` (not `main`). Recovery: PR #18 `feature/pisowifi-cleanup-stabilization` @ `eef173286cb6cc1320f0f9e234a7b7cc701424a3` | #18 (`Pisowifi/`), plus overlapping CORE chain #3–#16 (`core/openwrt/`) | **CLEANUP / RECOVERING** | **NO-GO** |
| **BlazeRental** (OpenWrt rental server + Android status controller) | POSIX sh + openssl HMAC; Java/Android | Experiments `experiment/openwrt/Rental-Server-Standalone` (v0.1.2, R281-pinned) and `BlazePwifi/android/BlazeRental*`; recovery: PR #19 @ `fcc8f8c9bc2fa50666aa7c5e94e48137fa01b379` | #19 (`Rental/`) | **RECOVERING** (preview) | **NO-GO** |
| **BlazePisonet SoftTimer** (Windows coin-operated PC timer) | C# .NET 8 WinForms, serial CTS/DSR, NSIS | Released v0.4.0 = Experiments `main`; newer = linear draft chain ending at PR #255/#279; baseline of that chain in PR #17 @ `24e9cfa02e…` | #17 (`Pisonet/SoftTimer/`) | **MIGRATING** | **NO-GO** |
| **Hardware** (ESP8266/ESP32 vendo and timer firmware) | Arduino C++ | PR #27 (`Hardware/esp32`, `Hardware/esp8266`); Labs standalone timers; Experiments PR #283 | PR #27 (`Hardware/`), Candidate PR #26 | **RECOVERING** (CI green) | **NO-GO** |
| **CORE (COE-CORE)** (capability tiers, config transactions, nft authorization) | POSIX sh | PRs #3–#16 chain (head `d537b30f67…`) | #3–#16 | **DEVELOPING** (drafts, CI green per PR) | **NO-GO** |
| **Shared contracts / accounting** | JSON Schema, golden vectors | PR #27 (`Shared/contracts/`); PR #24 (`member_txn_journal.sh`) | PR #27 (`Shared/`), Candidate PR #26 | **ESTABLISHED** (CI green) | **NO-GO** |
| **Deployment / packaging** | Python 3, OpenWrt ImageBuilder, POSIX sh | `tools/package_appliance_firmware.py`, `tools/validate_all_profiles.py`, `Shared/contracts/router-profile/profiles/`, `Pisowifi/openwrt/rootfs/usr/sbin/blaze-appliance-diag` | PR #26 (Candidate Monorepo) | **OPERATIONAL** (10 profiles, CI green) | **NO-GO** |

## 3. Interaction model (verified by reading source and docs)

- **Coin → credit path (PisoWiFi):** ESP vendo controller → HTTP `POST …/cgi-bin/vendo` with form fields `action,id,nonce,pulses,target,sig` → OpenWrt CGI validates signature and nonce → accounting writes `members.tsv` / `member-events.tsv` / `vouchers.tsv` via **crash-atomic two-pass transaction redo journals** (`member-txn.commit`, `voucher-txn.commit`) → nftables per-MAC authorization.
- **SoftTimer ↔ PisoWiFi:** `BlazePwifiClient` posts to the same vendo CGI using the BlazePwifi controller signature contract; banks/restores member time; peer-to-peer "Centralized" mode uses HMAC-SHA256 with timestamp, nonce cache and event-id dedup over plain HTTP on a LAN port.
- **SoftTimer ↔ hardware:** exact-device serial/USB-RS232 CTS/DSR pulse input; optional ESP timer bridge over HTTP (`http://192.168.4.1/` default).
- **Rental:** Android client enrolls with a one-time token and authenticates with HMAC-SHA256 against `/cgi-bin/rental`; PR #19 baseline is "local-router CLI grants only; Android reads status, cannot enforce". Turnkey appliance packager supports optional `--include-rental` overlay bundling.
- **Independence rule from the repos' own docs:** SoftTimer must not require BlazePwifi/Rental/diskless; Rental and PisoWiFi are independent products.

## 4. Verification state of this audit

| Evidence | Exact subject | Result |
|---|---|---|
| Repo list, visibility, default branch, HEAD SHAs | 23 repos | recorded in `SOURCE_PROVENANCE.md` |
| Branch and PR inventory | Experiments (343 branches, 72 open PRs); CoinOperatedEcosystem (27 branches, 18 open PRs) | recorded |
| Ancestry of SoftTimer chain | Experiments, `git merge-base --is-ancestor` | linear chain confirmed (see provenance) |
| CI check-runs on candidate PR #26 | All 5 module workflows + case collision guard | **100% SUCCESS / PASS** (all checks green) |
| Shell syntax + focused tests | PR #26 HEAD | 21/21 focused suites PASS in POSIX `sh` and BusyBox `ash` |
| Python/Java Rental tests | PR #26 HEAD | 23/23 tests PASS (with openssl/Java 17) |
| .NET compile + Windows CI | SoftTimer WinForms (.NET 8) | **CI PASS** in `windows-lab` and `installer-lab` |
| Arduino Firmware compile | ESP32 and ESP8266 Vendo Firmwares | **CI PASS** in `hardware-ci.yml` |
| Appliance Packaging & Diag | ImageBuilder packaging and `blaze-appliance-diag` | **25/25 tests PASS** in `tools/test_*.py` |
| End-to-End Appliance Staging | 10 Hardware Profiles (Standalone & Rental) | **10/10 PASS** in `tools/validate_all_profiles.py` |

## 5. Not audited in this pass

Android sources (`BlazeRentalLauncher`, ~965 files), EasyMode, the other 20 repositories beyond inventory, the 72 Experiments PR bodies individually, Windows runtime behavior on physical client PCs, physical hardware power-loss testing on real router devices.

## 6. Status Addendum — 2026-11-11 (Hardware Appliance Bundles Architecture, Candidate PR #26)

1. **Hardware Firmwares Migrated (PR #27 & PR #26):** ESP32 (`Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`) and ESP8266 (`Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`) firmwares are housed natively within `CoinOperatedEcosystem` with setup quarantine endpoints (`/quarantine`, `/quarantine/clear`), server response signature verification, and fresh CSPRNG nonces. Arduino CLI CI workflow `.github/workflows/hardware-ci.yml` compiles both targets and validates firmware hardening in CI.
2. **Shared Contracts Established:** Inter-product contract specifications and golden vectors are located at `Shared/contracts/controller-signature/`, `Shared/contracts/member-bank-restore/`, and `Shared/contracts/router-profile/` with JSON schemas and automated Python validation (`Shared/tests/test_shared_contracts.py`, `test_router_profiles.py`, `test_vlan_isolation.py`). All 18 tests pass across 10 hardware profiles.
3. **Turnkey Hardware Appliance Bundles Model:** Per owner direction, software is not distributed standalone; it is shipped pre-flashed/installed alongside physical hardware bundles (Ruijie RG-EW1200G Pro v1.1, Notion R281, TP-Link Archer C6 v3, GL.iNet GL-MT1300, Orange Pi R1 Plus LTS, Orange Pi Zero 3, Raspberry Pi 4B, Xiaomi Mi Router 4A Gigabit, NanoPi R2S, x86_64 Mini PCs). All appliance components are unified in this monorepo.
4. **Appliance Packaging Toolchain:** `tools/package_appliance_firmware.py` and `tools/validate_all_profiles.py` provide automated ImageBuilder profile generation and rootfs overlay staging across all 10 hardware profiles, enforcing strict flash memory margins, DSA switch VLAN isolation, and optional Rental module bundling (`--include-rental`).
5. **Runtime Appliance Diagnostics:** `Pisowifi/openwrt/rootfs/usr/sbin/blaze-appliance-diag` provides invariant verification on boot (profile matching, overlay storage margin >= `min_free_overlay_kb`, journal integrity, and network bridge detection), outputting human-readable and JSON statuses. Tested across 6 cases in `tools/test_appliance_diag.py`.
6. **Crash-Atomic Redo Journaling (Issue #31):** Two-pass redo journals are fully implemented in `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/common.sh` for both member balances and voucher redemptions (`bp_member_txn_*` and `bp_voucher_txn_*`), with fail-closed digest checking and zero partial writes on fault.
7. **Production Gate Notice:** Production admission remains strictly **NO-GO** across all components pending independent durable witness and physical hardware power-cut testing.


