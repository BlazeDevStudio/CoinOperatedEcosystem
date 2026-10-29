# Phoenix Migration Manifest

**Date:** 2026-10-28  
**Destination:** `BlazeDevStudio/CoinOperatedEcosystem`  
**Original untouched base:** `main@b0b0ebc27fbb8cbe9bb36e1d075a132060a819d0`  
**Stage:** destination structure plus a provenance-pinned branding reference; **NO application source files copied**.  
**Status:** STRUCTURE_CREATED; finance and hardware production NO-GO.

## Candidate paths needing exact source selection

| Old repository path | Proposed destination | SHA and PR verification |
| --- | --- | --- |
| `BlazeDevStudio/BlazingSystems-Experiments/experiment/openwrt/BlazePwifi/` | `core/` | Pending branch selection and dependency audit |
| `BlazeDevStudio/BlazingSystems-Experiments/experiment/openwrt/BlazePwifi/android/` | `rental/` | Pending signed-lease and Android PR reconciliation |
| `BlazeDevStudio/BlazingSystems-Experiments/experiment/windows/BlazePisonet-SoftTimer/` | `pisonet/` | Pending native serial and signing PR reconciliation |
| `BlazeDevStudio/BlazingSystems-Experiments/experiment/openwrt/BlazePwifi/esp8266/` | `controllers/esp8266/` | Pending protected-freshness and hardware evidence |
| `BlazeDevStudio/BlazingSystems-Experiments/experiment/openwrt/BlazePwifi/esp32/` | `controllers/esp32/` | Pending protected-freshness and hardware evidence |
| Shared APIs/receipts/protocols | `contracts/` | Identify authoritative revision and consumers |
| Existing native and integration fixtures | `integration-tests/` | Preserve original source-linked test identity and provenance |
| `BlazeDevStudio/BlazingSystems@8b08add6:branding/Logo-V2/` | `branding/Logo-V2/` | Exact reference/hash selected; runtime asset integration remains pending |

## Mandatory import record per batch

Record (1) original owner/repository/path/ref/full commit SHA, (2) all dependent draft PRs and base/head SHAs, (3) file paths and Git blob SHA/checksum, (4) destination commit SHA, (5) import/rename method and historical attribution, (6) build/import path changes, (7) exact executed CI run and artifact links, (8) independent QA decision and release gate. Do **not** claim Git history preservation from a plain file copy; the original repository and commits remain accessible, while copied files need explicit attribution.

## Safety and workflow holds

No original source or PR is deleted, closed, rebased, force-pushed, or merged by this migration. There are no executable workflows in this destination staging commit. Workflow isolation follows source import and test coverage mapping; signing, financial authority, fail-closed firmware behavior and source-to-artifact provenance cannot be weakened.
