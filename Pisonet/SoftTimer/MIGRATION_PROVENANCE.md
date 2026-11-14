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

## External-board active-low safety (2026-11-08)

The destination `SerialHardware.TryGetSignal` exposes whether a modem-control level is actually readable. `AppController.UpdateExternalBoard` now locks on unreadable/unsupported signals rather than inverting a default false value into an active-low unlock. The original `SerialHardware.cs` is compiled into the synthetic `NativeSerialPinFaultLab`; the new test executes true/false/throw/RI/disconnect cases. These tests do not attest physical device identity, and the exact-device paid coin gate stays disabled pending real native handle proof.

## Durable-first in-memory coin credit (2026-11-08)

`TimerEngine.TryPersistCredit` stages a copy of all financial fields and event IDs, invokes the real `Storage.SaveState` write **before** publishing state, and reports no success or timer UI callback if persistence fails. The timer latches `CreditPersistenceFaulted` on any uncertain save to prevent automatic retry. `AppController` now observes asynchronous coin handling faults, disconnects the serial acceptor after local credit storage failure, and prevents periodic reconnect while the latch is set. `tests/TimerCreditCommitGuard` compiles the actual production timer/storage code and injects deterministic write faults and duplicate IDs. A callback or disk failure cannot restore a physically consumed coin; manual operator reconciliation is still required. Other member-account mutation paths and physical hardware remain outside this focused gate.

## Post-fault countdown and access control (2026-11-08)

When a coin save raises an uncertain persistence error, `TimerEngine.Tick` now stops spending or rewriting paid time. The source-linked `TimerCreditCommitGuard` invokes the real private periodic callback in a disposable injected-storage engine and asserts no further debit or save. `AppController.EvaluateLockState` also treats `CreditPersistenceFaulted` as a customer lock condition, while admin maintenance remains available. This avoids infinite free play after the countdown is halted. Hardware lock behavior still needs Windows integration proof.

## Banked-time financial write isolation (2026-11-08)

Destination-only `TimerEngine` member banking, restoration, transfers and member-password updates now stage deep-copied paid state and persist before publication. Failed/ambiguous disk saves latch the existing financial persistence fault so no original member objects or callbacks are mutated. A periodic maintenance check locks the customer, disconnects the serial acceptor and blocks automatic reconnect after such a failure. The new `tests/MemberTimeCommitGuard` compiles the actual production timer and storage source and injects failing writes, checks unchanged original account references, and checks success ordering. Future audit must cover other persistence methods, recovery after power loss, and installed Windows UI lifecycle.

## Pending member reconciliation and remote bank reset (2026-11-08)

The destination TimerEngine now uses the same staged, deep-copied, persist-before-publish flow for recording/clearing BlazePwifi pending member operations, applying trusted remote-member snapshots, and resetting paid time after a confirmed remote bank. Failed writes preserve the existing pending event ID and remote member revision. A pending event ID cannot be replaced by a different unresolved operation. Source-linked MemberTimeCommitGuard tests reject failed pending-record/clear, reset and remote snapshot updates; a positive test verifies record → bank reset → clear and checks caller-owned object aliasing. No live network/payment claim or upstream merge.

## Timer-thread checkpoint failure hardening (2026-11-08)

The Windows `TimerEngine.Tick` periodic persistence path no longer writes directly to a published live-state object before disk acknowledgement. It stages the checkpoint, attempts the configured real persistence delegate, then publishes. If a checkpoint fails, it latches the existing financial storage-fault condition, emits no success notification, and **does not propagate an exception from the periodic ThreadPool timer callback**. Customer lock is still enacted by the AppController maintenance loop. The source-linked TimerCreditCommitGuard invokes the actual private Tick method using a deterministic elapsed monotonic tick and tests failed and successful checkpoint ordering. Uncommitted interim elapsed seconds and physical power failures still require dedicated acceptance testing.

## External authoritative timer persistence (2026-11-08)

`TimerEngine.SetAuthoritativeSeconds` now stages a new state, confirms any due storage checkpoint before publishing, and latches the existing persistence-fault lockout when an external serial/bridge update cannot be saved. Its event handlers no longer receive apparently successful state changes after a failed due checkpoint. The `Tick` error path now reports through the existing Audit event, which the production controller logs, rather than writing directly to ProgramData in the source-linked test. Added deterministic failed/successful external-authority storage cases to TimerCreditCommitGuard. Non-durable, short-lived external updates between checkpoint intervals remain part of current design and require hardware/operational review.

## Financial replay history retention (2026-11-09)

