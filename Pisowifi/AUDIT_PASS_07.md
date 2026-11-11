# Blaze PisoWiFi — Development Pass 07 (2026-11-08)

**Repository:** `BlazeDevStudio/CoinOperatedEcosystem`; **draft** PR #18, no merge/release/production.
**Scope:** strictly `Pisowifi/**`, including the OpenWrt first-party CGI and shell config.
**Primary fix commit:** `2ff8c618fb9f546a80dd7bc4f618b40503236594`.

## P0/P1 source defects reproduced

1. **Lost admin configuration updates across overlapping requests.** Previous `bp_config_set` let two independent CGI writers interleave the existing UCI snapshot/commit/apply/rollback. Exact previous source Git blob `da6319d5136f02f3b1d474460a91ccfef62dc449` reproducibly failed `tests/config_concurrency.sh` with "FAIL concurrent B committed before A rolled back": request B reported success while request A was still applying a change and could subsequently restore a stale value.
2. **False successful admin configuration read.** Original admin config_get arm turned a failed `uci get` into a normal empty value and emitted `ok:true`, even if the option existed and was unreadable. A genuine absent optional key must remain a successful empty value.
3. **False rollback assurance to operators.** Original config_set CGI emitted `config apply failed and was rolled back` for all failures, even distinct return code 8 meaning UCI rollback itself was unverified. It also implied live services were restored, which `bp_config_restore` cannot establish.

## Source changes and verified hashes

- `openwrt/rootfs/usr/lib/blazepwifi/config.sh` — Git blob `2c005528058275a4ad25d25470dd697aa5a51edd`, 100755. `bp_config_set` now operates in a subshell holding FD8 `flock -w 10` on a private, symlink-rejecting `$BP_RUN/config-write.lock` across the entire old-snapshot / change / commit / apply / optional rollback / audit path. It rejects malformed lock paths before modifying UCI. This **only serializes writers that cooperate via this function**, not external UCI scripts or first-boot services. Added `bp_config_get_optional` distinguishing a readable, genuinely absent UCI key from failure to read an existing key or its section.
- `openwrt/rootfs/www/blazepwifi/cgi-bin/admin` — Git blob `87a0a78daa4fae08ae7db84b9b0ce165108a56cc`, 100755. Admin config_get rejects failed existing reads while preserving empty optional settings. Admin config_set distinguishes rc 8 with an explicit uncertain-state message, and does not claim service rollback or return false success on other errors. CSRF and role checks remain.
- `tests/config_faults.sh` — Git blob `48c3b75af85285cc223ef967b9a99e290ac15873`, 100755. Adds isolated `BP_RUN` location and 4 optional-read checks, totals 18 mock UCI tests.
- `tests/config_concurrency.sh` — Git blob `9ebcd67fe022c28d82054c70172efaee070c57a2`, 100755. Adds a deterministic overlapping-two-writer conflict with one failed apply, plus symlink run-dir and lock-path refusal.
- `tests/admin_config_result.sh` — Git blob `d8c8d8fc74bcbc66f87fc9f044cb9b2dc023d2aa`, 100755. Sources the **actual extracted** admin config_get and config_set case arms with stubbed dependencies and tests 7 response/CSRF cases. The extracted admin case Git blob is `49651cf8f363a7d77c94fcdec5831e74f4a4888f`, verified to match exact local source fragment and current committed full CGI.
- `tests/run_focus.sh` includes both new regression scripts. All edits are limited to `Pisowifi/**`.

## Reproducible local test evidence

The exact previous `config.sh` Git hash `da6319d5136f02f3b1d474460a91ccfef62dc449` was reconstructed from the GitHub source; the new concurrency regression returned **RED exit 1**, failing on the lost-update race. The new `config.sh` exact Git hash `2c005528058275a4ad25d25470dd697aa5a51edd` returned **GREEN** in both `sh` and BusyBox `ash` on that same test.

| Check | POSIX /bin/sh | BusyBox ash |
|---|---|---|
| `tests/config_faults.sh` (18 synthetic UCI cases) | PASS | PASS |
| `tests/config_concurrency.sh` (1 conflict + 2 symlink cases) | PASS | PASS |
| `tests/admin_config_result.sh` (7 extracted CGI response cases) | PASS | PASS |
| `sh -n` / `ash -n` on tested shell files | PASS | PASS |

The executed full config file, UCI fault fixture, concurrency fixture, CGI case fragment and CGI test have all been compared to the **exact Git blob IDs above**. Their local test uses disposable `mktemp` directories and mocked `uci`; **it does not run full `admin` CGI or real OpenWrt services**. The shell tests use source-equivalent extracted CGI arms rather than a complete admin-request harness; that difference must not be concealed.

## Inventory and release gates

All **61 of 61 original OpenWrt rootfs files** remain present with original modes. **54 files** are byte-identical first-party source, **7 files** contain intentionally reviewed corrections. This count excludes OpenWrt paid-authority native package/build sources, which remain unadmitted. `SOURCE_INTAKE.json` records every path, original blob and current blob.

**GitHub Actions: NOT RUN** (no workflow within authorized `Pisowifi/**`; repository-wide `.github/workflows` remains outside write scope). Full exact-HEAD checkout of nine focused shell tests was not possible in this isolated network environment; earlier nft tests are not being claimed rerun. No actual Linux nft netns/kernel path, OpenWrt ImageBuilder, physical router, real UCI service reconfiguration or money/coin trial was performed.

**P0 NO-GO** remains for financial crash-atomicity (#31/#32), independently protected antirollback (#43), physical durability (#34), firewall4 startup and verified packet-path containment, signing/updater admission, native paid authority, and live UCI service rollback. Config read-only GET and external non-cooperating UCI mutations are not covered by the new config write mutex. `bp_config_apply` currently still returns success if the installed apply script is absent, so live service rollout remains unverified. These require independent tests and repair; never present source recovery as deployability.

## Next gate

Run all `Pisowifi/tests/run_focus.sh` tests on one actual checked-out exact HEAD (or bounded source-materialized mirror with every necessary Git blob verified), then execute the existing historic mock integration suites. Keep any failed cases RED; prioritize daemon safety, live service apply/rollback and confinement tests over new features. Never merge/release/flash/modify finances without separate owner authorization.
