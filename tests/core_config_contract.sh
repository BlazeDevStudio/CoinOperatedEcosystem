#!/bin/sh
# Exact migrated CORE config.sh: source-linked validation and rollback contracts.
# Mocked UCI lives entirely under /tmp; no router, payments or live config.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
LIB="$ROOT/core/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
T="$(mktemp -d /tmp/coe-config-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin"
printf '%s\n' 'blazepwifi.main.admin_port=8443' > "$T/uci.db"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
set -eu
DB="$COE_UCI_DB"
if [ "$1" = "-q" ]; then shift; fi
command="$1"; shift
case "$command" in
    get)
        awk -F= -v key="$1" '$1==key {found=1; print substr($0,length(key)+2)} END {if (!found) exit 1}' "$DB" ;;
    set)
        pair="$1"; key="$(printf '%s' "$pair" | cut -d= -f1)"; value="$(printf '%s' "$pair" | cut -d= -f2-)"
        awk -F= -v key="$key" '$1!=key {print}' "$DB" > "$DB.tmp"
        printf '%s=%s\n' "$key" "$value" >> "$DB.tmp"
        mv "$DB.tmp" "$DB"
        if [ -f "$COE_FAULT_DIR/set-fail-once" ]; then
            rm -f "$COE_FAULT_DIR/set-fail-once"
            exit 7
        fi ;;
    delete)
        key="$1"; awk -F= -v key="$key" '$1!=key {print}' "$DB" > "$DB.tmp"
        mv "$DB.tmp" "$DB" ;;
    show)
        [ "${COE_SHOW_FAIL:-0}" != 1 ] || exit 7
        cat "$DB" ;;
    commit)
        if [ -f "$COE_FAULT_DIR/commit-fail-once" ]; then
            rm -f "$COE_FAULT_DIR/commit-fail-once"
            exit 7
        fi
        if [ -f "$COE_FAULT_DIR/rollback-commit-fail" ]; then
            if [ -f "$COE_FAULT_DIR/initial-commit-seen" ]; then exit 7; fi
            : > "$COE_FAULT_DIR/initial-commit-seen"
        fi
        exit 0 ;;
    *) echo "unapproved UCI subcommand" >&2; exit 9 ;;
esac
UCI
chmod 700 "$T/bin/uci"
export COE_UCI_DB="$T/uci.db" COE_FAULT_DIR="$T" PATH="$T/bin:$PATH"
export BP_CONFIG_LOCK_FILE="$T/config.lock"
. "$LIB"
pass() {
    bp_config_validate "$1" "$2" || { echo "VALID_SOURCE_REJECTED: $1=$2" >&2; exit 1; }
}
deny() {
    if bp_config_validate "$1" "$2"; then
        echo "UNSAFE_SOURCE_ACCEPTED: $1=$2" >&2
        exit 1
    fi
}
pass capability_tier auto
pass capability_tier lite
pass capability_tier standard
pass capability_tier full
deny capability_tier disabled
pass lan_if br-lan.13
deny lan_if 'br-lan;touch/tmp/corrupt'
pass hotspot_vlan 0
pass hotspot_vlan 4094
deny hotspot_vlan 4095
deny hotspot_vlan -1
pass admin_port 1
pass admin_port 65535
deny admin_port 0
deny admin_port 65536
deny admin_port '8080;exit'
pass coin_window 5
pass coin_window 3600
deny coin_window 4
pass pulse_value_centavos 1
deny pulse_value_centavos 0
pass durable_sync 0
pass durable_sync 1
deny durable_sync yes
pass update_source_url 'https://example.invalid/releases/'
deny update_source_url 'http://example.invalid/releases/'
deny update_source_url 'https://example.invalid/evil path'
deny unknown_key 5
# Only fixed true/false commands in this test-only hook; no customer router.
export BP_CONFIG_APPLY_HOOK=true
bp_config_set admin_port 9443
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]
export BP_CONFIG_APPLY_HOOK=false
if bp_config_set admin_port 9555; then
    echo 'FAILED_APPLY_FALSE_ACK' >&2; exit 1
