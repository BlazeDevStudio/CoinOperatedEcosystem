#!/bin/sh
# Execute the exact admin config_get/config_set CASE arms with stubbed services.
# Does not source other CGI arms or execute any network/payment operations.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
[ -r "$ADMIN" ] || { echo 'FAIL missing admin CGI' >&2; exit 1; }
awk '/^  config_get\)/ {copy=1} /^  update_status\)/ {if(copy) exit} copy {print}' "$ADMIN" > "$T/arms"
[ "$(grep -Ec '^  config_(get|set)\)' "$T/arms")" -eq 2 ] || { echo 'FAIL config arms missing' >&2; exit 1; }
cat > "$T/prefix" <<'SHELL'
#!/bin/sh
bp_fail() { printf '{"ok":false,"error":"%s"}\n' "$1"; exit 0; }
bp_json() { printf '%s\n' "$1"; }
bp_json_escape() { printf '%s' "$1"; }
require_role() { :; }
bp_auth_csrf_ok() { [ "${TEST_CSRF_OK:-1}" = 1 ]; }
bp_param() { case "$1" in key) printf admin_port;; value) printf 9443;; esac; }
bp_config_key_allowed() { [ "$1" = admin_port ]; }
bp_config_validate() { [ "$1" = admin_port ]; }
bp_config_get_optional() { [ "${TEST_READ_FAIL:-0}" = 0 ] || return 8; [ "${TEST_READ_MISSING:-0}" = 0 ] || return 0; printf '8443\n'; }
bp_config_set() { return "${TEST_SET_RC:-0}"; }
case "${TEST_ACTION:-config_get}" in
SHELL
cat "$T/prefix" "$T/arms" > "$T/run.sh"
printf 'esac\n' >> "$T/run.sh"
sh -n "$T/run.sh"
run() { sh "$T/run.sh"; }
require_text() { printf '%s\n' "$1" | grep -Fq "$2" || { echo "FAIL response missing: $2" >&2; exit 1; }; }
out="$(TEST_ACTION=config_get TEST_READ_FAIL=1 run)"
require_text "$out" '"ok":false'
require_text "$out" 'configuration read failed'
printf 'PASS admin config read failure not reported as success\n'
out="$(TEST_ACTION=config_get run)"
require_text "$out" '"ok":true'
require_text "$out" '8443'
printf 'PASS admin config read success retained\n'
out="$(TEST_ACTION=config_get TEST_READ_MISSING=1 run)"
require_text "$out" '"ok":true'
require_text "$out" '"value":""'
printf 'PASS optional missing config remains empty and successful\n'
out="$(TEST_ACTION=config_set TEST_SET_RC=8 run)"
require_text "$out" '"ok":false'
require_text "$out" 'configuration state uncertain'
if printf '%s\n' "$out" | grep -Fq 'rolled back'; then echo 'FAIL false rollback confirmation' >&2; exit 1; fi
printf 'PASS uncertain configuration state gets explicit failure\n'
out="$(TEST_ACTION=config_set TEST_SET_RC=7 run)"
require_text "$out" '"ok":false'
require_text "$out" 'no setting modified'
printf 'PASS missing apply program does not claim a committed change\n'
out="$(TEST_ACTION=config_set TEST_SET_RC=1 run)"
require_text "$out" '"ok":false'
require_text "$out" 'inspect live service state'
printf 'PASS failed apply never claims live service restoration\n'
out="$(TEST_ACTION=config_set run)"
require_text "$out" '"ok":true'
require_text "$out" '9443'
printf 'PASS admin config set success retained\n'
out="$(TEST_ACTION=config_set TEST_CSRF_OK=0 run)"
require_text "$out" 'csrf validation failed'
printf 'PASS CSRF gate retained\n'
printf 'ALL PASS — extracted CGI config arms, stubbed service layer only\n'
