#!/bin/sh
# Behavior-preserving integration seam check. No real nft, credit, or hardware.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
COMMON="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
API="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/api"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state"
export BP_STATE="$T/state" BP_RUN="$T/run" REQUEST_METHOD=GET TEST_DIR="$T"
cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
printf '%s\n' "$*" >> "$TEST_DIR/commands"
[ "$*" = 'flush set inet blazepwifi auth_macs' ] || exit 99
[ "${TEST_FLUSH_FAIL:-0}" = 0 ] || exit 9
exit 0
NFT
chmod +x "$T/bin/nft"
PATH="$T/bin:$PATH"; export PATH
sh -n "$COMMON"
sh -n "$API"
. "$COMMON"
TEST_OLDMAC='02:11:22:33:44:55'
TEST_NEWMAC='02:11:22:33:44:66'
bp_now() { printf '1800000000\n'; }
bp_account_line() {
  printf 'device123\t100\t2000000000\t0\t0\t0\t%s\t10.0.0.1\t\n' "$TEST_OLDMAC"
}
bp_pause_limit_expired() { [ "${TEST_EXPIRE:-0}" = 1 ]; }
bp_account_write() { printf 'account-write\n' >> "$TEST_DIR/account-ops"; return 0; }
bp_deauthorize_mac() {
  printf 'revoke\n' >> "$TEST_DIR/account-ops"
  [ "${TEST_REVOKE_FAIL:-0}" = 0 ]
}
bp_authorize_mac() {
  printf 'grant\n' >> "$TEST_DIR/account-ops"
  [ "${TEST_GRANT_FAIL:-0}" = 0 ]
}
reset() {
 : > "$T/commands"; : > "$T/account-ops"
 unset TEST_REVOKE_FAIL TEST_GRANT_FAIL TEST_FLUSH_FAIL TEST_EXPIRE
}
assert_failure() { if bp_bind_device device123 "$TEST_NEWMAC" 10.0.0.2 0 > "$T/out" 2> "$T/err"; then echo 'FAIL binding reported success after fault' >&2; exit 1; fi; }
reset
TEST_REVOKE_FAIL=1; export TEST_REVOKE_FAIL
assert_failure
grep -Fqx 'flush set inet blazepwifi auth_macs' "$T/commands"
! grep -Fqx grant "$T/account-ops"
printf 'PASS failed old-MAC revoke prevents new grant and flushes auth\n'
reset
TEST_GRANT_FAIL=1; export TEST_GRANT_FAIL
assert_failure
grep -Fqx revoke "$T/account-ops"
grep -Fqx grant "$T/account-ops"
grep -Fqx 'flush set inet blazepwifi auth_macs' "$T/commands"
printf 'PASS failed new-MAC grant returns error after global flush\n'
reset
bp_bind_device device123 "$TEST_NEWMAC" 10.0.0.2 0
[ ! -s "$T/commands" ]
grep -Fqx grant "$T/account-ops"
printf 'PASS healthy MAC rebind preserves successful behavior\n'
reset
TEST_REVOKE_FAIL=1; TEST_FLUSH_FAIL=1; export TEST_REVOKE_FAIL TEST_FLUSH_FAIL
assert_failure
grep -Fq 'CRITICAL: nft authorization revocation unverified' "$T/err"
printf 'PASS failed fallback flush raises CRITICAL, not successful ACK\n'
reset
TEST_EXPIRE=1; TEST_REVOKE_FAIL=1; export TEST_EXPIRE TEST_REVOKE_FAIL
assert_failure
grep -Fqx 'flush set inet blazepwifi auth_macs' "$T/commands"
printf 'PASS pause-expiration revoke fault propagates\n'
for marker in \
 'network access unverified; account may already be charged' \
 'pause recorded but network revocation unverified' \
 'resume recorded but access unverified' \
 'disconnect recorded but revocation unverified' \
 'account binding or network state unverified'; do
  grep -Fq "$marker" "$API" || { echo "FAIL missing API network failure response: $marker" >&2; exit 1; }
done
printf 'PASS five API fail-response guards present in actual source\n'
printf 'ALL PASS — synthetic only; financial writes mocked, not approved\n'
