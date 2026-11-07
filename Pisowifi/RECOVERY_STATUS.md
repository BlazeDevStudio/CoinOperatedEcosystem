# Blaze PisoWiFi — recovery stage A (NONPRODUCTION)

This directory is a **partial first-party source recovery**, not a scaffold passed off as a finished product or a complete runtime.

## Verified source
- Destination: `BlazeDevStudio/CoinOperatedEcosystem`, new isolated branch `feature/pisowifi-cleanup-stabilization`, initially based on main `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- Original first-party public source repository: `BlazeDevStudio/BlazingSystems-Experiments`.
- Original immutable commit: `6d4c9b487af4d768c4d7627654d119417fcc6e00` (branch `blazepwifi-v0.6.0-audit-foundation` when inspected).
- Original project root: `experiment/openwrt/BlazePwifi/`.
- Original OpenWrt runtime root: `experiment/openwrt/BlazePwifi/openwrt/rootfs/`.
- First recovered script: `openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh`; original Git blob `3753966f3e52c04ffddbc080f04bb37e12af0e67`, originally mode `100755`.
- License: original BlazePwifi MIT LICENSE copied with its notice intact.

## Scope and limits
This stage preserves the **original** script byte-for-byte before a separate cleanup fix. No vendor firmware, private branding bundle, keys, router/site configs, balances, paid state, Windows/Pisonet, Android/Rental, Phoenix CORE or ESP firmware are imported. Other first-party code is still upstream and must be individually provenance-reviewed before migration.

Known defects to verify in separate cleanup commit: `df -Pk` available-column selection and false-success fallback on missing `/overlay`. This partial module is not a deployable image or complete feature set. No coin/credit, captive portal, networking, physical boot or payment test is asserted.

## Release gates
**Production NO-GO.** The documented upstream v0.6 train has unresolved real-money crash atomicity (#31/#32), independent antirollback witness (#43), physical hardware/durability (#34), secure signing/provisioning and migration. CI/synthetic test success must never be treated as physical acceptance. Nothing is merged, released or deployed.

## Next
Reproduce/fix the capability detector defect with source-linked mocked-`df` regression tests. Then inventory and recover the remaining PisoWiFi-only OpenWrt runtime and tests (not unrelated components) before runtime-wide cleanup or stabilization claims.
