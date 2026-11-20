# Stage 5.1 — actual BLAZE PisoWiFi v1 vendo bridge (LAB / NO-GO)

## What is now implemented

The exact existing first-party router code was inspected:

- `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/common.sh` lines containing `bp_vendo_sig_expected` sign outgoing controller requests using lowercase `sha256(secret|action|id|nonce|pulses|target|secret)`. This **legacy v1 hash is not HMAC**.
- `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo` has `action=poll` for a signed `insert`, `target_nonce`, `expires` response; `action=coin` performs real receipt/balance accounting with a signed `duplicate`, `credited_cents`, `credit_cents`, `target_nonce` response. It runs on the configured **dedicated vendo port** (default 4455), not the ordinary hotspot web port.
- `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/api` has customer-authenticated `coin_start` and `coin_stop` actions. They already create and close customer-specific target windows on the router. The bridge never fabricates a portal session.

**New**: `Hardware/tools/remote_cs_router_bridge.py` is a Python 3 **router companion/sidecar** using both real interfaces. The ESP still runs the full Stage 5 `BlazePisonetIntercon.ino` and `BLZCS1` HMAC protocol. The sidecar:

1. First asks the ESP for a **signed POLL**; an unsettled `EVNT` is handled before opening any new window.
2. For an empty slot, sends the router's exact signed v1 `poll` request and **validates its signed response** plus coin flags.
3. Derives a deterministic, nonzero 64-bit ESP session from the router's original target nonce and vendo ID. Stores `(ESP ID, session, original router target, expiry)` in SQLite with `synchronous=FULL`. Refuses inconsistent mappings.
4. With an operator-supplied `--enable-paid-lab` flag, sends a signed `OPEN` lease to the ESP with a **durably advanced, monotonic command sequence**. The lease is capped to 60 seconds, with margin before the router's original expiry.
5. When `EVNT` arrives, resolves the signed session to its **original, persisted router target** (not just MAC/IP), and derives a stable 32-hex router nonce keyed by ESP/event/session. Retries of the same physical event use **the same nonce, target and pulses**.
6. Calls existing `/cgi-bin/vendo?action=coin`; validates the **actual v1 signed paid receipt**. Unknown/failed/timeouts are **never treated as failure-proof or paid success**; the ESP event remains unsettled until a signed, recoverable result.
7. Persists the verified credit proof in SQLite **before** sending ESP `ACKN`. Lost ACK HTTP response is handled through the ESP's signed next POLL, without re-crediting the router.
8. If a router target is expired or a payment is missing/ambiguous, **stops**, leaves the ESP coin gate closed and requires operator reconciliation. It never reassigns a pulse to a different customer session.
9. Without `--enable-paid-lab`, the adapter performs read-only, cryptographically verified discovery and prints what it *would* do. It does **not** open the acceptor, forward a payment or ACK an event.

The bridge does not issue vouchers, manage coin rates or operate as a payment ledger: it delegates those to the **existing** router source.

## Local lab invocation (sidecar machine with Python 3.10+)

Follow `README_START_HERE.md` for Arduino firmware compilation. The separate bridge is started from the extracted `Tools/` folder:

```bash
export BLAZE_REMOTE_CS_KEY='<64 random HEX chars, SAME as ESP pairing>'
export BLAZE_VENDO_KEY='<actual long router UCI vendo_key>'
python3 Tools/remote_cs_router_bridge.py \
  --esp-url http://192.168.1.70 \
  --vendo-url http://192.168.1.1:4455/blazepwifi/cgi-bin/vendo \
  --esp-id 00ABCDEF \
  --controller-id A0000001 \
  --vendo-id my_remote_cs \
  --db ./remote-cs-durable.sqlite3
```

All shown IPs, IDs and account names are **examples only**; these are not discovered/verified user network details. The default mode is read-only. The `--enable-paid-lab --loop` flags require an isolated, physically supervised bench, a working **existing** router and an independently verified coin driver. Not a shop deployment recipe.

The ESP must be paired to exactly the same controller ID/IP/HMAC secret. The router's `vendo_key` is **different** from the ESP's HMAC key; never paste them into a public portal or commit them in Git. Set a dedicated sender IP pinned in ESP; NAT/relays can change this IP and prevent acceptance.

Use a secure persistent directory owned by the bridge process (0600 DB; do not store in `/tmp` or an auto-erased filesystem). Never delete the DB to reset credits or reuse a command counter. Before enabling any payment, inspect the real source's existing `coin_start`/selected vendo setup; choose a **hotspot-only** vendo. Rental targets are NOT supported in this adapter. Do not configure an occupied live shop machine.

## Independent validation

- `Hardware/tests/test_remote_cs_router_bridge.py` runs isolated **SQLite-backed** mock regressions: exact legacy v1 signature, forged signatures, invalid session, changed payload, paid reply dropped **after router commit**, lost ESP ACK HTTP response, missing uncredited event, expiry and dry-run isolation.
- CI also runs native C++ HMAC/journal tests and compiles the real NodeMCU sketch with ESP8266 core 3.1.2.
- The GitHub Actions source artifact packages the full `BlazePisonetIntercon/` folder, both tools, test script, exact setup docs and SHA-256 manifest, with **NO BIN** files.

These are source/build/fault tests, **not** live coin, OpenWrt RouterOS/network, sudden-power-cut or paid-customer acceptance tests.

## Release blockers

- The actual OpenWrt router code has **its own** financial NO-GO and production v2 paid authority is disabled. The v1 signed `poll` response does **not** include an independently protected, authoritative "financial state healthy" witness; router can still advertise insertion while a separate uncertainty marker is raised. Physical acceptor must remain disconnected from real customers until this backend gap is fixed and audited.
- OpenWrt appliances may not ship Python/SQLite. This is a **sidecar reference bridge**, not an installable OpenWrt service. A native BusyBox/OpenWrt adaptation with trusted startup/secrets and process supervision is not yet integrated.
- The backend `coin` interface has no signed target-*kind* field before accepting pulses. A reserved rental window could be mistaken for a hotspot window before the backend returns `rental:true`. Dedicate the vendo to hotspot coin windows; production must harden that binding at the server.
- The legacy `coin` journal remains bounded and lacks a protected anti-rollback witness. A signed v1 response and local SQLite receipt do not prove irreversible, exactly-once financial settlement under malicious rollback/storage failure.
- Power loss between the ESP's real electrical edge and first durable flash commit remains an unsolved physical issue. Driver power polarity, the D7 inactive state at cold boot, denomination-specific timing and a bench hold-up circuit require real measurements.
- Router/ESP network outages can postpone or strand a pending event until after window expiry; the adapter **does not invent time or money** to mask this. Operator reconciliation is required.
- All releases remain **DRAFT / LAB / NO-GO**. Do not flash an occupied shop machine or enable live monetary settlement based on passing CI.
