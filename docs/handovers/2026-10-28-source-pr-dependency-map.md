# Phoenix source-PR dependency map — 2026-10-28

**Scope:** Read-only inspection of current open draft pull-request metadata in `BlazingSystems/BlazingSystems-Experiments`. These are the head SHA and base SHA returned by the GitHub connection at discovery time. A base branch's live tip may have moved since PR creation; re-fetch before any actual source import or rebasing.

**Migration stage:** STRUCTURE_CREATED only. No source from the PRs in this table is copied to the destination; no regression or hardware acceptance is claimed.

| Responsibility | Original PR | Source head commit SHA | PR base branch | Reported base SHA | Relevant dependency |
|---|---|---|---|---|---|
| CORE | [#178](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/178) | `cb2db7e4235aa84f3dbfe452f55f27da244b1e9e` | `blazepwifi-v0.6.0-audit-foundation` | `9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed` | Disabled-controller transfer locking |
| CORE | [#194](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/194) | `153c6a928255525ea00a920a64e9790fa99c8831` | `phoenix/light-core-bank-restore-revocation-red-20261024` | `c76b42acc375105b5b8a7540cc463237baf16eaf` | Fail-closed controller registry |
| CORE | [#198](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/198) | `c90b66d5482b6835e5f7793cd1074f27c42a8669` | `phoenix/light-core-controller-registry-failclosed-20261024` | `153c6a928255525ea00a920a64e9790fa99c8831` | Controller registry post-rename sync failure |
| CORE | [#215](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/215) | `5104b0b1b42dbfe1b653193ae7ec80cf3e9b4f24` | `blazepwifi-v0.6.0-audit-foundation` | `1890e522843d262c33a5109dcea11768896c2e5f` | Transfer revocation locking |
| CORE/QA | [#222](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/222) | `954d1ab72e8108da6e464fb3d7c1eb70cfe3f800` | `integration/pay31-transfer-revocation-20261027` | `5104b0b1b42dbfe1b653193ae7ec80cf3e9b4f24` | Test-only disabled-controller transfer race |
| PISONET | [#197](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/197) | `d166335c0943cdb94cc7c49f31c9bdeb396bf744` | `phoenix/light-apps-exact-identity-failclosed-20261025` | `25adff355929163356c4af477d2eab5a74f3455a` | Open-time serial identity test |
| PISONET | [#216](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/216) | `d99d004013261ea993138c98ce15ea91d509ba41` | `phoenix/light-apps-open-time-com-swap-red-20261025` | `d166335c0943cdb94cc7c49f31c9bdeb396bf744` | Async coin dispatch source regression |
| PISONET | [#219](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/219) | `455e6c713bc332b51cf15e009c2bbfb306d2860f` | `phoenix/light-apps-open-time-com-swap-red-20261025` | `d166335c0943cdb94cc7c49f31c9bdeb396bf744` | Native V4/V5 reconnect test |
| PISONET | [#221](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/221) | `742b0d5300533314f931fffc5168a907a25dbd8d` | `phoenix/light-apps-open-time-com-swap-red-20261025` | `d166335c0943cdb94cc7c49f31c9bdeb396bf744` | Failed SerialPort.Open disposal |
| PISONET/RELEASE | [#217](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/217) | `d6cba608e9bcccc5e4ce92894828d214f873cdcc` | `blazepwifi-v0.6.0-audit-foundation` | `1890e522843d262c33a5109dcea11768896c2e5f` | Production signature gate |
| PISONET/RELEASE | [#218](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/218) | `fa184b371610a1cb0f6288ad0f2f565250bc60a9` | `blazepwifi-v0.6.0-audit-foundation` | `1890e522843d262c33a5109dcea11768896c2e5f` | Pinned Authenticode gate |
| PISONET/RELEASE | [#223](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/223) | `79da4dfeb6c4fc13482471d0d1357b47753e3523` | `blazepwifi-v0.6.0-audit-foundation` | `416525861a47c548f470ff8c19dda03ee3161ad7` | Compiled NSIS Unicode regression |
| CONTROLLERS | [#150](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/150) | `867cbbac952ffb24414635a6178021b7371ac123` | `blazepwifi-v0.6.0-audit-foundation` | `b239dde5cd76949e1c51590f15ab8fbc3118e138` | Pending-journal recovery promotion guard |
| CONTROLLERS/QA | [#183](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/183) | `3b892c67655ffda0b5adc0fc034a60e368254e17` | `blazepwifi-v0.6.0-audit-foundation` | `9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed` | ESP flash crash/rollback fixture |
| CONTROLLERS/QA | [#193](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/193) | `7c156cb0e0dd4a2311de7e79c3ba7044037c0767` | `phoenix/light-verify-esp-poll-guard-20261024` | `e5a9781ea5234b09501d5356cf966f9237ac8172` | Relay enable without journalable target |

## Required migration decision sequence

1. **CORE:** Reconcile the source-derived transfer locking and disabled-controller timing behavior at #178/#194/#198/#215/#222. Never confuse a test-only RED with a product-safe fix. Preserve receipt replay, authenticated admissions, lock ordering, crash atomicity and journal durability.
2. **PISONET:** Reconcile serial exact device identity and callback ownership in #197/#216/#219/#221 without losing failed-Open cleanup. Independently retain and verify signing gates from #217/#218/#223 before any release.
3. **CONTROLLERS:** Validate #150/#183/#193 against fail-closed GPIO control, journal rollback, identity/freshness, cold-reboot and hardware acceptance. RAM/unprotected flash alone does not satisfy protected freshness.
4. **RENTAL, CONTRACTS, INTEGRATION:** Identify exact authoritative Android lease source heads, shared wire schema revisions and test witness hooks before importing into their destination directories. No source revisions were selected in this pass.
5. Stage future source migrations in **separate draft PRs** from this structural PR. Record each exact source path, commit/blob SHA, destination commit SHA, import method and native CI evidence in `MIGRATION_MANIFEST.md`.
6. Do not merge, close, force-push or alter any of the original draft PRs while this dependency stack is unresolved.

**Production release status:** NO-GO for financial authority and hardware admission. File organization does not change release policy.
