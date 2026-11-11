# Blaze Shared Contracts & Interoperability Schemas

This directory contains versioned, language-agnostic data contracts, JSON schemas, and golden test vectors shared across the **Blaze Coin Operated Ecosystem**.

---

## 1. Architectural Boundaries & Dependency Direction

Per [`REPOSITORY_BOUNDARIES.md`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/docs/architecture/REPOSITORY_BOUNDARIES.md) §3 and [`TARGET_STATE.md`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/docs/architecture/TARGET_STATE.md) §3:

```
Shared/contracts  ←  { Pisowifi, Rental, Pisonet SoftTimer, Hardware }
```

- **Dependency Invariant:** Products depend on `Shared/contracts`; `Shared` **never** imports or depends on product source code.
- **Cross-Language Test Vectors:** Every contract includes golden test vectors consumed by each product's native test harness (POSIX `sh`, BusyBox `ash`, C# / .NET, and C++ / Arduino).
- **Financial Rule:** Financial authority stays in the accounting/domain layer; peripheral hardware controllers never decide monetary credit.

---

## 2. Active Contracts

### `contracts/controller-signature/` (V1)
- **Purpose:** Cryptographically signed mutual authentication between OpenWrt router (`/cgi-bin/vendo`) and ESP32/ESP8266 vendo hardware.
- **Components:**
  - [`schema_v1.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/controller-signature/schema_v1.json): Structural contract for signed requests (`action`, `id`, `nonce`, `pulses`, `target`, `sig`) and signed responses (`ok`, `server_time`, `response_sig`, `insert`, `target_nonce`, `expires`).
  - [`golden_vectors.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/controller-signature/golden_vectors.json): Reference test vectors for registration, polling, and coin submission.

### `contracts/member-bank-restore/` (V1)
- **Purpose:** Multi-file atomic transaction commit record and replay format for member balances and audit events.
- **Components:**
  - [`schema_v1.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/member-bank-restore/schema_v1.json): Schema defining atomic commit journal records (`VERSION=1`, multi-file SHA-256 manifest).
  - [`golden_vectors.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/member-bank-restore/golden_vectors.json): Reference test vectors for staged mutations, commit digests, and idempotent roll-forward recovery.

### `contracts/router-profile/` (V1)
- **Purpose:** Router hardware abstraction and isolation schema for OpenWrt deployments.
- **Components:**
  - [`schema_v1.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/router-profile/schema_v1.json): Schema defining hardware profile constraints, sysinfo board/model matching regex, flash/RAM boundaries, and switch/VLAN interface topologies.
  - [`profiles/ew1200g-pro.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/router-profile/profiles/ew1200g-pro.json): Exact profile for Ruijie RG-EW1200G Pro v1.1 (`ramips/mt7621`, 16MB flash, 128MB RAM, DSA switch, 1x WAN, 3x LAN).
  - [`profiles/r281.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/router-profile/profiles/r281.json): Exact profile for Notion R281 (`ramips/mt7621`, 32MB flash, 128MB RAM, DSA switch, 1x WAN, 2x LAN).
  - [`profiles/orangepi-r1-plus-lts.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/router-profile/profiles/orangepi-r1-plus-lts.json): Exact profile for Orange Pi R1 Plus LTS Appliance (`rockchip/arm64`, 4-core, 1GB RAM, eMMC, 2x GbE).
  - [`profiles/x86_64.json`](file:///home/antigravity/BlazeDevStudio/CoinOperatedEcosystem/Shared/contracts/router-profile/profiles/x86_64.json): Exact profile for Generic x86_64 OpenWrt Appliance (`x86/64`, generic switch, 1x WAN, 1x LAN).

---

## 3. Automated Verification

Run the contract verification test suites:
```sh
python3 -m unittest discover -s Shared/tests -p 'test_*.py' -v
```
Validates JSON schema syntax, verifies that all SHA-256 golden digests match mathematical calculations, and ensures all router hardware profiles conform to memory, flash, and VLAN topology invariants.

