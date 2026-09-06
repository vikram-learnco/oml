<!--
  Pull requests are for Contributors and maintainers. If you are proposing a
  misconception for the first time, open a New misconception issue instead:
  it gets a structured response without waiting for a maintainer, and it is
  the path to Contributor. See GOVERNANCE.md. PRs from outside the
  contributor list are closed with a pointer, not ignored.
-->

## What this PR does

<!-- One record per PR. Name the record ID, or describe the tooling change. -->

## Record review checklist

Tick each item, or say why it does not apply.

- [ ] The `statement` is a belief a learner could hold, not a wrong answer.
- [ ] A `kind` is chosen from the schema enum and fits the mechanism.
- [ ] At least one `evidence_patterns[]` entry has a concrete `example` with item, expected and response.
- [ ] `discriminators.vs_slip` is present, and `discriminators.vs` names every neighbour that shares an item shape (with the reciprocal entry added to the neighbour).
- [ ] `provenance.sources[]` is present with citations and DOIs or URLs where they exist.
- [ ] No proprietary text: statement and examples are original; sources are cited, not copied.
- [ ] `status` is `draft` (maintainers only may set `reviewed`).
- [ ] `oml validate records/` passes locally (including the duplicate-similarity warning) and `records/INDEX.md` and `oml trust` output are regenerated.
- [ ] Every commit is signed off (`git commit -s`) per the DCO.

## For merges and disputes

<!-- Link the issue. For a merge, name the surviving ID and the retired ID. -->
