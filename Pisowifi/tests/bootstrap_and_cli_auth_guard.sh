#!/bin/sh
# Source-linked regression test for CLI auth REQUEST_METHOD isolation and 99-blazepwifi fail-closed CSPRNG.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
AUTH="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
COMMON="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
UCI_DEFAULTS="$ROOT/openwrt/rootfs/etc/uci-defaults/99-blazepwifi"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state" "$T/run"

cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.auth_kdf_rounds') echo 8 ;;
  *'get blazepwifi.main.durable_sync') echo 0 ;;
  *) exit 1 ;;
esac
UCI
chmod +x "$T/bin/uci"
export PATH="$T/bin:$PATH"
export BP_STATE="$T/state" BP_RUN="$T/run" BP_LIB="$COMMON"

# 1. Verify auth.sh --set-password and --set-bootstrap do not block on open stdin when REQUEST_METHOD=POST is exported.
mkfifo "$T/fifo"
# Open FIFO read/write on fd 3 so stdin is open without EOF and without any newline.
exec 3<> "$T/fifo"
REQUEST_METHOD=POST "$AUTH" --set-bootstrap admin admin "BootstrapPass#1234" <&3
REQUEST_METHOD=POST "$AUTH" --set-password admin admin "UpdatedPass#12345" <&3
exec 3>&-
grep -q '^admin	admin	' "$T/state/admin-users.tsv"
printf 'PASS auth.sh CLI ignores inherited REQUEST_METHOD=POST with open non-EOF stdin\n'

# 2. Extract randhex() from 99-blazepwifi and verify fail-closed CSPRNG behavior.
sed '/^ensure_opt()/,$d' "$UCI_DEFAULTS" > "$T/randhex.sh"
. "$T/randhex.sh"

hex18="$(randhex 18)"
[ "${#hex18}" -eq 36 ]
printf '%s' "$hex18" | LC_ALL=C grep -Eq '^[0-9a-f]{36}$'
printf 'PASS 99-blazepwifi randhex emits verified lowercase hex from /dev/urandom\n'

for bad_src in /dev/null "$T/nonexistent-urandom"; do
  set +e
  bad_out="$(BP_URANDOM="$bad_src" randhex 18)"
  rc=$?
  set -e
  [ "$rc" -eq 8 ] || { echo "FAIL expected rc=8 for BP_URANDOM=$bad_src, got $rc" >&2; exit 1; }
  [ -z "$bad_out" ] || { echo "FAIL expected empty output on entropy failure, got $bad_out" >&2; exit 1; }
done
printf 'PASS 99-blazepwifi randhex fails closed without date/PID fallback\n'