fi
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]
if bp_config_set admin_port 0; then
    echo 'INVALID_PORT_FALSE_ACK' >&2; exit 1
fi
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]
# Refuse and never execute arbitrary environment-provided shell commands.
export BP_CONFIG_APPLY_HOOK="touch $T/unsafe-side-effect"
if bp_config_set admin_port 9555; then
    echo UNSAFE_DYNAMIC_HOOK_ACCEPTED >&2; exit 1
fi
[ ! -e "$T/unsafe-side-effect" ] || { echo HOOK_EXECUTED >&2; exit 1; }
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]
export BP_CONFIG_APPLY_HOOK='true; touch /tmp/coe-should-not-execute'
if bp_config_set admin_port 9555; then
    echo COMPOUND_HOOK_ACCEPTED >&2; exit 1
fi
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]
# UCI set may return an error after modifying a pending value.
export BP_CONFIG_APPLY_HOOK=true
: > "$T/set-fail-once"
if bp_config_set admin_port 9555; then echo 'FALSE_SET_ACK' >&2; exit 1; else
    [ "$?" -eq 1 ] || { echo 'BAD_SET_ERROR_CODE' >&2; exit 1; }
fi
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]

# Commit failure restores the original value and returns a denied status.
: > "$T/commit-fail-once"
if bp_config_set admin_port 9555; then echo 'FALSE_COMMIT_ACK' >&2; exit 1; else
    [ "$?" -eq 1 ] || { echo 'BAD_COMMIT_ERROR_CODE' >&2; exit 1; }
fi
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]

# An unverified rollback must be an explicit uncertain-state error, not ACK.
export BP_CONFIG_APPLY_HOOK=false
: > "$T/rollback-commit-fail"
if bp_config_set admin_port 9555; then echo 'FALSE_ROLLBACK_ACK' >&2; exit 1; else
    [ "$?" -eq 9 ] || { echo 'BAD_ROLLBACK_ERROR_CODE' >&2; exit 1; }
fi
rm -f "$T/rollback-commit-fail" "$T/initial-commit-seen"
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]

# On failed apply, a key that was initially absent is deleted, not blanked.
if bp_config_set portal_port 8080; then echo 'FALSE_ABSENCE_ACK' >&2; exit 1; else
    [ "$?" -eq 1 ] || { echo 'BAD_ABSENCE_ERROR_CODE' >&2; exit 1; }
fi
if uci -q get blazepwifi.main.portal_port >/dev/null 2>&1; then
    echo 'ABSENT_KEY_LEAKED' >&2; exit 1
fi

# A failed section read is not proof of a missing key.
export COE_SHOW_FAIL=1 BP_CONFIG_APPLY_HOOK=true
if bp_config_set portal_port 8080; then echo 'FALSE_SNAPSHOT_ACK' >&2; exit 1; else
    [ "$?" -eq 8 ] || { echo 'BAD_SNAPSHOT_ERROR_CODE' >&2; exit 1; }
fi
unset COE_SHOW_FAIL
if uci -q get blazepwifi.main.portal_port >/dev/null 2>&1; then
    echo 'FAILED_SNAPSHOT_MUTATED' >&2; exit 1
fi

# A second process holding the file lock must block config mutation.
flock "$BP_CONFIG_LOCK_FILE" sh -c 'touch "$COE_FAULT_DIR/lock-ready"; sleep 2' &
locker=$!
attempt=0
while [ ! -e "$T/lock-ready" ]; do
    attempt=$((attempt+1))
    [ "$attempt" -lt 100 ] || { echo 'LOCK_FIXTURE_NOT_READY' >&2; exit 1; }
    sleep 0.02
done
if bp_config_set admin_port 9555; then echo 'FALSE_LOCK_ACK' >&2; exit 1; else
    [ "$?" -eq 8 ] || { echo 'BAD_LOCK_ERROR_CODE' >&2; exit 1; }
fi
wait "$locker"
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]
echo 'COE CONFIG TRANSACTION PASS: partial write, commit, uncertain rollback, absent key, unreadable snapshot, lock refusal'
