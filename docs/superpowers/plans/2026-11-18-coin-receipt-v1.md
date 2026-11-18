# Coin Receipt V1 Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an exact, independently verifiable HMAC-SHA256 coin receipt contract without enabling runtime coin acceptance.

**Architecture:** A versioned contract document defines strict ordered serialization. A synthetic JSON fixture carries positive vectors, and a Python standard-library test verifies serialization, HMAC, replay stability, and field-mutation rejection. The existing focused runner invokes the verifier.

**Tech Stack:** Markdown, JSON, Python 3 standard library, POSIX shell test runner.

**Spec:** `docs/superpowers/specs/2026-11-18-coin-receipt-v1-design.md`

## Global Constraints

- Runtime firmware and paid ledger behavior remain unchanged and default-deny.
- No real secrets, production data, live devices, migration, flashing, release, or deployment.
- The receipt is not authoritative until a durable runtime ledger epoch/sequence and independent QA/HARDWARE verification exist.
- Preserve PR #29's draft/stacked status and source provenance.

## Review Focus

- Any single bound field mutation must invalidate the MAC.
- Non-canonical decimal or hexadecimal encodings must be rejected.
- Duplicate event delivery must reproduce the same receipt identity and ledger result.
- Unknown disposition/reason combinations must fail closed.
- Missing runtime epoch/sequence must never be replaced with placeholders.

---

### Task 1: Contract verifier RED

**Files:**
- Create: `Pisowifi/tests/coin_receipt_contract_v1.py`
- Test: `Pisowifi/tests/coin_receipt_contract_v1.py`

**Interfaces:**
- Consumes: `Pisowifi/docs/contracts/COIN_RECEIPT_V1_GOLDEN.json`
- Produces: deterministic contract verification exit status and `COIN_RECEIPT_V1_GOLDEN_PASS` output.

- [ ] Write a standard-library test that loads the absent vector file, validates field grammar/order, recomputes HMAC-SHA256, and checks mutation negatives.
- [ ] Run `python Pisowifi/tests/coin_receipt_contract_v1.py` and verify RED because the vector file does not exist.
- [ ] Commit the test-only RED checkpoint.

### Task 2: Canonical contract and vectors GREEN

**Files:**
- Create: `Pisowifi/docs/contracts/COIN_RECEIPT_V1.md`
- Create: `Pisowifi/docs/contracts/COIN_RECEIPT_V1_GOLDEN.json`
- Test: `Pisowifi/tests/coin_receipt_contract_v1.py`

**Interfaces:**
- Consumes: strict field definitions from the design.
- Produces: fixed canonical bytes and lowercase HMAC-SHA256 positive/negative vectors.

- [ ] Add the exact ordered field schema, grammars, disposition/reason table, replay invariant, and runtime activation gates.
- [ ] Add synthetic committed and rejected receipt vectors with exact canonical messages and MACs.
- [ ] Run `python Pisowifi/tests/coin_receipt_contract_v1.py` and verify PASS.
- [ ] Commit the minimal contract/vector implementation.

### Task 3: Focused runner and provenance

**Files:**
- Modify: `Pisowifi/tests/run_focus.sh`
- Modify: `Pisowifi/MIGRATION_MAP.md`
- Modify: `Pisowifi/SOURCE_INTAKE.json`

**Interfaces:**
- Consumes: Task 2 verifier.
- Produces: CI-visible execution and migration provenance for the new derived files.

- [ ] Invoke the Python verifier from the focused runner after shell fixtures.
- [ ] Record the derived files and explicit contract-only/no-runtime-authority status.
- [ ] Run the Python verifier locally and trigger exact-head repository CI.
- [ ] Record actual CI result without upgrading hardware/production readiness.
