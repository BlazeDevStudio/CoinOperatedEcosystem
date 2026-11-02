# COE CORE config apply hook cleanup — 2026-11-02

Source origin remains `BlazeDevStudio/BlazingSystems-Experiments@c2a7515f43aff7043b0c2274dcdc097f30d7efbb`, file `experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/config.sh`, upstream Git blob `7bde717f02d6f1d90ca099ab29bff336824ad81f`, original SHA-256 `4a73c0841614f841dd35df4e42f9bf1eedc3c5f8e89cb0d9a793f7ee692e20a2`.

The old `bp_config_apply()` executed arbitrary shell commands with `sh -c "$BP_CONFIG_APPLY_HOOK"`, an unsafe privileged test seam. The refactored function accepts only `true` and `false` as fixed test-only outcomes. Any other nonempty hook refuses the operation; the normal installed `/usr/lib/blazepwifi/apply-config.sh` path stays unchanged when unset.

The source-linked `tests/core_config_contract.sh` now asserts that arbitrary shell strings cannot be executed and that configuration is rolled back on denied apply. These are **disposable UCI shim** tests, not a claim about real router recovery.

Derived local SHA-256 `93b73d8ab79b550bc4639b06321cb5920fc8fdc68099b5c0a849dddaa62b4ff5`. The original source bytes, SHA and commit remain preserved in the intake manifest; the destination is `refactored`, not copied. No other CORE/RENTAL/PISONET/ESP owner paths are modified.

Real concurrent UCI updates, rollback persistence failure, live VLAN reload, privileged environment custody, financial durability, protected signer and physical relay/coin acceptance remain NO-GO. No deployment, keys, real payments, flashing, merge, release or unlicensed third-party source.
