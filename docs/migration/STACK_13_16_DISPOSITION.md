# Disposition of draft PRs #13–#16 against the canonical Pisowifi tree

Status: analysis only, 2026-11-11. Scope is **PRs #13–#16**. PRs #1–#12 were not re-analysed here.
Compared: stack tip `ecosystem/core-nft-authorize-verification-20261106` (`d537b30f…`, layout `core/openwrt/rootfs/…`)
against PR #24 head `3235b33bcf165305ef5b53f091f7d330bc4d46a6` (layout `Pisowifi/openwrt/rootfs/…`, 61-file rootfs).

The two trees are **different implementations of the same daemon** (`blazepwifi-core` blob `4a4a8efb…` in the stack vs `aa7a6bca…` in Pisowifi), with a different config-transaction design. A mechanical port is therefore not appropriate.

| PR | Purpose | Disposition | Evidence |
| :-- | :-- | :-- | :-- |
| #13 | Direct-daemon recovery gate | **Superseded** (title says DO NOT MERGE); do not port | PR title/state |
| #14 | Executable modes + extensionless intake bypass guard | **Covered, one gap closed.** Manifest already records `git_mode`; all 65 entries match the index. CI did not enforce modes — now does (PR #24 `3235b33`), negative-tested by dropping `+x` | `SOURCE_INTAKE.json`, CI step |
| #15 | Fence per-MAC grants with a config lock + pending marker | **Not portable as-is; design gap remains.** The stack gates grants on a durable `.config-transaction.pending` marker (`bp_config_recovery_status`). Pisowifi `config_set` instead takes `flock` on `config-write.lock` and returns rc8 for uncertain apply, with **no durable marker** the daemon can consult | no `bp_config_recovery_status`/pending marker in Pisowifi rootfs |
| #16 | Require nft membership readback; surface flush failures | **Already covered natively.** `bp_authorize_mac` does `add` then `get element` and returns 8 on failure; flush failure emits `CRITICAL: … revocation unverified`; `setup_nft` replaces the owned table in one nft transaction (the stack note says this was still open there) | `common.sh` `bp_authorize_mac`; `nft_membership_failclosed.sh`, `nft_atomic_setup.sh`, `nft_shutdown_guard.sh` PASS locally and in CI |

## Open decision (needs owner/architect)
Should Pisowifi gain a durable config-uncertain marker that `blazepwifi-core` checks before each grant? Without it, a config apply that ends in an uncertain state is reported to its caller but does not stop the daemon from continuing to grant. Impact is bounded (config keys are interface/port/walled lists; no paid state) but it is the only behavioural idea in #13–#15 not present. Options: (A) adopt the marker + recovery gate as a new, reviewed design in Pisowifi; (B) accept flock+rc8 as sufficient and close #13–#15 as superseded. No code was changed for this.

## Correction to earlier chat reports
The case collisions are `Pisonet`/`pisonet` and `Rental`/`rental` (audit finding **P1-2**), **not** `Pisowifi`/`pisowifi`. The stack uses `core/` for the PisoWiFi daemon, so it does not collide with `Pisowifi/`. The audit document was already correct; some chat summaries were not. Finding IDs in chat also differed from the audit (audit: P0-1 licensing/privacy, P0-2 atomicity, P1-1 empty `main`, P1-2 case collisions).

Nothing here is production approval. Hardware, power-cut and independent review gates are unchanged.
