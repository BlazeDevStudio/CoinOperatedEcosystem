# CORE configuration source intake — 2026-11-02

## Scope and precise ownership

Separate **CoinOperatedEcosystem** repository. Stages the original, **byte-identical**
OpenWrt `config.sh` next to the reviewed `capabilities.sh` in
`core/openwrt/rootfs/usr/lib/blazepwifi/`.

| Provenance | Value |
| --- | --- |
| Original source | `BlazeDevStudio/BlazingSystems-Experiments:experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/config.sh` |
| Owner PR | #252 (draft, still unmerged) |
| Original commit | `c2a7515f43aff7043b0c2274dcdc097f30d7efbb` |
| Original Git blob | `7bde717f02d6f1d90ca099ab29bff336824ad81f` |
| Original SHA-256 | `4a73c0841614f841dd35df4e42f9bf1eedc3c5f8e89cb0d9a793f7ee692e20a2` |
| Destination | `core/openwrt/rootfs/usr/lib/blazepwifi/config.sh` |
| State | `staged` (unaltered source; **not** deployable) |

## Why unchanged first

Configuration logic also owns `bp_config_set()`, `uci commit`, apply hooks
and best-effort rollback. Deleting or rewriting those paths before observing
the existing behavior could make a working router unmanageable. Existing
`BP_CONFIG_APPLY_HOOK` executes a shell command string and must be treated
as a privileged, **developer-only** test seam, never exposed to an untrusted
request or product configuration.

`tests/core_config_contract.sh` executes the original functions with an
isolated disposable `uci` shim. It tests only the input whitelist/ranges
and failure-to-apply rollback against synthetic state; it does not prove
crash-atomic configuration commits, real UCI persistence, cross-process
concurrency, live VLAN switching or hardware recovery.

## Next bounded stabilization

1. Design a serialized config transaction owner and a durable apply/rollback
   boundary, with explicit refusal if rollback fails.
2. Remove shell-string execution from runtime apply; support a fixed allowlisted
   operation and a separate test fixture seam.
3. Prove persisted/apply success before API ACK; independently review the
   router's real UCI behavior in a noncustomer environment.
4. Preserve all existing CORE money and controller admission NO-GO gates.

No source from LPB, JuanFi, iCafe/PanCafe, WiFi5Soft or ASAP Timer was copied.
No merges, production credentials, flashing, paid activity or deployment.
