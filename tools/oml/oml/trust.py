"""Reviewer registry and computed trust."""

from __future__ import annotations

import json
from pathlib import Path

from .config import Config

REVIEW_SCOPES = ("statement", "evidence", "discriminators", "sources")


def load_reviewers(config: Config) -> dict:
    path = config.root / "reviewers" / "registry.json"
    if not path.is_file():
        return {"thresholds": {"high": 1.0, "medium": 0.5}, "reviewers": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_schemes(config: Config) -> dict[str, dict]:
    path = config.root / "schemes" / "registry.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {s["name"]: s for s in data.get("schemes", [])}


def reviewer_id(review: dict) -> str | None:
    """Map a review's `by` to a registry id.

    human: the durable handle inside parentheses, e.g. "Vikram Maram (github:vikram-learnco)" -> github:vikram-learnco.
    model: the `by` string itself. attested: the fixed id "attested".
    """
    kind = review.get("kind")
    by = review.get("by")
    if kind == "attested":
        return "attested"
    if not isinstance(by, str):
        return None
    if kind == "human":
        if "(" in by and by.rstrip().endswith(")"):
            return by[by.rindex("(") + 1 : -1].strip()
        return by.strip()
    return by.strip()


def compute_trust(record: dict, registry: dict) -> str:
    weights = {r["id"]: float(r.get("weight", 0)) for r in registry.get("reviewers", [])}
    thresholds = registry.get("thresholds", {})
    high = float(thresholds.get("high", 1.0))
    medium = float(thresholds.get("medium", 0.5))
    score = 0.0
    for review in record.get("reviews", []) or []:
        if review.get("verdict") != "accept":
            continue
        rid = reviewer_id(review)
        if rid in weights:
            score += weights[rid]
    if score >= high:
        return "high"
    if score >= medium:
        return "medium"
    return "low"


def write_trust(config: Config, check_only: bool = False) -> tuple[int, list[Path]]:
    """Set `trust` on every record. Returns (records seen, records changed)."""
    from .loader import load_records

    registry = load_reviewers(config)
    changed: list[Path] = []
    records = load_records(config.records_dir)
    for rec in records:
        if not rec.data:
            continue
        expected = compute_trust(rec.data, registry)
        if rec.data.get("trust") != expected:
            changed.append(rec.path)
            if not check_only:
                data = dict(rec.data)
                data["trust"] = expected
                # keep key order stable: put trust right after status
                ordered = {}
                for k, v in data.items():
                    if k == "trust":
                        continue
                    ordered[k] = v
                    if k == "status":
                        ordered["trust"] = expected
                if "trust" not in ordered:
                    ordered["trust"] = expected
                rec.path.write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(records), changed
