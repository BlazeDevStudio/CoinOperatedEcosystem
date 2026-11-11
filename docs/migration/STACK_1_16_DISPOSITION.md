# Disposition of the PR #1–#16 stack against the canonical product branches

Status: analysis only, 2026-11-11. No PRs were closed or rewritten.
Compared: stack tip `ecosystem/core-nft-authorize-verification-20261106` (`d537b30f67f59c8df56cd0eee625d2a73095f968`, PR #16)
against the canonical product trees: PR #24 (`Pisowifi/`, 61-file rootfs), PR #22 (`Rental/`), PR #23 (`Pisonet/SoftTimer/`).

## Summary

The entire 16-PR stack contains only **4 OpenWrt runtime files** (`core/openwrt/rootfs/…`); the remaining 57 files of the PisoWiFi rootfs, all of Rental and all of Pisonet are absent (represented only by placeholder `README.md` files). On all 4 runtime files, the canonical `Pisowifi/` tree is either equivalent or **strictly safer**:

- **`etc/init.d/blazepwifi`:** stack `stop_service` runs `nft delete table inet blazepwifi || true`, which **removes the captive drop gate on service stop** and fails open. Canonical `Pisowifi` keeps the gate and only flushes `auth_macs`, failing closed (`rc=9` + `CRITICAL` log) if the flush fails (`nft_shutdown_guard.sh`). **Porting the stack version would be a security regression.**
- **`usr/lib/blazepwifi/capabilities.sh`:** both fix the `df -Pk` column-4 (available KB) fallback from `/overlay` to `/`. Equivalent (`capabilities.sh` test passes).
- **`usr/lib/blazepwifi/config.sh`:** lines 1–59 (key whitelist and validators) are byte-identical. Lines 60+ use different transaction designs: canonical has `bp_config_get_optional`, fixed-path executable apply preflight (`BP_CONFIG_APPLY_HOOK` character-whitelisted, never `eval`ed), `flock` on `config-write.lock`, and `rc=7/8` distinction (`config_faults.sh`, `config_apply_failclosed.sh`, `config_concurrency.sh`, `admin_config_result.sh` — 38 checks). Stack uses a durable `.config-transaction.pending` marker (`rc=9`).
- **`usr/sbin/blazepwifi-core`:** canonical validates `lan_if`/`portal_port` before interpolating into nft, replaces the table in **one** atomic `nft -f` batch (`nft_atomic_setup.sh`), and checks `bp_authorize_mac` / `bp_deauthorize_mac` return codes (which already do `nft get element` / `list set` readback in `common.sh`, `nft_membership_failclosed.sh`). The stack still uses a separate `nft delete table` before `nft -f` (an open-firewall window that PR #16's own note flags as unresolved).

## Per-PR table

| PR | State | Subject | Disposition vs canonical trees |
| :-- | :-- | :-- | :-- |
| #1 | OPEN draft | Monorepo skeleton + placeholder READMEs | **Superseded by #17/#18/#19 + PR #21 docs.** Its lowercase `pisonet/` and `rental/` placeholders cause the P1-2 case collision (guarded by PR #25). |
| #2 | CLOSED | Old Logo V2 anchor | Already closed as superseded. |
| #3 | OPEN draft | `tools/source_intake_guard.py` + `inventory/source-intake.json` (4 files) | **Covered for Pisowifi** by `Pisowifi/SOURCE_INTAKE.json` (61 runtime + 17 test blobs + modes) enforced in `pisowifi-ci.yml`. |
| #4 | OPEN draft | `component-baseline.yml` (runs upstream baselines) | **Superseded** by per-product CI on the actual migrated code (`pisowifi-ci.yml`, `rental-ci.yml`, `softtimer-windows-ci.yml`, all green). |
| #5, #6 | OPEN draft | Import `capabilities.sh` + fix `df -Pk` column 4 / `/overlay` fallback | **Already in `Pisowifi`** (`bp_cap_available_kb` + `tests/capabilities.sh`). |
| #7, #8, #9 | OPEN draft | Import `config.sh`, remove `eval` hook, serialize + rollback UCI writes | **Already in `Pisowifi`** (`bp_config_apply_program`, `flock`, `bp_config_restore`, 4 config test suites). |
| #10, #11, #12, #15 | OPEN draft | Durable `.config-transaction.pending` marker + boot/direct-exec/per-grant gate | **Different design; see open decision below.** Do not port blindly (and #11's `init.d` has the `stop_service` fail-open regression above). |
| #13 | OPEN draft | Direct-daemon recovery overlap | Title says **`[SUPERSEDED — DO NOT MERGE]`**. |
| #14 | OPEN draft | Enforce executable modes in intake | **Closed on PR #24 (`3235b33`)**: `pisowifi-ci.yml` now checks `git ls-files -s` modes against `SOURCE_INTAKE.json` (negative-tested). |
| #16 | OPEN draft | `nft get element` readback + flush failure diagnostic | **Already in `Pisowifi`** (`common.sh` `bp_authorize_mac`/`bp_deauthorize_mac`, `nft_membership_failclosed.sh`). |

## Only non-placeholder asset unique to the stack
`branding/Logo-V2/brand-manifest.json` and `brand-tokens.css` (from the branch between #2 and #3). Not runtime code; can be cherry-picked into a `Shared/branding/` or `docs/` location if desired.

## Recommendation (requires owner action)
1. **Do not merge PRs #1–#16.** Keep them as historical drafts or close them with a pointer to this document; merging #1 introduces the P1-2 case collision and merging #11–#16 regresses `stop_service` and atomic table replacement.
2. **Open design question (from #10/#11/#12/#15):** whether a failed `config_set` apply (`rc=8`) in `Pisowifi` should also drop a durable marker that stops `blazepwifi-core` until operator clear. Default remains **(B) not needed** (config keys are non-financial; `flock` + `rc=8` + UCI revert already contain the write). Choose **(A)** if you want that gate designed cleanly on top of `Pisowifi`.

Nothing here authorizes production release. All NO-GO gates (#31, #34, #43, P0-1 licensing) remain in force.
