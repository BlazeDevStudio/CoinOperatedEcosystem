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
| **Deployment / packaging** | n/a | none in primary repo; legacy `installer/`, `tools/` inside BlazePwifi | none | **not started** | **NO-GO** |

## 3. Interaction model (verified by reading source and docs)

- **Coin → credit path (PisoWiFi):** ESP vendo controller → HTTP `POST …/cgi-bin/vendo` with form fields `action,id,nonce,pulses,target,sig` → OpenWrt CGI validates signature and nonce → accounting writes `members.tsv` / `member-events.tsv` (text files; **not one crash-atomic transaction**, tracked as Experiments issue #31) → nftables per-MAC authorization.
- **SoftTimer ↔ PisoWiFi:** `BlazePwifiClient` posts to the same vendo CGI using the BlazePwifi controller signature contract; banks/restores member time; peer-to-peer "Centralized" mode uses HMAC-SHA256 with timestamp, nonce cache and event-id dedup over plain HTTP on a LAN port.
- **SoftTimer ↔ hardware:** exact-device serial/USB-RS232 CTS/DSR pulse input; optional ESP timer bridge over HTTP (`http://192.168.4.1/` default).
- **Rental:** Android client enrolls with a one-time token and authenticates with HMAC-SHA256 against `/cgi-bin/rental`; PR #19 baseline is "local-router CLI grants only; Android reads status, cannot enforce".
- **Independence rule from the repos' own docs:** SoftTimer must not require BlazePwifi/Rental/diskless; Rental and PisoWiFi are independent products.

## 4. Verification state of this audit

| Evidence | Exact subject | Result |
|---|---|---|
| Repo list, visibility, default branch, HEAD SHAs | 23 repos | recorded in `SOURCE_PROVENANCE.md` |
| Branch and PR inventory | Experiments (343 branches, 72 open PRs); CoinOperatedEcosystem (27 branches, 18 open PRs) | recorded |
| Ancestry of SoftTimer chain | Experiments, `git merge-base --is-ancestor` | linear chain confirmed (see provenance) |
| CI check-runs on PR heads | CoinOperatedEcosystem #1,#3–#19 | #3–#17 success; **#1, #18, #19 have none** |
| Shell syntax + focused tests | #18 @ `eef173286c…` | see `CODEBASE_AUDIT.md` §3 |
| Python/Java Rental tests | #19 @ `fcc8f8c9bc…` | see `CODEBASE_AUDIT.md` §3 |
| .NET compile | SoftTimer v0.4.0 (`f4e8a891…`), SDK 8.0.428 on Linux, `-warnaserror` | 0 warnings / 0 errors (**compile only, not a Windows run**) |

## 5. Not audited in this pass

Android sources (`BlazeRentalLauncher`, ~965 files), EasyMode, the other 20 repositories beyond inventory, the 72 Experiments PR bodies individually, EW1200G Pro OpenWrt support and VLAN/profile design, Windows runtime behavior, physical hardware.

## 6. Status Addendum — 2026-11-11 (Hardware & Shared Migration, Candidate PR #26, PR #27)

1. **Hardware Firmwares Migrated (PR #27):** ESP32 (`Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`) and ESP8266 (`Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`) firmwares are now housed natively within `CoinOperatedEcosystem` with setup quarantine endpoints (`/quarantine`, `/quarantine/clear`), server response signature verification, and fresh CSPRNG nonces. Arduino CLI CI workflow `.github/workflows/hardware-ci.yml` compiles both targets and validates firmware hardening in CI.
2. **Shared Contracts Established (PR #27):** Inter-product contract specifications and golden vectors are now located at `Shared/contracts/controller-signature/` and `Shared/contracts/member-bank-restore/` with JSON schemas and automated Python validation (`Shared/tests/test_shared_contracts.py`).
3. **Non-Proprietary Integration Candidate (PR #26):** Combines `docs/`, `Rental/`, `Pisonet/SoftTimer/`, `Hardware/`, `Shared/`, and `tools/` into a single unified candidate tree on branch `integration/ecosystem-nonproprietary-candidate-20261111` targeting `main`. Proprietary `Pisowifi/` remains held on Draft PR #18 / PR #24 in accordance with the P0-1 privacy boundary.
4. **Production Gate Notice:** Production admission remains strictly **NO-GO** across all components.
