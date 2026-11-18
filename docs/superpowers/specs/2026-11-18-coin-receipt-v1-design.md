# Coin Receipt V1 Contract Design

## Intent

Define the canonical authenticated receipt that a future BlazePwifi controller may verify after a coin POST. This closes the current producer/consumer specification gap while keeping every runtime path default-deny until CORE, QA, and HARDWARE independently implement and verify the contract.

## Goals

- Bind controller, key version, event and target nonces, pulse count, account binding, ledger epoch and sequence, timestamps, disposition, reason, and credited totals.
- Use ordered ASCII serialization and HMAC-SHA256 with synthetic golden vectors.
- Make an identical event replay produce the same receipt identity and authoritative ledger result.
- Provide mutation-negative tests for every security-relevant field.

## Non-goals and anti-goals

- Do not enable `coinPostDispositionVerified()` or any coin relay/output.
- Do not change paid ledger writes, migration state, keys, firmware, or production configuration.
- Do not describe the existing keyed-SHA256 response as HMAC or production authority.
- Do not invent a runtime ledger epoch/sequence; runtime emission remains blocked until those durable values exist.

## Constraints

- Existing PR #29 remains draft and stacked on COE integration PR #26.
- No secrets: all vectors use an explicitly synthetic key.
- No live device, real payment, migration, flash, release, or deployment.
- Preserve legacy response fields for compatibility; this change is contract/test-only.

## Approaches considered

1. Extend the existing `response_sig` immediately. Rejected because it is ad-hoc keyed SHA-256, lacks durable ledger sequence/epoch, and could accidentally authorize current firmware.
2. Add a runtime HMAC receipt with placeholder sequence values. Rejected because fabricated authority metadata is unsafe.
3. Publish a canonical contract plus golden vectors while runtime stays deny-only. Chosen because it is independently testable, establishes the shared interface, and does not weaken financial or hardware gates.

## Chosen contract

The canonical message is UTF-8/ASCII, one `name=value` line per field in a fixed order, terminated by a final newline. Values use strict field-specific grammars; no escaping is allowed. The MAC is lowercase hexadecimal HMAC-SHA256 over the exact bytes. Receipt identity is the SHA-256 event ID derived from the stable controller/event/target tuple; repeated delivery returns the same authoritative receipt fields and MAC.

The implementation in this slice consists only of the contract document, synthetic JSON vectors, and a standard-library verifier/mutation test integrated into the focused test runner. Runtime production is explicitly blocked.
