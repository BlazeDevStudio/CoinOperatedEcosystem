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
        mv "$DB.tmp" "$DB" ;;
    delete)
        key="$1"; awk -F= -v key="$key" '$1!=key {print}' "$DB" > "$DB.tmp"
        mv "$DB.tmp" "$DB" ;;
    commit) exit 0 ;;
    *) echo "unapproved UCI subcommand" >&2; exit 9 ;;
esac
UCI
chmod 700 "$T/bin/uci"
export COE_UCI_DB="$T/uci.db" PATH="$T/bin:$PATH"
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
echo 'COE CONFIG SOURCE CONTRACT PASS: whitelist, URL, VLAN, numeric limits and failed-apply rollback (synthetic only)'
