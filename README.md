# Open Misconception Library (OML)

[![validate](https://github.com/vikram-learnco/oml/actions/workflows/validate.yml/badge.svg)](https://github.com/vikram-learnco/oml/actions/workflows/validate.yml)
[![data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](LICENSE-DATA)
[![code: MIT](https://img.shields.io/badge/code-MIT-lightgrey.svg)](LICENSE)

OML is a public catalogue of misconceptions with stable IDs. A misconception
is a false but stable belief that produces predictable wrong answers, such as
"to add fractions you add the numerators and add the denominators". Each
record states the belief, names its kind, gives the evidence pattern that
distinguishes it from a slip or a neighbouring misconception, and records
where the claim comes from. Because the IDs are stable and public, any
learning platform, item bank, or research group can say *why* a learner got
something wrong in a shared vocabulary, and two systems that have never met
can agree they are talking about the same error.

## How to cite a record

Every record has a short ID and a stable URI. Cite either.

| Form  | Example                                              |
|-------|------------------------------------------------------|
| ID    | `oml:math.frac.add-across`                           |
| URI   | `https://oml.learnco.io/m/math.frac.add-across`      |
| JSON  | `https://oml.learnco.io/m/math.frac.add-across.json` |

IDs are lowercase, dot-separated, and never reused. A record may be
`deprecated` or `merged` into another, but its ID and URI keep resolving
and point you to the successor. Each record also carries a UUID for systems
that prefer opaque identifiers.

To cite the library as a whole, see [`CITATION.cff`](CITATION.cff). A DOI is
minted for each tagged release.

## How to consume

* **One record as JSON.** `records/<domain>/<rest-of-id>.json` in this repo,
  or `<URI>.json` on the site. Records conform to
  [`schema/oml-record.schema.json`](schema/oml-record.schema.json).
* **The whole library as JSON Lines or CSV.** `dist/oml.jsonl` and
  `dist/oml.csv`, attached to every release.
* **As a CASE framework.** `dist/oml.case.json` is a
  [1EdTech CASE 1.1](https://www.imsglobal.org/spec/case/v1p1) document with
  one `CFItem` per misconception, so it imports into any CASE consumer
  alongside your standards frameworks.
* **Diagnoses.** If your system emits a diagnosis that cites an OML record,
  [`schema/diagnosis-record.schema.json`](schema/diagnosis-record.schema.json)
  is the interchange shape.

Regenerate the distribution files locally with:

```sh
pip install -e tools/oml
oml validate records/
oml export all
oml build-site
```

The tooling is Python (3.10 or newer) with `jsonschema` as its only
dependency.

## Record status

| Status       | Meaning                                                            |
|--------------|--------------------------------------------------------------------|
| `draft`      | Proposed; has evidence and provenance but no human review yet.     |
| `reviewed`   | A maintainer has checked the statement, kind, evidence and sources. |
| `deprecated` | No longer recommended; the record says why.                        |
| `merged`     | Folded into another record; `history.merged_into` names it.        |

Most records in an early release are `draft`. Treat `draft` as "someone
thought this was worth writing down", not as a settled claim.

## How to contribute

One record per pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
review checklist and how to propose a merge or dispute a statement.

## Licence

Code under `tools/` and `site/` is [MIT](LICENSE). Everything under
`records/`, `schema/`, and `dist/` is
[CC BY 4.0](LICENSE-DATA). Cite the library when you redistribute the data.
