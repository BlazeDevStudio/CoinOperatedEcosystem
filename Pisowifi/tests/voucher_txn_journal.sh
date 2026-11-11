#!/bin/sh
# Issue #31 / Turnkey Appliances — voucher transaction journal: crash-injection regression suite.
# Disposable host-only mocks (shell function overrides). These are SIMULATED
# interruptions, NOT power-cut proof. Do not run on a shop router.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d "${TMPDIR:-/tmp}/bp-voucher-txn.XXXXXX")" || exit 2
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
mkdir -p "$T/state" "$T/run"

export BP_STATE="$T/state" BP_RUN="$T/run" REQUEST_METHOD=GET
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"

bp_cfg() {
  case "$1" in
    durable_sync) printf '0\n';;
    event_history) printf '128\n';;
    *) return 1;;
  esac
}
sync() { :; }

restore_common() {
  . "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
  bp_cfg() {
    case "$1" in
      durable_sync) printf '0\n';;
      event_history) printf '128\n';;
      *) return 1;;
    esac
  }
}

fail() { echo "FAIL: $*"; exit 1; }
pass() { echo "PASS: $*"; }

seed() {
  rm -f "$BP_STATE"/voucher-txn.* "$BP_STATE"/.voucher-txn.* "$BP_STATE/paid-state-uncertain"
  printf 'dev01\t500\t0\t0\t0\t0\t02:00:00:00:00:01\t10.0.0.10\t\n' > "$BP_ACCOUNTS"
  printf 'VCH-100\t100\t\nVCH-200\t200\t\nVCH-300\t300\t\n' > "$BP_VOUCHERS"
  chmod 600 "$BP_ACCOUNTS" "$BP_VOUCHERS"
}
acc_credit() { awk -F '\t' -v d="$1" '$1==d {print $2}' "$BP_ACCOUNTS"; }
vch_dev() { awk -F '\t' -v c="$1" '$1==c {print $4}' "$BP_VOUCHERS"; }
reconcile() { rm -f "$BP_STATE/paid-state-uncertain"; }
no_txn_files() {
  for f in "$BP_STATE"/voucher-txn.* "$BP_STATE"/.voucher-txn.*; do [ ! -e "$f" ] || return 1; done
  return 0
}
snapshot() { cat "$BP_ACCOUNTS" "$BP_VOUCHERS" | sha256sum | awk '{print $1}'; }

do_redeem() {
  _dev="$1"
  _code="$2"
  _mac="$3"
  _ip="$4"
  bp_lock || return 8
  _line="$(bp_account_line "$_dev")"
  _credit="$(printf '%s' "$_line" | cut -f2)"
  _expiry="$(printf '%s' "$_line" | cut -f3)"
  _rem="$(printf '%s' "$_line" | cut -f4)"
  _p="$(printf '%s' "$_line" | cut -f5)"
  _ps="$(printf '%s' "$_line" | cut -f6)"
  _ev="$(printf '%s' "$_line" | cut -f9)"
  _v_event="v:$(bp_event_hash "voucher|$_code")"
  _used="$(bp_find_event_device "$_v_event")"
  [ -z "$_used" ] || { bp_unlock; return 7; }
  _cents="$(awk -F '\t' -v c="$_code" '$1==c && (NF<3 || $3=="") {print $2; exit}' "$BP_VOUCHERS")"
  [ -n "$_cents" ] || { bp_unlock; return 7; }

  _newev="$(bp_events_push "$_ev" "$_v_event")" || { bp_unlock; return 8; }
  _newcredit=$((_credit+_cents))
  if ! bp_paid_begin; then
    bp_unlock
    return 8
  fi
  _now="$(bp_now 2>/dev/null || date +%s)"
  if ! bp_voucher_txn_begin ||
     ! bp_account_build "$BP_VOUCHER_TXN_ACCOUNTS" "$_dev" "$_newcredit" "$_expiry" "$_rem" "$_p" "$_ps" "$_mac" "$_ip" "$_newev" ||
     ! bp_voucher_build "$BP_VOUCHER_TXN_VOUCHERS" "$_code" "$_dev" "$_now"; then
    bp_voucher_txn_clear_stage
    bp_paid_abort
    bp_unlock
    return 8
  fi
  if ! bp_voucher_txn_commit; then
    bp_paid_abort
    bp_unlock
    return 8
  fi
  if ! bp_paid_commit; then
    bp_unlock
    return 8
  fi
  bp_unlock
  return 0
}

