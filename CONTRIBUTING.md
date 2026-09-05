# Contributing to OML

OML is a catalogue of misconceptions, not of wrong answers. A record earns
its place by stating a belief a learner could hold, giving the evidence
pattern that reveals it, and saying where the claim comes from. This page
tells you how to propose one, how to merge or dispute one, and what
`reviewed` means.

## Before you start

* Read two or three existing records, for example
  [`math.frac.add-across`](records/math/frac.add-across.json).
* Read [`schema/README.md`](schema/README.md) for the field list.
* Search [`records/INDEX.md`](records/INDEX.md) for neighbours. If a record
  with the same evidence pattern exists, improve it instead of adding a
  twin.

Tooling:

```sh
pip install -e tools/oml
oml validate records/      # must pass before you open a PR
oml index                  # regenerates records/INDEX.md; commit the result
```

## Propose a new misconception

One pull request, one record.

1. Pick an ID: `<domain>.<area>.<slug>`, lowercase, dots between segments,
   hyphens inside a segment (`math.frac.add-across`,
   `prog.var.assignment-is-equation`). IDs are permanent, so choose a name
   that describes the belief, not the topic.
2. Create `records/<domain>/<rest-of-id>.json`. The file name is the ID
   without its first segment. Generate a fresh UUID (`python3 -c "import
   uuid; print(uuid.uuid4())"`).
3. Fill in the required fields. The checklist below is what reviewers look
   for.
4. Set `status: draft`. Only maintainers set `reviewed`.
5. Run `oml validate records/` and `oml index`, commit both, open the PR.
   CI runs the same validation and blocks merge on any error.

### What a good record has

* **A belief, not a wrong answer.** "Fractions are added by adding
  numerators and adding denominators" is a belief. "1/2 + 1/3 = 2/5" is a
  wrong answer; it goes in the example.
* **A kind.** Pick the mechanism from the enum in the schema:
  `overgeneralization`, `undergeneralization`, `procedural-bug`,
  `missing-prerequisite`, `notation-confusion`, `misapplied-analogy`. If
  none fits, say so in the PR; do not invent a new one.
* **At least one evidence pattern with a concrete example.** `item_shape`
  says what kind of task shows it, `signature` is a rule a grader could
  apply, and `example` has the item, the correct response, and the response
  a holder of the belief gives.
* **Discriminators.** `vs_slip` says how to tell a stable belief from a
  one-off error. `vs` names every neighbour that shares an item shape and
  says which item separates them. Add the reciprocal entry to the
  neighbour's record in the same PR.
* **Provenance.** At least one source with a citation, and a DOI or URL
  where one exists. `origin` says how the record was produced;
  `llm-drafted` is allowed and must cite literature.
* **No proprietary text.** Write your own statement and examples. Do not
  paste item text or misconception descriptions from commercial item banks,
  competition datasets, or inventories that have not published a
  compatible licence. Citing them as a source is fine.

## Propose a merge

If two records describe the same belief:

1. Decide which ID survives. Prefer the older or the better-evidenced one.
2. On the record being retired, set `status: merged` and
   `history.merged_into: <surviving-id>`. Keep the file; the ID and URI
   must keep resolving.
3. On the surviving record, add `history.supersedes: [<retired-id>]` and
   fold in any evidence patterns or sources that were only on the retired
   record.
4. Update every `relations.*` and `discriminators.vs` entry that pointed at
   the retired ID.

Open the PR with the "Merge request" issue linked or the reasoning in the
description.

## Dispute a statement

Open an issue using the "Dispute" template. Say which record, which field,
what you think is wrong, and what evidence supports the change. A dispute
that changes the `statement` of a `reviewed` record is a breaking change to
that record: it bumps the record's major `version`, and after library v1.0
it bumps the library's major version too. Wording changes that keep the
meaning are patch bumps.

## What `reviewed` means

`reviewed` means a maintainer has read the record against the checklist
above, checked that the sources say what the record says they say, and
confirmed the discriminators against the neighbours. It is recorded in the
`review` block with the reviewer's name and date. Only maintainers set
`reviewed`; a PR from anyone else that sets it will be asked to change it
back to `draft`. `draft` records are published and citable like any other;
the status tells consumers how much scrutiny the record has had.

## Code contributions

The tooling under `tools/` is Python, MIT licensed, with `jsonschema` as
its only dependency. Run `python -m unittest discover -s tools/tests`
before opening a PR. Keep the validator strict: a new check belongs in
`tools/oml/oml/validate.py` with a broken fixture in `tools/tests/fixtures/broken/`.

## Licence of your contribution

By contributing you agree that your additions to `records/`, `schema/` and
`dist/` are released under CC BY 4.0 and your additions to `tools/` and
`site/` under MIT.
