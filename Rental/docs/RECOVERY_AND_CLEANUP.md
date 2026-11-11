# BlazeRental source verification and cleanup gate — 2026-11-08

## Exact repository boundary
- Repository: `BlazeDevStudio/CoinOperatedEcosystem`, default `main` at `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- Pre-existing `Rental` branch at `b0b0ebc27fbb8cbe9bb36e1d075a132060a819d0`, README-only. Neither has an executable case-sensitive `Rental/` tree.
- Historic migration PR #1 branch `migration/phoenix-monorepo-structure-20261028` at `3b84c75227a29eb0639b3aeba68c0d7c19010746`: LOWERCASE `rental/` README placeholders explicitly marked PHX-RENTAL / STRUCTURE_CREATED; not a standalone implementation.
- Live open PR review found no dedicated BlazeRental standalone PR; preserve unrelated branches and default HEAD.
- Earlier Android source: `BlazeDevStudio/BlazingSystems-Experiments/experiment/openwrt/BlazePwifi/android/BlazeRental/`. Historical client talks to `/cgi-bin/rental` and assumes BlazePwifi coin service. This is not standalone and is NOT silently imported or overwritten.
- Private archive: `BlazePwifi-R281-RentalHub-v0.1.0-installer.sh` (Google Drive file 1gMnZrkJL795jkcJtdDJxVzWCdm1WqECx, SHA-256 686f1d81e3557bfa7776f03e0a94c71d9c1192f663e3124746e69e652b475494). Consulted read-only, never executed or redistributed.

## Verified historical technical debt and corrective decisions
1. The R281 419-line installer embeds one UI and two CGI scripts, with duplicate form parsing, random generation, state writers and locks. Split responsibilities into one shared state module, a local administrative CLI and read-only CGI, rather than copying duplicated code.
2. Its time grants lack mandatory unique transaction IDs; repeated requests could grant time repeatedly. Put time state and transaction receipt in ONE locked, atomically replaced file; reject conflicting replays.
3. Old endpoints rely on an R281 board-specific and BlazePwifi-named state path. New code must use `/etc/blazerental` and independent `/cgi-bin/blazerental`; no assumed migration compatibility.
4. Old plaintext administrative HTTP token and CGI write paths are unacceptable for remote financial operations. Do not expose admin writes over HTTP in the isolated baseline.
5. Old Android source includes BlazePwifi URL labels and coin-start actions. Build a distinct status-only Android preview using a documented HMAC request/reply contract; keep device-owner/kiosk policy and payments disabled.
6. No in-scope executable historical Rental code can be refactored in place. Preserve it outside this PR and start a new, explicitly named **standalone** source baseline in authorized uppercase `Rental/`.
7. No approved logo was found or imported; do not improvise logo/artwork.

## Regression and release limits
- Host simulated tests, not router boot, flash wear, RTC, GPIO/coinslot or managed Android deployment.
- Power-cut durability, atomic directory fsync, process crash recovery and time manipulation require further testing.
- Installing an Actions workflow requires writing `.github/workflows/`, outside the authorized `Rental/` boundary. No cross-directory changes are allowed.
- No paid hardware, Phoenix, BlazePwifi, real signing keys, new public release or default-branch merge.
