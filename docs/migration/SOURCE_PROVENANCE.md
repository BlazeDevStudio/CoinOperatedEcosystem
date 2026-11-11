# Source Provenance

Read-only inventory taken 2026-11-11 (UTC) with an authenticated `gh` session as `BlazeDevStudio`. Default-branch HEAD SHAs were read from the remote, not from local clones.

## 1. Repository inventory (owner `BlazeDevStudio`, all PUBLIC, default branch `main`)

| Repository | Default HEAD | Branches | Open PRs | Role for this project |
|---|---|---:|---:|---|
| CoinOperatedEcosystem | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | 27 | 18 | **Destination** monorepo (only 2 files on `main`) |
| BlazingSystems-Experiments | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | 343 | 72 | **Historical** source for BlazePwifi, Rental, SoftTimer. Not a permanent production source |
| BlazingSystems-Labs | `5d8e4f1d95b6bfc551996634df9c6f7b86af56b4` | 9 | 0 | Hardware lab: `embedded/blaze-pisonet-timer-public`, `blaze-pisonet-universal` |
| BlazingSystems-Archives | `c31d38b335b13456f5f208aca52bdf73b796561d` | 2 | 0 | Archived Pisonet timer history notes |
| BlazingSystems-Projects | `c1c10fdc167fba2ff278447f25aeac2ef95d4b7a` | 2 | 0 | Portfolio |
| BlazingSystems | `e89167f0fa23bcab1f2ae7655b6813eda2f41d12` | 3 | 1 | Policy + portfolio docs (cloud artifact policy) |
| Forked-Projects | `481c3b18d8be6e34391ca5d69ebc2a089b81d639` | 3 | 1 | NRSuite ESP8266/ESP32 ports (hardware reference) |
| samdenty-esp32-port | `de09785562fe1d90a421e873c0db84960cfca37e` | 1 | 0 | ESP32 port (not audited) |
| BlazeMCU | `ef942d1e8f59621a5f86a53723862e0065088702` | 2 | 1 | **Separate product** (MCU), not part of this ecosystem |
| BlazeMCUstudio | `cbb64a690919eea1f76c768edc93bd04c58e9f0f` | 9 | 8 | **Separate product**, do not merge |
| BlazeMessenger | `27831493f705cf39e97ad0cfa7d536109b245de9` | 21 | 20 | Separate product (LAN Messenger) |
| AndroidDevel | `6b051faeabcbe8e621549dd9ba821c8bcb642c43` | 3 | 2 | Separate |
| B-Secure | `e5da83c545f5372f7c9b867b205da4789e97ce7a` | 2 | 1 | Separate |
| Blaze-Ultimate-Optimizer | `d89a4352b92361eb06cc8d49c13082566668beb3` | 4 | 2 | Separate |
| BlazeDevStudio.github.io | `44b09a8fb896a3287b4d839b9d8c4a497ad42916` | 1 | 0 | Site |
| BlazeExeCute | `f3d0e73cb42abb335a104bc86def9f2358eeb85e` | 1 | 0 | Separate |
| BlazeFM | `83f76793ef149ed4b17483a89f3e9f3a3ac4f494` | 2 | 1 | Separate |
| BlazeNetMonitor | `40c692275bf72b7fc24d597befadec12df7bba4f` | 2 | 1 | Separate |
| BlazeUnifiedElSim | `70f18d55da3cdd20efaf39993cd681a0247c038d` | 2 | 1 | Separate |
| BlazeWeb | `2347c8faf4a62a80ba923f2011c88119388874fc` | 1 | 0 | Separate |
| EasyMode | `9926b9b356b3514fe0d507ad4acf609be6fe6cfc` | 1 | 0 | Separate (also copied into Experiments `easymode-project`) |
| ThreadHarbor | `ad6a614c2bc35ea5ea323724ddd64d311c7f5c5d` | 2 | 1 | Separate |
| BCR-Repository | *(empty repository)* | 0 | 0 | Empty |

Not a GitHub owner: `BlazingSystems` (old name used inside policy documents; API returns not found).

## 2. Canonical source per product

