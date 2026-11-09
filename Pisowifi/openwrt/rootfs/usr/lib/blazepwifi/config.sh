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

# Optional admin settings may legitimately be unset. Never convert an actual
# read failure on an existing option into a falsely successful empty value.
bp_config_get_optional() (
	key="$1"
	bp_config_key_allowed "$key" || return 2
	snapshot="$(uci -q show blazepwifi.main 2>/dev/null)" || return 8
	printf '%s\n' "$snapshot" | grep -q '^blazepwifi\.main=' || return 8
	if value="$(uci -q get "blazepwifi.main.$key" 2>/dev/null)"; then
		printf '%s' "$value"
		return 0
	fi
	printf '%s\n' "$snapshot" | grep -Fq "blazepwifi.main.$key=" && return 8
	return 0
)

# Restore must be fully committed or its caller reports uncertain state.
# A subshell keeps UCI helper variables from clobbering the caller's key.
bp_config_restore() (
	key="$1"; had_old="$2"; old="$3"
	if [ "$had_old" = 1 ]; then
		uci set "blazepwifi.main.$key=$old" || return 8
	else
		uci -q delete "blazepwifi.main.$key" >/dev/null 2>&1 || return 8
	fi
	uci commit blazepwifi || return 8
)

# Applying live configuration requires a real, executable apply program.
# Test operators may select a single trusted executable; never evaluate shell
# strings. The installed runtime path is fixed, not a user-configurable UCI key.
bp_config_apply_program() {
	case "${BP_CONFIG_APPLY_HOOK:-}" in
		'') printf '%s\n' /usr/lib/blazepwifi/apply-config.sh ;;
		*[!A-Za-z0-9_./-]*|-*) return 7 ;;
		*) printf '%s\n' "$BP_CONFIG_APPLY_HOOK" ;;
	esac
}

bp_config_apply_preflight() (
	program="$(bp_config_apply_program)" || return 7
	case "$program" in
		*/*) [ -f "$program" ] && [ -x "$program" ] ;;
		*) command -v "$program" >/dev/null 2>&1 ;;
	esac || {
		echo "configuration apply executable unavailable; no UCI change permitted" >&2
		return 7
	}
)

bp_config_apply() {
	bp_config_apply_preflight || return 7
	program="$(bp_config_apply_program)" || return 7
	"$program" || {
		echo "CRITICAL: live configuration apply failed or disappeared" >&2
		return 8
	}
}

# Serialize the full snapshot -> commit -> apply -> rollback transaction.
# This only coordinates writers using bp_config_set, not external UCI users.
bp_config_set() (
	key="$1"; value="$2"
	bp_config_validate "$key" "$value" || return 2
	config_run="${BP_RUN:-/tmp/blazepwifi}"
	[ ! -L "$config_run" ] || return 8
	umask 077
	mkdir -p "$config_run" || return 8
	[ -d "$config_run" ] && [ ! -L "$config_run" ] || return 8
	chmod 700 "$config_run" || return 8
	config_lock="$config_run/config-write.lock"
	# A corrupt/hostile lock path must not be followed or overwritten.
	[ ! -L "$config_lock" ] || return 8
	[ ! -e "$config_lock" ] || [ -f "$config_lock" ] || return 8
	exec 8>"$config_lock" || return 8
	flock -w 10 8 || return 8
	# Refuse to commit options that the installed firmware cannot apply.
	bp_config_apply_preflight || return 7
	# A failed UCI get is ambiguous: the option may exist but its read failed.
	# Check a readable section snapshot first, and never treat an unreadable
	# existing option (or unreadable section) as an absent option to delete.
	section_snapshot="$(uci -q show blazepwifi.main 2>/dev/null)" || {
		echo "CRITICAL: cannot snapshot UCI section before config change: $key" >&2
		return 8
	}
	printf '%s\n' "$section_snapshot" | grep -q '^blazepwifi\.main=' || {
		echo "CRITICAL: UCI section missing or malformed before config change: $key" >&2
		return 8
	}
	if old="$(uci -q get "blazepwifi.main.$key" 2>/dev/null)"; then
		had_old=1
	else
		if printf '%s\n' "$section_snapshot" | grep -Fq "blazepwifi.main.$key="; then
			echo "CRITICAL: UCI option exists but its value cannot be read: $key" >&2
			return 8
		fi
		old=""; had_old=0
	fi
	uci set "blazepwifi.main.$key=$value" || return 1
	if ! uci commit blazepwifi; then
		if ! bp_config_restore "$key" "$had_old" "$old" >/dev/null 2>&1; then
			echo "CRITICAL: UCI rollback failed after config commit rejection: $key" >&2
			return 8
		fi
		return 1
	fi
	if ! bp_config_apply; then
		if ! bp_config_restore "$key" "$had_old" "$old" >/dev/null 2>&1; then
			echo "CRITICAL: UCI rollback failed after config apply rejection: $key" >&2
			return 8
		fi
		# Restoring UCI cannot prove that partially applied uhttpd/firewall
		# state was restored; never report an ordinary reversible failure.
		echo "CRITICAL: UCI restored, but live configuration state unverified: $key" >&2
		return 8
	fi
	if command -v bp_auth_audit >/dev/null 2>&1; then
		bp_auth_audit config_change "${BP_AUTH_USER:-local}" "${REMOTE_ADDR:-local}" "$key"
	fi
	return 0
)
