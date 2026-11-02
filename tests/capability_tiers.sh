#!/bin/sh
# Host-only, read-only regressions for the reviewed and provenance-pinned OpenWrt source.
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

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
cat > "$TMP/df" <<'MOCK'
#!/bin/sh
case "$DF_SCENARIO:$*" in
 'missing:-Pk /overlay') exit 1 ;;
 'missing:-Pk /') printf 'Filesystem 1024-blocks Used Available Use%% Mounted\n/dev/root 1048576 655360 393216 63%% /\n';;
 'low:-Pk /overlay') printf 'Filesystem 1024-blocks Used Available Use%% Mounted\n/dev/overlay 2097152 2080768 16384 99%% /overlay\n';;
 'low:-Pk /') printf 'Filesystem 1024-blocks Used Available Use%% Mounted\n/dev/root 2097152 0 2097152 0%% /\n';;
 'full:-Pk /overlay') printf 'Filesystem 1024-blocks Used Available Use%% Mounted\n/dev/overlay 2097152 1572864 524288 75%% /overlay\n';;
 *) exit 1 ;;
esac
MOCK
chmod 700 "$TMP/df"
# No BP_CAP_OVERLAY_KB override: exercise real df parsing and mount fallback.
assert_tier standard DF_SCENARIO=missing PATH="$TMP:$PATH" BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=1048576
assert_tier lite DF_SCENARIO=low PATH="$TMP:$PATH" BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=1048576
assert_tier full DF_SCENARIO=full PATH="$TMP:$PATH" BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=1048576
assert_tier lite DF_SCENARIO=absent PATH="$TMP:$PATH" BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=1048576
echo "COE CORE CAPABILITY CLEANUP PASS: actual code handles missing mount and low available space"
