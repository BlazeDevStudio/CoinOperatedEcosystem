# BlazeRental — independent development baseline

**Status:** P0 standalone preview source; **NOT a production rental system.**

This case-sensitive Rental/ source tree is independent of BlazePwifi, Pisonet, Phoenix CORE and all live payment services. Manual time grants are **local-router CLI only**; Android reads authenticated session status but cannot credit, unlock or enforce a phone.

- openwrt/: POSIX/BusyBox backend, local admin CLI, read-only CGI; persistent single-file device + transaction ledger.
- android/: independent Android status controller preview.
- docs/: historical provenance, security gaps and versioned API.
- tests/: host POSIX tests and Java crypto contract tests.

Quick local simulated test: python3 -m unittest discover -s Rental/tests -v from repository root (requires openssl, awk, POSIX shell and Java 17).

Do not execute the historical R281 installer as a means of installing this source. See docs/RECOVERY_AND_CLEANUP.md and docs/API_v1.md first.

Crash-safety scope: a missing or failed `sync`, interrupted rename, or killed writer may leave `.pending` / `.lock`; both admin and read-only status must fail closed until manual reconciliation. See [`docs/DURABILITY_AND_RECOVERY.md`](docs/DURABILITY_AND_RECOVERY.md). No automatic marker clearing or paid recovery exists.
