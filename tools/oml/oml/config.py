"""Repository layout and configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from `start` (default: cwd) until a directory holding oml.config.json."""
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "oml.config.json").is_file():
            return candidate
    raise FileNotFoundError("oml.config.json not found in this directory or any parent")


@dataclass
class Config:
    root: Path
    base_uri: str
    library_version: str
    title: str
    creator: str
    license: str
    license_uri: str
    extra: dict = field(default_factory=dict)
    schema_root: Path | None = None

    @classmethod
    def load(cls, root: Path | None = None) -> "Config":
        root = root or find_repo_root()
        raw = json.loads((root / "oml.config.json").read_text(encoding="utf-8"))
        known = {"base_uri", "library_version", "title", "creator", "license", "license_uri"}
        return cls(
            root=root,
            base_uri=raw["base_uri"].rstrip("/"),
            library_version=raw.get("library_version", "0.0.0"),
            title=raw.get("title", "Open Misconception Library"),
            creator=raw.get("creator", ""),
            license=raw.get("license", "CC-BY-4.0"),
            license_uri=raw.get("license_uri", "https://creativecommons.org/licenses/by/4.0/"),
            extra={k: v for k, v in raw.items() if k not in known},
            schema_root=Path(os.environ["OML_SCHEMA_DIR"]) if os.environ.get("OML_SCHEMA_DIR") else None,
        )

    @property
    def records_dir(self) -> Path:
        return self.root / "records"

    @property
    def schema_dir(self) -> Path:
        return self.schema_root or (self.root / "schema")

    @property
    def dist_dir(self) -> Path:
        return self.root / "dist"

    @property
    def site_dir(self) -> Path:
        return self.root / "site"

    def record_uri(self, record_id: str) -> str:
        return f"{self.base_uri}/m/{record_id}"
