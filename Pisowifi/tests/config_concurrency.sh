#!/bin/sh
# Run actual config.sh against disposable UCI. Never touch a router.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/run"
export TEST_DIR="$T" BP_RUN="$T/run" BP_CONFIG_APPLY_HOOK="$T/bin/hook" PATH="$T/bin:$PATH"
printf '%s\n' 'blazepwifi.main.admin_port=8443' > "$T/uci.db"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
[ "${1:-}" = -q ] && shift
case "$1" in
  show)
    [ "$2" = blazepwifi.main ] || exit 8
    printf '%s\n' 'blazepwifi.main=core'
    cat "$TEST_DIR/uci.db" ;;
  get)
    line="$(grep -F "${2}=" "$TEST_DIR/uci.db" | tail -n 1)"
    [ -n "$line" ] || exit 1
    printf '%s\n' "${line#*=}" ;;
  set)
    key="${2%%=*}"
    grep -Fv "$key=" "$TEST_DIR/uci.db" > "$TEST_DIR/new.db" || true
    printf '%s=%s\n' "$key" "${2#*=}" >> "$TEST_DIR/new.db"
    mv "$TEST_DIR/new.db" "$TEST_DIR/uci.db" ;;
  delete)
    grep -Fv "$2=" "$TEST_DIR/uci.db" > "$TEST_DIR/new.db" || true
    mv "$TEST_DIR/new.db" "$TEST_DIR/uci.db" ;;
  commit) : ;;
  *) exit 7 ;;
esac
UCI
cat > "$T/bin/hook" <<'HOOK'
#!/bin/sh
value="$(uci -q get blazepwifi.main.admin_port)"
case "$value" in
  9443)
    touch "$TEST_DIR/a_in_apply"
    n=0
    while [ ! -f "$TEST_DIR/release_a" ]; do
      sleep .05
      n=$((n+1))
      [ "$n" -lt 140 ] || exit 5
    done
    exit 1 ;;
  9555) exit 0 ;;
  *) exit 6 ;;
esac
HOOK
chmod 700 "$T/bin/uci" "$T/bin/hook"
CONFIG="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
sh -n "$CONFIG"
# Two concurrent configuration writes: A applies then fails, B should wait for
# A's rollback before committing. Without a mutex, A reverts B's success.
( . "$CONFIG"; set +e; bp_config_set admin_port 9443; rc=$?; printf "%s\n" "$rc" > "$T/a.status"; exit 0 ) > "$T/a.out" 2> "$T/a.err" & A=$!
i=0
while [ ! -f "$T/a_in_apply" ]; do
  sleep .05; i=$((i+1)); [ "$i" -lt 80 ] || { echo 'FAIL A never entered apply' >&2; exit 1; }
done
( . "$CONFIG"; set +e; bp_config_set admin_port 9555; rc=$?; printf "%s\n" "$rc" > "$T/b.status"; exit 0 ) > "$T/b.out" 2> "$T/b.err" & B=$!
# While A holds its in-flight config operation, B must not have acknowledged.
i=0
while [ "$i" -lt 20 ] && [ ! -f "$T/b.status" ]; do
  sleep .05; i=$((i+1))
done
if [ -f "$T/b.status" ]; then
  touch "$T/release_a"
  wait "$A" || true; wait "$B" || true
  echo 'FAIL concurrent B committed before A rolled back' >&2
  exit 1
fi
touch "$T/release_a"
wait "$A" || true
wait "$B" || true
[ -f "$T/a.status" ] || { echo "FAIL A status missing" >&2; exit 1; }
[ -f "$T/b.status" ] || { echo "FAIL B status missing" >&2; exit 1; }
[ "$(cat "$T/a.status")" = 1 ] || { echo "FAIL A status unexpected" >&2; exit 1; }
[ "$(cat "$T/b.status")" = 0 ] || { echo "FAIL B status unexpected" >&2; exit 1; }
[ "$(uci get blazepwifi.main.admin_port)" = 9555 ] || { echo "FAIL final config wrong" >&2; exit 1; }
printf 'PASS concurrent config writes are serialized across apply and rollback\n'
# Never follow attacker-controlled directory/lock-file symlinks.
printf '%s\n' 'blazepwifi.main.admin_port=8443' > "$T/uci.db"
mkdir -p "$T/private"
ln -s "$T/private" "$T/linkdir"
export BP_RUN="$T/linkdir"
if ( . "$CONFIG"; bp_config_set admin_port 9666 ) > "$T/out" 2> "$T/err"; then
  echo 'FAIL symlink lock directory accepted' >&2; exit 1
fi
[ "$(uci get blazepwifi.main.admin_port)" = 8443 ]
printf 'PASS symlink run directory denied before UCI mutation\n'
export BP_RUN="$T/run"
rm -f "$BP_RUN/config-write.lock"
ln -s "$T/uci.db" "$BP_RUN/config-write.lock"
if ( . "$CONFIG"; bp_config_set admin_port 9666 ) > "$T/out" 2> "$T/err"; then
  echo 'FAIL symlink lock file accepted' >&2; exit 1
fi
[ "$(uci get blazepwifi.main.admin_port)" = 8443 ]
printf 'PASS symlink lock file denied before UCI mutation\n'
printf 'ALL PASS — isolated config serialization / path safety checks\n'
