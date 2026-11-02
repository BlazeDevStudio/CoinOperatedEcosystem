# Component source baseline — Coin Operated Ecosystem

**Scope:** `BlazeDevStudio/CoinOperatedEcosystem`, before source migration.
The five current component owners remain in the separate historical development
repository. This PR does NOT copy app source, alter owner drafts or promote
any financial transaction.

## Why this is an executable code-cleanup prerequisite

A migration cannot be reviewed if "latest" is a mixture of unrelated branch
heads. This workflow checks out five **exact individual commits** from the
owner's first-party source repo into disposable GitHub-hosted test jobs:

| Component | Source PR | Baseline verification |
|---|---|---|
| CORE | #252 | CGI signed denial/duplicate replay, response binding host fixtures |
| RENTAL | #240 | Android launcher/update/TLS trust source contracts |
| PISONET | #255 | Native opened-HANDLE COM diagnostic and warnings-as-errors build |
| ESP8266 | #239 | Real sketch functions in offline host GPIO/poll mocks |
| ESP32 | #254 | Actual C++ header compiled with mbedTLS and denied hardware admission |

The source selection is intentionally **not** an integrated compatibility
proof. All five rows stay candidate-only in `inventory/source-intake.json`.
A pass means a narrow native/host test was executed at the stated commit,
not that signed money/relay authorization, physical coin hardware, rollback
witness or crash-atomic migration is ready.

The source-intake guard runs as a prerequisite. Individual component tests
are independent and can fail separately without cancelling the others.
No signing keys, customer credentials, firmware flashing, payment handling,
software release or third-party code import.

**Next:** record real CI results, inspect failing tests or cross-component
contract incompatibilities, select one complete dependency slice, clean that
source with its existing owner, then migrate byte-audited files via the intake
manifest. Do not blindly combine historical branches.
