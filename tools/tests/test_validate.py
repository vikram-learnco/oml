"""Tests for `oml validate`. Run from the repo root: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from oml.config import Config, find_repo_root
from oml.validate import validate_records

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
ROOT = find_repo_root(HERE)


def fixture_config(records_dir: Path) -> Config:
    """A Config whose records/ points at a fixture corpus but shares the real schema."""
    cfg = Config.load(ROOT)
    cfg.root = records_dir.parent
    cfg.schema_root = ROOT / "schema"
    return cfg


class GoodFixtures(unittest.TestCase):
    def test_good_records_pass(self):
        records = FIXTURES / "good" / "records"
        report = validate_records(records, fixture_config(records))
        self.assertEqual(report.errors, [], "\n".join(map(str, report.errors)))
        self.assertEqual(report.checked, 2)


class BrokenFixtures(unittest.TestCase):
    def setUp(self):
        self.records = FIXTURES / "broken" / "records"
        # Resolve relations against the good corpus so the only failures are the intended ones.
        self.config = fixture_config(FIXTURES / "good" / "records")
        self.report = validate_records(self.records, self.config, all_records_dir=FIXTURES / "good" / "records")
        self.by_file = {}
        for p in self.report.problems:
            self.by_file.setdefault(p.path.name, []).append(p.message)

    def assertProblem(self, filename: str, needle: str):
        msgs = self.by_file.get(filename, [])
        self.assertTrue(any(needle in m for m in msgs), f"{filename}: expected {needle!r} in {msgs}")

    def test_every_broken_fixture_fails(self):
        for path in sorted(self.records.rglob("*.json")):
            self.assertIn(path.name, self.by_file, f"{path.name} should have produced an error")
        self.assertFalse(self.report.ok)

    def test_id_mismatch(self):
        self.assertProblem("frac.id-mismatch.json", "does not match path")

    def test_bad_uri(self):
        self.assertProblem("frac.bad-uri.json", "uri must be")

    def test_duplicate_uuid(self):
        self.assertProblem("frac.dup-uuid.json", "already used by")

    def test_dangling_relation(self):
        self.assertProblem("frac.dangling.json", "is not a record in the repo")

    def test_reviewed_without_review(self):
        self.assertProblem("frac.no-review.json", "review")

    def test_merged_without_target(self):
        self.assertProblem("frac.bad-merge.json", "merged_into")

    def test_no_example_and_bad_kind(self):
        self.assertProblem("frac.no-example.json", "example")
        self.assertProblem("frac.no-example.json", "kind")

    def test_invalid_json(self):
        self.assertProblem("frac.not-json.json", "invalid JSON")


class CliExitCodes(unittest.TestCase):
    def run_cli(self, *args, cwd: Path, env: dict | None = None):
        env = {**os.environ, **(env or {})}
        return subprocess.run(
            [sys.executable, "-m", "oml", *args], cwd=cwd, env=env, capture_output=True, text=True
        )

    def test_real_records_pass(self):
        proc = self.run_cli("validate", "records/", cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("records checked / 0 errors", proc.stdout)

    def test_broken_fixture_exits_nonzero(self):
        proc = self.run_cli(
            "validate", "records/", cwd=FIXTURES / "broken", env={"OML_SCHEMA_DIR": str(ROOT / "schema")}
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("errors", proc.stdout)


class DiagnosisSchema(unittest.TestCase):
    def test_example_diagnosis_validates(self):
        from oml.validate import load_schema

        validator = load_schema(Config.load(ROOT), "diagnosis-record.schema.json")
        doc = {
            "item": "1/2 + 1/3",
            "expected": "5/6",
            "response": "2/5",
            "diagnoses": [{"oml_id": "math.frac.add-across", "confidence": 0.9, "matched_pattern": 0}],
            "oml_version": "0.1.0",
            "engine_version": "example/0.0.1",
        }
        self.assertEqual(list(validator.iter_errors(doc)), [])
        doc["diagnoses"][0]["confidence"] = 1.5
        self.assertTrue(list(validator.iter_errors(doc)))


if __name__ == "__main__":
    unittest.main()
