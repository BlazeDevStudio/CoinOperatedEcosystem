# LAB-only NSIS package — file-copy diagnostic

This unsigned LAB package is adapted from the historical public SoftTimer installer with independent LAB Program Files, shortcut and registry keys. It is **not** an installation/upgrade path for a customer kiosk. No code from the unrelated OpenWrt PisoWiFi backend is included.

**Isolation changes:** the LAB installer neither creates/deletes the ordinary Windows Task Scheduler entries, runs `--install-system-integration`, removes startup tasks, changes ProgramData ACLs, manipulates `maintenance.until`, nor kills running SoftTimer/Watchdog processes. The uninstaller only deletes its LAB Program Files, shortcuts and registry entries. The installer refuses an obvious regular SoftTimer installation or a nonempty canonical `%ProgramData%\BlazeSystems\BlazePisonetSoftTimer` directory.

**Important limitation:** the application executable itself still uses canonical Windows storage paths and, if configured, can create watchdog behavior when launched. Do not manually run it on a computer with any live paid state. Use a disposable clean Windows 10/11 VM, no coinslot, no customers, and no existing SoftTimer installation or session. The LAB installer is built but is **not executed by CI**. Host UAC/registry/file locking and real uninstaller lifecycle are unverified.

Do not promote this unsigned LAB binary to production. Build separate isolated LAB storage/task identities and verify install/uninstall on disposable Windows before any rollout.
