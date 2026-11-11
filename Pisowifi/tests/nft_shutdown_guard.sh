#!/bin/sh
# Execute original core signal trap and init stop_service in a fake nft sandbox.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
CORE="$ROOT/openwrt/rootfs/usr/sbin/blazepwifi-core"
INIT="$ROOT/openwrt/rootfs/etc/init.d/blazepwifi"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin"
sh -n "$CORE"
sh -n "$INIT"
# Only source the original signal handler line, not the infinite daemon loop.
grep '^trap .*TERM INT$' "$CORE" > "$T/trapline"
[ "$(wc -l < "$T/trapline")" -eq 1 ]
cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
printf '%s\n' "$*" >> "$TEST_DIR/operations"
case "$*" in
 'flush set inet blazepwifi auth_macs')
   [ "${TEST_FLUSH_FAIL:-0}" -eq 0 ] || exit 9
   printf 'gate-with-empty-auth\n' > "$TEST_DIR/table" ;;
 'delete table inet blazepwifi') rm -f "$TEST_DIR/table" ;;
 *) exit 91 ;;
esac
NFT
chmod +x "$T/bin/nft"
export PATH="$T/bin:$PATH" TEST_DIR="$T" ACTUAL_TRAP="$T/trapline" INIT_SCRIPT="$INIT"
run_trap() {
    set +e
    sh -c '. "$ACTUAL_TRAP"; kill -TERM "$$"; exit 89' > "$T/stdout" 2> "$T/stderr"
    rc=$?
    set -e
}
run_stop() {
    set +e
    sh -c '. "$INIT_SCRIPT"; stop_service' > "$T/stdout" 2> "$T/stderr"
    rc=$?
    set -e
}
TEST_FLUSH_FAIL=0; export TEST_FLUSH_FAIL
printf 'gate-with-valid-auth\n' > "$T/table"; : > "$T/operations"
run_trap
[ "$rc" -eq 0 ]
[ "$(cat "$T/table")" = gate-with-empty-auth ]
[ "$(cat "$T/operations")" = 'flush set inet blazepwifi auth_macs' ]
printf 'PASS core TERM removes auth, keeps firewall table\n'
printf 'gate-with-valid-auth\n' > "$T/table"; : > "$T/operations"
run_stop
[ "$rc" -eq 0 ]
[ "$(cat "$T/table")" = gate-with-empty-auth ]
[ "$(cat "$T/operations")" = 'flush set inet blazepwifi auth_macs' ]
printf 'PASS init stop removes auth, keeps firewall table\n'
TEST_FLUSH_FAIL=1; export TEST_FLUSH_FAIL
printf 'gate-with-valid-auth\n' > "$T/table"; : > "$T/operations"
run_trap
[ "$rc" -ne 0 ]
[ "$(cat "$T/table")" = gate-with-valid-auth ]
grep -q 'CRITICAL: nft client revocation unverified' "$T/stderr"
printf 'PASS failed core shutdown revocation reported and not disguised as success\n'
printf 'gate-with-valid-auth\n' > "$T/table"; : > "$T/operations"
run_stop
[ "$rc" -ne 0 ]
[ "$(cat "$T/table")" = gate-with-valid-auth ]
grep -q 'CRITICAL: nft client revocation unverified' "$T/stderr"
printf 'PASS failed init shutdown revocation reported and not disguised as success\n'
