"""`oml` command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import Config


def _cmd_validate(args: argparse.Namespace) -> int:
    from .validate import validate_records

    config = Config.load()
    target = Path(args.target) if args.target else config.records_dir
    if not target.exists():
        print(f"error: {target} does not exist", file=sys.stderr)
        return 2
    report = validate_records(target, config)
    for problem in report.problems:
        print(problem, file=sys.stderr)
    print(report.summary())
    if args.strict and report.warnings:
        return 1
    return 0 if report.ok else 1


def _cmd_validate_diagnosis(args: argparse.Namespace) -> int:
    from .validate import validate_diagnosis

    config = Config.load()
    rc = 0
    for f in args.files:
        report = validate_diagnosis(Path(f), config)
        for problem in report.problems:
            print(problem, file=sys.stderr)
        rc |= 0 if report.ok else 1
    print("ok" if rc == 0 else "errors found")
    return rc


def _cmd_trust(args: argparse.Namespace) -> int:
    from .trust import write_trust

    seen, changed = write_trust(Config.load(), check_only=args.check)
    verb = "would change" if args.check else "updated"
    print(f"{seen} records checked / {verb} {len(changed)}")
    for path in changed:
        print(f"  {path}")
    return 1 if (args.check and changed) else 0


def _cmd_index(args: argparse.Namespace) -> int:
    from .index import write_index

    out = write_index(Config.load())
    print(f"wrote {out}")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    from .export import export

    config = Config.load()
    written = export(config, args.format, version=args.version)
    for p in written:
        print(f"wrote {p}")
    return 0


def _cmd_build_site(args: argparse.Namespace) -> int:
    from .site import build_site

    config = Config.load()
    out = build_site(config, out_dir=Path(args.out) if args.out else None)
    print(f"built site in {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oml", description="Open Misconception Library tooling")
    parser.add_argument("--version", action="version", version=f"oml {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate records against the schema and cross-record rules")
    p.add_argument("target", nargs="?", help="records directory or a single record file (default: records/)")
    p.add_argument("--strict", action="store_true", help="treat warnings as errors")
    p.set_defaults(func=_cmd_validate)

    p = sub.add_parser("validate-diagnosis", help="validate diagnosis record files")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=_cmd_validate_diagnosis)

    p = sub.add_parser("trust", help="recompute each record's trust from reviews[] and reviewers/registry.json")
    p.add_argument("--check", action="store_true", help="exit non-zero if any record would change, without writing")
    p.set_defaults(func=_cmd_trust)

    p = sub.add_parser("index", help="regenerate records/INDEX.md")
    p.set_defaults(func=_cmd_index)

    p = sub.add_parser("export", help="write distribution files to dist/")
    p.add_argument("format", choices=["case", "jsonl", "csv", "all"])
    p.add_argument("--version", dest="version", help="release version to stamp (default: oml.config.json library_version)")
    p.set_defaults(func=_cmd_export)

    p = sub.add_parser("build-site", help="write the static site")
    p.add_argument("--out", help="output directory (default: site/_build)")
    p.set_defaults(func=_cmd_build_site)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
