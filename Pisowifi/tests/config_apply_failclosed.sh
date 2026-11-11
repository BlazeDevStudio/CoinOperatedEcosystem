#!/bin/sh
# Real config.sh, fake UCI and isolated test hooks. No live service or payment.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/run"
export TEST_DIR="$T" BP_RUN="$T/run" PATH="$T/bin:$PATH"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
[ "${1:-}" = -q ] && shift
cmd="$1"; key="${2:-}"
case "$cmd" in
  show)
    [ "$key" = blazepwifi.main ] || exit 2
    printf '%s\n' 'blazepwifi.main=core'
    cat "$TEST_DIR/uci.db" ;;
  get)
    row="$(grep -F "${key}=" "$TEST_DIR/uci.db" | tail -n 1)"
    [ -n "$row" ] || exit 1
    printf '%s\n' "${row#*=}" ;;
  set)
    printf 'set\n' >> "$TEST_DIR/mutations"
    option="${key%%=*}"
    grep -Fv "$option=" "$TEST_DIR/uci.db" > "$TEST_DIR/next.db" || true
    printf '%s=%s\n' "$option" "${key#*=}" >> "$TEST_DIR/next.db"
    mv "$TEST_DIR/next.db" "$TEST_DIR/uci.db" ;;
  delete)
    printf 'delete\n' >> "$TEST_DIR/mutations"
    grep -Fv "$key=" "$TEST_DIR/uci.db" > "$TEST_DIR/next.db" || true
    mv "$TEST_DIR/next.db" "$TEST_DIR/uci.db" ;;
  commit)
    printf 'commit\n' >> "$TEST_DIR/mutations"
    if [ -e "$TEST_DIR/one_commit_failure" ]; then
      rm "$TEST_DIR/one_commit_failure"; exit 1
    fi
    if [ -e "$TEST_DIR/remove_hook_at_commit" ]; then
      rm -f "$TEST_DIR/bin/vanishing_hook" "$TEST_DIR/remove_hook_at_commit"
    fi
    ;;
  *) exit 2 ;;
esac
UCI
chmod 700 "$T/bin/uci"
CONFIG="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
sh -n "$CONFIG"
. "$CONFIG"
bp_auth_audit() { printf 'AUDIT\n' >> "$T/audit"; }
reset() {
  rm -f "$T"/one_commit_failure "$T"/remove_hook_at_commit "$T"/live_changed
  printf '%s\n' 'blazepwifi.main.admin_port=8443' > "$T/uci.db"
  : > "$T/mutations"
  : > "$T/audit"
  unset BP_CONFIG_APPLY_HOOK
}
run_set() {
  set +e
  bp_config_set admin_port 9443 > "$T/stdout" 2> "$T/stderr"
  rc=$?
  set -e
}
assert_old() {
  [ "$(cat "$T/uci.db")" = 'blazepwifi.main.admin_port=8443' ]
  [ ! -s "$T/audit" ]
}
reset
if [ -e /usr/lib/blazepwifi/apply-config.sh ]; then
  echo 'SKIP missing-installed-apply check: host has a script; do not execute it'
else
  run_set
  [ "$rc" -eq 7 ]
  assert_old
  [ ! -s "$T/mutations" ]
  grep -Fq 'configuration apply executable unavailable; no UCI change permitted' "$T/stderr"
  printf 'PASS missing apply program blocks UCI mutation before commit\n'
  set +e
  bp_config_apply > "$T/stdout" 2> "$T/stderr"
  rc=$?
  set -e
  [ "$rc" -eq 7 ]
  printf 'PASS direct apply fails closed without runtime script\n'
fi
reset
BP_CONFIG_APPLY_HOOK=false; export BP_CONFIG_APPLY_HOOK
run_set
[ "$rc" -eq 8 ]
assert_old
[ "$(wc -l < "$T/mutations")" -eq 4 ]
grep -Fq 'CRITICAL: UCI restored, but live configuration state unverified' "$T/stderr"
printf 'PASS failed apply restores UCI but reports live state uncertain\n'
reset
BP_CONFIG_APPLY_HOOK=true; export BP_CONFIG_APPLY_HOOK
run_set
[ "$rc" -eq 0 ]
[ "$(cat "$T/uci.db")" = 'blazepwifi.main.admin_port=9443' ]
[ "$(wc -l < "$T/audit")" -eq 1 ]
printf 'PASS explicit successful test apply permits change and audit\n'
reset
BP_CONFIG_APPLY_HOOK="true; touch $T/injected"; export BP_CONFIG_APPLY_HOOK
run_set
[ "$rc" -eq 7 ]
assert_old
[ ! -s "$T/mutations" ]
[ ! -e "$T/injected" ]
printf 'PASS shell-string hook rejected before mutation\n'
reset
cat > "$T/bin/vanishing_hook" <<'HOOK'
#!/bin/sh
exit 0
HOOK
chmod 700 "$T/bin/vanishing_hook"
BP_CONFIG_APPLY_HOOK="$T/bin/vanishing_hook"; export BP_CONFIG_APPLY_HOOK
touch "$T/remove_hook_at_commit"
run_set
[ "$rc" -eq 8 ]
assert_old
grep -Fq 'CRITICAL: UCI restored, but live configuration state unverified' "$T/stderr"
printf 'PASS apply program disappearance fails safely after UCI commit\n'
reset
cat > "$T/bin/partial_hook" <<'HOOK'
#!/bin/sh
touch "$TEST_DIR/live_changed"
exit 1
HOOK
chmod 700 "$T/bin/partial_hook"
BP_CONFIG_APPLY_HOOK="$T/bin/partial_hook"; export BP_CONFIG_APPLY_HOOK
run_set
[ "$rc" -eq 8 ]
assert_old
[ -e "$T/live_changed" ]
printf 'PASS partial live side effect is not reported as rolled back\n'
reset
BP_CONFIG_APPLY_HOOK=true; export BP_CONFIG_APPLY_HOOK
touch "$T/one_commit_failure"
run_set
[ "$rc" -eq 1 ]
assert_old
printf 'PASS failed UCI commit before apply retains ordinary failure code\n'
reset
cat > "$T/bin/not_executable" <<'HOOK'
#!/bin/sh
exit 0
HOOK
chmod 600 "$T/bin/not_executable"
BP_CONFIG_APPLY_HOOK="$T/bin/not_executable"; export BP_CONFIG_APPLY_HOOK
run_set
[ "$rc" -eq 7 ]
assert_old
[ ! -s "$T/mutations" ]
printf 'PASS non-executable apply hook rejected before mutation\n'
printf 'ALL PASS — missing/failed apply fail-closed checks (disposable UCI)\n'
