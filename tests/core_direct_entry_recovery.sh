#!/bin/sh
# Source-linked, isolated direct daemon recovery gate. Never touch real nft/UCI.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CORE="$ROOT/core/openwrt/rootfs/usr/sbin/blazepwifi-core"
CONFIG="$ROOT/core/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
T="$(mktemp -d /tmp/coe-direct-core-XXXXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
ETC="$T/etc/blazepwifi"
LIBDIR="$T/usr/lib/blazepwifi"
LIB="$LIBDIR/config.sh"
MARKER="$ETC/.config-transaction.pending"
mkdir -p "$ETC" "$LIBDIR" "$T/bin" "$T/targets"
: > "$T/accounts"
cp "$CONFIG" "$LIB"
# Transform the actual daemon source ONLY inside the disposable test dir.
sed -e 's|/etc/blazepwifi/.config-transaction.pending|__COE_MARKER__|g' \
    -e "s|/etc/blazepwifi|$ETC|g" \
    -e "s|/usr/lib/blazepwifi/config.sh|$LIB|g" \
    -e "s|__COE_MARKER__|$MARKER|g" "$CORE" > "$T/core"
sh -n "$T/core"
test -x "$CORE"
test "$(grep -Fc "$MARKER" "$T/core")" -eq 1
test "$(grep -Fc "$LIB" "$T/core")" -eq 3

cat > "$T/common.sh" <<'COMMON'
#!/bin/sh
printf '%s\n' loaded-common >> "$COE_LOG"
BP_ACCOUNTS="$COE_T/accounts"
BP_TARGET_DIR="$COE_T/targets"
bp_init_dirs() { printf '%s\n' initialized >> "$COE_LOG"; }
bp_cfg() {
    case "$1" in
      walled_refresh_seconds) printf '120\n';;
      *) return 1;;
    esac
}
bp_now() { printf '100\n'; }
bp_time_sane() { return 1; }
bp_authorize_mac() { printf 'authorized\n' >> "$COE_LOG"; }
bp_deauthorize_mac() { printf 'deauthorized\n' >> "$COE_LOG"; }
COMMON
cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
printf 'nft %s\n' "$*" >> "$COE_LOG"
if [ "$1" = "-f" ]; then cat >/dev/null; fi
exit 0
NFT
cat > "$T/bin/sleep" <<'SLEEP'
#!/bin/sh
# Exit the service loop through its existing TERM handler.
kill -TERM "$PPID"
exit 0
SLEEP
chmod 700 "$T/bin/nft" "$T/bin/sleep"
export PATH="$T/bin:$PATH" BP_LIB="$T/common.sh" COE_T="$T" COE_LOG="$T/events"

deny_core() {
    rm -f "$COE_LOG"
    if sh "$T/core" 2>"$T/err"; then
        echo 'UNSAFE_DIRECT_CORE_START' >&2; exit 1
    else
        rc=$?
        [ "$rc" -eq 9 ] || { echo "WRONG_DIRECT_CORE_DENIAL_$rc" >&2; exit 1; }
    fi
    grep -Fq 'blazepwifi-core denied' "$T/err"
    [ ! -e "$COE_LOG" ] || {
        echo 'COMMON_OR_FIREWALL_MUTATED_BEFORE_PREFLIGHT' >&2
        cat "$COE_LOG" >&2
        exit 1
    }
}

printf '%s\n' 'COE_CONFIG_PENDING_V1 admin_port' > "$MARKER"
deny_core
[ -f "$MARKER" ]
BP_CONFIG_PENDING_FILE="$T/forged-missing-marker"; export BP_CONFIG_PENDING_FILE
deny_core
unset BP_CONFIG_PENDING_FILE
rm "$MARKER"

ln -s "$T/forged-missing-marker" "$MARKER"
deny_core
[ -L "$MARKER" ]
rm "$MARKER"

mv "$ETC" "$ETC.missing"
deny_core
mv "$ETC.missing" "$ETC"
mv "$ETC" "$ETC.actual"
ln -s "$ETC.actual" "$ETC"
deny_core
rm "$ETC"
mv "$ETC.actual" "$ETC"

mv "$LIB" "$LIB.missing"
deny_core
mv "$LIB.missing" "$LIB"
mv "$LIB" "$LIB.actual"
ln -s "$LIB.actual" "$LIB"
deny_core
rm "$LIB"
mv "$LIB.actual" "$LIB"

cp "$LIB" "$LIB.original"
printf '%s\n' '# no recovery function available' > "$LIB"
deny_core
mv "$LIB.original" "$LIB"

# Clean positive control, with fake nft/common. No host firewall changes.
rm -f "$COE_LOG"
sh "$T/core" 2>"$T/clean-err"
grep -Fq 'loaded-common' "$COE_LOG"
grep -Fq 'initialized' "$COE_LOG"
grep -Fq 'nft -f -' "$COE_LOG"
grep -Fq 'nft delete table inet blazepwifi' "$COE_LOG"
[ ! -e "$MARKER" ]
echo 'COE CORE DIRECT ENTRY PASS: clean, pending, override, symlink, missing guard, no preflight side effects'
