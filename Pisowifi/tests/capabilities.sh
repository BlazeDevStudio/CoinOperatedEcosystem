#!/bin/sh
# Source-linked regression: run exact OpenWrt detector with isolated fake df.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DETECTOR="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh"
T="$(mktemp -d)"
trap 'rm -rf "$T"' 0 HUP INT TERM
mkdir -p "$T/bin"
cat > "$T/bin/df" <<'DF'
#!/bin/sh
[ "$1" = "-Pk" ] || exit 98
printf 'Filesystem 1024-blocks Used Available Capacity Mounted-on\n'
case "$TEST_DF_MODE:$2" in
  low:/overlay) printf '/dev/overlay 5000000 4999996 4 99%% /overlay\n' ;;
  high:/overlay) printf '/dev/overlay 5000000 4400000 600000 88%% /overlay\n' ;;
  missing:/overlay) exit 1 ;;
  missing:/) printf '/dev/root 1000000 930000 70000 93%% /\n' ;;
  invalid:/overlay) printf '/dev/overlay 5000000 3000000 ??? 60%% /overlay\n' ;;
  invalid:/) printf '/dev/root 1000000 930000 70000 93%% /\n' ;;
  none:*) exit 1 ;;
  *) exit 99 ;;
esac
DF
chmod +x "$T/bin/df"
PATH="$T/bin:$PATH"
export PATH BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=2097152
check() {
  expected="$1" mode="$2"; shift 2
  actual="$(TEST_DF_MODE="$mode" BP_CAP_TIER=auto sh "$DETECTOR" --detect)"
  if [ "$actual" != "$expected" ]; then
    printf 'FAIL mode=%s expected=%s actual=%s\n' "$mode" "$expected" "$actual" >&2
    return 1
  fi
  printf 'PASS mode=%s tier=%s\n' "$mode" "$actual"
}
sh -n "$DETECTOR"
check lite low
check full high
check standard missing
check standard invalid
check lite none
actual="$(BP_CAP_TIER=standard sh "$DETECTOR" --detect)"
[ "$actual" = standard ] || { echo 'FAIL explicit tier' >&2; exit 1; }
if BP_CAP_TIER=invalid sh "$DETECTOR" --detect > "$T/out" 2> "$T/err"; then
  echo 'FAIL unknown tier should be rejected' >&2
  exit 1
fi
grep -q 'invalid capability tier' "$T/err"
printf 'PASS explicit tier and rejected unknown tier\n'
