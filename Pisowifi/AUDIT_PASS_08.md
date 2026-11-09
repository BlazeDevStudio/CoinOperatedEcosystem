# Blaze PisoWiFi — Development Pass 08 (2026-11-09)

**GitHub:** `BlazeDevStudio/CoinOperatedEcosystem` / `feature/pisowifi-cleanup-stabilization`; draft PR #18, no merge or release. Changes strictly under `Pisowifi/**`.

**Source/testing commit:** `cf59b41e5273bcc42acf59a7971481670e4b2611`. This pass contains an actual fix to a missing apply-program correctness defect, not a native financial-runtime admission.

## Exact root cause / observed RED

The previous OpenWrt `config.sh` accepted a config change when `/usr/lib/blazepwifi/apply-config.sh` did not exist, because `bp_config_apply` returned 0 whenever the fixed path was not executable. The complete source recovery already verified the installed `rootfs/` contains **no** `apply-config.sh`. Consequently, the admin CGI could report `ok:true` without applying the settings to the live uhttpd/firewall/network services.

The prior source `config.sh@2c005528058275a4ad25d25470dd697aa5a51edd` was reconstructed byte-for-byte in a disposable local directory and verified with `git hash-object`. The new `tests/config_apply_failclosed.sh` returned **RED exit 1** against this exact old source (unapplied missing-script change was erroneously accepted). Neither old nor new code was installed on a router.

## Precise corrective changes

- `openwrt/rootfs/usr/lib/blazepwifi/config.sh` Git blob `4535ef6993185208fb3b098842a0f8d69e71d5c7`, mode 100755: introduce `bp_config_apply_program`, `bp_config_apply_preflight` and a fail-closed `bp_config_apply`. Before any UCI snapshot/set/commit, and while holding the existing cooperating-writer lock, the setter checks that a real apply program is present and executable. A clean missing/invalid program is rejected with return **7** and **no UCI mutation**. The trusted test hook remains one executable, never a shell expression. The installed default is the fixed `/usr/lib/blazepwifi/apply-config.sh`, not a client-supplied URL or UCI parameter.
- If the program fails or disappears **after** UCI commits, the setter attempts UCI restoration and returns **8** with a CRITICAL warning even when the UCI rollback commits: UCI reversal does **not** prove reversal of arbitrary partially changed live uhttpd, firewall or network state. If UCI restoration itself fails, return 8 plus its existing critical warning. A commit failure with verified prior UCI restoration remains ordinary rc1; invalid value remains rc2.
- `www/blazepwifi/cgi-bin/admin` Git blob `6ec03db26a43d6669c067e452f6c0098bd2c8051`: distinct user-facing error for clean rc7 (`configuration apply program unavailable; no setting modified`), while rc8 remains explicitly uncertain. Never false `ok:true`.
- `tests/config_faults.sh` and `tests/config_concurrency.sh` adjusted to a synthetic explicit successful hook in test-only contexts and to conservative rc8 after post-commit failed application. The historical `tests/config.sh` fixture explicitly exports a fake-success hook for successful mock scenarios and resets it after the intentional failure case, rather than implicitly relying on the missing production script to be accepted.
- Added `tests/config_apply_failclosed.sh` hash `e6a6af64999769d5481506e7ee64e3934f4ae909`, mode 100755. `tests/run_focus.sh` now includes it. `tests/admin_config_result.sh` tests rc7 separately from rc8 and rc1.
- No routing/VLAN, authentication, voucher, account, wallet, pricing, payment, secrets, Android, Pisonet, CORE or unrelated project files changed.

## Tests executed (local disposable shell; not CI)

A subset of source/test files was reconstructed byte-for-byte from connected GitHub Git blobs into a local directory. Git hashes match the committed GitHub blobs; the admin CGI was **not** executed wholesale, only its exact extracted `config_get/config_set` arms, Git blob `ca291ac70125065b5d964294bc9ea7173dd4a2c6`, inside a stubbed handler.

| Test | Exact test Git blob | `sh` | BusyBox `ash` |
|---|---|---|---|
| `config_faults.sh` — 18 synthetic UCI checks | `8e8053f709d53e78cef154ee9b6d0242075bebf7` | 18 PASS | 18 PASS |
| `config_concurrency.sh` — 3 race/lock checks | `f8eaa2c0bc3cd1018942fe4bed7511a65db1118d` | 3 PASS | 3 PASS |
| `config_apply_failclosed.sh` — 9 absent/failure/side-effect checks | `e6a6af64999769d5481506e7ee64e3934f4ae909` | 9 PASS | 9 PASS |
| `admin_config_result.sh` — 8 stubbed CGI response checks | `975b3245d078e33faa54f22ac9fb5af0bfe49cf0` | 8 PASS | 8 PASS |

**Total 38 PASS checks per shell, 76 check executions across both shell interpreters**. The nine apply checks include missing program/no mutation, direct apply missing, failed hook rollback as unknown live state, explicit success/audit, shell string denied, executable removed after UCI commit, simulated partial live side effect, commit rejection before apply, and non-executable program refusal. Negative test against old exact source: **RED**.

**Not executed:** complete PR checkout's 10-script focused dispatcher (the isolated runner has no network clone access), the four legacy integrated admin/security/portal tests, actual OpenWrt `uci`, real kernel nft/firewall4 netns, ImageBuilder, a real apply script, actual service rollback, physical router, coin/payout/credit, power loss, or GitHub Actions. No CI run/job IDs. The historical config test's fixture was updated for compatibility but its full CGI was not executed; do not claim original integration suite PASS.

## Production impact and blockers

This correction is intentionally restrictive. **Since no real `apply-config.sh` is currently present in the recovered rootfs, live admin config changes will refuse cleanly (rc7)** until a secure, target-tested apply/rollback implementation is independently developed and admitted. This prevents false success, but does NOT deliver full functionality. A synthetic `BP_CONFIG_APPLY_HOOK=true` is for controlled test fixtures only; never set it on a production router.

Complete 61/61 first-party rootfs source inventory remains, with 54 byte-identical and seven intentional corrections (see `SOURCE_INTAKE.json` for full Git hash lineage). Native financial runtime remains excluded. The preexisting `etc/uci-defaults/99-blazepwifi` installs/enables services and reloads firewall; its startup safety is unproven. nft readback does not establish packet-path denial. Config lock does not coordinate external UCI writers or protect the live service reload against partial failures.

**P0 NO-GO:** protected paid-state crash atomicity (#31/#32), independent off-device antirollback (#43), physical durability (#34), startup firewall4 containment, native sign/update trust, hardware acceptance, and real live service transaction semantics. No Codex, merge, release, flashing, real money or keys.

## Next gate

Design and independently test a minimal **explicit** service-apply plan for only supported fields, with a real UCI/uhttpd/firewall configuration transaction, safe rollback path, stable captive-deny behavior and no unverified success. Build and validate an OpenWrt image only after real test runner and firewall checks. Keep this PR draft until these independent gates pass.
