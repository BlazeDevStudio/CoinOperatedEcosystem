#!/bin/sh
# Source-linked real CORE executable with only temp path substitutions.
# Synthetic nft, common, and sleep; no UCI, router, real clients or payment.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
SOURCE="$ROOT/core/openwrt/rootfs/usr/sbin/blazepwifi-core"
CONFIG="$ROOT/core/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
T="$(mktemp -d /tmp/coe-core-direct-XXXXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
DIR="$T/etc/blazepwifi"
LIB="$T/usr/lib/blazepwifi/config.sh"
PENDING="$DIR/.config-transaction.pending"
mkdir -p "$DIR" "$T/usr/lib/blazepwifi" "$T/bin" "$T/targets"
cp "$CONFIG" "$LIB"

# Substitute only canonical paths into a disposable copy, never production.
sed -e 's|/etc/blazepwifi/.config-transaction.pending|__COE_MARKER__|g' \
    -e "s|/etc/blazepwifi|$DIR|g" \
    -e "s|/usr/lib/blazepwifi/config.sh|$LIB|g" \
    -e "s|__COE_MARKER__|$PENDING|g" "$SOURCE" > "$T/core-under-test"
[ "$(grep -Fc "$LIB" "$T/core-under-test")" -eq 3 ]
[ "$(grep -Fc "$PENDING" "$T/core-under-test")" -eq 1 ]
sh -n "$T/core-under-test"

cat > "$T/common.sh" <<'COMMON'
#!/bin/sh
: > "$COE_COMMON_SOURCED"
BP_ACCOUNTS="$COE_ACCOUNTS"
BP_TARGET_DIR="$COE_TARGETS"
bp_init_dirs() { : > "$COE_INIT_CALLED"; }
bp_now() { printf '%s\n' 2000000000; }
bp_time_sane() { [ "$1" -ge 1700000000 ]; }
bp_cfg() {
    case "$1" in
        lan_if) printf 'br-lan\n' ;;
        portal_port) printf '8080\n' ;;
        walled_refresh_seconds) printf '120\n' ;;
        *) : ;;
    esac
}
bp_authorize_mac() { printf 'authorize %s\n' "$1" >> "$COE_AUTH_LOG"; }
bp_deauthorize_mac() { printf 'deauthorize %s\n' "$1" >> "$COE_AUTH_LOG"; }
COMMON

cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
printf '%s\n' "$*" >> "$COE_NFT_LOG"
exit 0
NFT
cat > "$T/bin/sleep" <<'SLEEP'
#!/bin/sh
case "$COE_SLEEP_ACTION" in
    pending)
        printf 'COE_CONFIG_PENDING_V1 admin_port\n' > "$COE_MARKER" ;;
    missing-library)
        mv "$COE_CONFIG_LIB" "$COE_CONFIG_LIB.hidden" ;;
    *) echo "unknown sleep test mode" >&2; exit 4 ;;
esac
exit 0
SLEEP
chmod 700 "$T/bin/nft" "$T/bin/sleep"
printf 'device\tcredit\texpiry\tremaining\tpaused\tpause_started\tmac\tip\tevents\n' > "$T/accounts.tsv"
# Replace header with one valid, otherwise live-looking *synthetic* account.
printf 'unit-test\t100\t2000001000\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.2\t0\n' > "$T/accounts.tsv"
export BP_LIB="$T/common.sh" PATH="$T/bin:$PATH"
export COE_COMMON_SOURCED="$T/common-sourced"
export COE_INIT_CALLED="$T/init-called"
export COE_TARGETS="$T/targets"
export COE_ACCOUNTS="$T/accounts.tsv"
export COE_AUTH_LOG="$T/authorization.log"
export COE_NFT_LOG="$T/nft.log"
export COE_MARKER="$PENDING"
export COE_CONFIG_LIB="$LIB"

