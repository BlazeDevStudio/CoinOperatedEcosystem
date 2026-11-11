# BlazeRental standalone Android preview

Android Java app with no BlazePwifi / Phoenix dependencies. Monitoring only: server URL, manually paired device ID and secret, read-only HMAC-signed lease status. Server is authoritative; client uses SystemClock.elapsedRealtime() for a display-only countdown and fails closed after process death. The app does NOT enforce kiosk restrictions or grant financial credits.

Prerequisites: JDK 17, Android SDK platform 35 and an installed Gradle 8.11-compatible toolchain. From this directory, gradle :app:assembleDebug is the intended development command; the environment does not include a Gradle wrapper binary. GitHub Actions cannot pick up workflows under Rental/ alone; enabling a workflow requires separate explicit permission to add .github/workflows/.

Security limitations: manual pairing secret stored in private application preferences; cleartext LAN HTTP allowed for lab-only connectivity and remains vulnerable to traffic observation. For production, add TLS/pinned local trust, Android Keystore-encrypted storage, operator-safe pairing, managed device enforcement, lifecycle regressions and real hardware testing. Never deploy this APK for paid/unattended rental devices.
