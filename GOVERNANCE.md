# Governance

**Open to propose, earned to write, one editor to bless.**

Anyone may propose a misconception. Nobody but a maintainer merges. The
library's value is that an `oml:` ID means the same thing this year as
last, so the bar to change what an ID says is deliberately higher than
the bar to suggest one.

## Roles

| Role | Who | May |
|------|-----|-----|
| **Reader** | anyone | Read, cite, redistribute under CC BY 4.0. No account needed. |
| **Proposer** | anyone | Open issues: propose a misconception, dispute a record, request a merge. This is the front door. |
| **Contributor** | invited | Open pull requests. Merge still belongs to maintainers. Earned by three accepted proposals. |
| **Reviewer** | nominated by a maintainer | Everything a Contributor may do, plus add a `human` review that promotes a record to `reviewed`. Listed in [`reviewers/registry.json`](reviewers/registry.json). |
| **Maintainer** | Vikram Maram, as an individual | Merge, edit `reviewed` statements, merge or deprecate IDs, nominate Reviewers, rule on disputes. |

**At launch, every tier above Proposer is empty except Maintainer.** There
are no Contributors and no Reviewers other than the maintainer. That is a
statement of fact, not a closed door: the ladder exists so it can be
climbed, and the first invitations will go to people whose proposals were
good.

Reviewer status is recorded in `reviewers/registry.json`, which also
carries the trust weight each reviewer's accept contributes. The registry
is the authority: `oml validate` rejects a `reviewed` record whose human
reviewer is not listed there, so adding yourself to a record achieves
nothing.

## Classes of change

Each class names who may make it and what else must happen.

### 1. Add a new `draft` record

*Who:* Proposer (via issue) or Contributor (via PR). *Requires:* CI green,
which means the schema, the cross-record checks and `oml trust --check`
all pass. A new record enters at `draft` with `trust: low`. No review is
needed to be published; `draft` says plainly how much scrutiny it has had.

### 2. Promote a record to `llm-reviewed` or `reviewed`

*Who:* `llm-reviewed` follows automatically from a model review with
verdict `accept` covering `statement` and `evidence`. `reviewed` requires
either a `human` accept from someone in the reviewer registry, or an
`attested` review pointing at a source in `provenance.sources[]` that
asserts the misconception.

*Requires:* the review is appended to `reviews[]`, never substituted for
an existing one, and `oml trust` is rerun so the computed `trust` matches.

### 3. Edit the `statement` of a `reviewed` record

*Who:* maintainer only. This is the one change that can break a
downstream citation, because the ID stops meaning what it meant.

*Requires:* a major version bump on the record; a `history.changelog`
entry saying what changed and why; and every prior review's `verdict`
reset to `revise`, because those reviewers accepted different words. The
record returns to `reviewed` only when it is reviewed again.

Wording changes that leave the belief identical are a patch bump and do
not reset reviews. If you are unsure which you are making, you are making
the first kind.

### 4. Merge or deprecate an ID

*Who:* maintainer only.

**An `oml:` ID is never deleted.** A merged record keeps its file, its
URI and its page; `status` becomes `merged` and `history.merged_into`
names the survivor. A deprecated record keeps everything and gains
`history.deprecated_reason`. Both keep resolving forever, and the site
and the JSON both point a reader at the successor. A consumer who stored
`oml:math.frac.add-across` in a gradebook in 2026 can still resolve it in
2036, whatever we later decide about that record.

The surviving record gains `history.supersedes` and folds in any evidence
patterns or sources that existed only on the retired one. Every
`relations.*` and `discriminators.vs` entry pointing at the retired ID is
updated in the same change.

## Disputes

Disagreement is expected. A catalogue of beliefs about beliefs will get
some of them wrong, and the useful response is a public record of the
argument, not a quiet edit.

1. Anyone opens a **Dispute** issue naming the record, the field, what is
   wrong, and the evidence.
2. A maintainer sets `disputed: true` on the record and adds the issue
   URL to `disputes[]`. **The record stays live and citable**; the site
   and the JSON show that it is disputed and link the issue. Nothing is
   hidden while an argument is in progress.
3. The maintainer rules, and the ruling is recorded in
   `history.changelog` whichever way it goes. If the dispute is upheld
   the record changes under the rules above; if it is not, `disputed`
   returns to false and the issue is closed with the reasoning. Either
   way the dispute stays linked in `disputes[]` as part of the record's
   history.

A dispute never disappears silently, and losing one is not a mark against
the person who raised it.

## Triage cadence

The maintainer triages open issues **weekly**. A proposal gets a
structured response before that, from the automated first review; the
weekly pass is where a human decides what happens next.

This cadence is what one maintainer can actually keep. If it slips, the
honest fix is to say so here, not to promise faster.

## Licence and provenance

Records, schemas and distributions are CC BY 4.0; tooling is MIT. By
proposing or contributing you agree your text is released under those
terms.

Text must be original or from a CC BY compatible source. Do not paste
item text, distractor rationales or misconception descriptions from
licensed banks: Eedi, Academic Benchmarks, commercial item vendors, or
any inventory that has not published a compatible licence. Citing such a
source in `provenance.sources[]` is fine and encouraged; copying its
words is not.

Every pull request must carry a `Signed-off-by` line
([DCO](https://developercertificate.org/)): `git commit -s`. It is your
statement that you have the right to contribute the text.

## Succession, and the right to fork

One maintainer is a single point of failure. Pretending otherwise would be
the dishonest way to run a shared vocabulary, so here is the arrangement
instead.

**If the maintainer is unresponsive for six months** — no merges, no
triage, no reply on the issue tracker — **the Reviewers named in
[`reviewers/registry.json`](reviewers/registry.json) at the time may fork
the library under the same name and the same IDs, and that fork becomes
the one people should use.** No permission is needed and none can be
withheld. Announce it on the issue tracker and in the fork's README so
adopters can follow.

Everything needed for that is already in place, deliberately:

* The licence permits redistribution and modification by anyone.
* Every release is archived at Zenodo with a DOI, so the full history
  survives the repository disappearing.
* The dataset is mirrored on Hugging Face.
* The IDs are strings, not URLs into any one host. `oml:math.frac.add-across`
  keeps meaning what it means whoever serves it, and the tooling can move
  the library to a new base URI in one command.

An `oml:` ID is meant to outlive the person maintaining it. If it cannot,
it is not worth adopting.

## Changing this document

Governance changes are maintainer decisions, made in a pull request so
the history is public. If the project ever has more than one maintainer,
this section is the first thing that needs rewriting.
