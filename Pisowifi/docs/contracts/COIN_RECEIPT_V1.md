# BlazePwifi Coin Receipt V1

Status: **CONTRACT CANDIDATE / TEST VECTORS ONLY / RUNTIME DENY**

This document defines the bytes that CORE proposes for an authenticated coin POST disposition. It does not authorize the current Vendo CGI or ESP firmware to emit, accept, clear, replay, or quarantine a paid event. `coinPostDispositionVerified()` must remain deny-only until independent CORE, QA, and HARDWARE review is complete at pinned source revisions.

## Cryptographic construction

- Domain: `blazepwifi-coin-receipt-v1`.
- MAC: HMAC-SHA256 with the provisioned controller receipt key selected by `key_version`.
- Encoding: ASCII; one `name=value` line per field; LF (`0x0a`) after every line, including the last.
- Field order is fixed exactly as shown below. Unknown, duplicate, missing, reordered, escaped, or non-canonical fields are invalid.
- MAC representation: exactly 64 lowercase hexadecimal characters.
- Request, poll, register, configuration, and receipt keys/domains are separate. Do not reuse the existing keyed-SHA256 `response_sig` construction as this MAC.

```text
domain=blazepwifi-coin-receipt-v1
controller_id=<controller-id>
key_version=<uint32>
receipt_id=<64-lowercase-hex>
event_nonce=<8..32-lowercase-hex>
target_nonce=<8..32-lowercase-hex>
pulse_count=<1..20>
account_id_hash=<64-lowercase-hex>
ledger_epoch=<16..32-lowercase-hex>
ledger_sequence=<uint64-positive>
issued_at=<uint64-unix-seconds>
expires_at=<uint64-unix-seconds>
disposition=<COMMITTED|REJECTED>
reason=<reason-code>
credit_delta_centavos=<uint32>
credit_total_centavos=<uint32>
```

Integers use canonical decimal: `0` or a nonzero digit followed by digits, with no sign, whitespace, or leading zero. `controller_id` is 2..96 characters from `[A-Za-z0-9_.:-]`. `expires_at` must be greater than `issued_at` and accepted only within the separately approved clock-skew policy.

## Stable event and account identities

`receipt_id` is lowercase SHA-256 of this exact event message:

```text
blazepwifi-coin-event-v1
controller_id=<controller-id>
event_nonce=<event-nonce>
target_nonce=<target-nonce>
pulse_count=<pulse-count>
```

The message also ends with LF. `account_id_hash` is lowercase SHA-256 of `blazepwifi-account-v1\ndevice_id=<canonical-device-id>\n`. The raw account/device identifier is not placed in the receipt.

## Ledger and replay invariants

- `ledger_epoch` is a durable installation-ledger identity, not a boot ID, timestamp, path hash, or constant shared by installations.
- `ledger_sequence` is the durable monotonically increasing commit sequence assigned by the money authority. It must be committed atomically with the ledger result represented by the receipt.
- The same `receipt_id` must always return the exact same canonical receipt bytes and MAC. A retry never changes `issued_at`, expiry, sequence, totals, disposition, or reason.
- A different pulse count, target, controller, account, or event nonce is a different event or an `EVENT_CONFLICT`; it must never reuse a committed receipt.
- An accepted `COMMITTED` receipt may clear controller pending state only after the controller durably stores the verified receipt and resulting disposition.
- A verified `REJECTED` receipt may move an event to quarantine only after durable negative-disposition evidence is stored. It must not silently erase the event.
- Missing, expired, unknown-key, malformed, mismatched, rollbacked, or unverifiable receipts remain an operator-reconciliation hold and must not be automatically replayed.

## Dispositions and reasons

| Disposition | Allowed reasons | Required delta |
|---|---|---:|
| `COMMITTED` | `CREDIT_COMMITTED`, `DUPLICATE_COMMITTED` | positive for `CREDIT_COMMITTED`; zero for `DUPLICATE_COMMITTED` |
| `REJECTED` | `ACCOUNT_NOT_FOUND`, `CONTROLLER_DISABLED`, `EVENT_CONFLICT`, `TARGET_EXPIRED` | zero |

Additional reasons require a new reviewed contract revision or an explicitly backward-compatible registry update with new golden vectors. Unknown values fail closed.

## Activation gates

Runtime emission and firmware acceptance stay disabled until all of the following exist and pass independently:

1. durable runtime `ledger_epoch` and atomic `ledger_sequence` implementation;
2. provisioned receipt key identity/version and protected key custody;
3. server storage and exact replay of the canonical receipt;
4. firmware parser, HMAC verifier, freshness/sequence rollback checks, and durable receipt store;
5. positive and every-field mutation-negative QA vectors at pinned producer/consumer SHAs;
6. authorized physical power-cut, relay, coin pulse, reconnect, and soak acceptance.

The synthetic vectors in `COIN_RECEIPT_V1_GOLDEN.json` contain no production secret or account data.
