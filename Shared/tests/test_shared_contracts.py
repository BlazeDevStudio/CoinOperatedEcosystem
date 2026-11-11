#!/usr/bin/env python3
"""Automated verification test for Blaze Coin Operated Ecosystem Shared Contracts."""
import hashlib
import json
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestSharedContracts(unittest.TestCase):
    def test_controller_signature_vectors(self):
        path = os.path.join(BASE_DIR, "contracts", "controller-signature", "golden_vectors.json")
        self.assertTrue(os.path.isfile(path), f"Missing golden vectors: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for v in data["vectors"]:
            key = v["secret_key"]
            action = v["action"]
            vendo_id = v["vendo_id"]
            nonce = v["request_nonce"]
            pulses = v["pulses"]
            target = v["target"]

            # Validate request base and signature
            calc_req_base = f"{key}|{action}|{vendo_id}|{nonce}|{pulses}|{target}|{key}"
            self.assertEqual(calc_req_base, v["expected_request_base"], f"Mismatch in request base: {v['description']}")
            calc_req_sig = hashlib.sha256(calc_req_base.encode("utf-8")).hexdigest()
            self.assertEqual(calc_req_sig, v["expected_request_sig"], f"Mismatch in request sig: {v['description']}")

            # If vector has response, validate response base and signature
            if "expected_response_base" in v:
                if action == "register":
                    server_time = v["server_time"]
                    calc_resp_base = f"{key}|register|{vendo_id}|{nonce}|{server_time}|{key}"
                elif action == "poll":
                    ins = v["insert"]
                    tgt = v["target_nonce"]
                    exp = v["expires"]
                    calc_resp_base = f"{key}|poll|{vendo_id}|{nonce}|{ins}|{tgt}|{exp}|{key}"
                else:
                    raise ValueError(f"Unknown action: {action}")

                self.assertEqual(calc_resp_base, v["expected_response_base"], f"Mismatch in response base: {v['description']}")
                calc_resp_sig = hashlib.sha256(calc_resp_base.encode("utf-8")).hexdigest()
                self.assertEqual(calc_resp_sig, v["expected_response_sig"], f"Mismatch in response sig: {v['description']}")

        print(f"Controller signature contract: {len(data['vectors'])} golden vectors verified PASS.")

    def test_member_bank_restore_vectors(self):
        path = os.path.join(BASE_DIR, "contracts", "member-bank-restore", "golden_vectors.json")
        self.assertTrue(os.path.isfile(path), f"Missing golden vectors: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for v in data["vectors"]:
            for staged in v["staged_files"]:
                content = staged["content"].encode("utf-8")
                calc_sha = hashlib.sha256(content).hexdigest()
                self.assertEqual(calc_sha, staged["expected_sha256"], f"Mismatch in staged file SHA: {staged['path']}")

            commit_bytes = v["commit_record_format"].encode("utf-8")
            calc_commit_sha = hashlib.sha256(commit_bytes).hexdigest()
            self.assertEqual(calc_commit_sha, v["expected_commit_sha256"], f"Mismatch in commit SHA: {v['description']}")

        print(f"Member bank restore contract: {len(data['vectors'])} golden vectors verified PASS.")

    def test_schema_validity(self):
        schemas = [
            os.path.join(BASE_DIR, "contracts", "controller-signature", "schema_v1.json"),
            os.path.join(BASE_DIR, "contracts", "member-bank-restore", "schema_v1.json"),
            os.path.join(BASE_DIR, "contracts", "router-profile", "schema_v1.json"),
        ]
        for s in schemas:
            self.assertTrue(os.path.isfile(s), f"Missing schema: {s}")
            with open(s, "r", encoding="utf-8") as f:
                obj = json.load(f)
                self.assertIn("$schema", obj)
                self.assertIn("title", obj)
                self.assertIn("type", obj)
        print(f"Schema validity: {len(schemas)} JSON schemas verified valid JSON.")


if __name__ == "__main__":
    unittest.main()
