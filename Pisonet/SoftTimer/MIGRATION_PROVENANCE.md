# BlazePisonet source migration provenance

Date: 2026-11-07. Destination: `BlazeDevStudio/CoinOperatedEcosystem`, branch `pisonet/softtimer-foundation-20261107`.

Historical pinned source: `BlazeDevStudio/BlazingSystems-Experiments@21b065535640a735a1e22bda57718b9e8ad86a1a` (PR #255). Imported `experiment/windows/BlazePisonet-SoftTimer/src/` and three source-linked native COM/serial test suites under `Pisonet/SoftTimer/`. Every imported file retains original relative layout and exact Git blob SHA; compare tree entries for byte identity.

Historical [PR #238](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/238) and [PR #255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255) remain open/unmerged upstream. No branch merges/cherry-picks were used.

Historical [PR #273](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/273) was CLOSED UNMERGED. The optional-diskless branch `feature/pisonet-optional-diskless-addon-20261107` at `a14e8b1e0ac1006d50880efb82856ea94116e978` remains reference-only; diskless source was NOT imported.

Source includes legacy `BlazePwifiClient.cs` as an optional Windows network component; it does not import the OpenWrt backend and must not be a standalone-runtime dependency. No router, Android, firmware, or other Phoenix source was migrated.

Do not treat import/compilation/CI as production or physical-payment readiness. No commercial release, physical validation, signing, or mainline merge is authorized.

## Follow-up safety revision

This draft branch subsequently changes `src/BlazePisonet.SoftTimer/Storage.cs` to **fail closed** on missing/corrupt paid state rather than silently replacing it with an empty instance. Its Git blob SHA therefore intentionally differs from the pinned initial import. `tests/StateRecoveryGuard` is a new source-linked disposable-file test; `.github/workflows/pisonet-softtimer-windows.yml` is destination-only CI. No upstream Experiments file was modified. The old source and initial import commits retain exact provenance.
