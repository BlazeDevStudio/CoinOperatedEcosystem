# BlazeRental standalone — unresolved transaction recovery gate

**Status:** developer preview only. Do not use with real credit, coin acceptors, unattended rental hardware or customer accounts.

## Why a pending marker exists

The local CLI keeps device lease state and receipt rows in one `state.tsv` file, written by a same-directory temporary file and atomic rename. An exclusive `.lock` serializes writers. Before replacing the ledger, it creates `.pending` and requests a system `sync`; after rename and a second `sync`, it deletes `.pending` and requests a final `sync`. An unconfirmed write deliberately blocks **both status and write** requests rather than reporting a credit.

Importantly, `sync` does **not** establish proven per-file and directory fsync durability on the target OpenWrt flash filesystem, nor does it prove power-loss reliability. The marker narrows ambiguity but cannot eliminate hardware-specific loss windows. Do not claim power-safe accounting from passing host tests.

## When a failure happens

**Do not restart paid operation, grant the time again with a different transaction ID, automatically delete the marker, or restore a stale snapshot over live state.** An interrupted rename may already have changed the ledger.

1. Stop external traffic and block any charging/unlocking path. Keep the router and storage intact.
2. Inspect whether an old CLI writer is still active before investigating `.lock`; a `SIGKILL` can leave it behind.
3. Create an offline, access-controlled copy of `/etc/blazerental/state.tsv`, `.pending`, `.lock` and any `.state.*` staged files. Capture exact bytes and SHA-256 values. These contain device secrets; never commit, publish or email them.
4. Independently reconcile the original operator transaction ID, expected device, requested seconds, any external funding record and the current receipt row. A receipt already present must **not** be granted again.
5. If ledger integrity, ownership, or the external transaction outcome is uncertain, keep the system disabled and escalate to manual data recovery. No automatic replay or repair exists in this preview.
6. Even after a reviewer confirms the ledger and receipt history, any manual removal of markers is a controlled maintenance action **outside the current software**, requiring a documented backup, operator sign-off and retesting. There is no unattended self-unlock.

## Known architecture gaps

- No per-file and directory fsync proof on flash; no power-cut-on-device acceptance.
- No automatic crash recovery, snapshot, multi-generation journal, database migration or wear analysis.
- `state.tsv` grows indefinitely. A capacity-bound and flash-write-budget design are required.
- Clock rollback/forward protection and authenticated external credit provenance remain unimplemented.
- CGI provides read-only status, but HTTPS/pairing confidentiality and secure Android credential storage are not production-ready.
- The old BlazePwifi R281 installer has not been ported or validated as this project's installer.

## Locally executed regression coverage

`python3 -m unittest discover -s Rental/tests -v`

The added `test_durability.py` covers 14 scenarios: time-credit replay/conflict, simultaneous retries, intent/write/final sync failure, rename failure, bad receipt references, malformed entropy, invalid credit parameters, stale lock timeout, writer process kill, BusyBox syntax, blocked registration and HTTP status denial during `.pending`. Tests are Linux host process simulations, not OpenWrt device or APK tests.

**Release gate: PRODUCTION NO-GO.**
