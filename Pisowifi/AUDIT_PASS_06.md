# Blaze PisoWiFi — Development Pass 06 (2026-11-08)

## Boundary and provenance

**Destination:** public `BlazeDevStudio/CoinOperatedEcosystem`, strictly `Pisowifi/**`. **Review:** draft PR #18; no merge, release, flash or customer operation. **Source:** already-public first-party MIT-licensed `BlazeDevStudio/BlazingSystems-Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00`, `experiment/openwrt/BlazePwifi/openwrt/rootfs/` (Git tree `f4a923aaacf1374e90c7bab5f335efe6c6ec55cf`).

**All 61/61 original OpenWrt rootfs files are now present, with original Git modes intact.** Of those, **55 byte-identical upstream blobs** and **six intentionally modified development-cleanup blobs**. This verifies complete *source-rootfs inventory*, **NOT** a bootable appliance, complete package/build system, payment authority, or approved release. See `SOURCE_INTAKE.json` for every original/destination blob SHA.

The remaining first-party runtime source was restored in separate provenance-only commits:
- `6498759d059255f8289689c6273a0b17eadb3d85`: original embedded admin CGI service dependencies (`rental.sh`, `rental_policy.sh`, `rental_update.sh`, `remote_apply.sh`, `update.sh`) — do not confuse original embedded subsystem code with any separate Android/Rental application repository.
- `ff1afb41ff7d3aec5971cf2abd8b4d2b01794835`: dormant native-v2 migration/freeze support scripts, byte-identical.
- `9a6d20cefad79b1b6920b6ee9597bc83185a2e4f`: original OpenWrt remote/update init and helper scripts, byte-identical.
- `143a1bd7cf0932f2b863ca22f6986fbe2d0546b6`: original embedded rental CGI and UI/media resources, byte-identical.

No imported subsystem was invoked, enabled or trusted for deployment; source file admission is not runtime/financial admission. No secret files, customer state or private branding bundle were imported.

## Repaired historical regression fixture

Commit `486049f1bfb320f26faf663eec6cb895a38b339e` repaired **only** the historical `Pisowifi/tests/config.sh` fake-UCI shim, adding `uci -q show blazepwifi.main` and correct failed-`get` status for absent options, required by the production safety change from Pass 05. Added `tests/config_fixture_smoke.sh` to test the **actual extracted mock** without invoking the full admin CGI and added it to `tests/run_focus.sh`.

Verification evidence:
- The complete updated fixture `tests/config.sh` has Git blob `4b1178a1c1242987b7a34fe8086e1273fe812b99`.
- Its exact 834-byte embedded UCI heredoc was extracted from that source through connected GitHub tools, yielding Git blob `6927acb0986799a0bd9cc7bad6fbfa7fe48b6fb8`. The same locally reconstructed embedded script was verified with `git hash-object` to the **same SHA**.
- The new `tests/config_fixture_smoke.sh` Git blob `a17f2e7885087a2c30d0a8e9c8d45098f28579b3` also matched the locally executed file's `git hash-object`.
- `sh -n` and BusyBox `ash -n`: PASS; `sh tests/config_fixture_smoke.sh` and `busybox ash tests/config_fixture_smoke.sh`: **3 smoke checks each PASS** on the isolated source-subset reproduction (UCI section+option, get missing semantics, set/delete transition).
- This did **NOT** run the full historical `tests/config.sh` admin CGI and did **NOT** execute full `tests/run_focus.sh` from an exact Git checkout. The isolated environment cannot resolve github.com to clone the live repo; there is no destination GitHub Actions workflow, so **NO CI RUN OR JOB ID**.

Original `tests/{portal,security,integration}.sh` remain bit-identical upstream; the original `tests/config.sh` now differs strictly by the mock compatibility repair. Four full-platform integration suites remain NOT RUN.

## Packaging and runtime blockers

- Upstream also has non-rootfs OpenWrt packaging such as `openwrt/paid-authority/Makefile` and `openwrt/paid-authority/src/v060_journal_authority.c` and a synthetic native lab package (the latter requires external source files). **These are NOT included in the 61 rootfs count or admitted into this PR.** Native financial code, independent witness and signing integration remain NO-GO.
- The original `etc/uci-defaults/99-blazepwifi` enables the OpenWrt daemon and remote/update guards on installation. Their presence here in Git does NOT enable them; later image packaging must explicitly gate first-boot behavior, firewall ordering and privileges before testing.
- No system `nftables` packet-path/netns/firewall4 test, ImageBuilder build, actual OpenWrt UCI/host service rollback, VLAN/AP/captive-browser physical observation, financial idempotence/power-loss, physical adapter/coin, or rollback witness evidence.
- Prior source-level nft add/delete failure fixes still cannot guarantee live traffic denial when global kernel revocation fails, and they have not been re-run against a complete exact-head checkout.
- Legacy financial durability (#31/#32), independent rollback witness (#43) and physical acceptance (#34) are outstanding. No merge, release, flashing, keys, payment operations or unrelated repositories.

## Next bounded engineering gate

Use a trusted isolated runner with the actual PR checkout to execute `sh Pisowifi/tests/run_focus.sh`, then run historic admin/config/security/integration suites with mock adapters. Repair any real failures before starting an OpenWrt target build. Keep the native paid-authority runtime quarantined from installation until independently accepted. Maintain the strict GitHub directory boundary and no-Codex instruction.
