# BlazePisonet SoftTimer — standalone Windows x64

**Status: source migration and synthetic Windows lab only. No commercial coin acceptance or customer installation authorization.**

This is the standalone Windows 10/11 .NET 8 WinForms timer and kiosk app. Internal-PC-timer and one-coinslot/one-PC operation must work without BlazePwifi, Android, Phoenix services, or any diskless manager.

- `src/BlazePisonet.SoftTimer/` — WinForms, timer, COM/serial, local storage, customer-lock enforcement.
- `src/BlazePisonet.SoftTimer.Watchdog/` — independent Windows watchdog.
- `tests/` — source-linked synthetic native COM and serial fault cases.

No Diskless Manager source was included: a future FOG/PXE/iSCSI companion must be separately installed with independent storage and must not impact paid sessions.

## Windows development commands

Requires Windows and .NET 8 SDK:

```powershell
dotnet build .\src\BlazePisonet.SoftTimer\BlazePisonet.SoftTimer.csproj -c Release -warnaserror
dotnet build .\src\BlazePisonet.SoftTimer.Watchdog\BlazePisonet.SoftTimer.Watchdog.csproj -c Release -warnaserror
dotnet run --project .\src\BlazePisonet.SoftTimer\BlazePisonet.SoftTimer.csproj -c Release -- --verify-timer-math
dotnet run --project .\tests\NativeComInterfaceHandleLab\NativeComInterfaceHandleLab.csproj -c Release
dotnet run --project .\tests\NativeSerialPinFaultLab\NativeSerialPinFaultLab.csproj -c Release -- --safety-gate
dotnet run --project .\tests\NativeCoinEventOwnershipGuard\NativeCoinEventOwnershipGuard.csproj -c Release
```

CI also publishes an **unsigned lab diagnostic artifact** only if all synthetic gates pass. It is not a native installer or a commercial release.

## P0 acceptance blockers

- Actual isolated voltage-correct coinslot/USB-RS232 wiring, active-low/CTS fault rejection, stable exact-device binding through disconnect/re-enumeration, no phantom/duplicate coin credit.
- Crash-consistent paid time and durable event IDs; source-linked restart/corruption and host-sleep cases.
- Windows kiosk lock recovery, admin access, watchdog service lifecycle and installer/uninstaller on disposable Windows 10/11.
- Physical coinslot/accounting tests and operator acceptance.

Never attach an unconditioned 12V coin pulse directly to PC serial pins. See `MIGRATION_PROVENANCE.md` for source boundaries.

## Installer compilation

A separate dependent CI job compiles an **unsigned NSIS LAB installer** after all source-linked tests pass. The installer has not been run or uninstalled on Windows, and its artifact is **not customer-ready**. See `installer/README-LAB.md`.

## Human debugging and non-destructive state recovery

See [`docs/STATE_RECOVERY_TROUBLESHOOTING.md`](docs/STATE_RECOVERY_TROUBLESHOOTING.md) for the module ownership map, fail-closed error guide, source-linked Windows commands, and incident evidence rules. Do not delete `state.json.tmp` or reset financial data as a troubleshooting shortcut.
