# OML schemas (v0.1)

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
| `status` | `draft`, `reviewed`, `deprecated`, or `merged`. |
| `title` | Short noun-phrase label. |
| `statement` | The belief as the learner holds it. A belief, not a wrong answer. |
| `kind` | Mechanism: `overgeneralization`, `undergeneralization`, `procedural-bug`, `missing-prerequisite`, `notation-confusion`, `misapplied-analogy`. |
| `domain` | Subject area matching the first segment of `id`; may be qualified. |
| `evidence_patterns[]` | At least one `{item_shape, signature, example{item, expected, response}}`. |
| `provenance` | `{sources[], origin}`; every source has `type` and `citation`, optionally `doi`, `url`, `identifier`, `license`. |
| `license` | Always `CC-BY-4.0`. |
| `about[]` | Concepts the misconception is about: `{scheme: CASE|OML, uri, label?}`. Prefer CASE URIs; an OML concept URI (`<base>/c/<concept-id>`) only where no CASE URI exists. |
| `level_band[]` | Education levels where it is typically seen. |
| `locale` | BCP 47 tag for the text; default `en`. |
| `discriminators` | `vs_slip` (systematic vs one-off) and `vs{<neighbour-id>: text}`. |
| `relations` | Closed object. `conflicts_with`, `resolved_by` → concepts as `{external: <uri>}`; `confusable_with` (symmetric), `specializes` → OML record ids. |
| `alignments[]` | `{scheme, uri|guid, code?, relation?, note?}` into external schemes. |
| `prevalence` | Reserved; not populated in v1. |
| `review` | `{reviewer, date, notes?}`; required when `status` is `reviewed`. |
| `history` | `supersedes[]`, `merged_into` (required when `merged`), `deprecated_reason`, `changelog[]`. |

### Conditional rules enforced by the schema

* `status: reviewed` requires `review`.
* `status: merged` requires `history.merged_into`.
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

## Decisions recorded in the schema (2026-09-05)

1. **Relations.** Misconception→Concept: `conflicts_with`, `resolved_by` only.
   Misconception→Misconception: `confusable_with` (symmetric; `oml validate`
   warns when the reverse edge is missing) and `specializes` only.
   `co_occurs_with` and `blocked_by` were dropped before any release.
2. **`about`.** CASE URIs directly; an OML concept URI only where no CASE
   URI exists. Both schemes are accepted, tagged by `scheme`.
3. **ID space.** A record's `id`/`uri` is the canonical public ID of the
   corresponding Knowledge Map Misconception node. There is no second
   identifier field; the `uuid` exists only for systems that need an opaque
   key (it is the CASE `CFItem.identifier`).

## Still provisional

* `prevalence` is reserved and unpopulated; its shape may change.
* The base URI (`https://oml.learnco.io`) is a placeholder until the domain
  is decided. Record `uri` values are rewritten mechanically when it changes.
