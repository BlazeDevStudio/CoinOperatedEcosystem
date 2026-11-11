# Dependency Map

Scope: relationships verified from repository contents and PR metadata on 2026-11-11. "Stack" means a chain of draft PRs where each PR's base is the previous PR's head branch.

## 1. Runtime dependencies between products

```mermaid
flowchart LR
    ESP["ESP8266 / ESP32 vendo firmware"] -- "HTTP form + signature (cgi-bin/vendo)" --> PW["Pisowifi OpenWrt core + CGI"]
    ST["Pisonet SoftTimer (Windows)"] -- "optional: member bank/restore via vendo CGI" --> PW
    ST -- "serial CTS/DSR coin pulses (local, required)" --> COIN["Coin acceptor"]
    ST -. "optional HTTP bridge" .-> ESPT["ESP timer board"]
    RA["BlazeRental Android"] -- "HMAC-SHA256 /cgi-bin/rental" --> RS["Rental OpenWrt server"]
    RS -. "optional, not required" .-> PW
    PW --> NFT["nftables per-MAC grants"]
    PW --> STORE[("members.tsv, member-events.tsv, UCI")]
```

Hard rules taken from the repositories' own documents and kept here: SoftTimer works with **no** PisoWiFi/Rental/diskless component; Rental and PisoWiFi are independently deployable; diskless manager is a separate add-on.

## 2. Source-lineage dependencies (what must land before what)

### SoftTimer (linear, verified with `git merge-base --is-ancestor` in `BlazingSystems-Experiments`)

```mermaid
flowchart TD
    A["main v0.4.0 (f4e8a891) - released"] --> B["blazepwifi-v0.6.0-audit-foundation - V2 ack verifier + tests"]
    B --> C["phoenix/pisonet-cts-session-atomic-v2-20261029"]
    C --> D["phoenix/pisonet-native-com-interface-20261030 (PR 255)"]
    D --> E["qa/pisonet-setupapi-hygiene-20261108 (PR 279)"]
    E --> F["qa/pisonet-setupapi-validation-20261111"]
    D -. "side branches, not ancestors of each other" .-> G["cleanup theme-readability (PR 265) -> timer-accounting-invariants (PR 268) / parallel pinned labs (PR 267)"]
    D -. "closed PR 273, reference only" .-> H["optional diskless add-on"]
```

`CoinOperatedEcosystem` PR #17 is a *separate, already-curated* import of this chain (pinned to Experiments `21b065535640…`) with additional fail-closed fixes. It is the destination of record; do not re-import.

### PR stack in `CoinOperatedEcosystem`

```mermaid
flowchart TD
    main["main a6513ab"] --> P1["#1 monorepo structure (docs, lowercase dirs)"]
    P1 --> P3["#3 clean-source-intake gate (via closed #2 branch)"]
    P3 --> P4["#4 pinned component baseline"] --> P5["#5 first byte-verified CORE import"]
    P5 --> P6["#6"] --> P7["#7"] --> P8["#8"] --> P9["#9"] --> P10["#10"] --> P11["#11"]
    P11 --> P12["#12"] --> P14["#14"] --> P15["#15"] --> P16["#16 head d537b30f67"]
    P11 -. "superseded, do not merge" .-> P13["#13"]
    main --> P17["#17 Pisonet SoftTimer"]
    main --> P18["#18 Pisowifi OpenWrt recovery"]
    main --> P19["#19 Rental recovery"]
```

PRs #17, #18, #19 target `main` directly and are independent of the #1–#16 stack. The #1–#16 branches were cut from the initial commit (`b0b0ebc`) and do **not** contain `main`'s `a6513ab` (verified: `main` is not an ancestor of #16's head); #1 → branding anchor (closed #2) → #3 ancestry was verified with `git merge-base --is-ancestor`.

## 3. Overlap / duplication found

| Concern | Locations | Evidence |
|---|---|---|
| OpenWrt core files duplicated and **diverged** | `core/openwrt/rootfs/{etc/init.d/blazepwifi,usr/lib/blazepwifi/capabilities.sh,usr/lib/blazepwifi/config.sh,usr/sbin/blazepwifi-core}` (#5–#16) vs `Pisowifi/openwrt/rootfs/…` (#18) | same relative file names; `capabilities.sh` blobs differ (`16ea0a9e…` vs `098eafbe…`) |
| Case-colliding directory names | `Pisonet/` (`main`, #17) vs `pisonet/` (#1); `Rental/` (#19) vs `rental/` (#1) | `git ls-tree` of #1 and `main`; breaks checkout on case-insensitive filesystems (Windows/macOS) |
| SoftTimer baseline attempted twice | #17 (kept) vs my closed #20 (v0.4.0 import) | #20 closed as superseded, branch kept as reference only |

## 4. Shared services (genuine integration needs only)

| Contract | Producer | Consumers | Present as code? |
|---|---|---|---|
| Controller signature / nonce / replay | PisoWiFi vendo CGI | ESP firmware, SoftTimer | implemented in each; **no shared schema** |
| Member bank/restore/transfer + event id | PisoWiFi | SoftTimer | implemented; **no shared schema** |
| Rental enrollment + lease status | Rental server | Android | implemented in #19; versioned `docs/API_v1.md` |
| Ledger events, idempotency keys, policy revision | none | none | **not defined** |

No shared contracts directory has content. Introduce contracts only when two products must interoperate (member bank/restore and controller signature are the first two candidates).
