#!/bin/sh
# Source-linked, deterministic concurrent registration regression (disposable state).
# Pause the first completed registry lookup after it has read 'absent';
# a second request must NOT independently append the same controller.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"
p1=; p2=
cleanup() {
  [ -z "$p1" ] || kill "$p1" 2>/dev/null || true
  [ -z "$p2" ] || kill "$p2" 2>/dev/null || true
  rm -rf "$T"
}
trap cleanup EXIT HUP INT TERM
export BP_STATE="$T/state" BP_RUN="$T/run"
mkdir -p "$BP_STATE" "$BP_RUN" "$T/bin"
bp_init_dirs() { mkdir -p "$BP_STATE" "$BP_RUN"; }
bp_durable_sync() { :; }
bp_tmp_suffix() { printf '%s' "$$"; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"

REAL_AWK="$(command -v awk)"; export REAL_AWK
cat > "$T/bin/awk" <<'INJECT'
#!/bin/sh
case "$*" in
  *'print "found"; exit'*)
    "$REAL_AWK" "$@" || exit 74
    # Only the first lookup holds AFTER seeing no row. Under the old source,
    # process 2 can also see 'absent' and append before process 1 resumes.
    if [ ! -e "$BP_STATE/first-lookup-observed" ]; then
      : > "$BP_STATE/first-lookup-observed"
      sleep 2
    fi
    exit 0
    ;;
esac
exec "$REAL_AWK" "$@"
INJECT
chmod 755 "$T/bin/awk"
PATH="$T/bin:$PATH"; export PATH
hash -r

(bp_controller_ensure 'raced.01') & p1=$!
i=0
while [ ! -e "$BP_STATE/first-lookup-observed" ] && [ "$i" -lt 100 ]; do
  sleep 0.05
  i=$((i + 1))
done
if [ ! -e "$BP_STATE/first-lookup-observed" ]; then
  echo 'CONTROLLER_REGISTRATION_RACE_INVALID: lookup injection not reached' >&2
  exit 2
fi
(bp_controller_ensure 'raced.01') & p2=$!
wait "$p1" || exit 2; p1=
wait "$p2" || exit 2; p2=
# Unknown devices remain disabled and exactly one row per identity is allowed.
if ! "$REAL_AWK" -F '\t' '$1=="raced.01" {
    n++; if (NF!=15 || $2!="0" || $3!="0") bad=1
  } END {exit (n==1 && !bad) ? 0 : 1}' "$BP_CONTROLLERS"; then
  echo 'CONTROLLER_REGISTRATION_RACE_RED: duplicate, malformed or auto-enabled row' >&2
  exit 1
fi
echo 'CONTROLLER_REGISTRATION_RACE_GREEN (real sourced shell; delayed lookup mock, no router/finance proof)'
