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

---

## 3. Automated Verification

Run the contract verification suite:
```sh
python3 Shared/tests/test_shared_contracts.py
```
Validates JSON schema syntax and verifies that all SHA-256 golden digests match mathematical calculations.
