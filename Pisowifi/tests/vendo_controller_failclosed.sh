#!/bin/sh
# Real staged Vendo CGI + shell libraries, disposable UCI/files only.
# Unreadable controller policy must never get OK or a signed response.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_port') echo 4455 ;;
  *'get blazepwifi.main.vendo_key') echo vendokey ;;
  *'get blazepwifi.main.durable_sync') echo 0 ;;
  *) exit 1 ;;
esac
UCI
chmod 755 "$T/bin/uci"
PATH="$T/bin:$PATH"; export PATH
export BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export SERVER_PORT=4455 REQUEST_METHOD=POST REMOTE_ADDR=127.0.0.1
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
id=guard.01
nonce=0102030405060708

request() {
  action="$1"
  sig="$(printf 'vendokey|%s|%s|%s|0||vendokey' "$action" "$id" "$nonce" | sha256sum | awk '{print $1}')"
  printf 'action=%s&id=%s&nonce=%s&pulses=0&target=&sig=%s' "$action" "$id" "$nonce" "$sig" | sh "$VENDO"
}
deny() {
  label="$1"
  output="$2"
  if ! printf '%s' "$output" | grep -Fq '"ok":false' ||
     printf '%s' "$output" | grep -Fq '"ok":true' ||
     printf '%s' "$output" | grep -Fq '"response_sig":'; then
    echo "VENDO_CONTROLLER_FAILCLOSED_RED: $label got success/malformed response" >&2
    exit 1
  fi
}

# Startup: controllers.tsv must not resolve outside its canonical state.
printf 'external-evidence\n' > "$T/outside"
cp "$T/outside" "$T/outside.original"
ln -s "$T/outside" "$BP_STATE/controllers.tsv"
for action in register ping poll; do
  out="$(request "$action")"
  deny "symlink:$action" "$out"
done
cmp -s "$T/outside" "$T/outside.original" || {
  echo 'VENDO_CONTROLLER_FAILCLOSED_RED: symlink target modified' >&2
  exit 1
}
[ ! -s "$BP_RUN/vendos.tsv" ] || {
  echo 'VENDO_CONTROLLER_FAILCLOSED_RED: advertised a failed heartbeat' >&2
  exit 1
}
rm -f "$BP_STATE/controllers.tsv"

# Valid controller path remains compatible and default-disabled.
out="$(request register)"
printf '%s' "$out" | grep -Fq '"ok":true' || {
  echo 'VENDO_CONTROLLER_FAILCLOSED_RED: healthy registration unavailable' >&2
  exit 1
}
printf '%s' "$out" | grep -Fq '"coin_enabled":0' || exit 1

# Late policy read error after heartbeat: no successful signed controller JSON.
REAL_AWK="$(command -v awk)"; export REAL_AWK
cat > "$T/bin/awk" <<'AWK'
#!/bin/sh
case "$*" in
  *'$1==d {print; exit}'*) exit 74 ;;
esac
exec "$REAL_AWK" "$@"
AWK
chmod 755 "$T/bin/awk"
hash -r
out="$(request ping)"
deny 'late controller policy read' "$out"
rm -f "$T/bin/awk"
hash -r

# Heartbeat metadata publication fault may not be followed by signed OK.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in
  */vendos.tsv) exit 74 ;;
esac
exec /bin/mv "$@"
MV
chmod 755 "$T/bin/mv"
hash -r
out="$(request ping)"
deny 'heartbeat rename failure' "$out"
rm -f "$T/bin/mv"
hash -r

# Explicitly no account mutation in these registration/read scenarios.
[ ! -s "$BP_STATE/accounts.tsv" ]
echo 'VENDO_CONTROLLER_FAILCLOSED_GREEN (real CGI, synthetic UCI/faults; no finance/hardware proof)'