The destination production `Storage.SaveState` now delegates to `SaveStateToPath`, which creates a serialization snapshot without changing the caller's `UpdatedUtc` or `AppliedEventIds`. It removes the prior implicit `2048 → 1024` pruning that could forget paid event identities and allow old replay IDs to be accepted later. The source-linked `StateRecoveryGuard` writes and reloads 2601/2602 unique event IDs from disposable files, checks old-ID retention and case-insensitive replay lookup, preserves `.bak` after successful replacement, and denies an unresolved `.tmp`. This intentionally favors financial correctness over bounded state size; production readiness still needs an explicit scalable durable event ledger / size and performance acceptance.

## LAB installer privilege and lifecycle boundary (2026-11-09)

The destination NSIS preview now performs only an isolated LAB Program Files / shortcuts / registry file installation. It no longer executes canonical `--install-system-integration` / `--uninstall-system-integration`, kills processes by shared basename, modifies the common `maintenance.until`, or changes ACLs on the canonical state directory. Setup aborts when an existing installed product executable or nonempty canonical ProgramData state is detected. `InstallerLayoutGuard/validate.ps1` source-checks these forbidden patterns and the protective check. This is a source-level and NSIS compilation gate only; an installed/uninstalled Windows VM execution and full runtime identity/storage isolation remain required.

## SetupAPI and Win32 P/Invoke platform boundary extraction (2026-11-11)

Imported the SetupAPI / Win32 P/Invoke platform isolation from historical `BlazeDevStudio/BlazingSystems-Experiments@669e3417dc932c28c5584c13aad0ae7ad436df3b` ([PR #279](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/279), `qa/pisonet-setupapi-hygiene-20261108`) with exact Git blob SHA identity:
- `src/BlazePisonet.SoftTimer/NativeComInterfaceTransport.cs` (`96952fc5c2425d90e29497ca8f567638142e1bd6`): separates exact-handle session ownership from raw Win32 P/Invoke interop.
- `src/BlazePisonet.SoftTimer/WindowsNativeComPlatform.cs` (`6bac39c1d120b5ea8fde8ce6b97b32be44942957`): isolates `WindowsNativeComPlatform`, `ReadDeviceInterface`, `ReadDetailAndInstanceId`, and SetupAPI/Kernel32 P/Invoke declarations.
- `tests/NativeComInterfaceHandleLab/NativeComInterfaceHandleLab.csproj` (`82c6805cd740667c8dbff09e1cde5d57e56adc0b`): links `WindowsNativeComPlatform.cs` alongside `NativeComInterfaceTransport.cs`.
Physical device attestation remains unproven and exact-device paid coin admission remains disabled (**NO-GO**).

## Member accounting validation cleanup (2026-11-15, isolated review)

A child review branch of the Windows M4 migration (`cleanup/pisonet-setupapi-platform-boundary-20261111` at `3ef98d426f0c2ab04928293917341275b78f47ac`) centralizes the duplicated load/save financial-state checks into `Storage.ValidateFinancialState`. It additionally rejects null, blank-key, negative-balance, or negative-revision local/remote member entries before any paid state is loaded or written. `tests/StateRecoveryGuard` now source-links those negative cases with disposable files. This is a **destination-only review change**, not a new upstream import, hardware validation, merge, or release. See `docs/STATE_RECOVERY_TROUBLESHOOTING.md` for human diagnostics; physical and production financial acceptance remain NO-GO.

## Configuration continuity after corruption (2026-11-15, isolated review)

Stacked exclusively on `cleanup/pisonet-member-state-validation-20261115` at `b21b04617d38a177260258de2d56b24382822117`. The old installed `Storage.LoadConfig` swallowed any configuration parsing/read error and returned a new `AppConfig` with a fresh `CentralSharedKey` and device identity. That could silently erase administrator settings or change protocol bindings; an existing `config.json.tmp` was not treated as a pending configuration transaction.

The new source-linked `LoadConfigFromPath` keeps true first installation operational but denies recovery when a prior configuration `.bak` or `.tmp` exists, **any neighboring paid-state `state.json`, `.bak`, or `.tmp` exists despite missing configuration**, a configured primary is malformed, a pending write is unresolved, or existing key/controller identity is empty. On denial, the original files remain untouched and the normal WinForms startup error handler exits rather than launching a reset environment. The `StateRecoveryGuard` fixture now executes disposable first-install, steady restart, malformed primary, missing-primary-with-backup, pending-write and missing-identity cases; `CONFIG_FAIL_CLOSED_RECOVERY_PASS` is a test marker, not evidence until an exact-head Windows run succeeds.

**Compatibility note:** previously saved, parseable legacy configuration missing `CentralSharedKey` or `BlazePwifiControllerId` now needs an explicit supervised migration plan; no automatic secret/controller regeneration is permitted. This is intentional fail-closed behavior. No migration, manual key provisioning, end-user installation, real payment or physical test was performed; production remains NO-GO.
