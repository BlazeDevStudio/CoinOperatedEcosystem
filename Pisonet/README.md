# BlazePisonet SoftTimer

## Product boundary

This directory is reserved for **BlazePisonet SoftTimer**, the standalone Windows 10/11 x64 coin-operated PC timer within the CoinOperatedEcosystem repository. Its core paid-session and PC-locking operation must not require BlazePwifi, BlazeRental, the Phoenix control plane, or a diskless manager.

## Development priorities

1. Clean up and audit verified Windows source and existing regression tests before feature changes.
2. Implement and verify exact-device serial/USB-RS232 coin input, CTS/DSR pulse safety, debounce, reconnect, and duplicate-event rejection.
3. Verify paid-time conversion, countdown, local lock/unlock enforcement, durable session recovery, and administrator controls.
4. Verify Windows startup/watchdog and installer/uninstaller lifecycle; build an unsigned customer evaluation package only after focused Windows regression tests pass.

Financial and hardware admission must fail closed. Synthetic tests do not establish physical coinslot acceptance or real-money accounting reliability.

## Optional diskless companion

Diskless Manager (FOG/PXE/iPXE/iSCSI) is a **separately installable optional add-on** with independent configuration and storage. It must not be loaded as an arbitrary DLL into the financial timer process; absence or failure of the add-on must not disrupt paid sessions.

## Source and migration policy

**Migration status (M0):** the released SoftTimer **v0.4.0** baseline is imported, byte-identical and with path history, into [`SoftTimer/`](SoftTimer/) from `BlazeDevStudio/BlazingSystems-Experiments` `main` `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` (`experiment/windows/BlazePisonet-SoftTimer`). See [the migration record](../docs/migration/records/M0-pisonet-softtimer-v0.4.0-baseline.md). The imported tree is the released baseline only: **newer, unmerged SoftTimer work exists on Experiments draft branches** (ack verifier, CTS session pulse safety, native COM interface, SetupAPI hygiene) and is scheduled as separate, reviewable increments (M1-M4) in the migration plan. Do not assume `SoftTimer/` contains that work.

Historical `BlazeDevStudio/BlazingSystems-Experiments` PR #273 is **closed and unmerged**; its branch `feature/pisonet-optional-diskless-addon-20261107` (historical HEAD `a14e8b1e0ac1006d50880efb82856ea94116e978`) is read-only reference only. Do not merge/cherry-pick wholesale. Consider only missing compatible pieces after auditing this destination.

Windows runtime, physical USB-RS232/coin-slot and real-money accounting behavior are **not** established by this import. Status: **MIGRATING / NO-GO for production**.

Do not merge critical payment/hardware changes or publish a commercial release without owner authorization and appropriate safety evidence.
