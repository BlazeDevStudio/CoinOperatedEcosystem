#!/bin/sh
# BlazePwifi capability-tier detector.
# Explicit capability_tier always wins. Auto mode chooses a conservative
# feature set so small routers are not overloaded by Standard/Full services.

bp_cap_read_mem_kb() {
	awk '/MemTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null || true
}

bp_cap_read_overlay_kb() {
	# df column 4 is AVAILABLE; column 2 is filesystem total, which
	# dangerously promotes nearly-full storage to a higher capability tier.
	# awk succeeds even on missing rows, so a pipeline || cannot detect
	# absent /overlay and must be replaced by an explicit value check.
	for mount in /overlay /; do
		free_kb="$(df -Pk "$mount" 2>/dev/null | awk 'NR==2 {print $4; exit}')"
		case "$free_kb" in
			''|*[!0-9]*) ;;
			*) printf '%s\n' "$free_kb"; return 0 ;;
		esac
	done
	return 1
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
