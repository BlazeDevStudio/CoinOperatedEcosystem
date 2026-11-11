#!/bin/sh
# BlazePwifi capability-tier detector.
# Explicit capability_tier always wins. Auto mode chooses a conservative
# feature set so small routers are not overloaded by Standard/Full services.

bp_cap_read_mem_kb() {
	awk '/MemTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null || true
}

bp_cap_available_kb() {
	target="$1"
	output="$(df -Pk "$target" 2>/dev/null)" || return 1
	available="$(printf '%s\n' "$output" | awk 'NR==2 {print $4; exit}')"
	case "$available" in ''|*[!0-9]*) return 1;; esac
	printf '%s\n' "$available"
}

bp_cap_read_overlay_kb() {
	bp_cap_available_kb /overlay || bp_cap_available_kb /
}

bp_cap_detect() {
	tier="${BP_CAP_TIER:-auto}"
	case "$tier" in
		lite|standard|full) printf '%s\n' "$tier"; return 0 ;;
		auto|'') ;;
		*) echo "invalid capability tier: $tier" >&2; return 2 ;;
	esac

	arch="${BP_CAP_ARCH:-$(uname -m 2>/dev/null || echo unknown)}"
	mem="${BP_CAP_MEM_KB:-$(bp_cap_read_mem_kb)}"
	overlay="${BP_CAP_OVERLAY_KB:-$(bp_cap_read_overlay_kb)}"
	case "$mem" in ''|*[!0-9]*) mem=0;; esac
	case "$overlay" in ''|*[!0-9]*) overlay=0;; esac

	case "$arch" in
		x86_64|amd64)
			if [ "$mem" -ge 1048576 ] && [ "$overlay" -ge 524288 ]; then
				printf 'full\n'
			elif [ "$mem" -ge 262144 ] && [ "$overlay" -ge 65536 ]; then
				printf 'standard\n'
			else
				printf 'lite\n'
			fi
			;;
		aarch64|arm64)
			if [ "$mem" -ge 262144 ] && [ "$overlay" -ge 65536 ]; then
				printf 'standard\n'
			else
				printf 'lite\n'
			fi
			;;
		*)
			printf 'lite\n'
			;;
	esac
}

case "${1:-}" in
	--detect|'') bp_cap_detect ;;
	*) echo "usage: $0 [--detect]" >&2; exit 2 ;;
esac
