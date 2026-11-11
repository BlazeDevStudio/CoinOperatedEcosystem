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

This folder currently documents the authorized destination. **No SoftTimer source or tested Windows installer has been migrated here by this directory-creation change.** Before source import, check the current source, branches, open PRs, provenance, and tests. Historical `BlazeDevStudio/BlazingSystems-Experiments` PR #273 is **closed and unmerged**; its branch `feature/pisonet-optional-diskless-addon-20261107` (historical HEAD `a14e8b1e0ac1006d50880efb82856ea94116e978`) is read-only reference only. Do not merge/cherry-pick wholesale. Consider only missing compatible pieces after auditing this destination.

Do not merge critical payment/hardware changes or publish a commercial release without owner authorization and appropriate safety evidence.
