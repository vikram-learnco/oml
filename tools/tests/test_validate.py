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
    for name in ("reviewers", "schemes"):
        dst = records_dir.parent / name / "registry.json"
        dst.parent.mkdir(exist_ok=True)
        src = ROOT / name / "registry.json"
        if not dst.exists() or dst.read_text() != src.read_text():
            dst.write_text(src.read_text())
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

    def test_reviewed_with_model_only(self):
        self.assertProblem("frac.model-only.json", "human review")

    def test_hand_typed_trust(self):
        self.assertProblem("frac.hand-trust.json", "trust must be")

    def test_human_review_needs_handle(self):
        self.assertProblem("frac.no-handle.json", "durable handle")

    def test_unregistered_reviewer_cannot_accept(self):
        self.assertProblem("frac.unregistered-reviewer.json", "not in reviewers/registry.json")

    def test_disputed_needs_a_linked_dispute(self):
        self.assertProblem("frac.disputed-no-link.json", "disputes")

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
        proc = self.run_cli("validate", "records/", "--strict", cwd=ROOT)
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


class SymmetricRelations(unittest.TestCase):
    def test_missing_reverse_confusable_with_warns(self):
        import copy
        import tempfile

        good = FIXTURES / "good" / "records" / "math"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "records" / "math").mkdir(parents=True)
            (root / "oml.config.json").write_text((ROOT / "oml.config.json").read_text())
            a = json.loads((good / "frac.add-across.json").read_text())
            b = json.loads((good / "frac.add-numerators-keep-denominator.json").read_text())
            b = copy.deepcopy(b)
            b["relations"].pop("confusable_with", None)
            (root / "reviewers").mkdir()
            (root / "reviewers" / "registry.json").write_text((ROOT / "reviewers" / "registry.json").read_text())
            (root / "schemes").mkdir()
            (root / "schemes" / "registry.json").write_text((ROOT / "schemes" / "registry.json").read_text())
            (root / "records" / "math" / "frac.add-across.json").write_text(json.dumps(a))
            (root / "records" / "math" / "frac.add-numerators-keep-denominator.json").write_text(json.dumps(b))
            cfg = fixture_config(root / "records")
            report = validate_records(root / "records", cfg)
            self.assertTrue(report.ok, [str(p) for p in report.errors])
            self.assertTrue(any("symmetric" in w.message for w in report.warnings), [str(w) for w in report.warnings])


