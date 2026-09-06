"""Near-duplicate detection across record statements.

Two records that describe the same belief in different words are the failure
mode this catches: the library's worth depends on one ID per belief. The check
is deliberately blunt and local — a token-overlap score, no model, no network —
so it runs in CI in milliseconds and gives the same answer on every machine.

A pair above the threshold is not an error. It is a question the author must
answer, and the answer is either "they are the same, merge them" or "they are
neighbours, so declare it": a `confusable_with` relation, or a
`discriminators.vs` entry, satisfies the check.

The threshold is set from the corpus rather than guessed. Measured over the
58 records of v0.1.1, every same-domain pair scoring above 0.29 already
declared its neighbour (the closest being the mirror beliefs
`multiply-makes-bigger` / `divide-makes-smaller` at 0.71), and the highest
*undeclared* pair scored 0.29. 0.55 therefore sits in an empty band: it
flags nothing that exists today, while catching a genuine restatement long
before it reaches the near-identical wording that a lazier threshold needs.
Re-measure when the corpus grows; `oml validate --duplicate-threshold`
exists for that.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Words that carry no signal about which belief a statement describes.
STOPWORDS = frozenset("""
a an and are as at be because been but by can do does for from has have if in into is it
its not of on or that the their them then there these they this to too us was were what
when which who will with you your
""".split())

DEFAULT_THRESHOLD = 0.55
TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    return {t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 2}


def similarity(a: str, b: str) -> float:
    """Jaccard overlap of content words, 0.0 to 1.0."""
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass
class DuplicatePair:
    left: str
    right: str
    score: float

    def __str__(self) -> str:
        return f"{self.left} ~ {self.right} ({self.score:.2f})"


def declared_neighbours(record: dict) -> set[str]:
    """IDs this record already acknowledges as near: confusable_with, specializes, or a discriminator."""
    out: set[str] = set()
    relations = record.get("relations") or {}
    for key in ("confusable_with", "specializes"):
        out |= {t for t in (relations.get(key) or []) if isinstance(t, str)}
    disc = record.get("discriminators") or {}
    out |= set((disc.get("vs") or {}).keys())
    return out


def find_duplicates(records: list[dict], threshold: float = DEFAULT_THRESHOLD) -> list[DuplicatePair]:
    """Pairs whose statements overlap above `threshold` and that declare no relationship.

    Only records in the same domain are compared: an identical phrasing about
    fractions and about variables is a coincidence of vocabulary, not a duplicate.
    """
    pairs: list[DuplicatePair] = []
    by_domain: dict[str, list[dict]] = {}
    for r in records:
        by_domain.setdefault(str(r.get("id", "")).split(".")[0], []).append(r)

    for group in by_domain.values():
        for i, left in enumerate(group):
            for right in group[i + 1 :]:
                lid, rid = left.get("id"), right.get("id")
                if not lid or not rid:
                    continue
                if rid in declared_neighbours(left) or lid in declared_neighbours(right):
                    continue
                score = similarity(left.get("statement", ""), right.get("statement", ""))
                if score >= threshold:
                    pairs.append(DuplicatePair(lid, rid, score))
    return sorted(pairs, key=lambda p: -p.score)
