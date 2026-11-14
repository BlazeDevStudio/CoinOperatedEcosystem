# PHX-QA | External-board active-low authority guard | 2026-11-15

**Status:** IN PROGRESS — test-only; Windows native execution NOT YET RUN.  
**Task:** [Experiments #164](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/164), independent source-linked migration regression.  
**Parent owner:** [COE PISONET DRAFT #30](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/30), exact parent `8144242c0469ffc9fc7757ebe91964caa4a2a527`.  
**Affected scope:** `Pisonet/SoftTimer/tests/NativeSerialPinFaultLab/` only. No production C# or release workflow changes.

## Source-confirmed migration risk

Old Experiments PISONET owner PR #255 at `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` has two cooperating unsafe behaviors when configured with `TimerActiveHigh=false`: `SerialHardware.GetSignal` returns `false` on an I/O exception; `AppController.UpdateExternalBoard` uses `!raw` and calls `SetAuthoritativeSeconds(1)`. This can turn an unreadable active-low board into an apparent active timer signal. This is a source-level conditional risk; **no real hardware or customer failure was observed**.

COE staged owner source already separates measurement success from level via `TryGetSignal(..., out raw)`, with an error branch setting 0 and returning **before** polarity inversion. Native fake-OS tests cover measurement unknown but did not assert that the actual `AppController.UpdateExternalBoard` source still contains this downstream fail-closed branch. A future blind old-code import could restore the unsafe access-control transition while leaving native serial tests green.

## Independent QA test contract

A small isolated `ExternalBoardAuthoritySourceGuard.cs` verifier will read the **actual production `AppController.cs`** from the checkout, extract the real `UpdateExternalBoard` method, and require:
1. Error-aware `!_serial.TryGetSignal(Config.TimerActiveSignal, out var raw)` branch.
2. That branch explicitly denies authority via `_timer.SetAuthoritativeSeconds(0, ...)` and `return;`.
3. The branch occurs **before** `Config.TimerActiveHigh ? raw : !raw`, which precedes `SetAuthoritativeSeconds(active ? 1 : 0, ...)`.
4. No old `_serial.GetSignal(...)` call exists within this access-control method.

This is a **static source-linked regression**, not a hardware or controller runtime test. The existing fake-serial tests remain the primary synthetic behavior evidence. The new guard runs from the already-CI-invoked `NativeSerialPinFaultLab` project with an explicit PASS marker `EXTERNAL_BOARD_CONTROLLER_AUTHORITY_SOURCE_GUARD_PASS`. A missing checkout source or changed method shape fails closed rather than skipping.

### Verification plan and rollback

Run in Windows CI from the QA draft PR's **exact HEAD**:

```powershell
cd Pisonet/SoftTimer
dotnet run --project ./tests/NativeSerialPinFaultLab/NativeSerialPinFaultLab.csproj -c Release -- --safety-gate
```

Require exit 0 and the **new controller-source marker**, the existing `EXTERNAL_BOARD_SIGNAL_UNKNOWN_DENIED_PASS`, and `READ_ERROR_SAFETY_GREEN: 4/4`. Reject compilation warnings under `TreatWarningsAsErrors`. Compare the owner and integrated source hashes before merging. No result is claimed until the returned CI job logs are inspected.

If the regression is RED, PISONET owns the production fix and PHX-QA records it without overwriting source. Rollback by closing the unmerged QA PR. Finance ledger, protected witness, migration, signing, USB-RS232 hardware testing, 150 power cuts, 30-device 24-hour soak and production release remain **NO-GO**.

**Resume:** Verify current parent and QA HEADs, read this note and control plane #172, inspect exact CI status, repair only QA test/harness defects, then provide BLAZE-COMMS/1 evidence to MASTER/PISONET.
