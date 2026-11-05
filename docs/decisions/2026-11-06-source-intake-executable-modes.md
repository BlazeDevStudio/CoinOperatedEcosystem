# COE executable-mode and source-intake cleanup — 2026-11-06

## Scope and ownership

This is a **separate CoinOperatedEcosystem** review-only continuation
stacked on active [COE draft PR #12](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/12).
It does NOT rewrite the owner-controlled PR #12 daemon source, its live account
loop guard, its regression tests or the original Phoenix source owners.

An independent overlapping draft [PR #13](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/13)
was created before discovering #12. The genuinely independent corrections
were separated here; PR #13 is not to be merged in parallel.

## Root causes

The original first-party OpenWrt blobs at
`BlazeDevStudio/BlazingSystems-Experiments@c2a7515f43aff7043b0c2274dcdc097f30d7efbb`
were tracked as **mode 100755**, including:

- `experiment/openwrt/BlazePwifi/openwrt/rootfs/etc/init.d/blazepwifi`
- `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/sbin/blazepwifi-core`
- `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/config.sh`
- `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh`

Their derived destination files in the separate ecosystem were staged as
**mode 100644**. A shell-invoked test can pass while the installed
`/usr/sbin/blazepwifi-core` cannot be executed by procd. This branch
restores mode `100755` without changing the content SHA, original Git blob,
the original owners' PRs or the recorded source provenance.

The intake guard also scanned runtime files based only on known suffixes
(`.sh`, `.py`, etc.). Extensionless `usr/sbin/blazepwifi-core` and
other commands could therefore be placed under a runtime directory without
being flagged when absent from the manifest.

The new gate refuses unknown files in runtime `usr/sbin`, `usr/bin` and
`etc/init.d` directories **regardless of suffix or executable bit**, as
well as existing known-suffix sources and otherwise executable files.
Two negative fixtures prove refusal of unregistered extensionless runtime
files with both 0755 and 0644 permissions.

## Verification and boundaries

The existing `core-exec-regression` CI step now checks that all four
staged OpenWrt sources remain executable before running the original
direct-core synthetic regression from PR #12. The source-intake workflow
also runs its existing unit suite plus the two additional negative tests.

This fixes **source packaging metadata and intake coverage only**.
It does not fix TOCTOU between daemon recovery checks and individual
authorization calls, failed nft containment, live firewall state,
durable flash power-cut witness, production controller signer,
reversible accounting migration or 150-cut/30-device acceptance.

No real router, payments, release, merge, flashing, protected keys, or
third-party proprietary source are involved. `production_authorized=false`.
