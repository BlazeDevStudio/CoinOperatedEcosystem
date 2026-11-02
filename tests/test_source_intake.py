"""Executable negative and positive checks for the real intake guard."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.source_intake_guard import IntakeError, audit


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="coe-intake-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        real = Path("inventory/source-intake.json")
        self.doc = json.loads(real.read_text(encoding="utf-8"))
        self.manifest = self.root / "source-intake.json"
        # Reconstruct only the actual checked-in staged files in this disposable
        # test directory. Candidate records must never materialize runtime source.
        for entry in self.doc["entries"]:
            if entry["state"] in ("staged", "refactored"):
                path = self.root / entry["destination_path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(Path(entry["destination_path"]).read_bytes())
                if entry["state"] == "refactored":
                    note = self.root / entry["review_note"]
                    note.parent.mkdir(parents=True, exist_ok=True)
                    note.write_bytes(Path(entry["review_note"]).read_bytes())
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.doc), encoding="utf-8")

    def verify_denied(self):
        with self.assertRaises(IntakeError):
            audit(self.root, self.manifest)

    def test_real_candidate_manifest(self):
        count, staged = audit(self.root, self.manifest)
        self.assertEqual((count, staged), (7, 2))

    def test_unauthorized_production_flag(self):
        self.doc["production_authorized"] = True
        self.save()
        self.verify_denied()

    def test_candidate_cannot_claim_staged_destination(self):
        self.doc["entries"][0]["destination_path"] = "core/finance/ledger.sh"
        self.save()
        self.verify_denied()

    def test_missing_or_invalid_sha(self):
        self.doc["entries"][0]["source_blob_sha"] = "deadbeef"
        self.save()
        self.verify_denied()

    def test_duplicate_identity(self):
        self.doc["entries"].append(copy.deepcopy(self.doc["entries"][0]))
        self.save()
        self.verify_denied()

    def test_duplicate_json_keys(self):
        self.manifest.write_text(
            '{"schema_version":1,"schema_version":1}', encoding="utf-8"
        )
        self.verify_denied()

    def test_cross_module_source_path(self):
        self.doc["entries"][0]["source_path"] = (
            "experiment/openwrt/BlazePwifi/android/LeaseClient.java"
        )
        self.save()
        self.verify_denied()

    def test_third_party_source_without_license_review(self):
        self.doc["entries"][0]["source_repo"] = "unauthorized/fork"
        self.save()
        self.verify_denied()

    def test_unregistered_executable_is_denied(self):
        path = self.root / "core" / "finance" / "unreviewed.sh"
        path.parent.mkdir(parents=True)
        path.write_text("echo unsafe\n", encoding="utf-8")
        self.verify_denied()

    def test_staged_file_must_match_both_hashes(self):
        record = self.doc["entries"][0]
        payload = b"dummy first-party source fixture; not production code\n"
        path = self.root / "core" / "members" / "example.sh"
        path.parent.mkdir(parents=True)
        path.write_bytes(payload)
        record["state"] = "staged"
        record["destination_path"] = "core/members/example.sh"
        record["content_sha256"] = hashlib.sha256(payload).hexdigest()
        record["source_blob_sha"] = hashlib.sha1(
            b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
        ).hexdigest()
        self.save()
        self.assertEqual(audit(self.root, self.manifest), (7, 3))
        path.write_bytes(payload + b"tampered")
        self.verify_denied()

    def test_staged_symlink_is_denied(self):
        record = self.doc["entries"][0]
        payload = b"source fixture\n"
        outside = self.root / "outside.sh"
        outside.write_bytes(payload)
        path = self.root / "core" / "members" / "example.sh"
        path.parent.mkdir(parents=True)
        path.symlink_to(outside)
        record["state"] = "staged"
        record["destination_path"] = "core/members/example.sh"
        record["content_sha256"] = hashlib.sha256(payload).hexdigest()
        record["source_blob_sha"] = hashlib.sha1(
            b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
        ).hexdigest()
        self.save()
        self.verify_denied()

    def test_existing_staged_file_mutation_is_denied(self):
        record = next(
            item for item in self.doc["entries"] if item["state"] in ("staged", "refactored")
        )
        path = self.root / record["destination_path"]
        path.write_bytes(path.read_bytes() + b"#unreviewed modification\n")
        self.verify_denied()

    def test_missing_checked_in_staged_file_is_denied(self):
        record = next(
            item for item in self.doc["entries"] if item["state"] in ("staged", "refactored")
        )
        (self.root / record["destination_path"]).unlink()
        self.verify_denied()

    def test_refactored_requires_valid_upstream_digest(self):
        record = next(e for e in self.doc["entries"] if e["state"] == "refactored")
        record["source_content_sha256"] = "invalid"
        self.save()
        self.verify_denied()

    def test_refactored_missing_review_is_denied(self):
        record = next(e for e in self.doc["entries"] if e["state"] == "refactored")
        (self.root / record["review_note"]).unlink()
        self.verify_denied()

    def test_refactored_cannot_erase_original_sha(self):
        record = next(e for e in self.doc["entries"] if e["state"] == "refactored")
        del record["source_content_sha256"]
        self.save()
        self.verify_denied()

    def test_path_traversal_denied(self):
        record = self.doc["entries"][0]
        record["source_path"] = "../tmp/sneak.sh"
        self.save()
        self.verify_denied()


if __name__ == "__main__":
    unittest.main()
