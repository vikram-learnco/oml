# Contributing to OML

**The front door is an issue, not a pull request.**

OML is a catalogue of misconceptions, not of wrong answers. A record earns
its place by stating a belief a learner could hold, giving the evidence
pattern that reveals it, and saying where the claim comes from. Anyone can
propose one. Merging is reserved to maintainers, and during v0.x pull
requests from people outside the contributor list are closed with a
pointer back here — not because the work is unwelcome, but because a
stable ID space needs one editor deciding what an ID means.

[GOVERNANCE.md](GOVERNANCE.md) has the full role ladder, the classes of
change, and who may make each one.

## Propose a misconception

Open a **[New misconception](../../issues/new?template=new-misconception.yml)**
issue. You need:

* **A statement.** The belief as the learner holds it. "Fractions are
  added by adding the numerators and adding the denominators" is a belief.
  "1/2 + 1/3 = 2/5" is a wrong answer; that belongs in the example.
* **A kind.** The mechanism: `overgeneralization`, `undergeneralization`,
  `procedural-bug`, `missing-prerequisite`, `notation-confusion`, or
  `misapplied-analogy`.
* **One evidence pattern with a concrete example.** What task reveals it,
  what rule the learner follows, and one item with the correct response
  and the response a holder of the belief gives.
* **Nearest neighbours.** Search [`records/INDEX.md`](records/INDEX.md).
  If a record with the same evidence pattern exists, say how yours
  differs, or propose improving that one instead.
* **Sources.** Citations with DOIs or URLs where they exist.

You get a structured response on the issue — belief-not-answer, evidence
pattern present, nearest neighbours, sources real — without waiting for a
maintainer. A maintainer triages weekly and decides what happens next.

## Dispute a record

Open a **[Dispute](../../issues/new?template=dispute.yml)** issue naming
the record, the field, what is wrong, and the evidence. The record is
flagged `disputed` and stays live and citable while the argument runs; the
ruling is recorded in the record's changelog either way. Losing a dispute
is not a mark against you. See
[GOVERNANCE.md](GOVERNANCE.md#disputes).

## Propose a merge

Open a **[Merge request](../../issues/new?template=merge-request.yml)**
issue when two records describe the same belief. Name which ID should
survive and why, and what evidence or sources exist only on the one being
retired.

**No `oml:` ID is ever deleted.** A merged record keeps its file, URI and
page; `history.merged_into` names the survivor and the redirect holds
forever.

## Becoming a Contributor

Three accepted proposals earns an invitation to open pull requests
directly. Reviewer status, which lets you promote a record to `reviewed`,
is by maintainer nomination and is recorded in
[`reviewers/registry.json`](reviewers/registry.json). At launch both tiers
are empty; the ladder exists to be climbed.

## If you are a Contributor: opening a pull request

One pull request, one record.

1. Pick an ID: `<domain>.<area>.<slug>`, lowercase, dots between segments,
   hyphens inside a segment. IDs are permanent, so name the belief, not
   the topic.
2. Create `records/<domain>/<rest-of-id>.json`. Generate a fresh UUID
   (`python3 -c "import uuid; print(uuid.uuid4())"`).
3. Set `status: draft`. Leave `reviews` and `trust` alone; `oml trust`
   computes trust, and only registered reviewers may accept a record.
4. Run the checks, commit what they regenerate, and open the PR:

```sh
pip install -e tools/oml
oml validate records/      # schema + cross-record checks; must pass
oml trust                  # computes trust from reviews; commit the result
oml index                  # regenerates records/INDEX.md; commit the result
```

CI runs the same checks with `--strict`, so warnings block the merge too.
One of those warnings is the duplicate check: if your statement reads like
an existing record's, either merge them or declare the neighbour in
`relations.confusable_with` and `discriminators.vs`.

### What a good record has

* **A belief, not a wrong answer.**
* **A kind** from the schema enum that fits the mechanism.
* **At least one evidence pattern with a concrete example**: `item_shape`,
  a `signature` a grader could apply, and an `example` with item, expected
  and the belief-driven response.
* **Discriminators.** `vs_slip` separates a stable belief from a one-off
  error; `vs` names every neighbour sharing an item shape and the item
  that separates them. Add the reciprocal entry to the neighbour in the
  same PR.
* **Provenance.** At least one source with a citation, and a DOI or URL
  where one exists. `origin: llm-drafted` is allowed and must cite
  literature.

## What `reviewed` means

Every record carries `reviews[]`. A review says who looked (`kind`:
`human`, `model` or `attested`), at what (`scope`: statement, evidence,
discriminators, sources), when, and with what `verdict`.

| Status | Requires |
|--------|----------|
| `draft` | Nothing. Evidence and provenance present, no review yet. |
| `llm-reviewed` | A model review with verdict `accept` covering `statement` and `evidence`. |
| `reviewed` | A human `accept` from someone in the reviewer registry, or an attested review. |

`oml validate` rejects a human `accept` from anyone not in
[`reviewers/registry.json`](reviewers/registry.json), so adding yourself
to a record achieves nothing. `draft` and `llm-reviewed` records are
published and citable like any other; the status says how much scrutiny
the record has had.

`trust` (`low`, `medium`, `high`) is computed, not written. `oml trust`
derives it from `reviews[]` and the registry weights, and CI fails if a
stored value disagrees.

## Licence and sign-off

Records, schemas and distributions are CC BY 4.0; tooling under `tools/`
and `site/` is MIT. By proposing or contributing you agree your additions
are released under those terms.

**Write your own text.** It must be original or from a CC BY compatible
source. Do not paste item text, distractor rationales or misconception
descriptions from licensed banks — Eedi, Academic Benchmarks, commercial
item vendors, or any inventory without a compatible published licence.
Citing such a source in `provenance.sources[]` is welcome; copying its
words is not.

**Sign off every commit.** Pull requests need a `Signed-off-by` line, which
is your assertion under the [Developer Certificate of
Origin](https://developercertificate.org/) that you have the right to
contribute the text:

```sh
git commit -s -m "your message"
```

## Code contributions

The tooling under `tools/` is Python with `jsonschema` as its only
dependency. Run `python -m unittest discover -s tools/tests` before
opening a PR. Keep the validator strict: a new check belongs in
`tools/oml/oml/validate.py` with a broken fixture in
`tools/tests/fixtures/broken/`.
