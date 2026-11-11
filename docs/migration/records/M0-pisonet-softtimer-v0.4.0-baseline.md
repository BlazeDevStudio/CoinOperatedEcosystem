# M0 — Pisonet SoftTimer v0.4.0 baseline import

| Field | Value |
|---|---|
| Status | MIGRATING (source preserved; **no behavior change**; NO-GO for production) |
| Source repository | `BlazeDevStudio/BlazingSystems-Experiments` (PUBLIC) |
| Source ref / commit | `main` @ `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` (2026-10-31) |
| Source path | `experiment/windows/BlazePisonet-SoftTimer` |
| Source tree object | `6e69b3e7d6c94a498d7a936f987296f44b143b19` |
| Destination | `BlazeDevStudio/CoinOperatedEcosystem`, branch `migration/pisonet-softtimer-v0.4.0-baseline-20261111` |
| Destination path | `Pisonet/SoftTimer/` |
| Method | `git subtree split` on the source path, then `git subtree add` (38 path commits, authorship/dates preserved) |

## Why this baseline (and not a newer one)

`main`'s SoftTimer tree is the released `softtimer-v0.4.0` line. Newer, **unmerged** SoftTimer work exists as a strictly linear chain on draft branches (verified with `git merge-base --is-ancestor`):

`main (v0.4.0)` → `blazepwifi-v0.6.0-audit-foundation` → `phoenix/pisonet-cts-session-atomic-v2-20261029` → `phoenix/pisonet-native-com-interface-20261030` (PR #255) → `qa/pisonet-setupapi-hygiene-20261108` (PR #279) → `qa/pisonet-setupapi-validation-20261111`

That chain changes coin-pulse capture, serial/COM identity and acknowledgment verification (financial/hardware-critical, owner-authored drafts). It is imported **incrementally in dependency order, one reviewable PR each (M1–M4, see `MIGRATION_PLAN.md`)**, not as one bulk import. Nothing newer was overwritten; the destination had no SoftTimer source before M0.

## File and directory mapping

`experiment/windows/BlazePisonet-SoftTimer/<x>` → `Pisonet/SoftTimer/<x>` for all 32 files (README, release notes, `build-local.ps1`, `docs/`, `installer/`, `src/BlazePisonet.SoftTimer/`, `src/BlazePisonet.SoftTimer.Watchdog/`). The existing boundary document `Pisonet/README.md` is kept and updated.

Intentionally **not** migrated: `.github/workflows/blazepisonet-softtimer-release.yml` (publishes a GitHub Release with `contents: write`; release authority stays with the owner). Replaced by the verification-only `.github/workflows/pisonet-softtimer-ci.yml`.

## Added by this increment (separate commits, no source edits)

- `Pisonet/SoftTimer/global.json` — pins SDK `8.0.425` / `latestPatch` (the value the historical release workflow used).
- `.github/workflows/pisonet-softtimer-ci.yml` — Windows build with `-warnaserror`, read-only token, no secrets, no publishing.
- `.gitignore` — build outputs and secret/signing material.

## Compatibility implications

None. Source bytes are unchanged. Namespaces, assembly names, config defaults and the BlazePwifi controller-signature client are untouched. Default endpoints remain `192.168.x.x` literals (see audit finding F-ST-3; not changed here).

## Validation evidence

| Check | Result | Notes |
|---|---|---|
| Tree identity: `git rev-parse HEAD:Pisonet/SoftTimer` at the import merge == source tree `6e69b3e7…` | **PASS** | byte-identical import |
| `dotnet build -c Release -r win-x64 -warnaserror` of both projects, .NET SDK 8.0.428 on Linux with `EnableWindowsTargeting` | **PASS** (0 warnings, 0 errors) | **Compile check only.** Not a Windows runtime test. |
| GitHub Actions `Pisonet SoftTimer CI` on the exact PR head | see PR | recorded in the PR; not claimed here |
| Windows runtime, installer, watchdog, serial/USB-RS232, coin acceptance | **NOT RUN** | no Windows host or physical hardware available |
| Secret scan (private-key markers, keystores) on the source repository `main` | none found | pattern scan only, not a full secret audit |

Reproduce tree identity:

```sh
git clone --no-tags --single-branch -b main https://github.com/BlazeDevStudio/BlazingSystems-Experiments.git /tmp/exp
git -C /tmp/exp rev-parse f4e8a891aed8af86d5fd315d28750a0ac3a7372b:experiment/windows/BlazePisonet-SoftTimer
# expect 6e69b3e7d6c94a498d7a936f987296f44b143b19
git rev-parse <import-merge-commit>:Pisonet/SoftTimer   # must be identical
```

## Rollback

Nothing outside this branch changed. Close the draft PR / delete the branch. The source repository is untouched and remains the historical reference; it is not deleted or modified by migration.

## Open items

- SoftTimer's `BlazePwifiClient` uses an unkeyed `SHA-256(secret|…|secret)` signature (audit finding F-ST-1, suspected). Compatibility with the BlazePwifi controller contract must be preserved; changing it is a coordinated protocol migration, not a cleanup.
- Owner decision needed on whether the SoftTimer product (as opposed to BlazePwifi) may live in this public repository. The destination README already designates it, so M0 follows that.
