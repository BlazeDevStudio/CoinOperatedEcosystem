# Codebase Audit

**Date:** 2026-11-11 · Severity: **P0** financial integrity / authorization / data corruption / source loss / unsafe device control · **P1** broken core function, deployment failure, severe maintainability · **P2** UI/UX, performance, compatibility, ordinary quality · **P3** optional.
Findings are split into **Confirmed** (observed by me on an exact SHA or in live GitHub metadata) and **Suspected** (read in source, not reproduced). Nothing here was fixed unless stated in §5.

## 1. Confirmed findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| P0-1 | P0 (governance) | **Privacy-gate conflict.** Owner directive: BlazePwifi is proprietary and must stay private. In reality its source is published in PUBLIC repos under an **MIT** license: Experiments `main` has 1268 files under `experiment/openwrt/BlazePwifi/` (1446 on the active branch), its README calls it "open-source", and PR #18 in the public `CoinOperatedEcosystem` imports 61 rootfs files, retaining the MIT `LICENSE` and describing it as "public MIT source recovery". | file counts via `git ls-tree`; `LICENSE` read; `Pisowifi/SOURCE_INTAKE.json` read |
| P0-2 | P0 | **Crash atomicity of member balances is not guaranteed.** The repo's own RED test fails at the exact head: `RED: no receipt, but member balances moved (170/130); issue #31 remains open`. | `sh Pisowifi/tests/member_crash_atomicity_red.sh` at #18 `eef173286cb6…` → exit 1 |
| P0-3 | P0 | **No independent anti-rollback witness** and no physical power-cut/soak acceptance (Experiments issues #43, #34). Production admission is correctly NO-GO. | PR #18 `README.md` (documented; not re-tested) |
| P1-1 | P1 | **`main` is empty of product code.** All work is in 18 unmerged drafts; nothing can be built from the default branch. | tree of `a6513ab4…` = 2 files |
| P1-2 | P1 | **Case-colliding directories** `Pisonet`/`pisonet` and `Rental`/`rental` between `main`/#17/#19 and the #1–#16 stack. Merging both onto a case-insensitive filesystem (Windows/macOS) corrupts the checkout. | `git ls-tree` of #1/#16 vs `main` |
| P1-3 | P1 | **Duplicated, diverged OpenWrt core.** `core/openwrt/rootfs/...` (#5–#16) and `Pisowifi/openwrt/rootfs/...` (#18) contain the same four files with different blobs (e.g. `capabilities.sh` `16ea0a9e…` vs `098eafbe…`). Two cleanups of one source will conflict and may fix different defects. | `git ls-tree -r` on both heads |
| P1-4 | P1 | **No CI at the exact heads of #18, #19 and #1.** Check-runs: #3–#17 success; #1/#18/#19 none. | `gh api …/commits/<sha>/check-runs` |
| P1-5 | P1 | **PisoWiFi `tests/integration.sh` fails at the cleanup head and is excluded from `run_focus.sh`.** It reaches `CRITICAL: nft authorization state uncertain; attempting global MAC revocation` then exits 1. Root cause unproven: the test's `nft` mock may not satisfy the new membership read-back, or the new code may regress. The original source at `6d4c9b48` did not complete either in this environment (still at `auth provision` when my 120 s timeout killed it, exit 124), so the comparison is **inconclusive**. | runs described in §3 |
| P1-6 | P1 | **Source lineage ambiguity for BlazePwifi.** Experiments `main` is stale (`VERSION` `0.5.3-dev.5`) relative to the active `blazepwifi-v0.6.0-audit-foundation` (`VERSION` `0.5.3`, different file set); the two differ in both directions. | `git rev-list --count` both ways: 22 / 1874 |
| P1-7 | P1 | **Rental repo variants.** Rental-Server-Standalone is pinned to `notion,r281` + OpenWrt 24.10.x, not the intended EW1200G Pro target; EW1200G Pro support is unverified anywhere in this audit. | `README.md` of Rental-Server-Standalone |
| P2-1 | P2 | **Dead cross-references.** Policy docs link to `github.com/BlazingSystems/...` (the old owner name). That owner no longer resolves (`404 … not recognized as either a GitHub user or an organization`). | `gh api users/BlazingSystems` |
| P2-2 | P2 | **Branch sprawl.** Experiments: 343 branches, 72 open PRs; CoinOperatedEcosystem: 27 branches including six empty placeholder branches (`Contracts`, `Controllers`, `Core`, `Integration-Tests`, `Pisonet`, `Rental`) at the initial commit. | `gh api …/branches` |
| P2-3 | P2 | **Governance BLOCKED:** repo policy requires reading the private Drive registry before creating artifacts; no Drive connector in this session. | session tooling |
| P2-4 | P2 | **Rental test requires `busybox`** (`busybox sh -n` syntax test) and fails with `FileNotFoundError` where it is absent; the test does not skip. | #19 run §3 |

## 2. Suspected findings (not reproduced)

| ID | Sev | Finding | Where |
|---|---|---|---|
| S-ST-1 | P1 (suspected) | Controller signature is `SHA-256(secret|action|id|nonce|pulses|target|secret)`, an ad-hoc keyed hash rather than HMAC, with unescaped `|` delimiters. Compatibility with BlazePwifi must be preserved, so any change is a coordinated protocol migration. Read at v0.4.0 (`f4e8a891`); **PR #17 code was not re-read**. | `BlazePwifiClient.Signature` |
| S-ST-2 | P2 | Hardcoded default endpoints `http://192.168.4.1/`, `http://192.168.1.2:8765/`, `http://192.168.1.1:4455/cgi-bin/vendo`. Not credentials; environment assumptions. | `AppConfig.cs` (v0.4.0) |
| S-ST-3 | P2 | "Centralized" peer protocol listens on plain HTTP (`http://+:port`) relying on HMAC and a subnet firewall rule; no transport confidentiality. | `Centralized.cs` (v0.4.0) |

## 3. Tests actually executed

All runs were on disposable detached worktrees; no repository state was modified.

| Subject | SHA | Command | Result |
|---|---|---|---|
| PisoWiFi shell syntax | #18 `eef173286cb6cc1320f0f9e234a7b7cc701424a3` | `sh -n` over every file with a shell shebang among 47 candidates (`*.sh`, CGI, init scripts) | **PASS**, 0 failures |
| PisoWiFi focused suite | same | `sh Pisowifi/tests/run_focus.sh` | **PASS** ("ALL FOCUSED SHELL TESTS PASS (MOCKS ONLY)"); this runs 10 scripts |
| PisoWiFi others | same | `security.sh`, `portal.sh`, `config.sh`, `capabilities.sh` | **PASS** (each exit 0) |
| PisoWiFi integration | same | `integration.sh` | **FAIL** exit 1 (P1-5) |
| PisoWiFi crash atomicity | same | `member_crash_atomicity_red.sh` | **FAIL by design** exit 1 (P0-2) |
| Rental | #19 `fcc8f8c9bc2fa50666aa7c5e94e48137fa01b379` | `python3 -m unittest discover -s Rental/tests -v` (Python 3.11, Java 17) | **22 run, 21 pass, 1 error** (`busybox` not installed here, so that one test is **NOT RUN**, not a product failure) |
| SoftTimer compile | Experiments `main` `f4e8a891aed8…` | `dotnet build -c Release -warnaserror` both projects, SDK 8.0.428 on Linux, `EnableWindowsTargeting` | **PASS**, 0 warnings, 0 errors. Compile check only |
| Original BlazePwifi integration | Experiments `6d4c9b487a…` | `sh tests/integration.sh`, 120 s timeout | **Inconclusive** (timed out at `auth provision`, exit 124) |

Environment limits: no OpenWrt, no real `nft`, no BusyBox, no Windows host, no hardware. These results are **host-side mock results** and establish no router, coin, payment, or Windows-runtime behavior.

## 4. Technical-debt register (by area)

| Area | Debt | Next action |
|---|---|---|
| Layout | Two naming conventions, duplicated core | Adopt `TARGET_STATE.md` layout; reconcile `core/` vs `Pisowifi/openwrt/` before more cleanup lands |
| Accounting | Text-file ledgers without atomic multi-file commit | Domain redesign per #31; needs explicit invariants and regression tests first |
| CI | #18/#19 have none; SoftTimer CI only compiles | Add exact-head CI for both; wire `integration.sh` decision |
| Config | Default IPs/ports baked into SoftTimer | Move to profile-driven config (VLAN/port profiles for PisoWiFi) |
| Provenance | Mixed byte-exact and derived files across three import styles | Standardize on `SOURCE_INTAKE.json`-style manifests + the existing intake guard |
| Docs | Stale owner URLs, placeholder READMEs | Fix links in a docs-only PR |

## 5. Code changed by this audit

None. This PR adds documents only. (A SoftTimer baseline import PR #20 was opened and then closed as a duplicate of #17 before merge; see `SOURCE_PROVENANCE.md`.)

## Status addendum — 2026-11-11 (P0-2 / Experiments #31)

The P0-2 evidence above was measured at PR #18 head `eef173286cb6…` and is kept unchanged as the historical baseline. A fix candidate now exists on Draft PR #24 (`cleanup/pisowifi-ci-and-cli-auth-hardening-20261111`, head `196cf3b021427ddfac694f911a789d8ce7936cde`): `members.tsv`, `member-events.tsv` and `member-revision` are committed through a SHA-256 commit record with roll-forward recovery under the member lock. The former RED test is now `member_receipt_failure_atomicity.sh` and passes; `member_txn_journal.sh` adds 8 simulated-fault cases. GitHub Actions passes under POSIX sh and BusyBox ash.

P0-2 is **not closed**: no power-cut/flash evidence (#34), no off-device anti-rollback witness (#43), unlocked readers can observe the apply window, all 6 member mutators and rental coin/lease mutators (`rental.sh`) are now journaled (10 simulated-fault cases pass); voucher redemption (`accounts.tsv`+`vouchers.tsv`) and multi-file rental device revocation remain unjournaled, and no independent QA review has occurred. P0-1 (privacy/licensing decision) is unaffected and still requires the owner.

## Status addendum — 2026-11-11 (P1-2 case collisions)

Reproduced with `git merge-tree` simulations: the stack tip (`d537b30f…`), #17 and #19 each pass a case-collision check alone; merging the stack with #17, #19 or #18 fails with `Pisonet`↔`pisonet` and `Rental`↔`rental` (plus files below them). The colliding stack paths are 8 placeholder `README.md` files, no code. A merged-tree guard (`tools/check_case_collisions.py`, 7 tests, CI green) is on Draft PR #25 (`9ab86577bcbfd3b64f3f982f37198d731d8f13b3`). **The collision itself is not resolved**: fixing it rewrites PR #1 and rebases the 15 stacked PRs, which requires owner approval.

PR #24 also now enforces manifest executable modes in CI (`3235b33bcf165305ef5b53f091f7d330bc4d46a6`), covering the actionable part of PR #14.

