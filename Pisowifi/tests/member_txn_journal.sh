#!/bin/sh
# Issue #31 — member transaction journal: crash-injection regression suite.
# Disposable host-only mocks (shell function overrides). These are SIMULATED
# interruptions, NOT power-cut proof. Do not run on a shop router.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d "${TMPDIR:-/tmp}/bp-member-txn.XXXXXX")" || exit 2
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
mkdir -p "$T/state" "$T/run"

export BP_STATE="$T/state" BP_RUN="$T/run" REQUEST_METHOD=GET
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"

bp_cfg() {
  case "$1" in
    durable_sync) printf '0\n';;
    member_event_history) printf '128\n';;
    *) return 1;;
  esac
}
sync() { :; }

fail() { echo "FAIL: $*"; exit 1; }
pass() { echo "PASS: $*"; }

seed() {
  rm -f "$BP_STATE"/member-txn.* "$BP_STATE"/.member-txn.* "$BP_STATE/paid-state-uncertain"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    a1 Alpha 1 lab salt hash 1 200 1 1700000000 fixture \
    b2 Beta 1 lab salt hash 1 100 1 1700000000 fixture > "$BP_MEMBERS"
  : > "$BP_MEMBER_EVENTS"
  printf '1\n' > "$BP_MEMBER_REVISION"
  chmod 600 "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION"
}
bal() { awk -F '\t' -v u="$1" '$1==u {print $8}' "$BP_MEMBERS"; }
rev() { cat "$BP_MEMBER_REVISION"; }
nev() { wc -l < "$BP_MEMBER_EVENTS" | tr -d ' '; }
# Marker is operator-reconciled in production; tests model that explicitly.
reconcile() { rm -f "$BP_STATE/paid-state-uncertain"; }
no_txn_files() {
  for f in "$BP_STATE"/member-txn.*; do [ ! -e "$f" ] || return 1; done
  return 0
}
snapshot() { cat "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION" | sha256sum | awk '{print $1}'; }

bp_member_init

# 1. Success: balances, receipt, revision advance together; journal is gone.
seed
bp_member_lock || fail 'lock'
bp_member_transfer a1 b2 30 fixture ev-ok >/dev/null || fail 'transfer should succeed'
bp_member_unlock
[ "$(bal a1)" = 170 ] && [ "$(bal b2)" = 130 ] || fail "balances $(bal a1)/$(bal b2)"
[ "$(nev)" = 1 ] || fail 'receipt count'
[ "$(rev)" = 2 ] || fail "revision $(rev)"
no_txn_files || fail 'journal files left after success'
[ ! -e "$BP_STATE/paid-state-uncertain" ] || fail 'marker left after success'
pass 'success commits balances, receipt and revision together'

# 2. Receipt failure before commit: live files byte-identical (incl. revision).
seed; before="$(snapshot)"
bp_member_event_record() { return 8; }
bp_member_lock || fail 'lock'
rc=0; bp_member_transfer a1 b2 30 fixture ev-rf >/dev/null 2>&1 || rc=$?
bp_member_unlock
[ "$rc" -ne 0 ] || fail 'receipt failure was acknowledged'
[ "$(snapshot)" = "$before" ] || fail 'live files changed despite receipt failure'
[ -e "$BP_STATE/paid-state-uncertain" ] || fail 'marker must be retained'
pass 'receipt failure leaves members, receipts and revision unchanged'
# restore real recorder
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"

# 3. Crash right after the commit record, before any file is applied.
seed
bp_member_txn_apply() { return 8; }       # simulated crash: nothing applied
bp_member_lock || fail 'lock'
rc=0; bp_member_transfer a1 b2 30 fixture ev-c1 >/dev/null 2>&1 || rc=$?
bp_member_unlock
[ "$rc" -ne 0 ] || fail 'interrupted commit was acknowledged'
[ "$(bal a1)" = 200 ] || fail 'live changed before apply'
[ -e "$BP_MEMBER_TXN_COMMIT" ] || fail 'commit record missing'
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"   # "reboot": real apply
bp_member_lock && fail 'lock must stay blocked by marker' || true
reconcile
bp_member_lock || fail 'recovery lock failed'
bp_member_unlock
[ "$(bal a1)" = 170 ] && [ "$(bal b2)" = 130 ] && [ "$(nev)" = 1 ] && [ "$(rev)" = 2 ] ||
  fail "roll-forward incomplete $(bal a1)/$(bal b2)/$(nev)/$(rev)"
