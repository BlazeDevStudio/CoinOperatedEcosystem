#!/bin/sh
# Source-linked synthetic tests; no system nft or real network writes.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
COMMON="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
CORE="$ROOT/openwrt/rootfs/usr/sbin/blazepwifi-core"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state"
export TEST_DIR="$T" BP_STATE="$T/state" BP_RUN="$T/run" BP_LIB="$COMMON" REQUEST_METHOD=GET
cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
printf '%s\n' "$*" >> "$TEST_DIR/commands"
[ -e "$TEST_DIR/table" ] || exit 2
mac="${6:-}"
mac="$(printf '%s' "$mac" | tr -d '{} ')"
case "$1 $2" in
  'add element')
    [ "${TEST_ADD_FAIL:-0}" = 0 ] || exit 3
    grep -Fqx "$mac" "$TEST_DIR/macs" && exit 4
    printf '%s\n' "$mac" >> "$TEST_DIR/macs" ;;
  'get element')
    [ "${TEST_GET_FAIL:-0}" = 0 ] || exit 5
    grep -Fqx "$mac" "$TEST_DIR/macs" ;;
  'delete element')
    [ "${TEST_DELETE_FAIL:-0}" = 0 ] || exit 6
    grep -Fqx "$mac" "$TEST_DIR/macs" || exit 7
    grep -Fvx "$mac" "$TEST_DIR/macs" > "$TEST_DIR/macs.next" || true
    mv "$TEST_DIR/macs.next" "$TEST_DIR/macs" ;;
  'list set')
    [ "${TEST_LIST_FAIL:-0}" = 0 ] || exit 8
    printf 'table inet blazepwifi {\n set auth_macs {\n  type ether_addr\n  elements = {\n'
    sed 's/^/   /;s/$/,/' "$TEST_DIR/macs"
    printf '  }\n }\n}\n' ;;
  'flush set')
    [ "${TEST_FLUSH_FAIL:-0}" = 0 ] || exit 9
    : > "$TEST_DIR/macs" ;;
  *) exit 10 ;;
esac
NFT
chmod +x "$T/bin/nft"
PATH="$T/bin:$PATH"; export PATH
# Load original source directly (no copied/mock function definitions).
. "$COMMON"
# Exclude daemon's live entrypoint, but source all original function definitions.
sed '/^bp_init_dirs$/,$d' "$CORE" > "$T/core-defs"
. "$T/core-defs"
bp_now() { printf '1800000000\n'; }
bp_time_sane() { [ "${TEST_TIME_BAD:-0}" = 0 ]; }
mac='02:11:22:33:44:55'
TEST_MAC="$mac"
reset() {
 : > "$T/macs"; : > "$T/commands"; : > "$T/table"
 unset TEST_ADD_FAIL TEST_GET_FAIL TEST_DELETE_FAIL TEST_LIST_FAIL TEST_FLUSH_FAIL TEST_TIME_BAD
}
assert_fail() { if "$@"; then echo "FAIL unexpected success: $*" >&2; exit 1; fi; }
assert_contains() { grep -Fqx "$1" "$T/macs" || { echo "FAIL missing MAC: $1" >&2; exit 1; }; }
reset
TEST_ADD_FAIL=1; export TEST_ADD_FAIL
assert_fail bp_authorize_mac "$mac"
[ ! -s "$T/macs" ]
printf 'PASS failed grant cannot report success\n'
reset
printf '%s\n' "$mac" > "$T/macs"
TEST_ADD_FAIL=1; export TEST_ADD_FAIL
bp_authorize_mac "$mac"
assert_contains "$mac"
printf 'PASS existing member grant idempotency verified\n'
reset
TEST_GET_FAIL=1; export TEST_GET_FAIL
assert_fail bp_authorize_mac "$mac"
printf 'PASS successful add with failed readback denied\n'
reset
printf '%s\n' "$mac" > "$T/macs"
TEST_DELETE_FAIL=1; export TEST_DELETE_FAIL
assert_fail bp_deauthorize_mac "$mac"
assert_contains "$mac"
printf 'PASS failed revocation cannot report success\n'
reset
bp_deauthorize_mac "$mac"
[ ! -s "$T/macs" ]
printf 'PASS absent member revocation is idempotent\n'
reset
TEST_LIST_FAIL=1; export TEST_LIST_FAIL
assert_fail bp_deauthorize_mac "$mac"
printf 'PASS unreadable authorization set denied\n'
reset
assert_fail bp_authorize_mac 'invalid; nft flush ruleset'
[ ! -s "$T/commands" ]
printf 'PASS malformed MAC rejected before nft mutation\n'
reset
TEST_TIME_BAD=1; TEST_FLUSH_FAIL=1; export TEST_TIME_BAD TEST_FLUSH_FAIL
assert_fail sync_accounts
printf 'PASS unsynchronized-clock flush failure propagates\n'
reset
printf '%s\n' "$mac" > "$T/macs"
printf 'device123\t0\t1700000000\t0\t1\t0\t%s\t10.0.0.2\t\n' "$mac" > "$T/state/accounts.tsv"
TEST_DELETE_FAIL=1; export TEST_DELETE_FAIL
assert_fail sync_accounts
[ ! -s "$T/macs" ]
printf 'PASS daemon flushes all auth after revoked-account failure\n'
reset
printf 'device123\t0\t2000000000\t0\t0\t0\t%s\t10.0.0.2\t\n' "$TEST_MAC" > "$T/state/accounts.tsv"
sync_accounts
assert_contains "$TEST_MAC"
printf 'PASS healthy account remains authorizable\n'
printf 'ALL PASS — mocked nft only; no physical or real-kernel evidence\n'