bp_init_dirs

# 1. Success: accounts and vouchers advance together; journal files removed.
seed
do_redeem dev01 VCH-100 02:00:00:00:00:01 10.0.0.10 || fail 'redeem should succeed'
[ "$(acc_credit dev01)" = 600 ] || fail "expected 600 credit, got $(acc_credit dev01)"
[ "$(vch_dev VCH-100)" = dev01 ] || fail "voucher VCH-100 not marked used by dev01"
no_txn_files || fail 'journal files left after success'
[ ! -e "$BP_STATE/paid-state-uncertain" ] || fail 'uncertain marker left after success'
pass 'success commits accounts and vouchers together'

# 2. Failure before commit: live files byte-identical.
seed; before="$(snapshot)"
bp_voucher_build() { return 8; }
rc=0; do_redeem dev01 VCH-200 02:00:00:00:00:01 10.0.0.10 || rc=$?
[ "$rc" -ne 0 ] || fail 'failure before commit was acknowledged'
[ "$(snapshot)" = "$before" ] || fail 'live files changed despite failure before commit'
[ -e "$BP_STATE/paid-state-uncertain" ] || fail 'uncertainty marker must be retained'
no_txn_files || fail 'stale stage left after pre-commit failure'
pass 'failure before commit leaves accounts and vouchers unchanged'
# restore real common.sh
restore_common

# 3. Crash right after commit record, before files are applied.
seed
bp_voucher_txn_apply() { return 8; } # simulated crash
rc=0; do_redeem dev01 VCH-200 02:00:00:00:00:01 10.0.0.10 || rc=$?
[ "$rc" -ne 0 ] || fail 'interrupted commit was acknowledged'
[ "$(acc_credit dev01)" = 500 ] || fail 'live accounts changed before apply'
[ -z "$(vch_dev VCH-200)" ] || fail 'live vouchers changed before apply'
[ -e "$BP_VOUCHER_TXN_COMMIT" ] || fail 'commit record missing'
restore_common # reboot: real apply
reconcile
bp_lock || fail 'recovery lock failed'
bp_unlock
[ "$(acc_credit dev01)" = 700 ] || fail "roll-forward incomplete on accounts $(acc_credit dev01)"
[ "$(vch_dev VCH-200)" = dev01 ] || fail "roll-forward incomplete on vouchers $(vch_dev VCH-200)"
no_txn_files || fail 'journal files left after recovery'
pass 'crash after commit record rolls forward both accounts and vouchers'

# 3b. Replay after recovery is idempotent (no double credit).
rc=0; do_redeem dev01 VCH-200 02:00:00:00:00:01 10.0.0.10 || rc=$?
[ "$rc" -ne 0 ] || fail 'replay of used voucher must be rejected'
[ "$(acc_credit dev01)" = 700 ] || fail 'double credit on replay'
pass 'replay after recovery is idempotent (no double credit)'

