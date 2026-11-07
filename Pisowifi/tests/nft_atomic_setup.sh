#!/bin/sh
# Execute the actual sourced setup_nft function using a disposable fake nft.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CORE="$ROOT/openwrt/rootfs/usr/sbin/blazepwifi-core"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin"
# Do not launch the daemon loop or modify the host firewall.
sh -n "$CORE"
sed '/^bp_init_dirs$/,$d' "$CORE" > "$T/defs.sh"
grep -q '^setup_nft() {' "$T/defs.sh"
cat > "$T/lib.sh" <<'LIB'
bp_cfg() {
  case "$1" in
    lan_if) printf '%s\n' "${TEST_LAN:-br-test0}" ;;
    portal_port) printf '%s\n' "${TEST_PORT:-8080}" ;;
    *) return 1 ;;
  esac
}
LIB
cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
case "$1" in
  list)
    [ "$*" = 'list table inet blazepwifi' ] || exit 91
    [ -f "$TEST_DIR/table" ]
    ;;
  -f)
    [ "$2" = '-' ] || exit 92
    cat > "$TEST_DIR/batch"
    printf 'batch\n' >> "$TEST_DIR/operations"
    [ "${TEST_BATCH_FAIL:-0}" = 0 ] || exit 93
    grep -q 'table inet blazepwifi {' "$TEST_DIR/batch" || exit 94
    if [ -f "$TEST_DIR/table" ]; then
      grep -q '^delete table inet blazepwifi$' "$TEST_DIR/batch" || exit 95
    else
      ! grep -q '^delete table inet blazepwifi$' "$TEST_DIR/batch" || exit 96
    fi
    printf 'replaced\n' > "$TEST_DIR/table"
    ;;
  delete)
    printf 'separate-delete\n' >> "$TEST_DIR/operations"
    rm -f "$TEST_DIR/table"
    ;;
  *) exit 97 ;;
esac
NFT
chmod +x "$T/bin/nft"
export PATH="$T/bin:$PATH" BP_LIB="$T/lib.sh" BP_DEFS="$T/defs.sh" TEST_DIR="$T"
run() {
  set +e
  sh -c '. "$BP_DEFS"; setup_nft' > "$T/stdout" 2> "$T/stderr"
  rc=$?
  set -e
}
# Existing captive gate must survive a failed replacement.
printf 'old\n' > "$T/table"
: > "$T/operations"
TEST_BATCH_FAIL=1; export TEST_BATCH_FAIL
run
[ "$rc" -ne 0 ]
[ "$(cat "$T/table")" = old ]
! grep -q separate-delete "$T/operations"
grep -q '^delete table inet blazepwifi$' "$T/batch"
printf 'PASS previous gate preserved on failed nft batch\n'
# Successful replacement must occur in only one nft batch.
TEST_BATCH_FAIL=0; export TEST_BATCH_FAIL
: > "$T/operations"
run
[ "$rc" -eq 0 ]
[ "$(cat "$T/table")" = replaced ]
[ "$(wc -l < "$T/operations")" -eq 1 ]
grep -q 'iifname "br-test0" drop' "$T/batch"
printf 'PASS existing gate replaced in one transaction\n'
# Fresh startup uses a single transaction without a separate delete.
rm -f "$T/table"
: > "$T/operations"
run
[ "$rc" -eq 0 ]
[ "$(cat "$T/table")" = replaced ]
! grep -q '^delete table inet blazepwifi$' "$T/batch"
printf 'PASS fresh creation has no invalid delete\n'
# Untrusted interface and port must never enter the nft batch.
for invalid in interface port; do
  printf 'old\n' > "$T/table"
  : > "$T/operations"
  TEST_LAN=br-test0; TEST_PORT=8080
  if [ "$invalid" = interface ]; then TEST_LAN='br-"; delete table inet firewall'; fi
  if [ "$invalid" = port ]; then TEST_PORT=65536; fi
  export TEST_LAN TEST_PORT
  run
  [ "$rc" -ne 0 ]
  [ "$(cat "$T/table")" = old ]
  [ ! -s "$T/operations" ]
  printf 'PASS rejected invalid %s without nft mutation\n' "$invalid"
done
printf 'PASS source-linked nft transaction fixture (5 cases)\n'
