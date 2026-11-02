# CORE OpenWrt capability detection: one bounded, original-source cleanup

Source: owner first-party `BlazeDevStudio/BlazingSystems-Experiments` PR #252,
commit `c2a7515f43aff7043b0c2274dcdc097f30d7efbb`.
Path: `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh`.
Original Git blob `3753966f3e52c04ffddbc080f04bb37e12af0e67`;
original SHA-256 `aabf049182fa0b25fba37be2e99cd75ac6b86c683698aea181348b3ef58c4305`.
Reviewed COE source path `core/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh`,
SHA-256 `0c610c67e3fc0ba7c867df9434517b0645d88a146b78ee5cf8cb4f5bc3fd387d`.

## Root cause and source correction

The legacy disk-space detector looked at `df -Pk` column 2 (TOTAL blocks),
not column 4 (AVAILABLE blocks), incorrectly upgrading a nearly-full device.
Its `df /overlay | awk ... || df /` pipeline skipped the root fallback when
awk succeeded with zero output on a missing mount. The isolated function now
tries `/overlay` and then `/`, accepts only numeric available-space data,
and conservatively returns failure/zero classification if neither is readable.

No other tier, authentication, money, payment ledger, GPIO, interface or
hardware logic was changed. Synthetic df mocks run low-space, missing-mount,
full-space and no-mount regressions. The offline guard distinguishes an exact
staged source from a reviewed refactor using original + destination hashes and
this required review note; a separate CI job fetches the exact original
first-party commit and verifies its blob and SHA-256 independently.

No external licensed code was copied. No customer release, real payment,
signing, keys, physical device, flashing, production merge or deployment.
