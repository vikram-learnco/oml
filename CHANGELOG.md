# Changelog

All notable changes to the Open Misconception Library are recorded here.
The library follows semantic versioning:

* **patch**: wording, metadata, tooling fixes; no record IDs or statements change.
* **minor**: records added; evidence, discriminators, sources or alignments added to existing records; records deprecated or merged (their IDs keep resolving).
* **major** (after 1.0): the `statement` of a `reviewed` record changes meaning, or a field is removed from the schema.

Before 1.0, minor releases may also change the schema; each such change is called out below.

## [Unreleased]

## [0.1.1] - 2026-09-05

First release archived by Zenodo; the concept DOI is minted on this tag.

### Changed (record schema 0.2)

* **Review model.** `review` is replaced by `reviews[]` (`kind: human|model|attested`, `by`, `date`, `scope[]`, `verdict`, `notes?`). Status lifecycle is `draft` → `llm-reviewed` → `reviewed` → `deprecated` | `merged`; the validator enforces that `llm-reviewed` has a model accept covering statement and evidence and that `reviewed` has a human accept or an attested review.
* **Computed trust.** New `trust` field (`low|medium|high`) computed by `oml trust` from `reviews[]` against `reviewers/registry.json`; never hand-typed, checked in CI.
* **Framework-agnostic alignments.** `about[]` and `alignments[]` are `{scheme, uri, code?, note?}` with a free-string `scheme`; known schemes are data in `schemes/registry.json` and the validator warns on unknown ones. corestandards.org URLs are labelled `CCSS` across all mathematics records.
* New optional top-level `notes` field for text that is not the belief itself (e.g. likely origins).
* `math.frac.add-across` (record #1, version 1.1.0): statement trimmed to the belief; likely origins moved to `notes`; review closed with Vikram Maram on 2026-09-05 and recorded as `reviews[]` (human accept, model accept, two attested reviews); `status: reviewed`, `trust: high`.
* Every other record gains a changelog entry and a patch version bump for the migration; all remain `draft` with `trust: low`.
* Hugging Face mirror targets the dataset `vikram-learnco/oml`.

### Fixed

* Release workflow was invalid (`secrets` used in a step `if`), so no run had ever executed before v0.1.0 was re-cut. The Hugging Face step now authenticates through the Hub's Trusted Publisher (GitHub OIDC), falls back to `HF_TOKEN` if present, and is skipped otherwise; the workflow can be re-run for an existing tag via `workflow_dispatch`.

## [0.1.0] - 2026-09-05

First citable release.

### Added

* `schema/oml-record.schema.json` v0.1 and `schema/diagnosis-record.schema.json` v0.1 (JSON Schema 2020-12).
* `oml` command-line tooling: `validate`, `index`, `export case|jsonl|csv|all`, `build-site`.
* 58 records: 1 `reviewed` (`math.frac.add-across`) and 57 `draft` across `math.fractions`, `math.decimals` and seven programming areas.
* CASE 1.1 export (`dist/oml.case.json`), JSON Lines and CSV distributions.
* Static site with one page per record at its stable URI.
* Contribution path: CONTRIBUTING.md, PR checklist, issue templates, Contributor Covenant 2.1.

### Decided before release (2026-09-05)

* Relations are a closed set: `conflicts_with`, `resolved_by` (to concepts), `confusable_with` (symmetric), `specializes` (to misconceptions).
* `about[]` entries are `{scheme: CASE|OML, uri}`; CASE preferred.
* The record `id`/`uri` is the canonical ID of the Knowledge Map Misconception node.

### Provisional

* Base URI `https://oml.learnco.io` is a placeholder pending the domain decision.

[Unreleased]: https://github.com/vikram-learnco/oml/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/vikram-learnco/oml/releases/tag/v0.1.1
[0.1.0]: https://github.com/vikram-learnco/oml/releases/tag/v0.1.0
