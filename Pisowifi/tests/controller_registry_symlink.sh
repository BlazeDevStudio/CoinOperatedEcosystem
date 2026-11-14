#!/bin/sh
# Noncustomer source-linked registry path integrity test, /tmp only.
# Reject symlinked registry before touch/chmod/read/write; a forged path
# must never modify the file outside the controller-state directory.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
export BP_STATE="$T/state" BP_RUN="$T/run"
mkdir -p "$BP_STATE" "$BP_RUN"
bp_init_dirs() { mkdir -p "$BP_STATE" "$BP_RUN"; }
bp_durable_sync() { :; }
bp_tmp_suffix() { printf '%s' "$$"; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"

printf 'external-evidence\n' > "$T/external.tsv"
cp "$T/external.tsv" "$T/original.tsv"
ln -s "$T/external.tsv" "$BP_CONTROLLERS"
if bp_controller_init; then
  echo 'CONTROLLER_REGISTRY_SYMLINK_RED: initialization accepted symlink' >&2
  exit 1
fi
if bp_controller_ensure 'forged.01'; then
  echo 'CONTROLLER_REGISTRY_SYMLINK_RED: auto-enrollment followed symlink' >&2
  exit 1
fi
if bp_controller_set 'forged.01' 1 1 0 0 -1 -1 -1 1 1 1 40 400 6; then
  echo 'CONTROLLER_REGISTRY_SYMLINK_RED: admin accepted forged path' >&2
  exit 1
fi
cmp -s "$T/external.tsv" "$T/original.tsv" || {
  echo 'CONTROLLER_REGISTRY_SYMLINK_RED: external target modified' >&2
  exit 1
}
[ -L "$BP_CONTROLLERS" ] || {
  echo 'CONTROLLER_REGISTRY_SYMLINK_RED: malicious symlink replaced' >&2
  exit 1
}
# A plain, regular registry remains usable following safe operator cleanup.
rm -f "$BP_CONTROLLERS"
bp_controller_ensure 'normal.01'
[ "$(LC_ALL=C awk -F '\t' '$1=="normal.01"{print $2 ":" $3}' "$BP_CONTROLLERS")" = "0:0" ]
echo 'CONTROLLER_REGISTRY_SYMLINK_GREEN (path rejected; external evidence intact; mock only)'
