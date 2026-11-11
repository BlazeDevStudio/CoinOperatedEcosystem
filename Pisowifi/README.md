NO-GO FOR SHOP INSTALL

# Blaze PisoWiFi — isolated OpenWrt source recovery

**Status:** DRAFT / DEVELOPMENT ONLY. No production authorization, customer installation, real coins, device flashing, merges, releases, or paid v2 acknowledgement. The recovered rootfs is **not** a bootable OpenWrt image or an installable router package.

## Ownership and source

- Product directory: `Pisowifi/` only, on the draft branch `feature/pisowifi-cleanup-stabilization` of `BlazeDevStudio/CoinOperatedEcosystem` (PR #18).
- Historical reference, retained read-only: `BlazeDevStudio/BlazingSystems-Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00:experiment/openwrt/BlazePwifi/`.
- Exact original/destination blob identities and edit status: [MIGRATION_MAP.md](MIGRATION_MAP.md) and [SOURCE_INTAKE.json](SOURCE_INTAKE.json). Legacy source copies remain intact and are superseded by the mapped draft only for these migrated paths.
- This tree does not own standalone Rental, Windows SoftTimer, ESP firmware, diskless/PXE or other Blaze projects.

## Layout

- `openwrt/rootfs/` — first-party OpenWrt filesystem overlay and CGI source; **not** a built image.
- `tests/` — host-side shell fixtures/mocks; not real router or physical payment acceptance.
- `AUDIT_PASS_01.md` through `AUDIT_PASS_08.md` — historical bounded reviews.

## Critical safety restrictions

- **Financial NO-GO:** [Experiments #31](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/31) remains open. Member balance/receipt/revision writes now commit through a journaled, roll-forward transaction (simulated-fault and CI tested only; no power-cut or hardware proof, see `docs/ISSUE_31_LEDGER_GATE.md`). Existing uncertainty markers are quarantine controls, **not** a proof of exactly-once accounting; never auto-clear a pending or uncertain marker, reapply a coin, or return a paid ACK while state cannot be proved.
- **Rental:** independent issue #32 and Rental draft PR #19 are separate product work; do not edit those trees here.
- **Configuration:** there is no installed live `apply-config.sh`; admin configuration must refuse until a real apply/rollback implementation and full verification exist.
- **Anti-rollback:** no independent, protected off-disk freshness witness (#43). Do not generate or commit signing keys.
- **Physical:** issue #34 requires a spare router/PC/ESP and actual power-cut and soak acceptance; no synthetic test substitutes for it.
- No known default admin password. A future install must generate an independent local admin secret at first boot; no credentials, business records, account databases, private keys, or shop-router images in Git.
- Keep `v2` paid acknowledgement disabled and preserve all production gates.

## Development evidence and limits

Historic focused mocked shell checks are documented in the audit passes but **are not newly rerun by this README/mapping commit**. For an actual checkout, syntax check with `find Pisowifi -name '*.sh' -type f -exec sh -n {} \;` and run `sh Pisowifi/tests/run_focus.sh` in an isolated disposable host fixture. Do **not** interpret those commands as executed until results are reported for the exact branch HEAD. BusyBox ash, OpenWrt build, real nft/firewall4, MCU, 30-device soak, power loss, and signed packaging remain unverified for this change.

## Review-only acceptance checklist

Clean-checkout build; crash replay/duplicate coin tests; receipt and balance durable atomicity; independent antirollback witness; secret scan; exact SHA provenance; safe configuration apply/rollback; protected signing; signed Windows installer (in its own product); and owner-performed physical acceptance must all pass before any customer deployment. Every missing gate is **NO-GO**.