run_direct_denied() {
    rm -f "$COE_COMMON_SOURCED" "$COE_INIT_CALLED" "$COE_AUTH_LOG" "$COE_NFT_LOG"
    if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
        echo 'DIRECT_CORE_UNSAFE_ACK' >&2; exit 1
    else
        rc="$?"
        [ "$rc" -eq 9 ] || { echo "DIRECT_DENIAL_WRONG_CODE: $rc" >&2; cat "$T/stderr" >&2; exit 1; }
    fi
    [ ! -e "$COE_COMMON_SOURCED" ] || { echo 'COMMON_SOURCED_BEFORE_RECOVERY' >&2; exit 1; }
    [ ! -e "$COE_INIT_CALLED" ] || { echo 'INIT_DIRS_ON_DENIAL' >&2; exit 1; }
    [ ! -e "$COE_NFT_LOG" ] || { echo 'NFT_MUTATION_ON_DENIAL' >&2; exit 1; }
    grep -Fq 'blazepwifi-core denied' "$T/stderr"
}

# Direct binary invocation must deny before sourcing common or changing nft.
printf 'COE_CONFIG_PENDING_V1 admin_port\n' > "$PENDING"
run_direct_denied
[ -f "$PENDING" ]

# Environment override must never hide the fixed authority path.
BP_CONFIG_PENDING_FILE="$T/forged-absent"; export BP_CONFIG_PENDING_FILE
run_direct_denied
[ -f "$PENDING" ]
unset BP_CONFIG_PENDING_FILE
rm "$PENDING"

# Dangling/symlinked marker, directory and library fail closed.
ln -s "$T/absent" "$PENDING"
run_direct_denied
rm "$PENDING"
mv "$DIR" "$DIR.saved"
ln -s "$DIR.saved" "$DIR"
run_direct_denied
rm "$DIR"
mv "$DIR.saved" "$DIR"
mv "$LIB" "$LIB.saved"
ln -s "$LIB.saved" "$LIB"
run_direct_denied
rm "$LIB"
mv "$LIB.saved" "$LIB"

# A missing/invalid recovery library cannot be bypassed.
mv "$LIB" "$LIB.missing"
run_direct_denied
mv "$LIB.missing" "$LIB"
mv "$LIB" "$LIB.saved"
printf '%s\n' '# bad recovery implementation' > "$LIB"
run_direct_denied
mv "$LIB.saved" "$LIB"

# A clean direct launch reaches the common module + nft + auth loop.
# The stub sleep then creates a pending marker; the next loop must refuse
# to authorize and attempt deauthorization, then exit with status 9.
COE_SLEEP_ACTION=pending; export COE_SLEEP_ACTION
rm -f "$COE_COMMON_SOURCED" "$COE_INIT_CALLED" "$COE_AUTH_LOG" "$COE_NFT_LOG"
if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
    echo 'CORE_STAYED_ACTIVE_AFTER_PENDING' >&2; exit 1
else
    rc="$?"
    [ "$rc" -eq 9 ] || { echo "PENDING_LOOP_WRONG_CODE: $rc" >&2; cat "$T/stderr" >&2; exit 1; }
fi
[ -f "$COE_COMMON_SOURCED" ] && [ -f "$COE_INIT_CALLED" ]
grep -Fq 'authorize aa:bb:cc:dd:ee:ff' "$COE_AUTH_LOG"
grep -Fq 'flush set inet blazepwifi auth_macs' "$COE_NFT_LOG"
grep -Fq 'core stopped' "$T/stderr"
[ -f "$PENDING" ]
rm "$PENDING"

# If the recovery library vanishes during runtime, the periodic guard must
# also refuse further access; no second authorization may be emitted.
COE_SLEEP_ACTION=missing-library; export COE_SLEEP_ACTION
rm -f "$COE_COMMON_SOURCED" "$COE_INIT_CALLED" "$COE_AUTH_LOG" "$COE_NFT_LOG"
if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
    echo 'CORE_STAYED_ACTIVE_WITH_MISSING_LIBRARY' >&2; exit 1
else
    rc="$?"
    [ "$rc" -eq 9 ] || { echo "MISSING_LIBRARY_LOOP_CODE: $rc" >&2; cat "$T/stderr" >&2; exit 1; }
fi
grep -Fq 'flush set inet blazepwifi auth_macs' "$COE_NFT_LOG"
grep -Fq 'core stopped' "$T/stderr"
[ "$(grep -Fc 'authorize ' "$COE_AUTH_LOG")" -eq 1 ]
echo 'COE CORE EXEC GUARD PASS: direct launch blocked, environment/symlink/missing guard denied, runtime pending/lost library stopped'
