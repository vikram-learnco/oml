---
license: cc-by-4.0
pretty_name: Open Misconception Library
language:
  - en
tags:
  - education
  - misconceptions
  - learning-analytics
  - assessment
size_categories:
  - n<1K
configs:
  - config_name: default
    data_files: oml.jsonl
---

# Open Misconception Library (OML)

A public catalogue of misconceptions with stable IDs. Each row is one
record: a belief a learner could hold, its kind, the evidence pattern that
reveals it (with a concrete example), discriminators against slips and
neighbouring misconceptions, alignments to external schemes, and
provenance.

This dataset mirrors `dist/oml.jsonl` from the tagged release of
<https://github.com/vikram-learnco/oml>. The canonical form of a record is
its stable URI, for example
<https://oml.learnco.io/m/math.frac.add-across>.

## Provenance caveat

Most records are `status: draft`: drafted from the cited literature and not
yet reviewed by a maintainer. Check the `status` and `review` fields before
treating a record as settled. `reviewed` records have been checked against
their sources by a named reviewer.

## Fields

| Field | Meaning |
|-------|---------|
| `id` | Stable ID (`math.frac.add-across`). Cite as `oml:<id>`. |
| `uri` | Stable URI. |
| `uuid` | Opaque identifier; the CASE `CFItem.identifier`. |
| `version`, `status` | Record semver and lifecycle (`draft`, `reviewed`, `deprecated`, `merged`). |
| `title`, `statement` | Short label and the belief as the learner holds it. |
| `kind` | Mechanism: overgeneralization, undergeneralization, procedural-bug, missing-prerequisite, notation-confusion, misapplied-analogy. |
| `domain`, `about`, `level_band`, `locale` | Subject, concepts, education levels, language. |
| `evidence_patterns` | List of `{item_shape, signature, example{item, expected, response}}`. |
| `discriminators` | `vs_slip` and `vs{<neighbour-id>: text}`. |
| `relations` | `conflicts_with`, `resolved_by`, and provisional `confusable_with`, `specializes`, `co_occurs_with`, `blocked_by`. |
| `alignments` | `{scheme, code, uri, relation, note}` into CCSS, progmiscon, etc. |
| `provenance` | `{sources[], origin, notes}`. |
| `review`, `history`, `license` | Review block, merge/supersede history, always `CC-BY-4.0`. |

Full field documentation: <https://github.com/vikram-learnco/oml/blob/main/schema/README.md>.

## Load

```python
from datasets import load_dataset
ds = load_dataset("vikram-learnco/oml")
```

## Cite

See `CITATION.cff` in the repository. A DOI is minted per release on Zenodo.

## Licence

CC BY 4.0. Attribute "Open Misconception Library (LearnCo and contributors)"
and link to the repository or the record URI.
