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
    -e "s|__COE_MARKER__|$PENDING|g" \
    -e "s|/var/run/blazepwifi-config.lock|$T/config.lock|g" "$SOURCE" > "$T/core-under-test"
[ "$(grep -Fc "$LIB" "$T/core-under-test")" -eq 3 ]
[ "$(grep -Fc "$PENDING" "$T/core-under-test")" -eq 1 ]
[ "$(grep -Fc "$T/config.lock" "$T/core-under-test")" -eq 1 ]
sh -n "$T/core-under-test"

cat > "$T/common.sh" <<'COMMON'
#!/bin/sh
: > "$COE_COMMON_SOURCED"
BP_ACCOUNTS="$COE_ACCOUNTS"
BP_TARGET_DIR="$COE_TARGETS"
bp_init_dirs() { : > "$COE_INIT_CALLED"; }
bp_now() { printf '%s\n' 2000000000; }
bp_time_sane() {
    if [ "$COE_GRANT_FAULT" = 'before-grant' ]; then
        printf 'COE_CONFIG_PENDING_V1 admin_port\n' > "$COE_MARKER"
    fi
    [ "$1" -ge 1700000000 ]
}
bp_cfg() {
    case "$1" in
        lan_if) printf 'br-lan\n' ;;
        portal_port) printf '8080\n' ;;
        walled_refresh_seconds) printf '120\n' ;;
        *) : ;;
    esac
}
bp_authorize_mac() {
    printf 'authorize %s\n' "$1" >> "$COE_AUTH_LOG"
    # Faithfully model upstream common.sh's nft error-suppressing wrapper.
    nft add element inet blazepwifi auth_macs "{ $1 }" >/dev/null 2>&1 || true
    if [ "$COE_GRANT_FAULT" = 'during-grant' ]; then
        printf 'COE_CONFIG_PENDING_V1 admin_port\n' > "$COE_MARKER"
    fi
}
bp_deauthorize_mac() { printf 'deauthorize %s\n' "$1" >> "$COE_AUTH_LOG"; }
COMMON

cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
printf '%s\n' "$*" >> "$COE_NFT_LOG"
case "${1:-} ${2:-}" in
    'add element')
        [ "$COE_NFT_FAULT" != 'add-denied' ] || exit 7
        printf 'present\n' > "$COE_ELEMENT_PRESENT" ;;
    'get element')
        [ "$COE_NFT_FAULT" != 'readback-denied' ] || exit 8
        [ -f "$COE_ELEMENT_PRESENT" ] || exit 9 ;;
    'flush set')
        [ "$COE_NFT_FAULT" != 'flush-denied' ] || exit 10
        rm -f "$COE_ELEMENT_PRESENT" ;;
esac
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
export COE_GRANT_FAULT=none
export COE_LOCK_READY="$T/lock-ready"
export COE_NFT_FAULT=none COE_ELEMENT_PRESENT="$T/element-present"

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
# Restore the fixture library consumed by the preceding missing-library test.
mv "$LIB.hidden" "$LIB"

# Inject pending AFTER the loop preflight, but BEFORE the first account grant.
# Previously the loop-wide check would permit an authorization in this gap.
COE_GRANT_FAULT=before-grant; COE_SLEEP_ACTION=pending
export COE_GRANT_FAULT COE_SLEEP_ACTION
rm -f "$COE_AUTH_LOG" "$COE_NFT_LOG" "$T/stdout" "$T/stderr"
if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
    echo 'PREGRANT_PENDING_WAS_GRANTED' >&2; exit 1
else
    [ "$?" -eq 9 ] || { echo 'PREGRANT_WRONG_RETURN' >&2; cat "$T/stderr" >&2; exit 1; }
fi
[ ! -s "$COE_AUTH_LOG" ] || { echo 'PREGRANT_ACCOUNT_AUTHORIZED' >&2; exit 1; }
grep -Fq 'flush set inet blazepwifi auth_macs' "$COE_NFT_LOG"
[ -f "$PENDING" ]
rm "$PENDING"

# External/noncooperating writers can race even a shared lock. If a marker
# appears INSIDE an authorization call, detect it immediately afterwards,
# attempt revocation and exit 9; no hardware fail-closed proof is claimed.
COE_GRANT_FAULT=during-grant; export COE_GRANT_FAULT
rm -f "$COE_AUTH_LOG" "$COE_NFT_LOG"
if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
    echo 'DURING_GRANT_PENDING_WAS_IGNORED' >&2; exit 1
else
    [ "$?" -eq 9 ] || { echo 'DURING_GRANT_WRONG_RETURN' >&2; exit 1; }
fi
[ "$(grep -Fc 'authorize ' "$COE_AUTH_LOG")" -eq 1 ]
grep -Fq 'flush set inet blazepwifi auth_macs' "$COE_NFT_LOG"
[ -f "$PENDING" ]
rm "$PENDING"

