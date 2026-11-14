#!/bin/sh
# Noncustomer /tmp-only source regression: implicit registration must DENY.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
BP_STATE="$T/state"; BP_RUN="$T/run"
export BP_STATE BP_RUN
mkdir -p "$BP_STATE" "$BP_RUN"
bp_init_dirs() { mkdir -p "$BP_STATE" "$BP_RUN"; }
bp_durable_sync() { :; }
bp_tmp_suffix() { printf '%s' "$$"; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"

# The old grep regex treated the literal '.' as any character and silently
# reused an unrelated controller row instead of creating an exact identity.
bp_controller_ensure 'unitA01'
bp_controller_ensure 'unit.01'
bp_controller_ensure 'unitA01'
[ "$(wc -l < "$BP_CONTROLLERS")" -eq 2 ] || {
  echo 'CONTROLLER_REGISTRATION_FAIL: identity collision or duplicate row' >&2
  exit 1
}
for id in 'unitA01' 'unit.01'; do
  result="$(LC_ALL=C awk -F '\t' -v d="$id" '$1==d {print $2 ":" $3; n++} END {if(n!=1)exit 8}' "$BP_CONTROLLERS")" || exit 1
  [ "$result" = '0:0' ] || {
    echo "CONTROLLER_REGISTRATION_FAIL: $id auto-enabled" >&2
    exit 1
  }
done

# Explicit admin provisioning still works for exactly the selected ID.
bp_controller_set 'unitA01' 1 1 0 0 -1 -1 -1 1 1 1 40 400 6
[ "$(LC_ALL=C awk -F '\t' '$1=="unitA01" {print $2 ":" $3}' "$BP_CONTROLLERS")" = '1:1' ]
[ "$(LC_ALL=C awk -F '\t' '$1=="unit.01" {print $2 ":" $3}' "$BP_CONTROLLERS")" = '0:0' ]
echo 'CONTROLLER_REGISTRATION_DEFAULT_DENY_PASS (disposable mocked sync; NOT hardware or finance acceptance)'