# 4. Crash mid-apply: accounts applied, but vouchers still staged.
seed
n=0
mv() {
  n=$((n+1))
  # 1: paid marker, 2: commit record, 3: accounts applied; 4 (vouchers): simulated crash
  if [ "$n" -ge 4 ]; then return 1; fi
  command mv "$@"
}
rc=0; do_redeem dev01 VCH-300 02:00:00:00:00:01 10.0.0.10 || rc=$?
unset -f mv
[ "$rc" -ne 0 ] || fail 'mid-apply crash was acknowledged'
[ "$(acc_credit dev01)" = 800 ] || fail "expected half-applied accounts got $(acc_credit dev01)"
[ -z "$(vch_dev VCH-300)" ] || fail 'vouchers was applied before crash'
reconcile
bp_lock || fail 'recovery lock failed'
bp_unlock
[ "$(acc_credit dev01)" = 800 ] && [ "$(vch_dev VCH-300)" = dev01 ] ||
  fail "mid-apply recovery incomplete $(acc_credit dev01)/$(vch_dev VCH-300)"
no_txn_files || fail 'journal files left after mid-apply recovery'
pass 'crash mid-apply is completed by recovery'

# 5. Tampered stage fails closed without touching live state.
seed
bp_voucher_txn_apply() { return 8; }
do_redeem dev01 VCH-100 02:00:00:00:00:01 10.0.0.10 || true
restore_common
before="$(snapshot)"
printf 'tampered-voucher\n' >> "$BP_VOUCHER_TXN_VOUCHERS"
reconcile
rc=0; bp_lock || rc=$?
[ "$rc" -eq 8 ] || fail "tampered stage must fail closed (rc=$rc)"
[ "$(snapshot)" = "$before" ] || fail 'live files changed on tampered recovery'
[ -e "$BP_VOUCHER_TXN_COMMIT" ] || fail 'evidence (commit record) must be preserved'
pass 'tampered stage fails closed without touching live state'

# 6. Uncommitted stage is discarded; live state untouched.
seed; before="$(snapshot)"
printf 'junk\n' > "$BP_VOUCHER_TXN_ACCOUNTS"
printf 'junk\n' > "$BP_VOUCHER_TXN_VOUCHERS"
bp_lock || fail 'lock'
bp_unlock
[ "$(snapshot)" = "$before" ] || fail 'live changed by stale stage'
no_txn_files || fail 'stale stage not discarded'
pass 'uncommitted stage is discarded; live state untouched'

# 7. End-to-end CGI redeem action test
seed
DEV_HEX="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
printf '%s\t500\t0\t0\t0\t0\t02:00:00:00:00:01\t10.0.0.10\t\n' "$DEV_HEX" > "$BP_ACCOUNTS"
mkdir -p "$T/bin"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.lan_if') echo br-lan;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *'get blazepwifi.main.event_history') echo 128;;
  *) exit 1;;
esac
UCI
cat > "$T/bin/ip" <<'IP'
#!/bin/sh
echo "10.0.0.10 dev br-lan lladdr 02:00:00:00:00:01 REACHABLE"
IP
chmod +x "$T/bin/"*
BODY="action=redeem&device=${DEV_HEX}&code=VCH-100"
CONTENT_LENGTH="${#BODY}"
OUTPUT="$(printf '%s' "$BODY" | PATH="$T/bin:$PATH" BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh" REQUEST_METHOD=POST HTTP_HOST="10.0.0.1" REMOTE_ADDR="10.0.0.10" CONTENT_TYPE="application/x-www-form-urlencoded" CONTENT_LENGTH="$CONTENT_LENGTH" sh "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/api")"
printf '%s' "$OUTPUT" | grep -q '{"ok":true,"credit_cents":600}' || fail "CGI redeem output mismatch: $OUTPUT"
[ "$(acc_credit "$DEV_HEX")" = 600 ] || fail "CGI redeem did not update credit: $(acc_credit "$DEV_HEX")"
[ "$(vch_dev VCH-100)" = "$DEV_HEX" ] || fail "CGI redeem did not mark voucher used"
no_txn_files || fail 'CGI redeem left journal files'
pass 'end-to-end CGI api redeem action commits through transaction journal'

echo 'ALL VOUCHER TXN JOURNAL TESTS PASS (SIMULATED FAULTS ONLY; NO POWER-CUT PROOF)'
