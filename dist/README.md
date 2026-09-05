# dist/

Generated distribution files. Regenerate with `oml export all`; committed
only on release (the release workflow attaches them to the GitHub release
and the Pages build serves them from the site root).

| File | What |
|------|------|
| `oml.case.json` | 1EdTech CASE 1.1 `CFPackage`: one `CFDocument`, a `Domain` `CFItem` per top-level domain, a `Misconception` `CFItem` per record, `isChildOf` associations record → domain → document, and `isRelatedTo` associations for every alignment with a URI and every `relations.*` target. |
| `oml.jsonl` | One record per line, exactly as in `records/` minus `$schema`. |
| `oml.csv` | One row per record with the scalar fields and the first evidence example. |

## CASE mapping

| OML | CASE |
|-----|------|
| library | `CFDocument` (`title`, `creator`, `licenseURI` → CC BY 4.0, `version` = release tag) |
| record `uuid` | `CFItem.identifier` |
| `oml:<id>` | `CFItem.humanCodingScheme` |
| `statement` | `CFItem.fullStatement` |
| `title` | `CFItem.abbreviatedStatement` |
| `kind` + first evidence pattern | `CFItem.notes` |
| `level_band` | `CFItem.educationLevel` (K, 01–12, UG, PG, AE) |
| domain | `CFItem` of type `Domain`; records are `isChildOf` it |
| `alignments[].uri` | `isRelatedTo` association to the external URI |
| `relations.conflicts_with` / `resolved_by` | `isRelatedTo`, relation name in `notes` |
| provisional M→M relations | `isRelatedTo`, relation name and "provisional" in `notes` (until decision (a)) |

Identifiers for the document, item types, licence and associations are
UUIDv5 values derived from the base URI, so re-exporting is deterministic.

## Conformance

`oml export case` runs a structural check (`tools/oml/oml/case_check.py`)
covering the required fields and association vocabulary of the CASE 1.1
REST/JSON binding. Validation against the official 1EdTech JSON Schema and
an import into a CASE consumer (OpenSALT) still need to be run by a
maintainer with access; record the tool and version here when done.

| Check | Tool / version | Date | Result |
|-------|----------------|------|--------|
| Official CASE 1.1 JSON Schema | pending | | |
| OpenSALT import | pending | | |
