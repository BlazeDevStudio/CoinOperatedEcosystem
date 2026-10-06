# Integration guide

## 1. Standard Pisonet: one coinslot / one PC

### Direct USB-RS232

`Coinslot -> USB-RS232 -> Windows PC -> BlazePisonet SoftTimer`

Select:

- Timer source: `InternalPcTimer`
- Coin topology: `StandardOneToOne`
- Serial selection: preferably `ExactDevice`

SoftTimer converts each accepted serial-control pulse to `SecondsPerCoin` and owns the countdown.

### External timer board

`Coinslot -> Allan/Piso timer board -> USB-RS232 -> SoftTimer`

Select:

- Timer source: `ExternalTimerBoard`
- configure the timer-active signal/polarity for the board.

The hardware timer remains authoritative; SoftTimer only enforces Windows access.

### Existing Blaze Pisonet Timer

`Coinslot -> Blaze ESP8266 Timer <-> Wi-Fi/LAN <-> SoftTimer PC`

Select `BlazePisonetTimer`, scan the local network, and pair the desired timer. SoftTimer follows the existing timer's remaining-time state. The ESP firmware remains responsible for physical timing/relay behavior.

## 2. Centralized Windows mode: one coinslot / many PCs

Coordinator:

- `CentralizedCoordinator`
- timer source `InternalPcTimer`
- USB-RS232 coinslot connected only to the coordinator
- set shared key and peer port.

Stations:

- `CentralizedStation`
- same shared key;
- coordinator URL points to the coordinator PC;
- unique station ID.

Flow:

1. Locked station requests the coin slot.
2. Coordinator places the station in its queue.
3. Only one station becomes READY at a time.
4. Coin pulse is accepted at the coordinator.
5. Coordinator creates a unique credit event and sends signed time to that station.
6. Station records the event ID before/with credit application; duplicates are ignored.

The default peer port is TCP 8765. The installer firewall rule is limited to the private local subnet.

## 3. Existing Blaze Pisonet Master/Slave system

Do not replace the current Master/Slave protocol merely to add SoftTimer.

Recommended deployment:

- keep one central coinslot on the existing Master;
- keep current Slave timers and local countdowns;
- pair each Windows SoftTimer instance to the Slave/timer belonging to that PC;
- SoftTimer then locks/unlocks Windows based on the already-routed timer state.

This is the least invasive almost-wireless integration.

## 4. BlazePwifi

SoftTimer can use the current Vendo endpoint directly.

Configuration requires:

- BlazePwifi Vendo URL, normally `http://SERVER:4455/cgi-bin/vendo`;
- controller ID;
- the current `vendo_key` shared secret.

The signing string matches the current BlazePwifi contract:

`SHA256(secret|action|id|nonce|pulses|target|secret)`

Supported current integration:

- signed `ping`/`poll`;
- controller heartbeat;
- detection of an active target-bound coin window;
- optional forwarding of a SoftTimer serial coin pulse as the existing signed/idempotent BlazePwifi `coin` event.

SoftTimer does not require changes to BlazePwifi accounting for this integration.
