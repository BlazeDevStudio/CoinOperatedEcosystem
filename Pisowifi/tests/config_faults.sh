#!/bin/sh
# Execute real config.sh with mocked UCI commands only; never write router UCI.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/run"
printf '%s\n' 'blazepwifi.main.admin_port=8443' > "$T/uci.db"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
[ "${1:-}" = -q ] && shift
cmd="$1"; shift
key="${1:-}"
case "$cmd" in
  show)
    [ ! -f "$TEST_DIR/fail_show" ] || exit 46
    [ "$key" = blazepwifi.main ] || exit 47
    [ ! -f "$TEST_DIR/fail_show_section" ] && printf '%s\n' 'blazepwifi.main=core'
    cat "$TEST_DIR/uci.db" ;;
  get)
    [ ! -f "$TEST_DIR/fail_get" ] || exit 48
    record="$(grep -F "${key}=" "$TEST_DIR/uci.db" | tail -n 1)"
    [ -n "$record" ] || exit 1
    printf '%s\n' "${record#*=}" ;;
  set)
    case "$key" in
      blazepwifi.main.admin_port=8443)
        [ ! -f "$TEST_DIR/fail_restore_set" ] || exit 41 ;;
    esac
    k="${key%%=*}"; v="${key#*=}"
    grep -Fv "$k=" "$TEST_DIR/uci.db" > "$TEST_DIR/next.db" || true
    printf '%s=%s\n' "$k" "$v" >> "$TEST_DIR/next.db"
    mv "$TEST_DIR/next.db" "$TEST_DIR/uci.db" ;;
  delete)
    [ ! -f "$TEST_DIR/fail_delete" ] || exit 42
    grep -Fv "$key=" "$TEST_DIR/uci.db" > "$TEST_DIR/next.db" || true
    mv "$TEST_DIR/next.db" "$TEST_DIR/uci.db" ;;
  commit)
    if [ -f "$TEST_DIR/fail_commit_once" ]; then rm "$TEST_DIR/fail_commit_once"; exit 43; fi
    returncode=0; [ ! -f "$TEST_DIR/fail_commit_always" ] || returncode=44
    exit "$returncode" ;;
  *) exit 45 ;;
