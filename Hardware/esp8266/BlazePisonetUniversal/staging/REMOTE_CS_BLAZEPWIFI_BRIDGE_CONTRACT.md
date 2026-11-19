# Stage 5: contract to existing BLAZE PisoWiFi OpenWrt backend

**State: bridge REQUIRED, not implemented, paid payment NO-GO.** This note is based on direct examination of the existing repo's `Pisowifi/` source. It is intentionally outside the OpenWrt product ownership tree, which remains draft and has unresolved financial and physical release gates.

## What exists, and what does not match

JuanFi (`ivanalayan15/JuanFi`) is a reference for the *coin-window lifecycle*, not a protocol compatible with BLAZE. The current BLAZE ESP8266 Remote CS mode implements `BLZCS1` HMAC-SHA256 messages on its private `/api/pisowifi/control` endpoint, with `OPEN`, `CLOS`, `POLL`, `ACKN`, `EVNT`, `EMPT`, `OKAY`.

The repo already includes a separate first-party OpenWrt backend:
- `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/api`: `action=coin_start` issues an **8–32-hex target_nonce** for one account/window; `action=coin_stop` closes it.
- `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo`: listens on dedicated configured `vendo_port` (default **4455**), checks its own `action,id,nonce,pulses,target,sig` authorization, and offers `action=poll` (signed `insert,target_nonce,expires`) and `action=coin` (signed money mutation with recorded replay history).
- `Shared/contracts/controller-signature/schema_v1.json`: request/response contract for **existing** backend signed vendo messages.
- `Pisowifi/README.md`: **NO-GO for shop install**; financial uncertainty and physical validation still unresolved. Do not silently enable v2 paid ACK or bypass safeguards.

The above backend is **not** an implementation of `BLZCS1`. Neither side should interpret arbitrary `target_nonce` values as 64-bit session IDs without a stable, durable mapping. Remote CS does not contact the hotspot directly or issue vouchers.

## Required router bridge (separate owner approval and implementation)

1. **Authorize customer window.** Use the backend's existing `coin_start` flow, obtain the selected vendo ID, original target nonce, expiry and customer identity. Verify the backend is healthy and `poll.insert=1` and `coin_enabled=1` for that vendo. Persist a mapping `(ESP chip, BLZCS1 session64) -> (vendo id, original target_nonce, customer account, expiry)`. Never infer the account from IP alone.
2. **Open electrically.** Send signed HMAC `OPEN` to ESP with an incrementing durable controller command sequence, matching its configured controller ID/IP/key, and window <= 60 sec and <= backend expiry. The ESP locks D7 on restart, disconnected STA, unknown flash state, expired lease or prior pending event.
3. **Handle coins.** Periodically HMAC `POLL` the ESP. On signed `EVNT`, verify the correct ESP chip ID, mapped session, strictly positive bounded physical pulse count, and never alter an existing (device,event) receipt payload. The router's conversion from pulses to currency is authoritative.
4. **Durably apply exactly once.** Convert event to a **stable backend nonce**; use the real `/cgi-bin/vendo?action=coin` with the original bound target nonce and the existing backend signature. Verify the existing backend's **signed response**, account/receipt and absence of uncertainty markers before acknowledging. A request timeout is *unknown*, not failed; retry with the **same** backend nonce/pulses/target; do not add credit a second time.
5. **Only then ACK ESP.** Send BLZCS1 `ACKN` for **exact** event, session and pulses, with a new monotonic controller command. If ACK packet is lost, issue read-only `POLL`; an already-cleared event must never trigger a second router grant.
6. **Close and reconcile.** Send `CLOS` and close the OpenWrt target window. Never drop an unacknowledged event on close or expiration. If the backend expires the target before the durable ESP event is settled, **do not regenerate a new customer credit silently**; hold for operator reconciliation.
7. **Crash recovery.** Persist mapping, event acknowledgement decision and controller command sequence durably in one backend transaction or recoverable state machine. On router restart, first query the backend ledger and ESP journal; pending/unknown state **blocks coin acceptance** until resolved.

## Blocking compatibility issues

- **Session encoding mismatch:** backend target nonce 8–32 hex, ESP session exactly 16 hex. Requires unambiguous durable indirection.
- **Replay/ACK mismatch:** backend v1 replay receipt keyed partly by controller nonce and target; ESP uses (ESP ID, event ID). Same event must map to same backend nonce across process restart.
- **Time mismatch:** short ESP lease vs router window expiry. A power outage can delay `EVNT` beyond the backend window. Do not make a fraudulent ACK or lose the physical event.
- **Security mismatch:** backend `bp_check_vendo_sig` uses its existing controller signature contract, while ESP uses independent HMAC-SHA256. Never reuse or expose either secret to portal JavaScript. Restrict physical network and transport to local trusted VLAN.
- **Unfinished first-party paid acceptance:** `Pisowifi/README.md`, its paid-state-uncertain marker and Issue #31 require separate approval and physical proof. No production deployment based on Stage 5 firmware CI alone.

**Current milestone:** fourth-role ESP source, signed device protocol, isolated journal, and reference transport CLI are implemented and CI-tested. Actual OpenWrt router bridge and real customer accounting are **not** implemented in Stage 5.
