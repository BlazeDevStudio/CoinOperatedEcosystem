#!/bin/sh
# Validated, capability-neutral BlazePwifi configuration layer.

BP_CONFIG_KEYS="capability_tier lan_if management_if hotspot_if controller_if rental_if portal_port vendo_port admin_port coin_window pulse_value_centavos rental_seconds_per_pulse event_history pause_max_seconds walled_refresh_seconds durable_sync firewall_zone management_vlan hotspot_vlan controller_vlan rental_vlan gpio_chip coin_line relay_line led_line coin_active_low relay_active_low led_active_low coin_debounce_ms pulse_group_ms default_speed_limit_kbps update_source_url update_stability_seconds update_retention update_max_mb advanced_terminal_enabled terminal_ttl_seconds terminal_idle_seconds terminal_command_timeout_seconds terminal_output_max_bytes"

bp_config_key_allowed() {
	key="$1"
	for k in $BP_CONFIG_KEYS; do [ "$k" = "$key" ] && return 0; done
	return 1
}

bp_config_uint_range() {
	value="$1"; min="$2"; max="$3"
	case "$value" in ''|*[!0-9]*) return 1;; esac
	[ "$value" -ge "$min" ] 2>/dev/null && [ "$value" -le "$max" ] 2>/dev/null
}

bp_config_iface() {
	printf '%s' "$1" | grep -Eq '^[A-Za-z0-9_.:-]{1,32}$'
}

bp_config_validate() {
	key="$1"; value="$2"
	bp_config_key_allowed "$key" || return 1
	case "$key" in
		capability_tier) case "$value" in auto|lite|standard|full) return 0;; *) return 1;; esac ;;
		lan_if|management_if|hotspot_if|controller_if|rental_if|firewall_zone|gpio_chip)
			bp_config_iface "$value"
			;;
		portal_port|vendo_port|admin_port) bp_config_uint_range "$value" 1 65535 ;;
		coin_window) bp_config_uint_range "$value" 5 3600 ;;
		pulse_value_centavos) bp_config_uint_range "$value" 1 100000 ;;
		rental_seconds_per_pulse) bp_config_uint_range "$value" 1 86400 ;;
		event_history) bp_config_uint_range "$value" 8 512 ;;
		pause_max_seconds) bp_config_uint_range "$value" 0 31536000 ;;
		walled_refresh_seconds) bp_config_uint_range "$value" 30 86400 ;;
		durable_sync|coin_active_low|relay_active_low|led_active_low|advanced_terminal_enabled) case "$value" in 0|1) return 0;; *) return 1;; esac ;;
		management_vlan|hotspot_vlan|controller_vlan|rental_vlan) bp_config_uint_range "$value" 0 4094 ;;
		coin_line|relay_line|led_line) bp_config_uint_range "$value" 0 4095 ;;
		coin_debounce_ms) bp_config_uint_range "$value" 1 2000 ;;
		pulse_group_ms) bp_config_uint_range "$value" 10 10000 ;;
		default_speed_limit_kbps) bp_config_uint_range "$value" 0 10000000 ;;
		update_source_url)
			case "$value" in https://*) [ "$(printf '%s' "$value" | wc -c)" -le 512 ] && ! printf '%s' "$value" | grep -q '[[:space:][:cntrl:]]';; *) return 1;; esac ;;
		update_stability_seconds) bp_config_uint_range "$value" 60 604800 ;;
		update_retention) bp_config_uint_range "$value" 1 10 ;;
		update_max_mb) bp_config_uint_range "$value" 8 512 ;;
		terminal_ttl_seconds) bp_config_uint_range "$value" 60 1800 ;;
		terminal_idle_seconds) bp_config_uint_range "$value" 15 900 ;;
		terminal_command_timeout_seconds) bp_config_uint_range "$value" 2 60 ;;
		terminal_output_max_bytes) bp_config_uint_range "$value" 1024 65536 ;;
		*) return 1 ;;
	esac
}

bp_config_get() {
	key="$1"
	bp_config_key_allowed "$key" || return 1
	uci -q get "blazepwifi.main.$key"
}

# Guard the entire UCI write, apply and restore window. Busy/unavailable
# locks refuse the write rather than racing another administrator.
bp_config_lock() {
    bp_cfg_lock_file="${BP_CONFIG_LOCK_FILE:-/var/run/blazepwifi-config.lock}"
    command -v flock >/dev/null 2>&1 || return 8
    [ ! -L "$bp_cfg_lock_file" ] || return 8
    (umask 077; : >> "$bp_cfg_lock_file") || return 8
    exec 8>>"$bp_cfg_lock_file" || return 8
    if ! flock -n 8; then exec 8>&-; return 8; fi
}
bp_config_unlock() {
    flock -u 8 >/dev/null 2>&1 || true
    exec 8>&-
}

