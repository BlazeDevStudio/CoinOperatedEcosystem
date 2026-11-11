# Blaze PisoWiFi — evidence-based Phase Zero inventory (2026-11-08)

**Classification:** limited read-only audit of the original OpenWrt runtime plus one isolated, tested capability-detector cleanup. This is NOT a whole-product code audit, runtime migration, production authorization or hardware acceptance.

## Verified routing and provenance
- Destination `BlazeDevStudio/CoinOperatedEcosystem` (PUBLIC), default `main`, verified original HEAD `a6513ab4412b4c014eee2863e45cbe32d06cb243`, with no `Pisowifi/` on `main`.
- Scoped destination branch `feature/pisowifi-cleanup-stabilization`, changes exclusively `Pisowifi/**`; Pisonet unchanged.
- Historical first-party public source `BlazeDevStudio/BlazingSystems-Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00`, directory `experiment/openwrt/BlazePwifi`, MIT license. Original rootfs tree `f4a923aaacf1374e90c7bab5f335efe6c6ec55cf` contains 61 files (including shell/uHTTPd CGI, configs, portal assets and vendor license material). Original source also contains builds, installer, tests, Android/ESP/rental components that are **not** automatically eligible for this project's isolated recovery.
- Source `openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh` imported in Stage A byte-for-byte, original blob `3753966f3e52c04ffddbc080f04bb37e12af0e67`, executable mode `100755`; MIT license source blob `1ee55b94183417be977ca287cd7391f9a6f7e721` preserved.

## P0 — Critical / no deployment
1. **Destination completeness (verified):** no complete PisoWiFi runtime, captive portal, session/credit persistence, installer, or whole-product regression suite recovered under `Pisowifi/`. Deployment is not possible.
2. **Financial integrity (upstream documented unresolved):** original v0.6 audit identifies #31/#32 paid crash-atomic custody, #43 independently protected antirollback witness, #34 physical durability, and signing/migration acceptance as NO-GO. No current independent device test was executed.
3. **Firewall authorization safety (source-observed, regression still needed):** source `common.sh` around original line 280 suppresses `nft add/delete element` errors with `|| true`. Original `blazepwifi-core` deletes its live nft table before `nft -f` reinstalls it, and its unsynchronized-time path ignores nft flush errors. Error handling, packet-path isolation and restart windows need fail-closed source-linked tests before any field use. No exploitability or live bypass has been proven here.
4. **Publication boundary (verified):** both source and destination GitHub repositories are PUBLIC. Only already-public MIT-licensed source code was imported in this branch; never import confidential credentials, private artwork, customer records, site configs or undisclosed proprietary materials.

## P1 — Important
1. **Capability-tier free-space classification — fixed in this branch:** original `capabilities.sh` read `df -Pk` column 2 (total blocks), not column 4 (available blocks), and piped to `awk` in a way that reported success with no data when `/overlay` was missing. This could overprovision resource-starved OpenWrt targets or underprovision a fallback-only target.
2. **Config apply trust (source-observed, not yet changed):** original `config.sh` executes an environment-selected `BP_CONFIG_APPLY_HOOK` via `sh -c`; review control of this input and remove string-executed hooks under the PisoWiFi-only code after full intake.
3. **Configuration crash/race recovery (source-observed, not yet changed):** original `bp_config_set` uses UCI set/commit/apply then best-effort restore with masked errors; independent consistency and interruption tests are required before copying it or enabling admin changes.
4. **Source identity and branch divergence:** `BlazingSystems-Experiments/main` and `blazepwifi-v0.6.0-audit-foundation` are divergent. The original PR #30 is closed as a draft, while other open draft branches and separate COE CORE PRs exist. Do not blindly merge, cherry-pick, or mistake synthetic CI for deployed behavior.

## P2 — Improvement
1. Keep tests independent and bounded so Lite-router code can be checked without x86, Node or Android dependencies.
2. Build an allowlist/intake manifest for each remaining original PisoWiFi-only file, preserving executable bits, licenses, content hashes, dependencies and release gates.
3. Consolidate historical handover and source maps without deleting prior audit history; avoid duplicate refactors already proposed in non-PisoWiFi PRs.

## Isolated cleanup and repeatable regression evidence
- Stage A exact original source+license+scope commit: `b1b9d38dfc3c6865ac727341c36c8fc645073956`.
- Stage B separate cleanup/test commit: `2eb8cf9bb310c919f81caa6367679d9ddbe273e8`.
- Modified runtime source: `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh`, new blob `098eafbe06193ff1ea7b4fc7e3bf4ae3b7b3e4cd`.
- New executable source-linked test: `Pisowifi/tests/capabilities.sh`, blob `542c68807b29fdd67bb1220b61e343daf5db88dd`.
- Local disposable shell test **before fix: FAIL** (`mode=low expected=lite actual=full`), using the verified upstream blob.
- Local disposable shell tests **after fix: PASS** for low free space -> Lite, high -> Full, missing `/overlay` -> Standard via `/`, malformed available -> fallback Standard, both mounts unavailable -> Lite, explicit Standard tier, and invalid-tier rejection; syntax check also PASS. All tested file Git blob hashes match the two committed Stage B Git blobs exactly.
- Tests are isolated fake-`df` shell simulations. **Not** OpenWrt ImageBuilder compilation, CI, real WAN/VLAN/nft, coin, power-cut, or hardware acceptance. GitHub Actions workflow runs on the exact Stage B commit: **0**, so CI status remains **NOT RUN**.

## Next gate
Recover and provenance-check the minimum complete PisoWiFi-only OpenWrt runtime and its original tests under `Pisowifi/**`, determine an authoritative source baseline from current owners' source/branches, then independently reproduce and contain the source-observed nft/config P0 risks before credit/session stabilization and any feature work. Source in other folders and unapproved merges/releases remain untouched.
