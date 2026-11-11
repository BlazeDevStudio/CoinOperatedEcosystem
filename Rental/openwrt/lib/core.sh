#!/bin/sh
# BlazeRental v1 — shared POSIX/BusyBox state operations. Local CLI is the only writer.
# Intentionally does not depend on BlazePwifi, Phoenix, ubus or any coin controller.
BR_STATE_DIR=${BLAZERENTAL_STATE_DIR:-/etc/blazerental}
BR_DB=$BR_STATE_DIR/state.tsv
export LC_ALL=C
umask 077

br_die() { printf 'BlazeRental: %s\n' "$*" >&2; return 1; }
br_id_ok() { printf '%s' "$1" | grep -Eq '^[0-9a-f]{24}$'; }
br_secret_ok() { printf '%s' "$1" | grep -Eq '^[0-9a-f]{64}$'; }
br_tx_ok() { printf '%s' "$1" | grep -Eq '^[A-Za-z0-9_-]{12,64}$'; }
br_uint_ok() { case "$1" in ''|*[!0-9]*) return 1;; esac; [ "$1" -le 4102444800 ] 2>/dev/null; }
br_clock() {
    BR_NOW=$(date +%s) || return 1
    br_uint_ok "$BR_NOW" && [ "$BR_NOW" -ge 1700000000 ] || br_die 'clock not synchronized'
}
br_init() {
    [ ! -L "$BR_STATE_DIR" ] || { br_die 'state directory is a symlink'; return 1; }
    mkdir -p "$BR_STATE_DIR" || return 1
    chmod 700 "$BR_STATE_DIR" || return 1
    [ ! -L "$BR_DB" ] || { br_die 'state file is a symlink'; return 1; }
    if [ ! -e "$BR_DB" ]; then
        # Exclusive creation; refuses to truncate a concurrently created file.
        ( set -C; : > "$BR_DB" ) 2>/dev/null || [ -f "$BR_DB" ] || return 1
    fi
    chmod 600 "$BR_DB" || return 1
    br_check
}
br_check() {
    # A prior writer may have died after preparing or replacing the state file.
    # Operators must reconcile its receipts before unblocking ANY read or write.
    { [ ! -e "$BR_STATE_DIR/.pending" ] && [ ! -L "$BR_STATE_DIR/.pending" ]; } || { br_die 'unresolved transaction: manual recovery required'; return 1; }
    { [ -f "$BR_DB" ] && [ ! -L "$BR_DB" ]; } || { br_die 'state file missing or unsafe'; return 1; }
    awk -F '\t' '
    $1=="D" {
        if(NF!=4 || length($2)!=24 || $2 !~ /^[0-9a-f]+$/ || length($3)!=64 || $3 !~ /^[0-9a-f]+$/ || $4 !~ /^[0-9]+$/ || $4+0>4102444800 || seenD[$2]++) bad=1
        if ($4 ~ /^[0-9]+$/) until[$2]=$4+0
        next
    }
    $1=="R" {
        if(NF!=5 || $2 !~ /^[a-zA-Z0-9_-]+$/ || length($2)<12 || length($2)>64 || length($3)!=24 || $3 !~ /^[0-9a-f]+$/ || $4 !~ /^[0-9]+$/ || $4+0<1 || $4+0>2592000 || $5 !~ /^[0-9]+$/ || $5+0>4102444800 || seenR[$2]++) bad=1
        referenced[$3]=1
        if ($5 ~ /^[0-9]+$/ && $5+0 > highest[$3]) highest[$3]=$5+0
        next
    }
    {bad=1}
    END {
        for (id in referenced) if (!(id in seenD) || highest[id] > until[id]) bad=1
        exit bad?1:0
    }' "$BR_DB" || br_die 'corrupted state; refusing operation'
}
br_lock() {
    i=0
    while ! mkdir "$BR_STATE_DIR/.lock" 2>/dev/null; do
        i=$((i+1)); [ "$i" -lt 5 ] || { br_die 'state locked; refusing operation'; return 1; }
        sleep 1
    done
    trap 'rmdir "$BR_STATE_DIR/.lock" 2>/dev/null || :' 0
    trap 'exit 130' 1 2 3 15
}
br_unlock() {
    rmdir "$BR_STATE_DIR/.lock" 2>/dev/null || return 1
    trap - 0 1 2 3 15
}
br_get_device() { awk -F '\t' -v id="$1" '$1=="D" && $2==id {print;exit}' "$BR_DB"; }
br_get_receipt() { awk -F '\t' -v id="$1" '$1=="R" && $2==id {print;exit}' "$BR_DB"; }
br_random() { openssl rand -hex "$1" 2>/dev/null || br_die 'secure entropy unavailable'; }
br_commit() {
    # The intent marker persists if a writer is killed or a sync fails.
    # Atomic same-filesystem rename protects the ledger/receipt pair; sync
    # barriers are bounded best-effort durability, NOT a flash power-loss proof.
    tmp=$1
    { [ -f "$tmp" ] && [ ! -L "$tmp" ]; } || { br_die 'unsafe staged file'; return 1; }
    chmod 600 "$tmp" || { br_die 'cannot secure staged file'; return 1; }
    { [ ! -e "$BR_STATE_DIR/.pending" ] && [ ! -L "$BR_STATE_DIR/.pending" ]; } || { br_die 'unresolved pending transaction'; return 1; }
    if ! ( set -C; printf 'PENDING\n' > "$BR_STATE_DIR/.pending" ); then
        br_die 'cannot create transaction intent'; return 1
    fi
    if ! sync; then
        br_die 'intent sync failed; recovery required'; return 1
    fi
    if ! mv -f "$tmp" "$BR_DB"; then
        br_die 'atomic replacement failed; recovery required'; return 1
    fi
    if ! sync; then
        br_die 'ledger sync failed; recovery required'; return 1
    fi
    if ! rm -f "$BR_STATE_DIR/.pending"; then
        br_die 'intent cleanup failed; recovery required'; return 1
    fi
    if ! sync; then
        # Re-create an intent barrier where possible: never report success.
        ( set -C; printf 'UNCONFIRMED\n' > "$BR_STATE_DIR/.pending" ) 2>/dev/null || :
        sync || :
        br_die 'final sync failed; recovery required'; return 1
    fi
}
br_registration() {
    br_clock && br_check && br_lock || return 1
    br_check || return 1
    id=$(br_random 12) || return 1
    secret=$(br_random 32) || return 1
    { br_id_ok "$id" && br_secret_ok "$secret"; } || { br_die 'random data invalid'; return 1; }
    [ -z "$(br_get_device "$id")" ] || { br_die 'id collision'; return 1; }
    tmp=$(mktemp "$BR_STATE_DIR/.state.XXXXXXXX") || return 1
    if cat "$BR_DB" > "$tmp" && printf 'D\t%s\t%s\t%s\n' "$id" "$secret" "$BR_NOW" >> "$tmp" && br_commit "$tmp"; then
        br_unlock || return 1
        printf 'device_id=%s\ndevice_secret=%s\n' "$id" "$secret"
    else
        rm -f "$tmp"; return 1
    fi
}
br_grant() {
    id=$1; seconds=$2; tx=$3
    { br_id_ok "$id" && br_tx_ok "$tx" && br_uint_ok "$seconds" && [ "$seconds" -ge 1 ] && [ "$seconds" -le 2592000 ]; } || { br_die 'invalid grant parameters'; return 1; }
    br_clock && br_check && br_lock || return 1
    br_check || return 1
    receipt=$(br_get_receipt "$tx")
    if [ -n "$receipt" ]; then
        oldid=$(printf '%s\n' "$receipt" | cut -f3)
        oldseconds=$(printf '%s\n' "$receipt" | cut -f4)
        lease=$(printf '%s\n' "$receipt" | cut -f5)
        { [ "$oldid" = "$id" ] && [ "$oldseconds" = "$seconds" ]; } || { br_die 'transaction conflict'; return 1; }
        br_unlock || return 1
        printf 'lease_until=%s\nreplayed=true\n' "$lease"
        return 0
    fi
    device=$(br_get_device "$id")
    [ -n "$device" ] || { br_die 'unknown device'; return 1; }
    secret=$(printf '%s\n' "$device" | cut -f3)
    lease=$(printf '%s\n' "$device" | cut -f4)
    br_uint_ok "$lease" || { br_die 'invalid lease'; return 1; }
    [ "$lease" -ge "$BR_NOW" ] || lease=$BR_NOW
    new=$((lease + seconds))
    [ "$new" -le 4102444800 ] || { br_die 'lease overflow'; return 1; }
    tmp=$(mktemp "$BR_STATE_DIR/.state.XXXXXXXX") || return 1
    if awk -F '\t' -v id="$id" '!( $1=="D" && $2==id )' "$BR_DB" > "$tmp" &&
      printf 'D\t%s\t%s\t%s\n' "$id" "$secret" "$new" >> "$tmp" &&
      printf 'R\t%s\t%s\t%s\t%s\n' "$tx" "$id" "$seconds" "$new" >> "$tmp" &&
      br_commit "$tmp"; then
        br_unlock || return 1
        printf 'lease_until=%s\nreplayed=false\n' "$new"
    else
        rm -f "$tmp"; return 1
    fi
}
br_status() {
    id=$1
    br_id_ok "$id" && br_clock && br_check || return 1
    device=$(br_get_device "$id"); [ -n "$device" ] || { br_die 'unknown device'; return 1; }
    lease=$(printf '%s\n' "$device" | cut -f4)
    br_uint_ok "$lease" || { br_die 'invalid lease'; return 1; }
    printf 'server_time=%s\nlease_until=%s\n' "$BR_NOW" "$lease"
}
