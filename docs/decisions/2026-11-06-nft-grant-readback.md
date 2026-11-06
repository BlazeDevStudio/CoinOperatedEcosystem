# CORE nftables authorization membership readback — 2026-11-06

## Provenance and review boundary

This change is in the **separate** `BlazeDevStudio/CoinOperatedEcosystem` repository, on top of unmerged draft PR #15. No Phoenix source-owner PRs, customer router installations or live financial devices were modified.

First-party origin: `BlazeDevStudio/BlazingSystems-Experiments`, CORE draft #252 at `c2a7515f43aff7043b0c2274dcdc097f30d7efbb`, path `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/sbin/blazepwifi-core`, original Git blob `94c6bfa462b509587e0ea5416c0481de0cb641f0`, original SHA-256 `f789066018389fb014e56c50718376bdbbc1611d173a6b004a10aa090a3b818a`.

The derived `core/openwrt/rootfs/usr/sbin/blazepwifi-core` SHA-256 is `2682b9cd4680968ef662f95eedebfff14579f780c906f174267cbd436c783a32`, state `refactored`; `production_authorized=false`. Original Git mode `100755` remains intact.

## Source defect and bounded correction

The original `common.sh` implementation of `bp_authorize_mac` uses `nft add element ... || true`. That can return status 0 even when nft failed (permission, missing table/set, invalid element). The prior CORE per-MAC lock/recovery preflight therefore did not prove the firewall accepted the MAC.

The bounded refactor keeps the existing common helper, but immediately checks `nft get element inet blazepwifi auth_macs "{ $bp_core_auth_mac }"` **while the same config lock is held**. An absent element, failed lookup, unsupported lookup, or other unsuccessful nft status invokes the existing deny/flush/exit-9 path. An existing element meets this narrow observable membership condition even if adding a duplicate was rejected. The loop and post-grant config recovery checks remain intact.

The stop path now emits `CRITICAL: nft authorization revocation unverified` if `nft flush set ... auth_macs` fails, while still returning exit 9. This is an operator diagnostic, not evidence of successful revocation.

The source-linked `tests/core_direct_exec_recovery.sh` uses a disposable nft program and a mock common helper that deliberately suppresses failed nft adds, matching the error-return semantics of the original first-party function. New negative cases cover silent add failure, failed readback after a synthetic add, failed flush diagnostics, and successful add/readback while preserving previous pending/restart/lock-contention scenarios.

## Not proven, and still NO-GO

- `nft get element` proves only a successful user-space membership lookup at one instant. It does **not** prove actual packet forwarding behavior, rule priority, anti-bypass routing, independent sender authority, post-readback stability or hardware network containment.
- A pre-existing MAC membership can satisfy the lookup after a failed duplicate add; the positive condition is **membership**, not an unambiguously new successful add. Uncoordinated nft writers still exist outside the config lock.
- On failure to flush, previously authorized clients may remain authorized. An exit code and a log line **do not revoke network access**; stronger atomic ruleset installation and hardware evidence are required.
- The source still replaces its firewall table through an earlier separate `nft delete table` and `nft -f`; partial setup/failure semantics need a separate atomic-replacement review before acceptance.
- No verified production router/kernel/nftables version, physical boot, power cut, signed identity, financial migration or safe controller activation. The existing 150-power-cut and 30-client hardware criteria remain unmet.

No merge, release, flashing, real credentials, paid transactions, production signing keys, or proprietary third-party source copying. This is synthetic host regression evidence only.