class TrustComputation(unittest.TestCase):
    def test_record_one_is_high_and_drafts_are_low(self):
        from oml.trust import compute_trust, load_reviewers

        reg = load_reviewers(Config.load(ROOT))
        one = json.loads((ROOT / "records" / "math" / "frac.add-across.json").read_text())
        self.assertEqual(compute_trust(one, reg), "high")
        stub = json.loads((ROOT / "records" / "math" / "frac.add-numerators-keep-denominator.json").read_text())
        self.assertEqual(compute_trust(stub, reg), "low")

    def test_trust_check_is_clean(self):
        proc = subprocess.run([sys.executable, "-m", "oml", "trust", "--check"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class DuplicateDetection(unittest.TestCase):
    """The duplicate check must fire on a restatement and stay quiet otherwise."""

    def setUp(self):
        self.records = [json.loads(f.read_text()) for f in sorted((ROOT / "records").rglob("*.json"))]
        self.original = next(r for r in self.records if r["id"] == "math.frac.add-across")

    def _twin(self, **overrides):
        import copy

        twin = copy.deepcopy(self.original)
        twin["id"] = "math.frac.add-tops-and-bottoms"
        twin["statement"] = "Fractions are added by adding the numerators together and adding the denominators."
        twin["relations"] = {}
        twin["discriminators"] = {"vs_slip": "unchanged"}
        twin.update(overrides)
        return twin

    def test_live_corpus_is_clean(self):
        from oml.duplicates import find_duplicates

        self.assertEqual(find_duplicates(self.records), [])

    def test_restatement_is_reported(self):
        from oml.duplicates import find_duplicates

        pairs = find_duplicates(self.records + [self._twin()])
        self.assertEqual([(p.left, p.right) for p in pairs], [("math.frac.add-across", "math.frac.add-tops-and-bottoms")])

    def test_declared_neighbour_is_not_reported(self):
        from oml.duplicates import find_duplicates

        twin = self._twin(relations={"confusable_with": ["math.frac.add-across"]})
        self.assertEqual(find_duplicates(self.records + [twin]), [])

    def test_discriminator_also_counts_as_declaring(self):
        from oml.duplicates import find_duplicates

        twin = self._twin(discriminators={"vs_slip": "x", "vs": {"math.frac.add-across": "differs by ..."}})
        self.assertEqual(find_duplicates(self.records + [twin]), [])

    def test_other_domains_are_not_compared(self):
        from oml.duplicates import find_duplicates

        twin = self._twin(id="prog.frac.add-tops-and-bottoms")
        self.assertEqual(find_duplicates(self.records + [twin]), [])

    def test_threshold_has_headroom_over_the_live_corpus(self):
        """No real pair sits near the threshold, so the check has room to tighten."""
        from oml.duplicates import DEFAULT_THRESHOLD, declared_neighbours, similarity

        worst = 0.0
        for i, left in enumerate(self.records):
            for right in self.records[i + 1 :]:
                if left["id"].split(".")[0] != right["id"].split(".")[0]:
                    continue
                if right["id"] in declared_neighbours(left) or left["id"] in declared_neighbours(right):
                    continue
                worst = max(worst, similarity(left["statement"], right["statement"]))
        self.assertLess(worst, DEFAULT_THRESHOLD - 0.2, f"closest undeclared pair scores {worst:.2f}")


class RebaseUri(unittest.TestCase):
    """A base-URI move rewrites the public ID of every record, so it must be total.

    These run against a throwaway copy of the repo: the operation edits records
    in place, and a half-applied rewrite is exactly the failure being guarded
    against.
    """

    def setUp(self):
        import shutil
        import tempfile

        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "repo"
        self.root.mkdir()
        for name in ("oml.config.json", "records", "schema", "schemes", "reviewers"):
            src = ROOT / name
            dst = self.root / name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy(src, dst)
        self.config = Config.load(self.root)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _read(self, rel):
        return json.loads((self.root / rel).read_text())

    def test_rewrites_every_kind_of_reference(self):
        from oml.rebase import rebase

        new = "https://openmisconceptions.example"
        report = rebase(self.config, new)
        self.assertGreater(report.occurrences, 100, "expected a corpus-wide rewrite")

        record = self._read("records/math/frac.add-across.json")
        self.assertTrue(record["uri"].startswith(new), "record uri not rewritten")
        self.assertEqual(self._read("oml.config.json")["base_uri"], new)
        self.assertTrue(self._read("schema/oml-record.schema.json")["$id"].startswith(new))

        # Concept URIs live in about[] and in relations.*[].external.
        prog = self._read("records/prog/var.assignment-is-equation.json")
        self.assertTrue(prog["about"][0]["uri"].startswith(new))
        self.assertTrue(prog["relations"]["conflicts_with"][0]["external"].startswith(new))

    def test_scheme_registry_regex_is_rewritten(self):
        """Regression: the OML pattern stores the host regex-escaped.

        Plain text substitution misses `oml\\.learnco\\.io`, leaving the OML
        scheme matching the old host. That surfaced as a warning on every
        record carrying an OML concept URI, which blocks CI under --strict.
        """
        from oml.rebase import rebase

        new = "https://openmisconceptions.example"
        rebase(self.config, new)
        pattern = next(
            s["uri_pattern"] for s in self._read("schemes/registry.json")["schemes"] if s["name"] == "OML"
        )
        self.assertNotIn("learnco", pattern)
        self.assertIn("openmisconceptions", pattern)

        # And the rewritten pattern must actually match the rewritten URIs.
        import re

        concept = self._read("records/prog/var.assignment-is-equation.json")["about"][0]["uri"]
        self.assertRegex(concept, pattern)

    def test_rebased_corpus_validates_with_no_warnings(self):
        from oml.rebase import rebase

        rebase(self.config, "https://openmisconceptions.example")
        config = Config.load(self.root)
        config.schema_root = self.root / "schema"
        report = validate_records(config.records_dir, config)
        self.assertEqual(report.errors, [], "\n".join(map(str, report.errors)))
        self.assertEqual(report.warnings, [], "\n".join(map(str, report.warnings)))

    def test_round_trip_leaves_no_residue(self):
        from oml.rebase import rebase

        before = {p: p.read_text() for p in sorted(self.root.rglob("*.json"))}
        rebase(self.config, "https://openmisconceptions.example")
        rebase(Config.load(self.root), "https://oml.learnco.io")
        after = {p: p.read_text() for p in sorted(self.root.rglob("*.json"))}
        changed = [str(p.relative_to(self.root)) for p in before if before[p] != after.get(p)]
        self.assertEqual(changed, [], f"round trip left residue in {changed}")

    def test_rebasing_to_the_same_base_is_a_no_op(self):
        from oml.rebase import rebase

        report = rebase(self.config, self.config.base_uri)
        self.assertEqual(report.changed, [])
