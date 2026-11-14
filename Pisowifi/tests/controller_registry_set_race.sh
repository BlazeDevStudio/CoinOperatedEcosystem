#!/bin/sh
# Two authenticated-style policy writers updating distinct controller IDs.
# Delay an actual source-linked staged copy after it snapshots controllers.tsv.
# No live router or payment system is used.
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
bp_tmp_suffix() { od -An -N6 -tx1 /dev/urandom | tr -d ' \n'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"

bp_controller_ensure unit.A
bp_controller_ensure unit.B
[ "$(wc -l < "$BP_CONTROLLERS")" -eq 2 ]
REAL_AWK="$(command -v awk)"; export REAL_AWK
cat > "$T/bin/awk" <<'INJECT'
#!/bin/sh
case "$*" in
  *'$1!=d {print}'*)
    "$REAL_AWK" "$@" || exit 74
    if [ ! -e "$BP_STATE/first-copy-observed" ]; then
      : > "$BP_STATE/first-copy-observed"
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

(bp_controller_set unit.A 1 1 0 0 -1 -1 -1 1 1 1 40 400 6) & p1=$!
i=0
while [ ! -e "$BP_STATE/first-copy-observed" ] && [ "$i" -lt 100 ]; do
  sleep 0.05
  i=$((i + 1))
done
if [ ! -e "$BP_STATE/first-copy-observed" ]; then
  echo 'CONTROLLER_ADMIN_RACE_INVALID: copy delay not injected' >&2
  exit 2
fi
(bp_controller_set unit.B 1 1 0 0 -1 -1 -1 1 1 1 40 400 6) & p2=$!
wait "$p1" || exit 2; p1=
wait "$p2" || exit 2; p2=
if ! "$REAL_AWK" -F '\t' '{
    if (NF!=15 || ++seen[$1]>1) bad=1
    if (($1=="unit.A" || $1=="unit.B") &&
        ($2!="1" || $3!="1" || $15!="2")) bad=1
  } END {
    if (NR!=2 || seen["unit.A"]!=1 || seen["unit.B"]!=1 || bad) exit 1
  }' "$BP_CONTROLLERS"; then
  echo 'CONTROLLER_ADMIN_RACE_RED: lost or corrupted one controller update' >&2
  exit 1
fi
echo 'CONTROLLER_ADMIN_RACE_GREEN (disjoint source-linked policy updates survived; mocked sync only)'
