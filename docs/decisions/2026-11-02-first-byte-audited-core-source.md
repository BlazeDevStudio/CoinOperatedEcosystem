# First byte-audited runtime-source migration — OpenWrt capability selector

**Source:** first-party `BlazeDevStudio/BlazingSystems-Experiments` draft PR #252,
commit `c2a7515f43aff7043b0c2274dcdc097f30d7efbb`, path
`experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh`.

**Destination:** `core/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh`.
**Original Git blob:** `3753966f3e52c04ffddbc080f04bb37e12af0e67`.
**Source/destination SHA-256:** `aabf049182fa0b25fba37be2e99cd75ac6b86c683698aea181348b3ef58c4305`.
Import method: **exact-byte copy with explicit source attribution**, not a Git-history transplant.
This does not claim the original source PR is merged, and the original repository
and review history remain authoritative.

This small standalone script was selected first because it makes **read-only**
OpenWrt hardware capability-tier decisions from memory/overlay information and
does not initialize accounting, authenticate a controller, actuate GPIO, spend
member balances or accept coins.

The source remains **verbatim** until independently verified. Newly added
`tests/capability_tiers.sh` exercises fixed profiles, automatic x86/ARM/unknown
thresholds, bad resource values, and invalid input. The negative and positive
source-intake tests are updated to include one actually staged file and to
reject file mutations or missing content. The original 5 candidate anchors
are still candidate-only and are **not** integrated or promoted.

**Potential cleanup review, not an implementation claim:** the upstream
`bp_cap_read_overlay_kb` fallback pipeline needs a separate test for a
missing `/overlay` mount; the first awk pipeline can return success with empty
stdout. Correct only in a successor review after this exact-source import is
verified, and do not silently rewrite the imported blob.

No third-party product source, production money, real-device access, paid
authority, physical hardware, secrets, signing, release or deployment.