no_txn_files || fail 'journal files left after recovery'
pass 'crash after commit record rolls forward all three files'

# 3b. Retry of the same event after recovery must NOT credit twice.
bp_member_lock || fail 'lock'
r="$(bp_member_transfer a1 b2 30 fixture ev-c1)" || fail 'replay should ACK idempotently'
bp_member_unlock
[ "$(bal a1)" = 170 ] && [ "$(bal b2)" = 130 ] && [ "$(nev)" = 1 ] || fail 'double credit on replay'
pass 'replay after recovery is idempotent (no double credit)'

# 4. Crash mid-apply: members renamed, events/revision still staged.
seed
n=0
mv() {
  n=$((n+1))
  # 1: paid marker, 2: commit record, 3: members applied; 4+ (events): crash
  if [ "$n" -ge 4 ]; then return 1; fi
  command mv "$@"
}
bp_member_lock || fail 'lock'
rc=0; bp_member_transfer a1 b2 30 fixture ev-c2 >/dev/null 2>&1 || rc=$?
bp_member_unlock
unset -f mv
[ "$rc" -ne 0 ] || fail 'mid-apply crash was acknowledged'
[ "$(bal a1)" = 170 ] && [ "$(nev)" = 0 ] || fail "expected half-applied fixture got $(bal a1)/$(nev)"
reconcile
bp_member_lock || fail 'recovery lock failed'
bp_member_unlock
[ "$(bal a1)" = 170 ] && [ "$(bal b2)" = 130 ] && [ "$(nev)" = 1 ] && [ "$(rev)" = 2 ] ||
  fail "mid-apply recovery incomplete $(bal a1)/$(bal b2)/$(nev)/$(rev)"
no_txn_files || fail 'journal files left after mid-apply recovery'
pass 'crash mid-apply is completed by recovery (balance never lacks receipt)'

# 5. Tampered staged file: recovery fails closed and keeps evidence.
seed
bp_member_txn_apply() { return 8; }
bp_member_lock || fail 'lock'
bp_member_transfer a1 b2 30 fixture ev-t >/dev/null 2>&1 || true
bp_member_unlock
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
before="$(snapshot)"
printf 'tampered\n' >> "$BP_MEMBER_TXN_MEMBERS"
reconcile
rc=0; bp_member_lock || rc=$?
[ "$rc" -eq 8 ] || fail "tampered stage must fail closed (rc=$rc)"
[ "$(snapshot)" = "$before" ] || fail 'live files changed on tampered recovery'
[ -e "$BP_MEMBER_TXN_COMMIT" ] || fail 'evidence (commit record) must be preserved'
pass 'tampered stage fails closed without touching live state'

# 6. Uncommitted stage (crash before commit record): discarded, live untouched.
seed; before="$(snapshot)"
printf 'junk\n' > "$BP_MEMBER_TXN_MEMBERS"; printf 'junk\n' > "$BP_MEMBER_TXN_EVENTS"
bp_member_lock || fail 'lock'
bp_member_unlock
[ "$(snapshot)" = "$before" ] || fail 'live changed by stale stage'
no_txn_files || fail 'stale stage not discarded'
pass 'uncommitted stage is discarded; live state untouched'

