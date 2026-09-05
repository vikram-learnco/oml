"""Schema validation plus the cross-record checks the schema cannot express."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .config import Config
from .loader import LoadedRecord, expected_id_for_path, load_records

CONCEPT_RELATIONS = {"conflicts_with", "resolved_by"}
MISCONCEPTION_RELATIONS = {"confusable_with", "specializes"}
RELATION_KEYS = CONCEPT_RELATIONS | MISCONCEPTION_RELATIONS
SYMMETRIC_RELATIONS = {"confusable_with"}


@dataclass
class Problem:
    path: Path
    message: str
    level: str = "error"  # error | warning

    def __str__(self) -> str:
        return f"{self.level}: {self.path}: {self.message}"


@dataclass
class Report:
    checked: int = 0
    problems: list[Problem] = field(default_factory=list)

    @property
    def errors(self) -> list[Problem]:
        return [p for p in self.problems if p.level == "error"]

    @property
    def warnings(self) -> list[Problem]:
        return [p for p in self.problems if p.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        return (
            f"{self.checked} records checked / {len(self.errors)} errors"
            + (f" / {len(self.warnings)} warnings" if self.warnings else "")
        )


def load_schema(config: Config, name: str = "oml-record.schema.json") -> Draft202012Validator:
    schema = json.loads((config.schema_dir / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _relation_targets(record: dict):
    relations = record.get("relations")
    if not isinstance(relations, dict):
        return
    for key, targets in relations.items():
        if not isinstance(targets, list):
            continue
        for target in targets:
            yield key, target


def validate_records(
    target: Path,
    config: Config,
    *,
    all_records_dir: Path | None = None,
) -> Report:
    """Validate every record under `target`.

    Relation targets are resolved against `all_records_dir` (default: the
    repo's records/ directory) so a single file can be validated in context.
    """
    report = Report()
    validator = load_schema(config)
    records = load_records(target)
    report.checked = len(records)

    corpus_dir = all_records_dir or config.records_dir
    corpus = load_records(corpus_dir) if corpus_dir.exists() else []
    known_ids = {r.id for r in corpus if r.id} | {r.id for r in records if r.id}

    seen_uuids: dict[str, Path] = {}
    seen_ids: dict[str, Path] = {}
    for r in corpus:
        if r.data:
            uuid = r.data.get("uuid")
            if isinstance(uuid, str):
                seen_uuids.setdefault(uuid, r.path)
            if r.id:
                seen_ids.setdefault(r.id, r.path)

    corpus_by_id: dict[str, dict] = {r.id: r.data for r in corpus if r.id and r.data}
    for r in records:
        if r.id and r.data:
            corpus_by_id.setdefault(r.id, r.data)

    for rec in records:
        _validate_one(rec, config, validator, known_ids, corpus_by_id, seen_uuids, seen_ids, report)

    return report


def _validate_one(
    rec: LoadedRecord,
    config: Config,
    validator: Draft202012Validator,
    known_ids: set[str],
    corpus_by_id: dict[str, dict],
    seen_uuids: dict[str, Path],
    seen_ids: dict[str, Path],
    report: Report,
) -> None:
    path = rec.path
    if rec.error or rec.data is None:
        report.problems.append(Problem(path, rec.error or "could not load"))
        return
    data = rec.data

    schema_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    for err in schema_errors:
        where = "/".join(str(p) for p in err.absolute_path) or "<root>"
        report.problems.append(Problem(path, f"schema: {where}: {err.message}"))
    if schema_errors:
        # Continue with the structural checks that still make sense.
        pass

    record_id = data.get("id")
    if not isinstance(record_id, str):
        return

    # id <-> filename/directory
    expected = expected_id_for_path(path, config.records_dir)
    if expected is not None and expected != record_id:
        report.problems.append(
            Problem(path, f"id {record_id!r} does not match path (expected {expected!r})")
        )

    # domain <-> first id segment
    domain = data.get("domain")
    if isinstance(domain, str) and domain.split(".")[0] != record_id.split(".")[0]:
        report.problems.append(
            Problem(path, f"domain {domain!r} does not match first segment of id {record_id!r}")
        )

    # uri == base + /m/ + id
    expected_uri = config.record_uri(record_id)
    if data.get("uri") != expected_uri:
        report.problems.append(Problem(path, f"uri must be {expected_uri!r}, got {data.get('uri')!r}"))

    # uuid unique
    uuid = data.get("uuid")
    if isinstance(uuid, str):
        other = seen_uuids.get(uuid)
        if other is not None and other.resolve() != path.resolve():
            report.problems.append(Problem(path, f"uuid {uuid} already used by {other}"))
        seen_uuids.setdefault(uuid, path)

    # id unique
    other = seen_ids.get(record_id)
    if other is not None and other.resolve() != path.resolve():
        report.problems.append(Problem(path, f"id {record_id!r} already used by {other}"))
    seen_ids.setdefault(record_id, path)

    # relations resolve
    for key, target in _relation_targets(data):
        if key not in RELATION_KEYS:
            report.problems.append(Problem(path, f"relations.{key}: unknown relation type (allowed: {sorted(RELATION_KEYS)})"))
            continue
        if key in MISCONCEPTION_RELATIONS:
            if not isinstance(target, str):
                report.problems.append(Problem(path, f"relations.{key}: targets must be OML record ids"))
            elif target == record_id:
                report.problems.append(Problem(path, f"relations.{key}: record points at itself"))
            elif target not in known_ids:
                report.problems.append(Problem(path, f"relations.{key}: target {target!r} is not a record in the repo"))
            elif key in SYMMETRIC_RELATIONS:
                other = corpus_by_id.get(target)
                if other is not None:
                    reverse = ((other.get("relations") or {}).get(key) or [])
                    if record_id not in reverse:
                        report.problems.append(
                            Problem(path, f"relations.{key}: {target!r} does not list {record_id!r} back (relation is symmetric)", "warning")
                        )
        else:  # concept relations: external URIs only
            if not (isinstance(target, dict) and target.get("external")):
                report.problems.append(
                    Problem(path, f"relations.{key}: targets are concepts and must be {{\"external\": \"<uri>\"}}")
                )

    # about: OML-scheme URIs live under <base>/c/
    for entry in data.get("about", []) or []:
        if isinstance(entry, dict) and entry.get("scheme") == "OML":
            uri = str(entry.get("uri", ""))
            if not uri.startswith(config.base_uri + "/c/"):
                report.problems.append(Problem(path, f"about: OML concept URI must start with {config.base_uri}/c/ (got {uri!r})"))

    # discriminators.vs keys resolve
    vs = (data.get("discriminators") or {}).get("vs") if isinstance(data.get("discriminators"), dict) else None
    if isinstance(vs, dict):
        for neighbour in vs:
            if neighbour == record_id:
                report.problems.append(Problem(path, "discriminators.vs: record points at itself"))
            elif neighbour not in known_ids:
                report.problems.append(
                    Problem(path, f"discriminators.vs: {neighbour!r} is not a record in the repo")
                )

    # history targets resolve
    history = data.get("history") if isinstance(data.get("history"), dict) else {}
    merged_into = history.get("merged_into")
    if isinstance(merged_into, str) and merged_into not in known_ids:
        report.problems.append(Problem(path, f"history.merged_into: {merged_into!r} is not a record in the repo"))
    for old in history.get("supersedes", []) or []:
        if isinstance(old, str) and old not in known_ids:
            report.problems.append(Problem(path, f"history.supersedes: {old!r} is not a record in the repo", "warning"))

    # status rules (schema enforces presence; enforce non-emptiness here)
    status = data.get("status")
    if status == "reviewed":
        review = data.get("review")
        if not isinstance(review, dict) or not review.get("reviewer") or not review.get("date"):
            report.problems.append(Problem(path, "status 'reviewed' requires a non-empty review block"))
    if status == "merged" and not merged_into:
        report.problems.append(Problem(path, "status 'merged' requires history.merged_into"))
    if status == "deprecated" and not history.get("deprecated_reason"):
        report.problems.append(Problem(path, "status 'deprecated' should give history.deprecated_reason", "warning"))

    # at least one example
    patterns = data.get("evidence_patterns")
    if isinstance(patterns, list):
        if not any(isinstance(p, dict) and isinstance(p.get("example"), dict) for p in patterns):
            report.problems.append(Problem(path, "at least one evidence_patterns[].example is required"))

    # provenance non-empty
    prov = data.get("provenance")
    if isinstance(prov, dict) and not prov.get("sources"):
        report.problems.append(Problem(path, "provenance.sources must not be empty"))

    # license matches config
    if data.get("license") != config.license:
        report.problems.append(Problem(path, f"license must be {config.license!r}"))


def validate_diagnosis(path: Path, config: Config) -> Report:
    """Validate a diagnosis record file against the diagnosis schema."""
    report = Report(checked=1)
    validator = load_schema(config, "diagnosis-record.schema.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.problems.append(Problem(path, f"invalid JSON: {exc}"))
        return report
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.absolute_path) or "<root>"
        report.problems.append(Problem(path, f"schema: {where}: {err.message}"))
    return report