# Pending markers are written before UCI mutations; surviving a restart
# means administrator reconciliation is REQUIRED, never silent auto-restore.
bp_config_pending_path() {
    printf '%s\n' "${BP_CONFIG_PENDING_FILE:-/etc/blazepwifi/.config-transaction.pending}"
}
bp_config_recovery_status() {
    bp_pending="$(bp_config_pending_path)"
    # File, directory or symlink is an unresolved/unsafe transaction.
    if [ -e "$bp_pending" ] || [ -L "$bp_pending" ]; then
        printf '%s\n' 'config transaction pending: operator recovery required' >&2
        return 9
    fi
    return 0
}
bp_config_mark_pending() {
    bp_pending="$(bp_config_pending_path)"
    bp_dir="${bp_pending%/*}"
    [ "$bp_dir" != "$bp_pending" ] && [ -d "$bp_dir" ] &&
        [ ! -L "$bp_dir" ] || return 9
    bp_config_recovery_status || return 9
    command -v mktemp >/dev/null 2>&1 || return 9
    command -v sync >/dev/null 2>&1 || return 9
    bp_tmp="$(umask 077; mktemp "$bp_pending.tmp.XXXXXXXX")" || return 9
    if ! printf 'COE_CONFIG_PENDING_V1 %s\n' "$1" > "$bp_tmp" ||
       ! chmod 600 "$bp_tmp" ||
       ! mv "$bp_tmp" "$bp_pending"; then
        rm -f "$bp_tmp" >/dev/null 2>&1 || true
        return 9
    fi
    # An OS sync is not proof of hardware power-loss durability.
    sync || return 9
    return 0
}
bp_config_clear_pending() {
    bp_pending="$(bp_config_pending_path)"
    [ -f "$bp_pending" ] && [ ! -L "$bp_pending" ] || return 9
    rm "$bp_pending" || return 9
    sync || return 9
    return 0
}

bp_config_restore() {
    key="$1"; had_old="$2"; old="$3"
    if [ "$had_old" = 1 ]; then
        uci set "blazepwifi.main.$key=$old" || return 1
    else
        uci -q delete "blazepwifi.main.$key" || return 1
    fi
    uci commit blazepwifi || return 1
    if [ "$had_old" = 1 ]; then
        current="$(uci -q get "blazepwifi.main.$key")" || return 1
        [ "$current" = "$old" ] || return 1
    else
        section="$(uci -q show blazepwifi.main)" || return 1
        if printf '%s\n' "$section" | awk -F= -v k="blazepwifi.main.$key" '$1==k {found=1} END {exit(found ? 0 : 1)}'; then
            return 1
        fi
    fi
}

bp_config_apply() {
	# No arbitrary shell strings in privileged config apply. Fixed test
	# sentinels preserve previous true/false test outcomes.
	case "${BP_CONFIG_APPLY_HOOK:-}" in
		'') ;;
		true) return 0 ;;
		false) return 1 ;;
		*) return 2 ;;
	esac
	if [ -x /usr/lib/blazepwifi/apply-config.sh ]; then
		/usr/lib/blazepwifi/apply-config.sh || return 1
	fi
	return 0
}

# Error 1: UCI restored; 9: restoration cannot be verified.
bp_config_abort() {
    if bp_config_restore "$1" "$2" "$3" && bp_config_clear_pending; then
        bp_config_unlock
        return 1
    fi
    # Failed rollback or marker clear: refuse with uncertain state.
    bp_config_unlock
    return 9
}

bp_config_set() {
    key="$1"; value="$2"
    bp_config_validate "$key" "$value" || return 2
    bp_config_lock || return 8
    bp_config_recovery_status || { bp_config_unlock; return 9; }

    if old="$(uci -q get "blazepwifi.main.$key" 2>/dev/null)"; then
        had_old=1
    else
        # A failed get may be an I/O error, not an absent setting.
        snapshot="$(uci -q show blazepwifi.main)" || { bp_config_unlock; return 8; }
        if printf '%s\n' "$snapshot" | awk -F= -v k="blazepwifi.main.$key" '$1==k {found=1} END {exit(found ? 0 : 1)}'; then
            bp_config_unlock; return 8
        fi
        old=""; had_old=0
    fi

    # Install + flush pending marker before any UCI write.
    bp_config_mark_pending "$key" || { bp_config_unlock; return 9; }
    # UCI set can mutate a staging area even when it reports a failure.
    if ! uci set "blazepwifi.main.$key=$value"; then
        bp_config_abort "$key" "$had_old" "$old"; return $?
    fi
    if ! uci commit blazepwifi; then
        bp_config_abort "$key" "$had_old" "$old"; return $?
    fi
    current="$(uci -q get "blazepwifi.main.$key")" || {
        bp_config_abort "$key" "$had_old" "$old"; return $?
    }
    if [ "$current" != "$value" ]; then
        bp_config_abort "$key" "$had_old" "$old"; return $?
    fi

    if ! bp_config_apply; then
        bp_config_abort "$key" "$had_old" "$old"; return $?
    fi
    # A successful apply callback alone is not sufficient to ACK a change.
    current="$(uci -q get "blazepwifi.main.$key")" || {
        bp_config_abort "$key" "$had_old" "$old"; return $?
    }
    if [ "$current" != "$value" ]; then
        bp_config_abort "$key" "$had_old" "$old"; return $?
    fi

    # Clear only after readback and apply; failure must never ACK.
    bp_config_clear_pending || { bp_config_unlock; return 9; }
    bp_config_unlock
    if command -v bp_auth_audit >/dev/null 2>&1; then
        bp_auth_audit config_change "${BP_AUTH_USER:-local}" "${REMOTE_ADDR:-local}" "$key"
    fi
    return 0
}
