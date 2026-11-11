#!/bin/sh
# Explicit installation for a verified OpenWrt with uHTTPd CGI at /www/cgi-bin.
# No auto-install, no network/firewall/UCI mutations, no service restart.
set -eu
[ "$(id -u)" -eq 0 ] || { echo 'root required' >&2; exit 1; }
[ -f /etc/openwrt_release ] || { echo 'OpenWrt required' >&2; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo 'openssl required' >&2; exit 1; }
command -v uci >/dev/null 2>&1 || { echo 'uci required' >&2; exit 1; }
[ "$(uci -q get uhttpd.main.home)" = /www ] || { echo 'uHTTPd /www required' >&2; exit 1; }
[ "$(uci -q get uhttpd.main.cgi_prefix)" = /cgi-bin ] || { echo 'uHTTPd /cgi-bin required' >&2; exit 1; }
cd "$(dirname "$0")"
for path in /usr/lib/blazerental/core.sh /usr/sbin/blazerentalctl /www/cgi-bin/blazerental; do
    [ ! -e "$path" ] || { echo "Refusing to overwrite $path" >&2; exit 1; }
done
install -d -m 700 /usr/lib/blazerental /etc/blazerental
install -m 644 lib/core.sh /usr/lib/blazerental/core.sh
install -m 755 bin/blazerentalctl /usr/sbin/blazerentalctl
install -m 755 cgi-bin/blazerental /www/cgi-bin/blazerental
/usr/sbin/blazerentalctl init
printf '%s\n' 'BlazeRental read-only controller API installed. No paid access or remote administrative control enabled.'
