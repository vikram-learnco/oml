# Open Misconception Library (OML)

[![validate](https://github.com/open-misconceptions/oml/actions/workflows/validate.yml/badge.svg)](https://github.com/open-misconceptions/oml/actions/workflows/validate.yml)
[![data: CC0 1.0](https://img.shields.io/badge/data-CC0%201.0-lightgrey.svg)](LICENSE-DATA)
[![code: MIT](https://img.shields.io/badge/code-MIT-lightgrey.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22416011.svg)](https://doi.org/10.5281/zenodo.22416011)
[![Hugging Face dataset](https://img.shields.io/badge/dataset-open--misconceptions%2Foml-yellow.svg)](https://huggingface.co/datasets/open-misconceptions/oml)

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
| URI   | `https://open-misconceptions.github.io/oml/m/math.frac.add-across`      |
| JSON  | `https://open-misconceptions.github.io/oml/m/math.frac.add-across.json` |

IDs are lowercase, dot-separated, and never reused. A record may be
`deprecated` or `merged` into another, but its ID and URI keep resolving
and point you to the successor. Each record also carries a UUID for systems
that prefer opaque identifiers.

To cite the library as a whole, use the concept DOI
[10.5281/zenodo.22416011](https://doi.org/10.5281/zenodo.22416011), which always resolves to
the latest release; each release also has its own version DOI (v0.1.1:
[10.5281/zenodo.22416012](https://doi.org/10.5281/zenodo.22416012)). Author and title
metadata are in [`CITATION.cff`](CITATION.cff). The whole library is also
mirrored as the Hugging Face dataset
[`open-misconceptions/oml`](https://huggingface.co/datasets/open-misconceptions/oml).

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

**Propose a misconception by opening an issue**, not a pull request. You get
a structured response without waiting for a maintainer, and three accepted
proposals earns the right to open pull requests directly.

* [CONTRIBUTING.md](CONTRIBUTING.md) — what a good proposal contains, and
  what `reviewed` means.
* [GOVERNANCE.md](GOVERNANCE.md) — who may make which change, how disputes
  are settled, and why an `oml:` ID is never deleted.

## Licence

Code under `tools/` and `site/` is [MIT](LICENSE). Everything under
`records/`, `schema/` and `dist/` is [CC0 1.0](LICENSE-DATA) — public
domain. You may use, adapt and redistribute the records for any purpose
without asking, without attributing, and without thinking about who
maintains them. That is deliberate: a shared vocabulary that carries
obligations is one fewer platform's legal review away from adoption.

A citation is welcome and is not required. If you want to, the concept
DOI is [10.5281/zenodo.22416011](https://doi.org/10.5281/zenodo.22416011).

Releases up to and including v0.1.1 were published under CC BY 4.0. That
grant is public and irrevocable, so those releases remain available under
it; v0.2.0 onward is CC0.
