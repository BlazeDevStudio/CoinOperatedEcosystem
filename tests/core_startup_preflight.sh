#!/bin/sh
# Simulated OpenWrt rc.common/procd startup check: only temporary files.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ORIGINAL="$ROOT/core/openwrt/rootfs/etc/init.d/blazepwifi"
CONFIG="$ROOT/core/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
T="$(mktemp -d /tmp/coe-boot-gate-XXXXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
ETC="$T/etc/blazepwifi"
LIBDIR="$T/usr/lib/blazepwifi"
LIB="$LIBDIR/config.sh"
MARKER="$ETC/.config-transaction.pending"
mkdir -p "$ETC" "$LIBDIR"
cp "$CONFIG" "$LIB"
# Production paths are constant. Substitute them ONLY in a throwaway script;
# a deployed environment variable cannot redirect the pending marker.
sed -e 's|/etc/blazepwifi/.config-transaction.pending|__COE_MARKER__|g' \
    -e "s|/etc/blazepwifi|$ETC|g" \
    -e "s|/usr/lib/blazepwifi/config.sh|$LIB|g" \
    -e "s|__COE_MARKER__|$MARKER|g" "$ORIGINAL" > "$T/init-test"
[ "$(grep -Fc "$LIB" "$T/init-test")" -eq 2 ]
[ "$(grep -Fc "$MARKER" "$T/init-test")" -eq 1 ]
sh -n "$T/init-test"
. "$T/init-test"
config_load() { [ "$1" = blazepwifi ]; }
config_get_bool() { enabled="$COE_ENABLED"; }
procd_open_instance() { : > "$T/core-opened"; }
procd_set_param() { :; }
procd_close_instance() { : > "$T/core-started"; }
deny_start() {
    rm -f "$T/core-opened" "$T/core-started"
    if start_service 2>"$T/err"; then
        echo 'UNSAFE_CORE_START_ACK' >&2
        exit 1
    fi
    [ ! -e "$T/core-opened" ] && [ ! -e "$T/core-started" ] || {
        echo 'CORE_INSTANCE_OPENED_ON_DENIAL' >&2; exit 1;
    }
    grep -Fq 'core startup denied' "$T/err"
}
COE_ENABLED=1; export COE_ENABLED
start_service
[ -f "$T/core-opened" ] && [ -f "$T/core-started" ]
rm -f "$T/core-opened" "$T/core-started"

# A disabled service remains disabled and never starts procd.
COE_ENABLED=0; export COE_ENABLED
start_service
[ ! -e "$T/core-opened" ] && [ ! -e "$T/core-started" ]
COE_ENABLED=1; export COE_ENABLED

# An interrupted transaction prevents a core launch and is not deleted.
printf '%s\n' 'COE_CONFIG_PENDING_V1 admin_port' > "$MARKER"
deny_start
[ -f "$MARKER" ]
# Inherited environment overrides cannot hide the canonical marker.
BP_CONFIG_PENDING_FILE="$T/forged-empty-path"; export BP_CONFIG_PENDING_FILE
deny_start
[ "$BP_CONFIG_PENDING_FILE" = "$MARKER" ]
unset BP_CONFIG_PENDING_FILE
rm "$MARKER"

# Symlinks to markers never count as clean pending state.
ln -s "$T/forged-empty-path" "$MARKER"
deny_start
[ -L "$MARKER" ]
rm "$MARKER"

# Absent or redirected configuration directories are unsafe.
mv "$ETC" "$ETC.missing"
deny_start
mv "$ETC.missing" "$ETC"
mv "$ETC" "$ETC.saved"
ln -s "$ETC.saved" "$ETC"
deny_start
rm "$ETC"
mv "$ETC.saved" "$ETC"

# Missing or symlinked recovery code is not allowed to start core.
mv "$LIB" "$LIB.missing"
deny_start
mv "$LIB.missing" "$LIB"
mv "$LIB" "$LIB.saved"
ln -s "$LIB.saved" "$LIB"
deny_start
rm "$LIB"
mv "$LIB.saved" "$LIB"

# Invalid recovery library cannot return a clean result.
cp "$LIB" "$LIB.saved"
printf '%s\n' '# invalid recovery library' > "$LIB"
bp_config_recovery_status() { return 9; }
deny_start
mv "$LIB.saved" "$LIB"

# After independent synthetic correction, clean core start is possible.
start_service
[ -f "$T/core-opened" ] && [ -f "$T/core-started" ]
echo 'COE STARTUP PREFLIGHT PASS: disabled, pending, env override, symlinks, missing dir/library, invalid guard, clean'
