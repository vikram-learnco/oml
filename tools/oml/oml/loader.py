"""Load OML records from disk."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class LoadedRecord:
    path: Path
    data: dict | None
    error: str | None = None

    @property
    def id(self) -> str | None:
        if isinstance(self.data, dict):
            value = self.data.get("id")
            return value if isinstance(value, str) else None
        return None


def iter_record_files(target: Path) -> Iterator[Path]:
    """Yield record JSON files under `target` (a directory) or `target` itself (a file)."""
    if target.is_file():
        yield target
        return
    for path in sorted(target.rglob("*.json")):
        if path.name.startswith("."):
            continue
        yield path


def load_records(target: Path) -> list[LoadedRecord]:
    out: list[LoadedRecord] = []
    for path in iter_record_files(target):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            out.append(LoadedRecord(path, None, f"invalid JSON: {exc}"))
            continue
        if not isinstance(data, dict):
            out.append(LoadedRecord(path, None, "top level must be an object"))
            continue
        out.append(LoadedRecord(path, data))
    return out


def expected_id_for_path(path: Path, records_dir: Path) -> str | None:
    """`records/math/frac.add-across.json` -> `math.frac.add-across`.

    Resolves against `records_dir` when the file lives under it, otherwise
    against the nearest ancestor directory named `records` (fixture corpora).
    """
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(records_dir.resolve())
    except ValueError:
        parts_all = resolved.parts
        if "records" not in parts_all:
            return None
        idx = len(parts_all) - 1 - parts_all[::-1].index("records")
        rel = Path(*parts_all[idx + 1 :])
    parts = list(rel.parts)
    if not parts or not parts[-1].endswith(".json"):
        return None
    parts[-1] = parts[-1][: -len(".json")]
    return ".".join(parts)