# A config transaction holder prevents an independent grant from claiming
# success; a competing reader never authorizes while the lock is held.
COE_GRANT_FAULT=none; export COE_GRANT_FAULT
rm -f "$COE_AUTH_LOG" "$COE_NFT_LOG" "$COE_LOCK_READY"
flock "$T/config.lock" sh -c 'printf locked > "$COE_LOCK_READY"; /bin/sleep 2' &
locker=$!
attempt=0
while [ ! -f "$COE_LOCK_READY" ]; do
    attempt=$((attempt+1))
    [ "$attempt" -lt 100 ] || { echo 'LOCK_FIXTURE_NOT_READY' >&2; exit 1; }
    /bin/sleep 0.02
done
if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
    echo 'CONTENDED_GRANT_WAS_ACCEPTED' >&2; exit 1
else
    [ "$?" -eq 9 ] || { echo 'CONTENDED_GRANT_WRONG_RETURN' >&2; exit 1; }
fi
wait "$locker"
[ ! -s "$COE_AUTH_LOG" ] || { echo 'CONTENDED_ACCOUNT_AUTHORIZED' >&2; exit 1; }
grep -Fq 'flush set inet blazepwifi auth_macs' "$COE_NFT_LOG"
[ ! -e "$PENDING" ]

echo 'COE CORE GRANT BARRIER PASS: before/during-grant pending, shared-lock contention, no unverified grant'

# The real common.sh ignores nft add's non-zero return. An attempted
# authorization must not be ACKed until 'nft get element' confirms membership.
# The synthetic nft add intentionally fails while the helper returns success.
for fault in add-denied readback-denied; do
    COE_NFT_FAULT="$fault"; export COE_NFT_FAULT
    COE_GRANT_FAULT=none; export COE_GRANT_FAULT
    COE_SLEEP_ACTION=pending; export COE_SLEEP_ACTION
    rm -f "$COE_ELEMENT_PRESENT" "$COE_AUTH_LOG" "$COE_NFT_LOG" "$PENDING"
    if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
        echo "NFT_UNVERIFIED_GRANT_ACKED_$fault" >&2; exit 1
    else
        [ "$?" -eq 9 ] || { echo "NFT_UNVERIFIED_GRANT_WRONG_EXIT_$fault" >&2; cat "$T/stderr" >&2; exit 1; }
    fi
    [ "$(grep -Fc 'authorize ' "$COE_AUTH_LOG")" -eq 1 ]
    grep -Fq 'get element inet blazepwifi auth_macs' "$COE_NFT_LOG"
    grep -Fq 'flush set inet blazepwifi auth_macs' "$COE_NFT_LOG"
    grep -Fq 'grant barrier uncertain' "$T/stderr"
    [ ! -e "$PENDING" ] || { echo "UNEXPECTED_PENDING_$fault" >&2; exit 1; }
done

# A successful synthetic add and readback must preserve the positive path:
# only the existing fixture's sleep-triggered marker terminates the loop.
COE_NFT_FAULT=none; export COE_NFT_FAULT
rm -f "$COE_ELEMENT_PRESENT" "$COE_AUTH_LOG" "$COE_NFT_LOG" "$PENDING"
if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
    echo 'HEALTHY_GRANT_DID_NOT_RECHECK_RUNTIME_RECOVERY' >&2; exit 1
else
    [ "$?" -eq 9 ] || { echo 'HEALTHY_GRANT_WRONG_EXIT' >&2; exit 1; }
fi
grep -Fq 'get element inet blazepwifi auth_macs' "$COE_NFT_LOG"
grep -Fq 'authorize aa:bb:cc:dd:ee:ff' "$COE_AUTH_LOG"
[ -f "$PENDING" ]
rm "$PENDING"

# A flush failure must emit an explicit emergency message. The service
# still denies, but no test claims the firewall is actually deauthorized.
COE_NFT_FAULT=flush-denied; export COE_NFT_FAULT
printf 'COE_CONFIG_PENDING_V1 admin_port\n' > "$PENDING"
if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
    echo 'FAILED_FLUSH_WAS_TREATED_AS_SUCCESS' >&2; exit 1
else
    [ "$?" -eq 9 ] || { echo 'FAILED_FLUSH_WRONG_EXIT' >&2; exit 1; }
fi
# Startup preflight denies before the runtime flush; to exercise the
# runtime flush failure, force marker creation in the account grant path.
rm "$PENDING"
COE_GRANT_FAULT=before-grant; export COE_GRANT_FAULT
if timeout 6 sh "$T/core-under-test" >"$T/stdout" 2>"$T/stderr"; then
    echo 'FAILED_RUNTIME_FLUSH_ACKED' >&2; exit 1
else
    [ "$?" -eq 9 ] || { echo 'FAILED_RUNTIME_FLUSH_WRONG_EXIT' >&2; exit 1; }
fi
grep -Fq 'CRITICAL: nft authorization revocation unverified' "$T/stderr"
grep -Fq 'flush set inet blazepwifi auth_macs' "$COE_NFT_LOG"
[ -f "$PENDING" ]
echo 'COE NFT VERIFICATION PASS: suppressed add failure denied, unreadable membership denied, verified add, flush failure surfaced'
