BLAZEPISONET SOFTTIMER INSTALLATION
==================================
1. Extract the entire release ZIP.
2. Right-click Install-BlazePisonetSoftTimer.ps1 -> Run with PowerShell.
   If Windows blocks script execution, open an Administrator PowerShell in the extracted folder and run:
     powershell -ExecutionPolicy Bypass -File .\installer\Install-BlazePisonetSoftTimer.ps1
3. First run: create the administrator password. There is no universal default password.
4. Configure Hardware -> Timer source / Coin topology.
5. For USB-RS232, use Rescan then either select the COM port or Bind Exact Device.
6. Enable SoftTimer only after testing the hardware.

ADMIN SECRET PATH WHILE LOCKED
------------------------------
Ctrl+Alt+Delete is owned by Windows and is intentionally not intercepted.
Return from the Windows secure screen, then press HOME during the short admin window.
Enter the SoftTimer administrator password.

CENTRALIZED MODE
----------------
- Coordinator: one PC physically connected to the coinslot/USB-RS232 adapter.
- Station: client PCs request the central slot over LAN/Wi-Fi.
- Use the same Centralized shared key on all participating PCs.
- Default peer port: TCP 8765, private/local subnet only.
