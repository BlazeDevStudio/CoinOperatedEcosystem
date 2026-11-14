# PHX-RELEASE — ImageBuilder wrapper safety and operator handover

**Checkpoint:** 2026-11-15 Asia/Manila. **Status:** DRAFT / CI PENDING / PRODUCTION NO-GO.  
**Repository:** `BlazeDevStudio/CoinOperatedEcosystem`.  
**Base:** integration candidate PR #26, source HEAD `b382d233ff06c8791b1028bed3c617cc7b670d12`.  
**Branch:** `phoenix/release-imagebuilder-failclosed-20261115`.

## Canonical ownership

Only `tools/package_appliance_firmware.py`, its `tools/test_package_appliance_firmware.py` regressions, and this release-specific handover are modified. No OpenWrt networking, accounting, Android, Windows, ESP firmware or financial schema is changed. MASTER controls actual integration order; QA must independently examine source.

## Verified source defect and bounded correction

Before this patch, generated ImageBuilder wrappers accepted an absent target image directory or a directory with zero firmware outputs, printing a misleading "completed successfully" message. They searched only the top architecture directory rather than exact target/subtarget, potentially including unrelated images. Their command could pass a relative `FILES` path, then change into ImageBuilder, resolving that overlay from the wrong working directory.

The proposed nonshipping wrapper requires an existing staged rootfs, an ImageBuilder Makefile, the expected exact `bin/targets/<target>/<subtarget>` directory, and at least one real `.bin` or `.img.gz` file. It generates a sorted SHA256 manifest only after these checks. Shell argument generation uses `shlex.quote` and an absolute staging path. The generated script prints **PREVIEW**; it is not a signed, flashable, or hardware-certified release.

**Source commit:** `45d960ab68fb47ac482db27ea4047c2d67f04531`.  
**Test commit:** `35098bbd912498ffcc6459b17064bf59d6684993`.

## Tests and rollback

New disposable GNU Make fixtures cover missing target directory, empty expected directory, images in the wrong subtarget, and a successful synthetic image using a relative staging path containing spaces. Every image from these fixtures is labeled `SYNTHETIC-NOT-FIRMWARE` and must never be shipped.

**Actual test execution:** NOT YET VERIFIED on this checkpoint; no real ImageBuilder toolchain, real OpenWrt binaries, signed release or hardware acceptance claimed. Existing native compile and physical/financial P0 release gates remain unchanged.

**Rollback:** do not merge the stacked draft, or revert only the bounded release-packager commits. Never use a generated SHA256 manifest as a substitute for signed source provenance, trusted build logs, exact target identification, recovery image testing or power-cut acceptance.

**NEXT EXACT ACTION:** create stacked draft PR against PR #26, run exact-head Python tool tests and all profile staging checks, inspect failed jobs, repair only measured REDs, request QA+MASTER review before any merge or release.

## Verified CI checkpoint — 2026-11-15

The first exact-head [GitHub Actions run #43635417891](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43635417891) checked out literal code-and-handover HEAD `b602486934cccc72a7b6bc2e19617b479162f3ff` and completed **SUCCESS**. The `validate` job proves **29/29 tools test cases PASS** (including all four new synthetic wrapper cases), **18/18 Shared contract tests PASS**, and **10/10 standalone + Rental staging profiles PASS**. The ESP8266 and ESP32 Arduino CLI compile jobs also completed **SUCCESS**, uploaded separate **nonproduction** artifacts:

- ESP8266 GitHub artifact ID `14129323398`, provider-reported outer ZIP SHA256 `4b45456a067d330c265e5bdf84aa71c2163aded18a40aca8df73ca18ee69a1cd`, 2,208,745 bytes.
- ESP32 GitHub artifact ID `14129283315`, provider-reported outer ZIP SHA256 `e12465d1aa79c7d83674d80e22ec093bfb7a9f2464aae9bf22f7ea269cffd230`, 7,418,618 bytes.

[Case-collision run #43635417892](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43635417892) **SUCCESS**. These are CI-provider artifact archive digests, **not independently downloaded firmware-byte or signer verification**. No physical router flash, actual ImageBuilder produced appliance image, customer cash, power cuts, 24-hour soak or hardware acceptance occurred. Source scripts and tested Python tests remain unchanged after the exact code-head run; this checkpoint is documentation only.

**New follow-up blocker routed to MASTER/CORE/HARDWARE:** `generate_network_uci` presently emits invalid ULA prefix `fd00:db8:blaze::/48` (non-hexadecimal IPv6 segment). This release PR deliberately does not change networking or VLAN ownership. Exact target OpenWrt bridge/DSA behavior and a valid prefix require independent correction and on-device verification before a release gate. Production remains **NO-GO**.

**NEXT EXACT ACTION:** independent PHX-QA + PHX-MASTER review of this PR's manifest admission, path quoting, synthetic acceptance limits, and staged hardware migration. Require a real version-pinned OpenWrt ImageBuilder build, exact target/flash-size verification, signed provenance, rollback package, and real noncustomer hardware acceptance before production.
