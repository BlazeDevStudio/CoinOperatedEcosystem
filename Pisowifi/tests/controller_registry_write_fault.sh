#!/bin/sh
# P0 controller registry write-fault regression. /tmp only; no real device.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
export BP_STATE="$T/state" BP_RUN="$T/run"
mkdir -p "$BP_STATE" "$BP_RUN" "$T/bin"
bp_init_dirs() { mkdir -p "$BP_STATE" "$BP_RUN"; }
bp_durable_sync() { :; }
bp_tmp_suffix() { printf '%s' "$$"; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"

bp_controller_ensure 'unit.01'
bp_controller_ensure 'unitB02'
[ "$(wc -l < "$BP_CONTROLLERS")" -eq 2 ]
before="$(sha256sum "$BP_CONTROLLERS" | cut -d' ' -f1)"
REAL_AWK="$(command -v awk)"; export REAL_AWK
cat > "$T/bin/awk" <<'AWK_FAULT'
#!/bin/sh
case "$*" in
  *'$1!=d {print}'*)
    printf 'copy-fault\n' >> "$BP_STATE/awk-fault-invoked"
    exit 74
    ;;
esac
exec "$REAL_AWK" "$@"
AWK_FAULT
chmod 755 "$T/bin/awk"
PATH="$T/bin:$PATH"; export PATH
hash -r
if bp_controller_set 'unit.01' 1 1 0 0 -1 -1 -1 1 1 1 40 400 6; then
  echo 'CONTROLLER_REGISTRY_FAULT_RED: admin ACKed failed state-copy' >&2
  exit 1
fi
[ -s "$BP_STATE/awk-fault-invoked" ] || {
  echo 'CONTROLLER_REGISTRY_FAULT_INVALID: copy failure not injected' >&2
  exit 2
}
after="$(sha256sum "$BP_CONTROLLERS" | cut -d' ' -f1)"
[ "$before" = "$after" ] || {
  echo 'CONTROLLER_REGISTRY_FAULT_RED: failed copy destroyed or modified registry' >&2
  exit 1
}
echo 'CONTROLLER_REGISTRY_FAULT_GREEN: denied failed copy; both controller rows preserved (mock only)'
