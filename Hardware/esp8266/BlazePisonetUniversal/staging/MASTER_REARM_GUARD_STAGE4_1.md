# BLAZE INTERCON — Stage 4.1 Master reboot quarantine (DRAFT / HARDWARE NO-GO)

## Problem addressed
Stage 4 tracked unresolved physical coin pulses in RAM. A restart wiped that alarm and could let the Master re-enable D7 even if money fell just before a failed flash commit. Stage 4.1 changes the safety posture to **locked on every Master boot**, including first boot after an upgrade. The operator must inspect/reconcile the coin chute before a Master can take paid coins.

## Behavior
- The Master starts every boot with D7 and software coin acceptance disabled, regardless of prior saved CS enable preference. Standard standalone behavior and Slave paid-balance restoration are unchanged.
- The operator disables CS and inspects the acceptor/any already accepted coins and outstanding transaction receipts. No pending Master event, unread pulses, active PWR_SW operation, or unhealthy journal may be present.
- Through the ESP's own AP only, with changed AP/admin passwords, the operator confirms reconciliation. The firmware provisions or verifies an immutable LittleFS `/intercon-arm1` marker bound to local chip, paired chip and journal key fingerprint; writes use temp+flush+readback+rename+readback. An existing corrupt/mismatched marker is an unrecoverable **hard lock** until external service; do not delete it to bypass reconciliation.
- Successful operator confirmation allows arming **for the current boot only**. It does NOT automatically enable CS; the operator separately enables CS. The persistent marker remains. Any restart forces another inspection/confirmation.
- Journal failure, unresolved pulse burst or uncertain ACK keeps the Master coin gate disabled. Pending durable grants can still retry and settle after a reboot; the operator may re-arm only after they settle.
- The authenticated status page distinguishes reboot quarantine, current-boot arming, and marker faults.

## Exact limitation
This is a **detection and operator hold**, not hardware-guaranteed lossless accounting. It cannot prove if a coin fell before an ESP flash write or determine an unknown denomination/pulse count after power loss. Only electrical hold-up, acceptor inhibit verification and tests on real hardware can establish that behavior. It does not change Stage 4's 650 ms burst prototype, 60-second Slave countdown checkpoints, one-pair topology or flash wear constraints.

## Lab protocol
1. With two disconnected, unoccupied lab rigs, flash the test build (not an unattended paid machine).
2. Master boots quarantined. Confirm D7 external enable is OFF even if last saved CS preference was ON.
3. Journal and pair the two nodes. From the Master's AP, change defaults, disable CS, inspect chute, verify zero pending payments, and use the explicit reconciliation control.
4. Confirm marker created, unchanged on subsequent normal credit, and that only a separate manual CS enable can open D7.
5. Simulate pending CRED, lost ACK, restart, Wi-Fi outage, partial coin burst, flash-full/corrupt marker. After reboot D7 must remain OFF until manual reconciliation. Valid pending CRED may still retry and ACK.
6. Force power cut at every real coin edge and file-write boundary. Compare physical coin collection against both journals; any missing coin, double credit, unsafe relay transition or unexpected CS enable is a hardware release blocker.

## Release
**DRAFT / NO-GO.** Native marker-codec tests and ESP8266 CI compilation are necessary but insufficient. No automatic merging or field-payment activation.