| Product | Canonical implementation (as of this audit) | Historical / duplicates | Confidence |
|---|---|---|---|
| **SoftTimer** | **Destination:** CoinOperatedEcosystem PR #17 `pisonet/softtimer-foundation-20261107` @ `24e9cfa02e…`, pinned to Experiments `21b065535640a735a1e22bda57718b9e8ad86a1a` (PR #255 stack) plus fail-closed fixes. **Upstream release:** Experiments `main` v0.4.0 (tree `6e69b3e7d6c94a498d7a936f987296f44b143b19`, 89 branches share it) | Experiments branches in the chain below; closed #273 diskless branch (`a14e8b1e0ac1…`, reference only); closed CoinOperatedEcosystem PR #20 branch (v0.4.0, reference only) | High for lineage; **no dedicated SoftTimer repo exists** |
| **BlazePwifi / PisoWiFi** | Experiments branch `blazepwifi-v0.6.0-audit-foundation` (draft PR #30 in Experiments per its handover). Recovery in CoinOperatedEcosystem PR #18 from Experiments `6d4c9b487af4d768c4d7627654d119417fcc6e00` | Experiments `main` (stale snapshot, `VERSION` 0.5.3-dev.5); `core/openwrt` in the #3–#16 stack (diverged copy) | Medium: two live recovery lines (P1-3) |
| **BlazeRental** | Rental recovery PR #19 @ `fcc8f8c9bc2fa50666aa7c5e94e48137fa01b379`; upstream `experiment/openwrt/Rental-Server-Standalone` (v0.1.2) and `BlazePwifi/android/BlazeRental*` | Experiments branch `fix/rental-standalone-entropy` (newer standalone fixes; 6 distinct trees of that path across 332 branches) | Medium |
| **Hardware** | Experiments `BlazePwifi/esp8266`, `esp32`; Labs embedded projects; Forked-Projects NRSuite | Experiments PRs #252/#254 (ESP32 CORE auth, DENY-only) | Low (not audited) |
| **CORE** | CoinOperatedEcosystem #3–#16 | overlaps #18 | Medium |

## 3. SoftTimer lineage (verified, `BlazingSystems-Experiments`)

All tips below share merge base `8af76924` with `main`; `main` is behind by 22 commits and the tips are 1898–2054 commits ahead (the Experiments `main` branch is a curated line that does not contain them). Ancestry verified with `git merge-base --is-ancestor`:

| Tip | SHA (12) | SoftTimer files | Notes |
|---|---|---:|---|
| `main` (v0.4.0 per `csproj`/release notes) | `f4e8a891aed8` | 32 | tree `6e69b3e7…` |
| `blazepwifi-v0.6.0-audit-foundation` | `7a32197276a2` (live tip; PR #18 pins ancestor `6d4c9b487af4`, **20 commits behind** this tip) | 44 | adds V2 ack verifier + 3 test projects |
| `phoenix/pisonet-cts-session-atomic-v2-20261029` | `0496482a22c2` | n/a | 212 commits ahead of the previous row |
| `phoenix/pisonet-native-com-interface-20261030` (PR #255) | `d01fd1642c10` | 68 | native COM transport/capture |
| `qa/pisonet-setupapi-hygiene-20261108` (PR #279) | `8f476ef05893` | 68 | behavior-preserving SetupAPI extraction |
| `qa/pisonet-setupapi-validation-20261111` | `32028de8ebef` | 68 | + CI-only commit |
| `cleanup/phoenix-softtimer-theme-readability-20261031` (PR #265) → `…timer-accounting-invariants-20261102` (PR #268), `qa/phoenix-parallel-pinned-labs-20261102` (PR #267) | `b20895064ce8`, `da5e4bd8d0e9`, `ff5367990c2d` | 68–69 | side branches, not ancestors of the tips above |
| `feature/pisonet-optional-diskless-addon-20261107` (closed PR #273) | `a14e8b1e0ac1` | 83 | reference only, **do not merge** |

## 4. CoinOperatedEcosystem PR stack (heads read from the remote)

| PR | Head SHA (10) | Base | CI (exact head) | Content |
|---|---|---|---|---|
| #1 | `3b84c75227` | main | none | structure + dependency map docs (lowercase dirs) |
| #3 | `84f0d32159` | `branding/logo-v2-authority-anchor` (closed #2; descends from #1) | success ×1 | clean-source-intake guard + branding |
| #4–#16 | `2ee1de6276` … `d537b30f67` | previous PR head | success ×6 … ×15 | CORE: capability tiers, config transactions, boot preflight, nft authorization readback |
| #13 | `91c88b4d5d` | #11 head | success ×15 | marked SUPERSEDED, do not merge |
| #17 | `24e9cfa02e` | main | success ×2 | `Pisonet/SoftTimer` |
| #18 | `eef173286c` | main | **none** | `Pisowifi/` |
| #19 | `fcc8f8c9bc` | main | **none** | `Rental/` |

Because #1–#16 were cut from the initial commit, their branches do not contain `main`'s `a6513ab` (`Pisonet/README.md`).

## 5. Provenance of this audit's own artifacts

| Artifact | Detail |
|---|---|
| Closed PR #20 | `migration/pisonet-softtimer-v0.4.0-baseline-20261111` @ `27a94f1f3e09d96a62bf8773c2ee239788de06c1`; byte-identical import (tree `6e69b3e7…`) of Experiments `main` `f4e8a891…`; **closed as a duplicate of #17**; branch retained unmodified as reference; do not merge |
| Local scratch | blobless mirror of Experiments in `/tmp` (not part of the repo; no source copied elsewhere) |

## 6. Blocked or not established

- **Private Drive registries** (`BLAZE_PROJECT_REGISTRY`, `BLAZE_ARTIFACT_MANIFEST`, `BLAZE_SYNC_LEDGER`): **BLOCKED** (no Drive connector). No artifact was created or stored.
- Experiments' other 330+ branches and 72 PR bodies were classified by name and ancestry only, not read individually.
- Whether other repos duplicate Ecosystem source (e.g. `BlazingSystems-Labs` Pisonet timer) beyond naming: **NOT ESTABLISHED**.
- A private repository for restricted code: **not created**; awaiting owner decision on P0-1.
