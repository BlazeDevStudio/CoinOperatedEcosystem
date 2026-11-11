#!/bin/sh
# P0 Experiments #31 — regression: a failed receipt must leave balances unchanged.
# Was an expected-RED witness until the member transaction journal landed
# (see member_txn_journal.sh for the crash-injection suite).
# Disposable host-only failure injection. Do not execute on a shop router.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d "${TMPDIR:-/tmp}/bp-member-atomic.XXXXXX")" || exit 2
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
mkdir -p "$T/state" "$T/run"

export BP_STATE="$T/state" BP_RUN="$T/run" REQUEST_METHOD=GET
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"

# No production UCI, flush, real disk sync or customer records.
bp_cfg() {
  case "$1" in
    durable_sync) printf '0\n';;
    member_event_history) printf '128\n';;
    *) return 1;;
  esac
}
sync() { :; }

# Exactly 11 tab-separated fields per real member record.
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  a1 Alpha 1 lab salt hash 1 200 1 1700000000 fixture \
  b2 Beta 1 lab salt hash 1 100 1 1700000000 fixture \
  > "$BP_MEMBERS"
: > "$BP_MEMBER_EVENTS"
printf '1\n' > "$BP_MEMBER_REVISION"
bp_member_init

# Force the receipt write to fail AFTER the real transfer function attempts
# its members.tsv snapshot rename. This is a POSIX shell mock, not power loss.
bp_member_event_record() { return 8; }

bp_member_lock || { echo 'SETUP FAIL: member lock'; exit 2; }
rc=0
bp_member_transfer a1 b2 30 fixture transfer-fi-001 >/dev/null 2>&1 || rc=$?
bp_member_unlock

[ "$rc" -ne 0 ] || { echo 'FAIL: transfer acknowledged without receipt'; exit 1; }
[ -e "$BP_STATE/paid-state-uncertain" ] ||
  { echo 'FAIL: financial uncertainty marker missing'; exit 1; }
[ ! -s "$BP_MEMBER_EVENTS" ] ||
  { echo 'FAIL: unexpected receipt'; exit 1; }

# A retry must not add a second coin while state is quarantined.
retry_rc=0
bp_member_transfer a1 b2 30 fixture transfer-fi-001 >/dev/null 2>&1 || retry_rc=$?
[ "$retry_rc" -ne 0 ] || { echo 'FAIL: uncertain transfer retried'; exit 1; }

from="$(awk -F '\t' '$1=="a1" {print $8}' "$BP_MEMBERS")"
to="$(awk -F '\t' '$1=="b2" {print $8}' "$BP_MEMBERS")"

# This is the required atomicity invariant: if there is no committed receipt,
# neither member row may advance. The journaled commit in member.sh upholds
# this; the uncertainty marker additionally stops ACK and later credits.
if [ "$from" = 200 ] && [ "$to" = 100 ]; then
  echo 'PASS: failed receipt left both balances unchanged'
  exit 0
fi
echo "FAIL: no receipt, but member balances moved (${from:-missing}/${to:-missing}); issue #31 regression"
exit 1