esac
UCI
chmod +x "$T/bin/uci"
export PATH="$T/bin:$PATH" TEST_DIR="$T" BP_RUN="$T/run"
CONFIG="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
sh -n "$CONFIG"
. "$CONFIG"
# $1 target value, capture return code and stderr without set -e abort.
run_set() {
  set +e
  bp_config_set admin_port "$1" > "$T/stdout" 2> "$T/stderr"
  rc=$?
  set -e
}
get_port() { uci get blazepwifi.main.admin_port; }
reset() {
  rm -f "$T"/fail_* "$T/injected"
  printf '%s\n' 'blazepwifi.main.admin_port=8443' > "$T/uci.db"
  BP_CONFIG_APPLY_HOOK=true; export BP_CONFIG_APPLY_HOOK
  : > "$T/audit"
}
bp_auth_audit() { printf 'called\n' >> "$T/audit"; }
reset
run_set 9443
[ "$rc" -eq 0 ] && [ "$(get_port)" = 9443 ] && [ "$(wc -l < "$T/audit")" -eq 1 ]
printf 'PASS normal config commit and audit\n'
reset
touch "$T/fail_show"
run_set 9443
[ "$rc" -eq 8 ] && [ "$(get_port)" = 8443 ] && [ ! -s "$T/audit" ]
grep -q 'CRITICAL: cannot snapshot UCI section' "$T/stderr"
printf 'PASS section snapshot I/O failure refuses mutation\n'
reset
touch "$T/fail_show_section"
run_set 9443
[ "$rc" -eq 8 ] && [ "$(get_port)" = 8443 ] && [ ! -s "$T/audit" ]
grep -q 'CRITICAL: UCI section missing' "$T/stderr"
printf 'PASS missing section refuses mutation\n'
reset
touch "$T/fail_get"
run_set 9443
[ "$rc" -eq 8 ] && [ ! -s "$T/audit" ]
[ "$(cat "$T/uci.db")" = 'blazepwifi.main.admin_port=8443' ]
grep -q 'CRITICAL: UCI option exists but its value cannot be read' "$T/stderr"
printf 'PASS read error for existing option refuses mutation\n'
reset
: > "$T/uci.db"
run_set 9443
[ "$rc" -eq 0 ] && [ "$(get_port)" = 9443 ]
printf 'PASS truly absent option can be configured\n'
reset
BP_CONFIG_APPLY_HOOK=false; export BP_CONFIG_APPLY_HOOK
run_set 9443
[ "$rc" -eq 8 ] && [ "$(get_port)" = 8443 ] && [ ! -s "$T/audit" ]
grep -Fq 'CRITICAL: UCI restored, but live configuration state unverified' "$T/stderr"
printf 'PASS failed apply restores UCI but leaves live status uncertain\n'
reset
: > "$T/uci.db"
BP_CONFIG_APPLY_HOOK=false; export BP_CONFIG_APPLY_HOOK
run_set 9443
[ "$rc" -eq 8 ] && [ -z "$(cat "$T/uci.db")" ] && [ ! -s "$T/audit" ]
printf 'PASS absent option restored by delete on failed apply\n'
reset
touch "$T/fail_commit_once"
run_set 9443
[ "$rc" -eq 1 ] && [ "$(get_port)" = 8443 ] && [ ! -s "$T/audit" ]
printf 'PASS commit failure restores old value\n'
reset
touch "$T/fail_restore_set"
BP_CONFIG_APPLY_HOOK=false; export BP_CONFIG_APPLY_HOOK
run_set 9443
[ "$rc" -eq 8 ] && [ "$(get_port)" = 9443 ] && [ ! -s "$T/audit" ]
grep -q 'CRITICAL: UCI rollback failed' "$T/stderr"
printf 'PASS failed rollback reported as uncertain, not ordinary rejection\n'
reset
: > "$T/uci.db"
touch "$T/fail_delete"
BP_CONFIG_APPLY_HOOK=false; export BP_CONFIG_APPLY_HOOK
run_set 9443
[ "$rc" -eq 8 ] && [ "$(get_port)" = 9443 ] && [ ! -s "$T/audit" ]
grep -q 'CRITICAL: UCI rollback failed' "$T/stderr"
printf 'PASS failed rollback delete reported as uncertain\n'
reset
BP_CONFIG_APPLY_HOOK="false; touch $T/injected"; export BP_CONFIG_APPLY_HOOK
run_set 9443
[ "$rc" -ne 0 ] && [ "$(get_port)" = 8443 ] && [ ! -e "$T/injected" ] && [ ! -s "$T/audit" ]
printf 'PASS hook with shell operators rejected without code execution\n'
reset
BP_CONFIG_APPLY_HOOK=true; export BP_CONFIG_APPLY_HOOK
run_set 9443
[ "$rc" -eq 0 ] && [ "$(get_port)" = 9443 ]
printf 'PASS single executable hook preserved\n'
reset
run_set 70000
[ "$rc" -eq 2 ] && [ "$(get_port)" = 8443 ] && [ ! -s "$T/audit" ]
printf 'PASS invalid config rejected before UCI mutation\n'
reset
BP_CONFIG_APPLY_HOOK=false; export BP_CONFIG_APPLY_HOOK
touch "$T/fail_commit_always"
run_set 9443
[ "$rc" -eq 8 ] && [ "$(get_port)" = 8443 ] && [ ! -s "$T/audit" ]
grep -q 'CRITICAL: UCI rollback failed' "$T/stderr"
printf 'PASS persistent commit failure reported as uncertain\n'
reset
value="$(bp_config_get_optional admin_port)"
[ "$value" = 8443 ]
printf 'PASS optional config getter reads existing setting\n'
reset
: > "$T/uci.db"
value="$(bp_config_get_optional admin_port)"
[ -z "$value" ]
printf 'PASS optional config getter permits genuinely absent option\n'
reset
touch "$T/fail_get"
set +e
value="$(bp_config_get_optional admin_port)"
getter_rc=$?
set -e
[ "$getter_rc" -eq 8 ] && [ -z "$value" ]
printf 'PASS optional getter rejects unreadable existing setting\n'
reset
touch "$T/fail_show"
set +e
value="$(bp_config_get_optional admin_port)"
getter_rc=$?
set -e
[ "$getter_rc" -eq 8 ] && [ -z "$value" ]
printf 'PASS optional getter rejects unreadable section\n'
printf 'ALL PASS — source-linked UCI fault injection (18 cases)\n'
