#!/usr/bin/env python3
"""Verify the contract-only BlazePwifi coin receipt v1 golden vectors."""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VECTOR_PATH = ROOT / "docs" / "contracts" / "COIN_RECEIPT_V1_GOLDEN.json"
FIELD_ORDER = (
    "domain",
    "controller_id",
    "key_version",
    "receipt_id",
    "event_nonce",
    "target_nonce",
    "pulse_count",
    "account_id_hash",
    "ledger_epoch",
    "ledger_sequence",
    "issued_at",
    "expires_at",
    "disposition",
    "reason",
    "credit_delta_centavos",
    "credit_total_centavos",
)
HEX_RE = re.compile(r"^[0-9a-f]+$")
ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{2,96}$")


def canonical_event(fields: dict[str, object]) -> bytes:
    return (
        "blazepwifi-coin-event-v1\n"
        f"controller_id={fields['controller_id']}\n"
        f"event_nonce={fields['event_nonce']}\n"
        f"target_nonce={fields['target_nonce']}\n"
        f"pulse_count={fields['pulse_count']}\n"
    ).encode("ascii")


def canonical_receipt(fields: dict[str, object]) -> bytes:
    if tuple(fields) != FIELD_ORDER:
        raise AssertionError("receipt fields are not in canonical order")
    return "".join(f"{name}={fields[name]}\n" for name in FIELD_ORDER).encode("ascii")


def validate_fields(fields: dict[str, object]) -> None:
    assert fields["domain"] == "blazepwifi-coin-receipt-v1"
    assert ID_RE.fullmatch(str(fields["controller_id"]))
    for name in ("key_version", "pulse_count", "ledger_sequence", "issued_at", "expires_at",
                 "credit_delta_centavos", "credit_total_centavos"):
        value = fields[name]
        assert isinstance(value, int) and str(value) == f"{value:d}" and value >= 0
    assert fields["key_version"] > 0
    assert 1 <= fields["pulse_count"] <= 20
    assert fields["ledger_sequence"] > 0
    assert fields["issued_at"] < fields["expires_at"]
    for name, minimum, maximum in (
        ("receipt_id", 64, 64),
        ("event_nonce", 8, 32),
        ("target_nonce", 8, 32),
        ("account_id_hash", 64, 64),
        ("ledger_epoch", 16, 32),
    ):
        value = str(fields[name])
        assert minimum <= len(value) <= maximum and HEX_RE.fullmatch(value)
    expected_receipt_id = hashlib.sha256(canonical_event(fields)).hexdigest()
    assert fields["receipt_id"] == expected_receipt_id

    disposition = fields["disposition"]
    reason = fields["reason"]
    if disposition == "COMMITTED":
        assert reason in {"CREDIT_COMMITTED", "DUPLICATE_COMMITTED"}
        if reason == "CREDIT_COMMITTED":
            assert fields["credit_delta_centavos"] > 0
        else:
            assert fields["credit_delta_centavos"] == 0
    elif disposition == "REJECTED":
        assert reason in {
            "ACCOUNT_NOT_FOUND",
            "CONTROLLER_DISABLED",
            "EVENT_CONFLICT",
            "TARGET_EXPIRED",
        }
        assert fields["credit_delta_centavos"] == 0
    else:
        raise AssertionError("unknown disposition")


def alternate_value(name: str, value: object) -> object:
    if isinstance(value, int):
        return value + 1
    if name == "disposition":
        return "REJECTED" if value == "COMMITTED" else "COMMITTED"
    if name == "reason":
        return "EVENT_CONFLICT" if value != "EVENT_CONFLICT" else "ACCOUNT_NOT_FOUND"
    text = str(value)
    replacement = "0" if text[-1] != "0" else "1"
    return text[:-1] + replacement


def main() -> None:
    fixture = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    assert fixture["contract"] == "blazepwifi-coin-receipt-v1"
    key = bytes.fromhex(fixture["synthetic_key_hex"])
    assert len(key) == 32
    vectors = fixture["vectors"]
    assert len(vectors) >= 3

    verified: dict[str, dict[str, object]] = {}
    for vector in vectors:
        fields = vector["fields"]
        validate_fields(fields)
        canonical = canonical_receipt(fields)
        assert vector["canonical"] == canonical.decode("ascii")
        expected_mac = hmac.new(key, canonical, hashlib.sha256).hexdigest()
        assert vector["mac"] == expected_mac
        for name in FIELD_ORDER:
            mutated = copy.deepcopy(fields)
            mutated[name] = alternate_value(name, mutated[name])
            mutated_mac = hmac.new(key, canonical_receipt(mutated), hashlib.sha256).hexdigest()
            assert not hmac.compare_digest(mutated_mac, vector["mac"]), name
        verified[vector["name"]] = vector

    first = verified["committed_first"]
    retry = verified["committed_retry"]
    assert retry["fields"] == first["fields"]
    assert retry["canonical"] == first["canonical"]
    assert retry["mac"] == first["mac"]
    print("COIN_RECEIPT_V1_GOLDEN_PASS")


if __name__ == "__main__":
    main()
