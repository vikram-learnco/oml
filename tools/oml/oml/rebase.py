"""Move the library to a new base URI.

A record's `uri` is its public identifier, so a base-URI change rewrites the
most load-bearing field in the library. Doing that with `sed` across 100-odd
occurrences invites a partial rewrite that leaves some records pointing at the
old host, so it lives here instead: one command, every affected place, and
`oml validate` proves the result (it already requires `uri == base + "/m/" + id`).

The operation is idempotent and re-runnable, which matters because the move is
expected to happen twice — to a GitHub Pages URL first, then to a permanent
domain once one is chosen.

What it does NOT change: the `oml:` IDs themselves. Only the host that resolves
them moves.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config

# Files outside records/ and schema/ that embed the base URI in prose or metadata.
DOC_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "CITATION.cff",
    ".zenodo.json",
    "dist/README.md",
    "dist/huggingface/README.md",
    "schema/README.md",
    "schemes/registry.json",
)


@dataclass
class RebaseReport:
    old_base: str
    new_base: str
    changed: list[Path] = field(default_factory=list)
    occurrences: int = 0

    def summary(self) -> str:
        return (
            f"{self.old_base} -> {self.new_base}: "
            f"{self.occurrences} occurrences in {len(self.changed)} files"
        )


def _rewrite(path: Path, old: str, new: str, dry_run: bool) -> int:
    """Replace `old` with `new` in a file. Returns the number of occurrences."""
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return 0
    count = text.count(old)
    if count and not dry_run:
        path.write_text(text.replace(old, new), encoding="utf-8")
    return count


def rebase(config: Config, new_base: str, *, dry_run: bool = False) -> RebaseReport:
    old_base = config.base_uri.rstrip("/")
    new_base = new_base.rstrip("/")
    report = RebaseReport(old_base, new_base)
    if old_base == new_base:
        return report

    root = config.root
    targets: list[Path] = [
        root / "oml.config.json",
        *sorted(config.records_dir.rglob("*.json")),
        *sorted(config.schema_dir.glob("*.json")),
        *(root / name for name in DOC_FILES),
        # Test fixtures carry their own copies of the config and of records.
        *sorted((root / "tools" / "tests" / "fixtures").rglob("*.json")),
    ]

    seen: set[Path] = set()
    for path in targets:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        count = _rewrite(path, old_base, new_base, dry_run)
        if path.name == "registry.json" and path.parent.name == "schemes":
            count += _rewrite_scheme_patterns(path, old_base, new_base, dry_run)
        if count:
            report.changed.append(path.relative_to(root))
            report.occurrences += count
    return report


def _rewrite_scheme_patterns(path: Path, old_base: str, new_base: str, dry_run: bool) -> int:
    """Rewrite the base URI inside `schemes/registry.json` regex patterns.

    The pattern stores the host regex-escaped (`oml\\.learnco\\.io`), so a plain
    text replacement of the unescaped base misses it and leaves the OML scheme
    matching the old host — which surfaces as a warning on every record with an
    OML concept URI, and blocks CI under --strict. Rewriting the parsed value
    keeps the escaping correct whatever the new host looks like.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    old_escaped, new_escaped = re.escape(old_base), re.escape(new_base)
    count = 0
    for scheme in data.get("schemes", []):
        pattern = scheme.get("uri_pattern")
        if isinstance(pattern, str) and old_escaped in pattern:
            count += pattern.count(old_escaped)
            scheme["uri_pattern"] = pattern.replace(old_escaped, new_escaped)
    if count and not dry_run:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return count