# 7. Balance change and member delete also go through the journal.
seed
bp_member_lock || fail 'lock'
bp_member_balance_change a1 add 50 fixture ev-add >/dev/null || fail 'add failed'
bp_member_unlock
[ "$(bal a1)" = 250 ] && [ "$(nev)" = 1 ] && [ "$(rev)" = 2 ] || fail 'balance_change not atomic'
bp_member_lock || fail 'lock'
bp_member_balance_change a1 subtract 250 fixture ev-sub >/dev/null || fail 'subtract failed'
bp_member_delete a1 fixture >/dev/null || fail 'delete failed'
bp_member_unlock
[ -z "$(awk -F '\t' '$1=="a1"' "$BP_MEMBERS")" ] && [ "$(nev)" = 3 ] && [ "$(rev)" = 4 ] || fail 'delete not atomic'
no_txn_files || fail 'journal files left'
pass 'balance_change and delete commit through the journal'

# 8. Member create, patch and set_password also commit via the journal;
# receipt failure on create leaves members.tsv and revision untouched.
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
seed; before="$(snapshot)"
bp_member_event_record() { return 8; }
bp_member_lock || fail 'lock'
rc=0; bp_member_create c3 Charlie 'SecretPass123' fixture >/dev/null 2>&1 || rc=$?
bp_member_unlock
[ "$rc" -ne 0 ] || fail 'create receipt failure was acknowledged'
[ "$(snapshot)" = "$before" ] || fail 'create receipt failure mutated live state'
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
reconcile
bp_member_lock || fail 'lock'
bp_member_create c3 Charlie 'SecretPass123' fixture >/dev/null || fail 'create failed'
bp_member_patch c3 'CharlieUpdated' 1 fixture >/dev/null || fail 'patch failed'
bp_member_set_password c3 'NewSecret456' fixture >/dev/null || fail 'set_password failed'
bp_member_unlock
[ "$(nev)" = 3 ] && [ "$(rev)" = 4 ] || fail "create/patch/password rev=$(rev) nev=$(nev)"
no_txn_files || fail 'journal files left after create/patch/password'
pass 'member create, patch and set_password commit atomically through the journal'

# 9. Rental coin-credit journal: receipt failure leaves lease unchanged,
# and crash after rental-txn.commit rolls forward both devices and events.
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
reconcile
bp_rental_init
printf 'dev01\tsec01\t1800000000\tPhone1\t1700000000\n' > "$BP_RENTAL_DEVICES"
: > "$BP_RENTAL_EVENTS"
chmod 600 "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS"
r_before="$(cat "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS" | sha256sum | awk '{print $1}')"
bp_rental_append_paid_receipt() { return 8; }
rc=0; bp_rental_apply_coin dev01 vendo1 nonce1 dev01 2 >/dev/null 2>&1 || rc=$?
[ "$rc" -ne 0 ] || fail 'rental receipt failure was acknowledged'
r_after="$(cat "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS" | sha256sum | awk '{print $1}')"
[ "$r_after" = "$r_before" ] || fail 'rental lease changed despite receipt failure'
[ -e "$BP_STATE/paid-state-uncertain" ] || fail 'rental uncertainty marker missing'
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
reconcile
bp_rental_txn_apply() { return 8; }
rc=0; bp_rental_apply_coin dev01 vendo1 nonce1 dev01 2 >/dev/null 2>&1 || rc=$?
[ "$rc" -ne 0 ] || fail 'interrupted rental commit acknowledged'
[ -e "$BP_RENTAL_TXN_COMMIT" ] || fail 'rental commit record missing'
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
reconcile
# Next replay/read recovers the committed rental transaction and ACKs as duplicate
dup_out="$(bp_rental_apply_coin dev01 vendo1 nonce1 dev01 2)" || fail 'rental replay after recovery failed'
printf '%s' "$dup_out" | grep -q '^duplicate	' || fail "unexpected rental replay output: $dup_out"
[ ! -e "$BP_RENTAL_TXN_COMMIT" ] || fail 'rental commit record left after recovery'
pass 'rental coin-credit journal prevents unreceipted lease changes and rolls forward on recovery'

echo 'ALL MEMBER & RENTAL TXN JOURNAL TESTS PASS (SIMULATED FAULTS ONLY; NO POWER-CUT PROOF)'

