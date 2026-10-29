# Blaze Systems Logo V2 — Phoenix brand anchor

**State:** `REFERENCE_PINNED` on 2026-10-30. This is the visual authority for the Coin Operated Ecosystem. It does not make any subsystem release-ready.

## Authority

- Source repository: [BlazeDevStudio/BlazingSystems](https://github.com/BlazeDevStudio/BlazingSystems)
- Immutable source commit: [`8b08add6319df58a8c8cd1a41d1dcd6f4caab04c`](https://github.com/BlazeDevStudio/BlazingSystems/commit/8b08add6319df58a8c8cd1a41d1dcd6f4caab04c)
- Owner-approved board: [`branding/Logo-V2/ORIGINAL/113704.png`](https://github.com/BlazeDevStudio/BlazingSystems/blob/8b08add6319df58a8c8cd1a41d1dcd6f4caab04c/branding/Logo-V2/ORIGINAL/113704.png)
- Git blob: `5b1bb07fc6a875207ec56600f547a56f0da83f94`
- SHA-256: `56fb15d1ed4faa44af7dafc3defa5e3eb04252966df853bd96f587a7a3d9132d`
- Actual encoding and size: JPEG, 1536 × 1024, 234,556 bytes; the uploaded filename has a `.png` suffix.
- Exact-source package: [`Logo-V2-Branding-Package.zip`](https://github.com/BlazeDevStudio/BlazingSystems/blob/8b08add6319df58a8c8cd1a41d1dcd6f4caab04c/branding/Logo-V2/Logo-V2-Branding-Package.zip), Git blob `68db81f6ae64ee51baa056496436403b64b4b8a3`, 7,804,110 bytes, downloaded archive SHA-256 `8cd0d32f8023e7d8259a268f9bdbb6c7b3dfdf55d7ba2a205fd39f800bfa22b9`.

The original board is the authority. The older files under the source repository's `assets/vector/`, `mockups/`, `preview/` and `samples/` are reconstructed approximations; they must not become ecosystem logo masters.

## Identity carried into ecosystem interfaces

| Element | Approved value |
| --- | --- |
| Brand | BLAZE SYSTEMS |
| Symbol | Blue ribbon/flame-like B |
| Motto | SYSTEMS THAT EMPOWER A BRIGHTER TOMORROW. |
| Pillars | PEOPLE · TECHNOLOGY · PROGRESS |
| Typeface named by the board | Montserrat |
| Blaze Blue | `#0066FF` |
| Electric Blue | `#00B0FF` |
| Deep Blue | `#001A3D` |
| Light Blue | `#7DD3FF` |
| Neutral | White |

Use Deep Blue for primary dark chrome and splash surfaces, Blaze Blue for primary actions, Electric Blue for active/highlight states, and Light Blue for low-emphasis information. Operational warning, fault, payment-denial and relay-safety colors remain semantic safety signals; branding must not turn them blue.

Product names such as BlazePwifi, BlazeRental and BlazePisonet sit beside or below the approved Blaze Systems identity. Do not rewrite the wordmark, insert product names inside the symbol, or create a different emblem per subsystem.

## Logo handling

- Preserve silhouette, proportions, colors and orientation.
- Do not redraw, retrace, regenerate, stretch, rotate, bevel, shadow or recolor the mark.
- The exact-source package's `ASSETS/app-icon-from-board.png` is an unchanged crop from the approved board (269 × 262; SHA-256 `92c8354a2dc00eb208f396aff64cc944ffe396b3b5f3ed9ff19b5091bc247c33`). It is a reference crop, not proof of Android/Windows icon acceptance.
- Platform resizing, transparency cleanup or icon-mask adaptation requires a separate reviewed product change and must keep the original mark visually unchanged.
- The placeholder GitHub URL and QR printed on the board are part of the source image and are not ecosystem distribution links.

## Scanned active integration

The active BlazePwifi development tree at immutable commit `6d4c9b487af4d768c4d7627654d119417fcc6e00` already carries one verified exact package asset:

- `experiment/openwrt/BlazePwifi/tools/BlazeSystems-Logo-V2.png`
- source member `Logo-V2/ASSETS/logo-on-dark-from-board.png`
- Git blob `ef0bb8a384c5880936f78624f0c931983c31d6ad`
- SHA-256 `c4e61f370a1a9541722f4fcee522cec8d20c3c9e2917fc1a32286f4870193690`
- 278 × 175 pixels, 31,649 bytes

Its provenance note and `tests/test_rental_qr_branding.py` verify byte-for-byte embedding in the two offline BlazeRental QR templates. This is an approved exact crop usage; it does not authorize other files as Logo V2 masters.

The separate Android launcher asset `android/BlazeRentalLauncher/res/drawable-nodpi/blaze_lcm_brand.png` (Git blob `19f1c2f843dca1f9f6e320ea0dbd94580f85e608`) does not match any file in the pinned exact-source package. It remains product-specific LCM artwork, outside this Logo V2 authority. Any replacement or adaptation is a product-scoped visual change requiring screenshots, accessibility evidence, density/adaptive-icon review and exact source hashes.

## Integration rule

Every UI-branding PR must identify the product surface, the exact source asset/hash used, light/dark treatment, accessibility name `Blaze Systems`, and before/after screenshots. This anchor changes no runtime UI, APK, Windows executable, firmware, payment flow, signing state or release gate.
