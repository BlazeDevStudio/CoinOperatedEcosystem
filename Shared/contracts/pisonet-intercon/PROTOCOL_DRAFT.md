# BLAZE INTERCON — ESP8266 peer protocol vNext (DRAFT, not implemented)

Status: **SPECIFICATION / REVIEW ONLY**. This is deliberately distinct from the currently deployed BlazePwifi `controller-signature` HTTP Vendo contract, and is not a claim that the legacy plaintext UDP peer firmware is ready for paid operation.

## Purpose

An ESP8266 BLAZE PISONET fleet may discover peers on a trusted local Wi-Fi network, offer a local admin portal on each device, and operate in one of three selectable roles:

| Operator label | Internal role | Coin authority and runtime |
| --- | --- | --- |
| **Standard** (default) | `ROLE_STANDALONE` | Own local coin input, own paid timer, own sales journal, independent of peers. Ignores remote credit by default. |
| **Master** | `ROLE_MASTER` | Own physical coin acceptor and coin-slot-enable output. An approved slave requests/receives a target-bound coin window. Master accepts, journals and routes that coin event to exactly one selected slave. Does not simultaneously credit its own timer. |
| **Slave** | `ROLE_SLAVE` | Retains its local display, paid timer, relays, buzzer, power-button pulses, EEPROM recovery and admin portal. Hardware coin input is disabled for credit accounting; receives time only from its **paired, authenticated** master. |

An optional BlazePwifi integration adapter may nominate the OpenWrt accounting backend as authority for target/time/price. In that mode the ESPs do not independently create monetary value. Standalone clusters can use local configurable coin-to-seconds conversion, with explicit different accounting policy. No automatic shared bank migration between modes.

## Networking and discoverability

- **AP stays available:** use `WIFI_AP_STA` once STA is provisioned; keep a local WPA2 AP for each board while connected to the configured Wi-Fi. AP credentials must be unique or operator-configured. Preserve an accessible AP after STA join/loss, including without internet.
- **STA is optional and configurable:** SSID/password, DHCP or validated static LAN address, gateway, subnet and DNS. Display separate AP IP and STA IP. When the operator says "WAN IP", treat a Wi-Fi-router-assigned **STA/LAN IP** as the intended administrative address unless explicitly configured otherwise. Do not publish the portal or coin UDP endpoint to a public WAN.
- **AP+STA share the ESP8266's Wi-Fi radio/channel.** AP rechanneling and temporary disconnects must not interrupt local paid countdown or relay state.
- **Discovery:** periodically send low-rate UDP LAN broadcast/multicast HELLO with protocol version, immutable device ID and *non-sensitive* capabilities; also accept authenticated unicast registration and manual IP entry when router client isolation or broadcast blocking prevents discovery. Never discover nodes by trusting an SSID alone.
- **Pairing:** admin-authorized, physically scoped enrollment; store peer ID/key and explicit group membership. Discovery is *not* trust. Duplicate device names/IDs or conflicting masters are rejected.
- **Master selection:** one active target slave per physical coin window in the first implementation. An operator selects a discovered slave in the portal or the slave requests an insertion window. A window expires automatically and must be acknowledged before coin input is enabled.
- No dependency on Windows applications, Magic Packets, external internet, or an always-running central PC.

## Command contract (design; new version incompatible with legacy UDP)

Reserve a versioned, authenticated `intercon/v2` envelope rather than accepting legacy `CREDIT|...|millis()` packets. Wire-format choice (compact JSON or binary) is open; consumers **must** agree before implementation.

Required fields:
- `version`, `kind`, `group_id`, `sender_id`, `recipient_id`
- `boot_epoch` (random startup identifier), `sequence`, `event_id` (stable across retransmission)
- `coin_window_id`, `session_id`, `expires` or equivalent monotonic-window lease
- `payload` containing the bounded number of accepted pulses or granted seconds
- `key_id` and `auth_tag` computed with HMAC-SHA256 over canonical serialization

Proposed message kinds:
`DISCOVER`, `HELLO`, `PAIR_REQUEST`, `PAIR_ACCEPT`, `STATUS`, `REQ_WINDOW`, `WINDOW_GRANT`, `WINDOW_BUSY`, `COIN_EVENT`, `CREDIT_APPLIED`, `EVENT_STATUS`, `WINDOW_CLOSE`, `PING`.

The signed `COIN_EVENT` is **not** a blind grant of money. In standalone mode it is a physical coin event + an explicit conversion policy / credit grant; in BlazePwifi-managed mode financial authority and conversion live in the router. For both, the target and unique session/window must match.

## Reliability / paid-event state machine

1. Master receives an authenticated request from a paired slave and allocates a single target-bound coin window.
2. Master checks durable storage health before enabling its physical coin slot; deny coins if no valid target, authorization, journal space or network acknowledgment path.
3. When coin pulses arrive, master **writes and commits** an immutable event ID, target and pulse amount before transmitting it. Unjournaled pulses are quarantined/disabled, never silently discarded.
4. Slave authenticates source and target, verifies window/sequence and looks up the persisted event ID. It applies one credit update atomically with durable deduplication and then sends an authenticated `CREDIT_APPLIED` receipt.
5. If the ACK is lost, the master retransmits the **same** event ID; a slave returns `duplicate` or a status proof and **does not grant time twice**. After a timeout the event remains `UNRESOLVED`, not assumed failed or successful.
6. Master never changes the active target or accepts further paid events while an unknown/unreconciled event is outstanding. Resolve with `EVENT_STATUS`, a durable journal and operator intervention if needed.
7. During network outage, slave continues existing paid time and normal PC shutdown countdown; master disables remote coin intake or quarantines uncertain pulses, not fail-open. Standard role continues standalone.
8. After an unexpected reboot or power cut, local balances are recovered without double-credit. PWR_SW pulses are not replayed; all assumed PC states are explicitly marked estimated.

**Safety:** GPIO CS enable must not directly power a high-current coin acceptor. PC PWR_SW relay must be isolated and time-limited. Relay 1 may not cut PC mains before a normal Windows shutdown has completed.

## Role changes and permissions

Changing roles/pairings or STA network settings requires authenticated admin access with CS disabled during the transition. Block role switching with active coin windows or unresolved paid events. Preserve existing paid timers in every role; never silently zero a balance. A slave must fail closed on unpaired masters; Standard ignores `COIN_EVENT` entirely. Manual time grants are admin-only, separate from paid sales accounting and auditable.

No authentication through device name, source IP, Wi-Fi SSID, a mere shared password, or the legacy `millis()` credit token.

## Minimum test gates before promotion

- Same role on 2–10 nodes; mixed role topologies and duplicate IDs.
- AP+STA on the exact ESP8266 board with channel changes, STA reconnect, isolated client LANs, manual IP fallback.
- Pairing with invalid signature, unpaired master, forged source IP, replayed IDs, reordered/dropped packet and duplicate events.
- Flash power cuts: before journal, after journal, during slave application, after ACK lost, during reboot.
- Paid timer independently survives master loss, network split, ESP restart and remote admin outage.
- No credit loss or duplication, no unauthorized relay/PWR_SW pulse, no CS enabled on unresolved accounting state.
- Genuine Arduino/ESP8266 build, memory headroom, watchdog/heap soak, and isolated real coin + relay electrical tests.

**Release status: NO-GO.** This draft informs reviewed engineering work; existing upstream controller-signature and member-bank contracts are not altered.
