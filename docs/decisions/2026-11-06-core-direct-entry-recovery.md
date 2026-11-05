# COE CORE direct entrypoint recovery gate — 2026-11-06

**Separate repository:** `BlazeDevStudio/CoinOperatedEcosystem`, stacked on unmerged COE PR #11. Does not modify `BlazingSystems-Experiments` or any Phoenix owner PR.

## First-party provenance

| Attribute | Value |
| --- | --- |
| Original repository | `BlazeDevStudio/BlazingSystems-Experiments` |
| Original source PR/commit | `#252 @ c2a7515f43aff7043b0c2274dcdc097f30d7efbb` |
| Original path | `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/sbin/blazepwifi-core` |
| Original Git blob | `94c6bfa462b509587e0ea5416c0481de0cb641f0` |
| Original SHA-256 | `f789066018389fb014e56c50718376bdbbc1611d173a6b004a10aa090a3b818a` |
| Derived destination | `core/openwrt/rootfs/usr/sbin/blazepwifi-core` |
| Derived Git blob | `579359a2599cf71a544538b81d3fbba689da5e36` |
| Derived SHA-256 | `5311613dcd209d48fcac2356dd07afbb3f9930ef23817e334c8c10a90470ba87` |
| Status | `refactored`; `production_authorized=false` |

## Why this needs a second guard

The previous draft #11 protected `/etc/init.d/blazepwifi` before it registered the `procd` instance. But direct execution of `/usr/sbin/blazepwifi-core`, including an independently invoked or respawned command, did not traverse that init code. It could load `common.sh`, initialize runtime directories, delete/build nftables rules and authorize historical accounts despite an unresolved configuration marker.

The new daemon guard executes at its own entrypoint **before the existing `BP_LIB` source statement or any nftables action**. It uses fixed canonical `/etc/blazepwifi`, `/usr/lib/blazepwifi/config.sh` and `/etc/blazepwifi/.config-transaction.pending` paths, ignores inherited marker redirects, rejects symlinks and missing recovery helpers, and invokes the previously migrated read-only `bp_config_recovery_status`. Any uncertain result exits code `9`; successful check proceeds through the original implementation.

`tests/core_direct_entry_recovery.sh` uses a disposable path-translated copy of the **real daemon source**, plus mocked common.sh, nft and sleep. The test requires no loading of normal CORE code and no firewall command on every denied case: pending marker, inherited bypass attempt, symlink marker, missing/symlink config directory, missing/symlink/invalid guard library. A clean synthetic positive run exercises the prior nft setup and controlled TERM cleanup using a fake nft binary.

## Source-intake / execution mode repair

All four previously staged OpenWrt shell entrypoint/helpers came from upstream **executable** Git blobs but were accidentally stored with mode `100644`. This branch preserves their content bytes while restoring Git mode `100755` for `blazepwifi` init, `blazepwifi-core`, `config.sh`, and `capabilities.sh`.

The source-intake validator previously ignored extensionless files unless explicitly entered in the manifest. It now rejects unregistered files in `usr/sbin`, `usr/bin`, and `etc/init.d` regardless of suffix or executable mode. Additional unit tests exercise an unregistered extensionless executable and a chmod-0644 script in the runtime directory.

## Limits and NO-GO

- This is an unmerged review-only migration. No package installation, physical OpenWrt boot, network reconfiguration, flash endurance or cold-reboot acceptance was executed.
- Direct execution guard is a **point-in-time** preflight, not a durable independent anti-rollback witness. The existing marker implementation still lacks power-loss persistence proof. A marker appearing after preflight, a source compromise, and other privileged startup paths are outside this isolated test.
- Remote-admin and update services remain unguarded by this particular patch; their separate privileges and recovery ownership need independent review.
- This does not authorize coin GPIO, payment credit, rental leases, production signer custody, active migration, keys, flashes, releases or merges. No third-party proprietary source was copied.
