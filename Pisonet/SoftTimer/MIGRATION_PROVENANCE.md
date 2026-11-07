# BlazePisonet source migration provenance

Date: 2026-11-07. Destination: `BlazeDevStudio/CoinOperatedEcosystem`, branch `pisonet/softtimer-foundation-20261107`.

Historical pinned source: `BlazeDevStudio/BlazingSystems-Experiments@21b065535640a735a1e22bda57718b9e8ad86a1a` (PR #255). Imported `experiment/windows/BlazePisonet-SoftTimer/src/` and three source-linked native COM/serial test suites under `Pisonet/SoftTimer/`. Every imported file retains original relative layout and exact Git blob SHA; compare tree entries for byte identity.

Historical [PR #238](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/238) and [PR #255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255) remain open/unmerged upstream. No branch merges/cherry-picks were used.

Historical [PR #273](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/273) was CLOSED UNMERGED. The optional-diskless branch `feature/pisonet-optional-diskless-addon-20261107` at `a14e8b1e0ac1006d50880efb82856ea94116e978` remains reference-only; diskless source was NOT imported.

Source includes legacy `BlazePwifiClient.cs` as an optional Windows network component; it does not import the OpenWrt backend and must not be a standalone-runtime dependency. No router, Android, firmware, or other Phoenix source was migrated.

Do not treat import/compilation/CI as production or physical-payment readiness. No commercial release, physical validation, signing, or mainline merge is authorized.

## Follow-up safety revision

This draft branch subsequently changes `src/BlazePisonet.SoftTimer/Storage.cs` to **fail closed** on missing/corrupt paid state rather than silently replacing it with an empty instance. Its Git blob SHA therefore intentionally differs from the pinned initial import. `tests/StateRecoveryGuard` is a new source-linked disposable-file test; `.github/workflows/pisonet-softtimer-windows.yml` is destination-only CI. No upstream Experiments file was modified. The old source and initial import commits retain exact provenance.

## NSIS lab packaging

`installer/BlazePisonet-SoftTimer.nsi` is an adapted, deliberately lab-namespaced derivative of historical Windows-only NSIS source blob `cb0c777d5272d53638f884b19eef23f82a7ea102`. `build-local.ps1` is copied byte-identically from blob `7070695dfbd67d44e8dca6f98dbf0c33784e1ab5`. Only the Windows Pisonet subsystem is involved; the LAB installer is neither installed nor commercially released by CI.

## Paid-state restart integrity hardening (2026-11-08)

The destination `Storage.cs` decoder now rejects an unresolved `.tmp` even with an existing primary, omitted required accounting fields, negative accounting counters and a significant future clock timestamp. It restores case-insensitive event/member lookup after JSON deserialization. `tests/StateRecoveryGuard/Program.cs` exercises those actual decoder paths using disposable files, while permitting a valid primary with a conventional old `.bak`. This is destination-only code; the pinned upstream historical source remains untouched. A synthetic pass does not certify physical payment behavior.

## Crash-safe write-path cleanup (2026-11-08)

`Storage.AtomicWrite` now creates its `.tmp` using `FileMode.CreateNew`, performs a flush-to-disk request, and uses Windows `File.Replace` without a non-atomic copy/overwrite fallback. Existing `.tmp` evidence blocks writes until reconciliation. The production method is exercised from the disposable `StateRecoveryGuard` test (initial commit, replace/backup, pending write preservation). Storage guarantees remain limited by underlying filesystem and power-loss behavior; no physical power-fault acceptance is claimed.
