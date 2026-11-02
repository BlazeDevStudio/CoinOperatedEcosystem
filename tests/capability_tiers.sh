#!/bin/sh
# Host-only, read-only regressions for the byte-identical OpenWrt capability tier source.
# Values are injected as synthetic environment; no router or payment state is used.
set -eu
SCRIPT=core/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh
sh -n "$SCRIPT"

assert_tier() {
    expected="$1"; shift
    got="$(env -i PATH="$PATH" "$@" sh "$SCRIPT" --detect)" || {
        echo "capabilities executable failed for $expected" >&2; exit 1;
    }
    [ "$got" = "$expected" ] || {
        echo "expected $expected; got $got" >&2; exit 1;
    }
}
assert_tier full BP_CAP_TIER=full
assert_tier standard BP_CAP_TIER=standard
assert_tier lite BP_CAP_TIER=lite
assert_tier full BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=1048576 BP_CAP_OVERLAY_KB=524288
assert_tier standard BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=262144 BP_CAP_OVERLAY_KB=65536
assert_tier lite BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=262143 BP_CAP_OVERLAY_KB=65536
assert_tier lite BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=1048576 BP_CAP_OVERLAY_KB=65535
assert_tier standard BP_CAP_TIER=auto BP_CAP_ARCH=aarch64 BP_CAP_MEM_KB=262144 BP_CAP_OVERLAY_KB=65536
assert_tier lite BP_CAP_TIER=auto BP_CAP_ARCH=arm64 BP_CAP_MEM_KB=262143 BP_CAP_OVERLAY_KB=65536
assert_tier lite BP_CAP_TIER=auto BP_CAP_ARCH=mips BP_CAP_MEM_KB=2097152 BP_CAP_OVERLAY_KB=2097152
assert_tier lite BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=not-a-number BP_CAP_OVERLAY_KB=524288
assert_tier lite BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=1048576 BP_CAP_OVERLAY_KB=-1
if env -i PATH="$PATH" BP_CAP_TIER=invalid sh "$SCRIPT" --detect >/dev/null 2>&1; then
    echo "invalid forced tier was accepted" >&2; exit 1
fi
if sh "$SCRIPT" --unknown >/dev/null 2>&1; then
    echo "unknown argument was accepted" >&2; exit 1
fi
echo "COE CORE CAPABILITY BASELINE PASS: exact first-party source, synthetic tier/threshold tests only"
