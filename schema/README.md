# OML schemas (record schema 0.2, diagnosis schema 0.1)

Both schemas are JSON Schema 2020-12. Validate with any conforming validator;
the repo's `oml validate` command adds cross-record checks the schema cannot
express (ID/filename agreement, relation targets, UUID uniqueness).

## `oml-record.schema.json`

One misconception. Required fields first.

| Field | Meaning |
|-------|---------|
| `id` | Stable ID, `^[a-z]+(\.[a-z0-9-]+)+$`; first segment is the domain; never reused. |
| `uri` | Base URI + `/m/` + `id`. |
| `uuid` | Opaque unique identifier; becomes the CASE `CFItem.identifier`. |
| `version` | Semver of the record's content. |
| `status` | `draft` → `llm-reviewed` → `reviewed` → `deprecated` \| `merged`. `llm-reviewed` needs a model review with verdict `accept` covering `statement` and `evidence`; `reviewed` needs a human `accept` or an attested review. |
| `trust` | `low`, `medium`, `high`. Computed by `oml trust` from `reviews[]` against `reviewers/registry.json`; never hand-typed. |
| `title` | Short noun-phrase label. |
| `statement` | The belief as the learner holds it. A belief, not a wrong answer. |
| `notes` | Free text that is not the belief itself, e.g. likely origins. |
| `kind` | Mechanism: `overgeneralization`, `undergeneralization`, `procedural-bug`, `missing-prerequisite`, `notation-confusion`, `misapplied-analogy`. |
| `domain` | Subject area matching the first segment of `id`; may be qualified. |
| `evidence_patterns[]` | At least one `{item_shape, signature, example{item, expected, response}}`. |
| `provenance` | `{sources[], origin}`; every source has `type` and `citation`, optionally `doi`, `url`, `identifier`, `license`. |
| `license` | Always `CC-BY-4.0`. |
| `about[]` | Concepts the misconception is about: `{scheme, uri, code?, note?}`. `scheme` is a free string; known schemes are data in `schemes/registry.json` and the validator warns on unknown ones. Prefer `CASE` item URIs; `OML` concept URIs (`<base>/c/<concept-id>`) only where no CASE URI exists. |
| `level_band[]` | Education levels where it is typically seen. |
| `locale` | BCP 47 tag for the text; default `en`. |
| `discriminators` | `vs_slip` (systematic vs one-off) and `vs{<neighbour-id>: text}`. |
| `relations` | Closed object. `conflicts_with`, `resolved_by` → concepts as `{external: <uri>}`; `confusable_with` (symmetric), `specializes` → OML record ids. |
| `alignments[]` | `{scheme, uri, code?, relation?, note?}` into external schemes. Same framework-agnostic shape as `about`. |
| `prevalence` | Reserved; not populated in v1. |
| `reviews[]` | `{kind: human\|model\|attested, by, date, scope[], verdict: accept\|revise\|reject, notes?}`. `human.by` is a name plus a durable handle, `"Vikram Maram (github:vikram-learnco)"`; `model.by` is a model id and version; `attested.by` is an index into `provenance.sources[]`. `scope` values: `statement`, `evidence`, `discriminators`, `sources`. |
| `history` | `supersedes[]`, `merged_into` (required when `merged`), `deprecated_reason`, `changelog[]`. |
| `disputed` | `true` while an open dispute challenges the record. It stays live and citable; see [GOVERNANCE.md](../GOVERNANCE.md#disputes). Requires at least one entry in `disputes`. |
| `disputes[]` | URLs of dispute issues, open or settled. Entries are never removed. |

### Conditional rules enforced by the schema

* `status: reviewed` and `llm-reviewed` require a non-empty `reviews[]`; the validator checks the lifecycle rules above.
* `status: merged` requires `history.merged_into`.
* `trust` must equal the value `oml trust` computes; CI runs `oml trust --check`.
* A human review with verdict `accept` is rejected unless its handle is in `reviewers/registry.json`; the registry, not the record, decides who may promote a record to `reviewed`.
* `disputed: true` requires a linked dispute in `disputes[]`.
* Two records in the same domain whose statements overlap above the similarity threshold are reported unless one declares the other in `relations.confusable_with`, `relations.specializes` or `discriminators.vs`. Tune with `oml validate --duplicate-threshold`.
* Every evidence pattern has a concrete `example`.
* Concept relations (`conflicts_with`, `resolved_by`) take `{"external": "<uri>"}`; misconception relations (`confusable_with`, `specializes`) take OML record ids. No other relation keys are accepted.

## `diagnosis-record.schema.json`

One diagnosed learner response, for systems that emit diagnoses citing OML.

| Field | Meaning |
|-------|---------|
| `item` | The task, or a stable reference to it. |
| `expected` | The correct response. |
| `response` | What the learner gave; may be empty. |
| `diagnoses[]` | `{oml_id, confidence 0..1, matched_pattern, rationale?}`; may be empty. |
| `oml_version` | Library release diagnosed against. |
| `engine_version` | Identifier and version of the diagnosing system. |
| `tenant_local_id` | Local id when the diagnosis is against a record not in OML. |
| `insufficient_evidence` | `true` when the response was too thin to diagnose. |
| `observed_at` | Optional timestamp. |

## Registries (data, not schema)

* `schemes/registry.json`: known alignment schemes with a URI pattern and homepage. The schema never names frameworks; add one here.
* `reviewers/registry.json`: reviewers (humans, model versions, the literature-attestation entry) with a trust weight. `oml trust` sums the weights of `accept` reviews and maps the score to `low`/`medium`/`high` using the thresholds in the file. Change a weight, rerun `oml trust`, commit the records it rewrites.

## Decisions recorded in the schema (2026-09-05)

1. **Relations.** Misconception→Concept: `conflicts_with`, `resolved_by` only.
   Misconception→Misconception: `confusable_with` (symmetric; `oml validate`
   warns when the reverse edge is missing) and `specializes` only.
   `co_occurs_with` and `blocked_by` were dropped before any release.
2. **`about` and `alignments` are framework-agnostic.** The schema encodes
   the shape `{scheme, uri, code?, note?}` and never an enum of frameworks;
   `schemes/registry.json` names the known ones. CASE URIs are preferred;
   corestandards.org URLs carry `CCSS` until their CASE GUIDs are confirmed.
4. **Review model.** `review` became `reviews[]` with human, model and
   attested kinds, a `draft` → `llm-reviewed` → `reviewed` lifecycle enforced
   by the validator, and `trust` computed from the reviewer registry.
3. **ID space.** A record's `id`/`uri` is the canonical public ID of the
   corresponding Knowledge Map Misconception node. There is no second
   identifier field; the `uuid` exists only for systems that need an opaque
   key (it is the CASE `CFItem.identifier`).

## Still provisional

* `prevalence` is reserved and unpopulated; its shape may change.
* The base URI (`https://oml.learnco.io`) is a placeholder until the domain
  is decided. Record `uri` values are rewritten mechanically when it changes.
