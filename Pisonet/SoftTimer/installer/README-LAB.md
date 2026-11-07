# LAB-only NSIS package

This installer was adapted from the public historical Windows SoftTimer v0.4.0 NSIS script, original blob `cb0c777d5272d53638f884b19eef23f82a7ea102`, with destination-relative payload/output paths. The preview uses separate **LAB** Program Files/registry/shortcut names, blocks an obvious existing regular install and warns the operator before running.

**No pre-existing SoftTimer installation, member accounts or paid time may be present on the test PC.** The app itself still uses canonical Windows Task Scheduler names and ProgramData paths, so two installations cannot safely coexist. Keep this test inside a disposable VM or clean isolated machine.

No automatic centralized-port firewall rule is added. Source-linked synthetic CI gates must pass before compile; CI DOES NOT run this installer or uninstaller, verify kiosk policies, test real serial adapters, prove the watchdog recovery, or authorize real-money use.

After real Windows lifecycle and hardware acceptance, design separate stable installer/upgrade/rollback semantics. Do not promote this lab binary to a commercial release.
