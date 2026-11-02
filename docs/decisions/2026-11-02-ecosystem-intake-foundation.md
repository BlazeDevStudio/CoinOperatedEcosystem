# Coin Operated Ecosystem — source cleanup/intake gate (2026-11-02)

This work is for **BlazeDevStudio/CoinOperatedEcosystem**, a separate repository.
Its `main` has only the README. The existing migration + Logo V2 branch provides
**directory and reference scaffolding**, not the application source.

## Why this code exists

Before copying historical code from the owner-controlled development repo,
the system now demands **per-file provenance** instead of mixing unrelated
work-in-progress branch snapshots. `inventory/source-intake.json` records five
live-verified reference anchors (CORE, RENTAL, PISONET, ESP8266, ESP32).
Each entry contains the source repo, exact source commit, PR, individual source
file, and Git blob SHA. All five are **candidate** status; ZERO imported runtime
source files. These anchors do not select a coherent integrated release and do not
verify every file in a module. The old branches and their PRs are untouched.

`tools/source_intake_guard.py` is a testable offline **fail-closed tool**.
It validates field names, mandatory module identity, non-relative unsafe paths,
SHA format, duplicate records, first-party ownership, absence of undocumented
runtime files, and the global production NO-GO marker. Future staged files
must have BOTH a SHA-256 of exact bytes and their Git blob SHA; staging with
symlinks, content mutations, or cross-module paths fails.

The tool does NOT fetch GitHub remotely or independently authenticate the
source commit/blob claim: that requires a separate connector/source retrieval
step before staging and review of copied bytes against the real source object.
It also does NOT authorize real coins, paid balances, firmware, key provisioning,
signatures, deployment, or release.

## Code hygiene before feature work

1. **Choose one authoritative writer for money and one immutable receipt format.**
   Do not reimplement the same transaction separately for OpenWrt, Windows, and
   Android. Identify duplicate paths and keep existing deny-first behavior.
2. **Separate validation from side effects.** Protocol parsing and authorization
   must be pure and tested; actual credit, persistent commit, GPIO, and UI updates
   need different owners and explicit failure handling.
3. **Migrate coherent dependency slices**, preserving original source blobs,
   attribution, required licenses and notices, tests, and honest CI outcomes.
4. **Run native/host tests after code cleanup**, and physical fail-closed evidence
   later on isolated owner-owned noncustomer devices. Simulated tests cannot
   prove protected key custody or anti-rollback durability.
5. **Leave historical drafts untouched** until owners reconcile exact heads,
   dependent PRs, provenance and rollback evidence.

External projects (LPB, iCafe/PanCafe, JuanFi, WiFi5Soft, ASAP Timer) are
architecture and UX references. No third-party source is copied in this change.
Direct imports from non-first-party repositories are intentionally rejected
until a separate license and attribution review is implemented.

## Execution

```sh
python3 -m unittest discover -s tests -p test_source_intake.py -v
python3 tools/source_intake_guard.py --root . --manifest inventory/source-intake.json
```

Every imported source file must have a matching `staged` manifest record and
pass CI; source selection and safety acceptance remain separate operations.
