# Changelog

All notable changes to the Open Misconception Library are recorded here.
The library follows semantic versioning:

* **patch**: wording, metadata, tooling fixes; no record IDs or statements change.
* **minor**: records added; evidence, discriminators, sources or alignments added to existing records; records deprecated or merged (their IDs keep resolving).
* **major** (after 1.0): the `statement` of a `reviewed` record changes meaning, or a field is removed from the schema.

Before 1.0, minor releases may also change the schema; each such change is called out below.

## [Unreleased]

### Changed

* **OML is maintained by Vikram Maram as an individual project.** The MIT copyright holder, the `creator` in `oml.config.json` (which flows into the CASE `CFDocument`), and the dataset-card attribution now name the maintainer rather than a company. Nothing about the `oml:` IDs changes.

### Added

* **Succession and the right to fork** in `GOVERNANCE.md`: if the maintainer is unresponsive for six months, the Reviewers named in the registry may fork under the same name and IDs, and that fork becomes the one to use. The licence, the Zenodo DOI, the Hugging Face mirror and host-independent IDs exist so that this is always possible.
* **`oml rebase-uri <new-base>`**: moves the library to a new base URI, rewriting every record `uri`, every OML concept URI in `about[]` and `relations.*`, both schema `$id`s, the scheme registry's URI pattern, the config and the docs. Idempotent, `--dry-run` supported, and covered by round-trip tests — a record `uri` is a public identifier, so a partial rewrite is the failure mode worth engineering against.

* **`GOVERNANCE.md`**: role ladder (Reader → Proposer → Contributor → Reviewer → Maintainer, with every tier above Proposer empty at launch except Maintainer), the four classes of change and who may make each, the dispute process, and the weekly triage cadence. Linked from the README and the site footer.
* **Dispute fields**: `disputed` (boolean) and `disputes[]` (issue URLs) on a record. A disputed record stays live and citable; the site shows a banner and links the issues. `disputed: true` requires a linked dispute.
* **Duplicate detection**: `oml validate` reports two same-domain records whose statements overlap above a similarity threshold unless one declares the other in `relations.confusable_with`, `relations.specializes` or `discriminators.vs`. Threshold 0.55, set from the corpus (highest undeclared pair scores 0.29) and tunable with `--duplicate-threshold`.
* **DCO check** (`.github/workflows/dco.yml`): every non-merge commit in a pull request must carry a `Signed-off-by` line.
* **Governance gates** (`.github/workflows/gate.yml`): pull requests from outside the contributor list are closed with a pointer to the issue templates; issues that never completed a template are closed after 7 days (the `keep-open` label exempts one). `CODEOWNERS` names the maintainer.
* Zenodo concept DOI 10.5281/zenodo.22416011 in `CITATION.cff`, the README badge and the dataset card (minted on v0.1.1; version DOI 10.5281/zenodo.22416012).

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

### Changed

* **`CONTRIBUTING.md` leads with propose, not contribute.** The front door is an issue; external pull requests are not merged during v0.x, and the path to Contributor (three accepted proposals) is stated. Licence section names the banks whose text must not be pasted, and documents `git commit -s`.
* **The reviewer registry is now authoritative.** A human review with verdict `accept` from a handle not in `reviewers/registry.json` is an error, not a warning: adding yourself to a record no longer promotes it.

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
