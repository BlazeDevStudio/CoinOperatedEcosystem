NO-GO FOR SHOP INSTALL

# PisoWiFi migration map — source preserved, destination draft only

Source snapshot: `BlazeDevStudio/BlazingSystems-Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00`, under `experiment/openwrt/BlazePwifi/`.
Destination: `BlazeDevStudio/CoinOperatedEcosystem` / `feature/pisowifi-cleanup-stabilization`, scoped exclusively to `Pisowifi/`.
Evidence: `SOURCE_INTAKE.json` (schema 8); this table mirrors its pinned Git blob SHAs and records whether each file changed.

**Source retention:** The source copies remain in Experiments; for these explicitly mapped draft destination paths, the source copy is **superseded, not deleted**. Other histories and products are not superseded. A different blob SHA records an intentional edit, not an unchanged copy. **No file is approved for production.**

## Migrated OpenWrt overlay files

| Original source path (relative to pinned project root) | New destination path | Source Git blob SHA | Destination Git blob SHA | Migration status |
|---|---|---|---|---|
| `openwrt/rootfs/etc/blazepwifi/portal/portal.json` | `Pisowifi/openwrt/rootfs/etc/blazepwifi/portal/portal.json` | `96d549c10713afbe408ed1a36df915c0f2519448` | `96d549c10713afbe408ed1a36df915c0f2519448` | copied unchanged; source retained |
| `openwrt/rootfs/etc/config/blazepwifi` | `Pisowifi/openwrt/rootfs/etc/config/blazepwifi` | `f913bd0812a83b048601dc0c39e8bb96620b6d12` | `f913bd0812a83b048601dc0c39e8bb96620b6d12` | copied unchanged; source retained |
| `openwrt/rootfs/etc/init.d/blazepwifi` | `Pisowifi/openwrt/rootfs/etc/init.d/blazepwifi` | `4a3d6240e700520c78acff4d3daea5b98d5df5d7` | `11c4679f95d804fe9f96fb9918b4ae2be8d5c92e` | intentionally edited; source retained |
| `openwrt/rootfs/etc/init.d/blazepwifi-remote-admin` | `Pisowifi/openwrt/rootfs/etc/init.d/blazepwifi-remote-admin` | `8ee0e7f73f04c3b24011b0c8f616e12009e6d76e` | `68fb8748792fc4d58cb45842a04ab83b8e164f5c` | intentionally edited; source retained |
| `openwrt/rootfs/etc/init.d/blazepwifi-remote-guard` | `Pisowifi/openwrt/rootfs/etc/init.d/blazepwifi-remote-guard` | `fc613ea6402330bd91d000b580754d37e81db66d` | `fc613ea6402330bd91d000b580754d37e81db66d` | copied unchanged; source retained |
| `openwrt/rootfs/etc/init.d/blazepwifi-update-guard` | `Pisowifi/openwrt/rootfs/etc/init.d/blazepwifi-update-guard` | `c2b81cc7c1283611645e0d1148a91045c4d89d17` | `c2b81cc7c1283611645e0d1148a91045c4d89d17` | copied unchanged; source retained |
| `openwrt/rootfs/etc/uci-defaults/99-blazepwifi` | `Pisowifi/openwrt/rootfs/etc/uci-defaults/99-blazepwifi` | `82dc54f717bc5cad91160286333529b5868ef17b` | `532727f06d78c05b87fef28d1c0e89a7c5de8308` | intentionally edited; source retained |
| `openwrt/rootfs/lib/upgrade/keep.d/blazepwifi` | `Pisowifi/openwrt/rootfs/lib/upgrade/keep.d/blazepwifi` | `82167b8ef1fc683b6b531dce0a7cbbd4ed4fcd56` | `82167b8ef1fc683b6b531dce0a7cbbd4ed4fcd56` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/auth.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/auth.sh` | `ecf2f1e8af8a56a6c02c5bd28a066c587741bfc0` | `872385dfcd07bdd978c6c36ef166dd4130d56f84` | intentionally edited; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh` | `3753966f3e52c04ffddbc080f04bb37e12af0e67` | `098eafbe06193ff1ea7b4fc7e3bf4ae3b7b3e4cd` | intentionally edited; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/common.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/common.sh` | `4ccb10777b08f541d092f7c2c2d2aad4d2f6562e` | `ae00667da26c68c9e44a54a941887191029afc11` | intentionally edited; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/config.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/config.sh` | `7bde717f02d6f1d90ca099ab29bff336824ad81f` | `4535ef6993185208fb3b098842a0f8d69e71d5c7` | intentionally edited; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/console_ops.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/console_ops.sh` | `92a44fa1c7f69a81b750acf6bac4acc98c637a3b` | `92a44fa1c7f69a81b750acf6bac4acc98c637a3b` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/controller.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/controller.sh` | `54bdc59949884bd3e734f8c07ddeb1d7c2cf9848` | `3219f99b02556eddced4bccd644a13baa0633260` | intentionally edited: default-deny exact identity, failed-copy registry preservation and locked concurrent registration/admin writes; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/member_migration.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/member_migration.sh` | `058891bf2b13b59333b4247743fcccc8741bf9b4` | `058891bf2b13b59333b4247743fcccc8741bf9b4` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/member.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/member.sh` | `69af39052959a1d6a349851b4fbd909a9ad53aeb` | `7c2e599996d83751433ef2ceef87646c943bff7c` | locally derived (Issue #31 member transaction journal); source retained; real-router test NOT_RUN |
| `openwrt/rootfs/usr/lib/blazepwifi/portal.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/portal.sh` | `702bb344d2531eb046c189adebfb193ba7ca4e6e` | `702bb344d2531eb046c189adebfb193ba7ca4e6e` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/remote_apply.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/remote_apply.sh` | `ef85698211f79108e6e152c6f4ea1165d6c5f44c` | `ef85698211f79108e6e152c6f4ea1165d6c5f44c` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh` | `dcaed944f6ee7bea5d8e806c139d25c8eddeb4df` | `dcaed944f6ee7bea5d8e806c139d25c8eddeb4df` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/rental_update.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/rental_update.sh` | `783c0a45ee650f3eea8a890ea4d24b086d36a31a` | `783c0a45ee650f3eea8a890ea4d24b086d36a31a` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/rental.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/rental.sh` | `7bb51bc9f38ae42441393ed20f0d67a35d5687f2` | `35fcff9699fbcb55cbc1f1dcc094709d1d2abb2a` | locally derived (Issue #31 rental transaction journal & device revocation); source retained; real-router test NOT_RUN |
| `openwrt/rootfs/usr/lib/blazepwifi/update-migrate.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/update-migrate.sh` | `bbfd3817da2f50af9174218be65d9801965446b1` | `bbfd3817da2f50af9174218be65d9801965446b1` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/update.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/update.sh` | `8b8153fba470cd9e3edbc30dd89d915b03417102` | `8b8153fba470cd9e3edbc30dd89d915b03417102` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/v2_frozen_capture.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/v2_frozen_capture.sh` | `229085fcb3f7457a14b51a378acf4be78a6e970e` | `229085fcb3f7457a14b51a378acf4be78a6e970e` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/v2_maintenance_freeze.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/v2_maintenance_freeze.sh` | `07b8c98b70a77a90bda3a85f57fabe540aabfb2c` | `07b8c98b70a77a90bda3a85f57fabe540aabfb2c` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/v2_migration_preflight.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/v2_migration_preflight.sh` | `a1feb66e19580859bffca17ac3b4f4382a02ffc0` | `a1feb66e19580859bffca17ac3b4f4382a02ffc0` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/v2_migration_stage.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/v2_migration_stage.sh` | `cdcff8a0918dc623327b498fe655e71b322aa6dc` | `cdcff8a0918dc623327b498fe655e71b322aa6dc` | copied unchanged; source retained |
| `openwrt/rootfs/usr/lib/blazepwifi/v2_shadow.sh` | `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/v2_shadow.sh` | `cd6f2421dfb4c0abad86e37547db863ac5f38768` | `cd6f2421dfb4c0abad86e37547db863ac5f38768` | copied unchanged; source retained |
| `openwrt/rootfs/usr/sbin/blazepwifi-core` | `Pisowifi/openwrt/rootfs/usr/sbin/blazepwifi-core` | `94c6bfa462b509587e0ea5416c0481de0cb641f0` | `aa7a6bca9a894952903c6dc95ee3d449cdad9ace` | intentionally edited; source retained |
| `openwrt/rootfs/usr/sbin/blazepwifi-remote-admin-run` | `Pisowifi/openwrt/rootfs/usr/sbin/blazepwifi-remote-admin-run` | `7d6d2f4b18d6c5a5a925f5ce885305dec9b24db5` | `1aabdc1a1f605ba7db0d474090fd651b7c6c2fc4` | intentionally edited; source retained |
| `openwrt/rootfs/usr/sbin/blazepwifi-remote-guard` | `Pisowifi/openwrt/rootfs/usr/sbin/blazepwifi-remote-guard` | `b45a5de7f79c87396257716c9918bfafb24297c4` | `523d5af30b89f1556e8cd7e7ab6e165e57027dc1` | intentionally edited; source retained |
| `openwrt/rootfs/usr/sbin/blazepwifi-update` | `Pisowifi/openwrt/rootfs/usr/sbin/blazepwifi-update` | `9c88305013d6214bf6ec35a818019ae93e3c84c3` | `9c88305013d6214bf6ec35a818019ae93e3c84c3` | copied unchanged; source retained |
| `openwrt/rootfs/usr/share/blazepwifi/VERSION` | `Pisowifi/openwrt/rootfs/usr/share/blazepwifi/VERSION` | `be14282b7fffb9ba95d51c6546ed9816dc8f3ff8` | `be14282b7fffb9ba95d51c6546ed9816dc8f3ff8` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/admin.html` | `Pisowifi/openwrt/rootfs/www/blazepwifi/admin.html` | `ffc85a2d9efc7b2a658d785045ddcefb21acaa6c` | `ffc85a2d9efc7b2a658d785045ddcefb21acaa6c` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/admin/console-v05.js` | `Pisowifi/openwrt/rootfs/www/blazepwifi/admin/console-v05.js` | `edb79264af9a0cede96a4c38b0f3a52c923d554b` | `edb79264af9a0cede96a4c38b0f3a52c923d554b` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/admin/controllers.js` | `Pisowifi/openwrt/rootfs/www/blazepwifi/admin/controllers.js` | `b128a876c64508ce945c32950d20bd30ce0ad01e` | `b128a876c64508ce945c32950d20bd30ce0ad01e` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/admin/core.js` | `Pisowifi/openwrt/rootfs/www/blazepwifi/admin/core.js` | `0e8d2b47cd1c4de762e58c889cee2bd3f98c0243` | `0e8d2b47cd1c4de762e58c889cee2bd3f98c0243` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/admin/members.js` | `Pisowifi/openwrt/rootfs/www/blazepwifi/admin/members.js` | `97be9909437b5f08bed9025e85891703c9e3a7fb` | `97be9909437b5f08bed9025e85891703c9e3a7fb` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/admin/rental.js` | `Pisowifi/openwrt/rootfs/www/blazepwifi/admin/rental.js` | `93cae4f8386c6fa872972d7afb9abd5d27ab1032` | `93cae4f8386c6fa872972d7afb9abd5d27ab1032` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/cgi-bin/admin` | `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/admin` | `2fc9615c3a2f101ecc2e7d01a35d5bb67883d58e` | `6ec03db26a43d6669c067e452f6c0098bd2c8051` | intentionally edited; source retained |
| `openwrt/rootfs/www/blazepwifi/cgi-bin/admin-login` | `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/admin-login` | `92d28546045a792413c45fbda60ef6be21a29e3d` | `92d28546045a792413c45fbda60ef6be21a29e3d` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/cgi-bin/admin-logout` | `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/admin-logout` | `dfc35c4bd77a8b86f3eb2355684d5f1edb90daa8` | `dfc35c4bd77a8b86f3eb2355684d5f1edb90daa8` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/cgi-bin/admin-session` | `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/admin-session` | `00ecb12446fd4a55b8ad206f796eef6e94276e84` | `00ecb12446fd4a55b8ad206f796eef6e94276e84` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/cgi-bin/api` | `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/api` | `a59c0080c04cdb6bd8fd830b623bdc62640fb6a5` | `fabbd6fb28a34c162fb40403aec2a40d6fe1a65b` | intentionally edited; source retained |
| `openwrt/rootfs/www/blazepwifi/cgi-bin/rental` | `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/rental` | `644d2c0a16f084f2ce98560d7008b0f20fdd30ff` | `644d2c0a16f084f2ce98560d7008b0f20fdd30ff` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/cgi-bin/vendo` | `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo` | `db58041c0575ad0a1101d99cb85403e03c8dcb22` | `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e` | intentionally edited; source retained |
| `openwrt/rootfs/www/blazepwifi/connecttest.txt` | `Pisowifi/openwrt/rootfs/www/blazepwifi/connecttest.txt` | `1a64fdd7a5ed97571bf98ac6517741f358810c50` | `1a64fdd7a5ed97571bf98ac6517741f358810c50` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/games.html` | `Pisowifi/openwrt/rootfs/www/blazepwifi/games.html` | `0ad4532d7853aab7ccbe0143b2ad9f53d2c294ea` | `0ad4532d7853aab7ccbe0143b2ad9f53d2c294ea` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/generate_204` | `Pisowifi/openwrt/rootfs/www/blazepwifi/generate_204` | `1a64fdd7a5ed97571bf98ac6517741f358810c50` | `1a64fdd7a5ed97571bf98ac6517741f358810c50` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/hotspot-detect.html` | `Pisowifi/openwrt/rootfs/www/blazepwifi/hotspot-detect.html` | `1a64fdd7a5ed97571bf98ac6517741f358810c50` | `1a64fdd7a5ed97571bf98ac6517741f358810c50` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/index.html` | `Pisowifi/openwrt/rootfs/www/blazepwifi/index.html` | `8a1deecedc3b672b5f5441aae0a4a899bed7b343` | `8a1deecedc3b672b5f5441aae0a4a899bed7b343` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/media.html` | `Pisowifi/openwrt/rootfs/www/blazepwifi/media.html` | `ad4074f409eb041eb492410c68ae640264df0828` | `ad4074f409eb041eb492410c68ae640264df0828` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/ncsi.txt` | `Pisowifi/openwrt/rootfs/www/blazepwifi/ncsi.txt` | `1a64fdd7a5ed97571bf98ac6517741f358810c50` | `1a64fdd7a5ed97571bf98ac6517741f358810c50` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/portal-editor.html` | `Pisowifi/openwrt/rootfs/www/blazepwifi/portal-editor.html` | `bb2a4ab2387e4ef30170b026391fd4bcfcf5f0f4` | `bb2a4ab2387e4ef30170b026391fd4bcfcf5f0f4` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/vendor/blazefusion/blaze-fusion.css` | `Pisowifi/openwrt/rootfs/www/blazepwifi/vendor/blazefusion/blaze-fusion.css` | `2183a469834855275c798c11d6b2dab499a1d372` | `2183a469834855275c798c11d6b2dab499a1d372` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/vendor/blazefusion/blaze-fusion.js` | `Pisowifi/openwrt/rootfs/www/blazepwifi/vendor/blazefusion/blaze-fusion.js` | `e106597dbe4a7a3a610128909af100a9bf865250` | `e106597dbe4a7a3a610128909af100a9bf865250` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/vendor/qrcode/LICENSE` | `Pisowifi/openwrt/rootfs/www/blazepwifi/vendor/qrcode/LICENSE` | `150770c0fc2994865ccdbef6662735cc083e780d` | `150770c0fc2994865ccdbef6662735cc083e780d` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/vendor/qrcode/qrcode.js` | `Pisowifi/openwrt/rootfs/www/blazepwifi/vendor/qrcode/qrcode.js` | `df13f829bf41f36b82f0ed85751ed3b4c39cfeb8` | `df13f829bf41f36b82f0ed85751ed3b4c39cfeb8` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/vendor/tailadmin/blaze-tailadmin.css` | `Pisowifi/openwrt/rootfs/www/blazepwifi/vendor/tailadmin/blaze-tailadmin.css` | `a6f69f49f67bd16f9d6920c178a324d662de4166` | `a6f69f49f67bd16f9d6920c178a324d662de4166` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/vendor/tailadmin/LICENSE` | `Pisowifi/openwrt/rootfs/www/blazepwifi/vendor/tailadmin/LICENSE` | `cb92d4176b21b0594e5a6caf94d79340505e3d33` | `cb92d4176b21b0594e5a6caf94d79340505e3d33` | copied unchanged; source retained |
| `openwrt/rootfs/www/blazepwifi/vendor/tailadmin/NOTICE.md` | `Pisowifi/openwrt/rootfs/www/blazepwifi/vendor/tailadmin/NOTICE.md` | `f0425bbbe34c1227311098173b1eae0c3e2a807b` | `f0425bbbe34c1227311098173b1eae0c3e2a807b` | copied unchanged; source retained |

## Migrated original tests

| Original source path | New destination path | Source Git blob SHA | Destination Git blob SHA | Migration status |
|---|---|---|---|---|
| `tests/config.sh` | `Pisowifi/tests/config.sh` | `a42a7d5ef27169f5aa72e7bf8d19b8637fbd3d80` | `d585b772538030bac20400197a981639eb3dd4b2` | intentionally edited; source retained |
| `tests/integration.sh` | `Pisowifi/tests/integration.sh` | `f6e98112da059f0c853fbfc90ebc70192f78c692` | `557b4d3d5d8478811ad057eb59a2d9ecf5c3a6a5` | intentionally edited; source retained |
| `tests/portal.sh` | `Pisowifi/tests/portal.sh` | `71b3c9622f51a80dc09a446389ba6faa001b7897` | `71b3c9622f51a80dc09a446389ba6faa001b7897` | copied unchanged; source retained |
| `tests/security.sh` | `Pisowifi/tests/security.sh` | `bd40ccbd7c0c339bce6128c7b19f1467316d6fc4` | `bd40ccbd7c0c339bce6128c7b19f1467316d6fc4` | copied unchanged; source retained |

## New or separately derived fixtures (not copied from the original snapshot)

These source-linked test fixtures were generated/reworked on the draft branch; they are not misrepresented as unchanged upstream source copies.

| Destination file | Current recorded Git blob SHA | Status |
|---|---|---|
| `Pisowifi/tests/nft_atomic_setup.sh` | `34f0e4cf60565b9c6978fb6d9cdce999af62d1db` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/nft_shutdown_guard.sh` | `96f164d65cc9ab5047141c72808b89f3f7984fb7` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/nft_membership_failclosed.sh` | `9f27d228b3b6a8677902e26d9d91a689b4c60ec8` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/nft_account_binding_guard.sh` | `a7ee6a2ce2459c02ce7f83eef05f4b384092ad09` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/capabilities.sh` | `542c68807b29fdd67bb1220b61e343daf5db88dd` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/config_faults.sh` | `8e8053f709d53e78cef154ee9b6d0242075bebf7` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/config_fixture_smoke.sh` | `a17f2e7885087a2c30d0a8e9c8d45098f28579b3` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/run_focus.sh` | `fa1f4f2c6393504499d50659d8bf980caf7ff85b` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/config_concurrency.sh` | `f8eaa2c0bc3cd1018942fe4bed7511a65db1118d` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/admin_config_result.sh` | `975b3245d078e33faa54f22ac9fb5af0bfe49cf0` | locally derived; source retained where applicable; CI NOT_RUN |
| `Pisowifi/tests/config_apply_failclosed.sh` | `e6a6af64999769d5481506e7ee64e3934f4ae909` | locally derived; source retained where applicable; CI NOT_RUN |

| `Pisowifi/tests/bootstrap_and_cli_auth_guard.sh` | `1bb5aa0072084ad6f0b24e118bb07ad2b597213a` | locally authored CLI auth REQUEST_METHOD isolation and 99-blazepwifi fail-closed CSPRNG regression |
| `Pisowifi/tests/member_receipt_failure_atomicity.sh` | `19dfc3cc50e1884b30e62cf0e71a5d02f123979b` | locally authored #31 receipt-failure regression (formerly expected-RED `member_crash_atomicity_red.sh`); dash PASS, CI PENDING |
| `Pisowifi/tests/member_txn_journal.sh` | `01dc9c65ae9d74eaafb403d47aebcd20edd14390` | locally authored #31 journal crash-injection suite (simulated faults only); dash PASS, CI PENDING |

## Other provenance

- `Pisowifi/LICENSE` is the imported first-party license, recorded as blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- `Pisowifi/README.md`, this map, and `AUDIT_PASS_*.md` are documentation created on the destination branch, not copies of the OpenWrt runtime source.
- Later edits require updating the destination Git blob SHA and marking the row *intentionally edited*, while preserving the original source blob SHA.
- No customer configuration, credential material, installed binaries, account databases or signing keys are authorized as migration inputs.
- Real OpenWrt image/build/package sources remain outside the recovered 61-file overlay. DO NOT equate rootfs recovery with a bootable image.
- Any unverified file or test remains **NO-GO**. No release, merge, flashing or payment acceptance.

## 2026-11-15 CORE candidate reconciliation (draft, NO-GO)

- Historical source blob 54bdc59949884bd3e734f8c07ddeb1d7c2cf9848 is retained in Experiments and in the provenance field above. Destination controller source changed to 69be1941c66cb619a342785f16177458aedac75e to initialize unknown controllers with `enabled=0` and `coin_enabled=0`, and to match identity using literal TSV field equality instead of a regex. The new disposable regression is `Pisowifi/tests/controller_registration_defaults.sh` (blob 169791816bb2d9633c8216762224728c5aa11ef8); it is invoked by `run_focus.sh`.
- This is deliberately **not** a wholesale port of the newer CORE controller admission lock, finance ledger or response-authentication stack. Reconcile those differences with the owner of Experiments PR #252 and independent QA before any integration. No commercial financial admission, migration, flash or release is authorized.

### 2026-11-15 controller registry copy failure correction (CORE draft)

- GitHub Actions [test-first RED #43633308345](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43633308345) on `2c7a2e32b0a106a8ab1e7ffec4c2dca2af21fcc1` exercised a real sourced `bp_controller_set` with fault-injected `awk`. Old `bp_controller_write` returned success after failed copy and could replace a multi-controller registry with an incomplete row. The new controller source Git blob `a75d4776e50f91d375c9e4361b0d73bd8e68ab7a` refuses the incomplete copy and checks every append, chmod, rename and durability step before acknowledging. The same test is still disposable `/tmp` mocked-sync only; physical flash/power-loss acceptance remains NO-GO.

### 2026-11-15 concurrent controller registration containment (PHX-CORE draft)

- Actual source test-first [CI RED #43634427828](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43634427828) at `fc039686e1e4b9e312e708d833df83c09e0472f4`: two first-time heartbeats returned duplicate rows for one identity in `controllers.tsv` (a delayed real `awk` lookup, no financial or hardware simulation).
- This patch introduces the fd4 `controller-admission.lock` file path used by existing Experiments CORE PR #252 and locks both first-time ensure and admin read/modify/write. Locking the registry does not port CORE's paid-admission predicate, ambiguous-write barriers, off-device witness, protected signer or flash proof. The source snapshot is preserved; the new derived destination blob is `3219f99b02556eddced4bccd644a13baa0633260`.
