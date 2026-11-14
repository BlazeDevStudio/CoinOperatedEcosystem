# BlazePisonet SoftTimer — paid-state troubleshooting (development/lab)

**Status: DRAFT / production NO-GO.** These instructions are read-only until an authorized operator reviews a paid-state discrepancy. They are not a reset/recovery script and do not authorize accepting physical coins.

## Which component owns what?

- `src/BlazePisonet.SoftTimer/Storage.cs`: JSON decoding, financial-state validation, atomic state writes, audit log helper and passwords.
- `src/BlazePisonet.SoftTimer/TimerEngine.cs`: local paid-time and member-bank transitions. Successful financial transitions must persist before becoming visible to the customer session.
- `src/BlazePisonet.SoftTimer/SerialHardware.cs` and `NativeComInterfaceTransport.cs`: physical input/discovery and experimental exact-handle identity. A passing synthetic COM harness does **not** authorize physical coin admission.
- `tests/StateRecoveryGuard/Program.cs`: actual Storage source linked into a disposable-files test; it never touches an operator's ProgramData.
- `tests/TimerCreditCommitGuard/` and `tests/MemberTimeCommitGuard/`: source-linked persistence/credit regressions. They are not real hardware tests.

## Where is local state?

The production Storage class currently uses `%ProgramData%\BlazeSystems\BlazePisonetSoftTimer\` on Windows:

| Name | Purpose |
| --- | --- |
| `state.json` | Committed paid seconds, member balances, replay IDs, pending member operation |
| `state.json.bak` | Previous committed snapshot after replace |
| `state.json.tmp` | Unresolved in-progress write; **preserve it** |
| `config.json` | Operator configuration, controller identity, and **secrets**; must not be replaced by defaults on corruption |
| `config.json.bak` | Prior committed configuration snapshot; preserve for authorized review |
| `config.json.tmp` | Unresolved configuration update, possibly containing changed keys/passwords; preserve |
| `softtimer.log` | Operator diagnostic log; review for sensitive content before sharing |

**Never** delete, rename, overwrite or auto-promote a `.tmp` or `.bak` to make startup succeed. An unresolved write may represent consumed money. Isolate the device, preserve all original evidence and escalate reconciliation. Do not reconnect live coin inputs until the financial/capture gate is independently accepted.

## Typical fail-closed errors and first response

| Symptom | Where detected | Safe first action |
| --- | --- | --- |
| Paid state missing but backup/pending write present | `LoadStateFromPath` | Preserve all three files, inspect incident timeline read-only |
| Parseable JSON missing required accounting fields | `LoadStateFromPath` | Preserve original file and compare to the prior verified schema |
| Negative time, sales count, replay identity or member bank/revision | `ValidateFinancialState` | Do not normalize or clamp; record exact error and review the source of corruption |
| Pending write after a crash | `AtomicWrite` / startup decoder | Stop paid intake; reconcile pending and committed evidence offline |
| Corrupt installed config or missing coordinator key/controller ID | `LoadConfigFromPath` | Do not regenerate keys; preserve `config.json/.bak/.tmp`, stop startup and review authorized recovery |
| Unknown or disconnected COM device | Native serial ownership layer | Treat device as unavailable; do not use a COM-name-only fallback |
| Credit persistence fault latched | `TimerEngine` | Do not automatically retry a consumed coin or remove the customer lock |

Errors in the new member validation deliberately identify **local** versus **remote** member accounting without exposing usernames, passwords or tokens.

## Source-linked developer verification

From the `Pisonet/SoftTimer` directory on a Windows .NET 8 SDK machine:

```powershell
dotnet build .\src\BlazePisonet.SoftTimer\BlazePisonet.SoftTimer.csproj -c Release -warnaserror
dotnet run --project .\tests\StateRecoveryGuard\StateRecoveryGuard.csproj -c Release
dotnet run --project .\tests\TimerCreditCommitGuard\TimerCreditCommitGuard.csproj -c Release
dotnet run --project .\tests\MemberTimeCommitGuard\MemberTimeCommitGuard.csproj -c Release
```

Expected source-linked recovery output includes `CONFIG_FAIL_CLOSED_RECOVERY_PASS` and `STATE_MEMBER_ACCOUNT_VALIDATION_PASS` when all regression assertions pass. Its presence must be verified in an **actual exact-commit** workflow log, not inferred from source. The repo's `pisonet-softtimer-windows.yml` runs Windows synthetic CI for changes under this subtree.

## Reporting a reproducible bug

Record exact repository, commit SHA, branch/PR, Windows version and .NET SDK, test command, failing log step, synthetic-versus-real device evidence and whether customer money/hardware was involved. Redact `CentralSharedKey`, admin/member password hashes and salts, usernames, member tokens and serial identifiers before sharing outside authorized troubleshooting. Preserve raw originals in approved private evidence storage; provide only sanitized excerpts to public issues.

**Still blocked:** independent ledger/rollback witness, physical USB-RS232/voltage-correct coin acceptance, crash/power-cut endurance, installer lifecycle, and signed production admission.
