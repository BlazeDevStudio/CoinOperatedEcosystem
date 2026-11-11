#!/bin/sh
# Exercise the ACTUAL embedded fake UCI from tests/config.sh, not a duplicated mock.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
SOURCE="$ROOT/tests/config.sh"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin"
# Extract only the script the legacy fixture would install, without launching
# the full admin CGI (which has remaining unrecovered runtime dependencies).
sed -n '/^cat > .*bin\/uci.*<<.*UCI.*$/,/^UCI$/p' "$SOURCE" |
  sed '1d;$d' > "$T/bin/uci"
[ -s "$T/bin/uci" ] || { echo 'missing legacy fake UCI' >&2; exit 1; }
chmod 700 "$T/bin/uci"
export TEST_UCI_DB="$T/uci.db"
printf '%s\n' 'blazepwifi.main.admin_port=8443' > "$TEST_UCI_DB"
sh -n "$T/bin/uci"
output="$("$T/bin/uci" -q show blazepwifi.main)"
printf '%s\n' "$output" | grep -Fxq 'blazepwifi.main=core'
printf '%s\n' "$output" | grep -Fxq 'blazepwifi.main.admin_port=8443'
printf 'PASS UCI show returns core section and existing option\n'
[ "$("$T/bin/uci" -q get blazepwifi.main.admin_port)" = 8443 ]
if "$T/bin/uci" -q get blazepwifi.main.missing >/dev/null 2>&1; then
  echo 'FAIL missing option incorrectly reads successfully' >&2; exit 1
fi
printf 'PASS UCI get distinguishes existing and absent options\n'
"$T/bin/uci" set 'blazepwifi.main.admin_port=9443'
[ "$("$T/bin/uci" get blazepwifi.main.admin_port)" = 9443 ]
"$T/bin/uci" -q delete blazepwifi.main.admin_port
if "$T/bin/uci" get blazepwifi.main.admin_port >/dev/null 2>&1; then
  echo 'FAIL deleted option still visible' >&2; exit 1
fi
printf 'PASS UCI set/delete transition\n'
printf 'ALL PASS — isolated legacy UCI fixture smoke; admin CGI NOT RUN\n'
