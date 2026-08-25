#!/usr/bin/env python3
"""Measure a scholar term table.

Reads the study's own artifacts — ``terms.jsonl``, ``sources.jsonl``,
``brief.md`` — and never the corpus, so it behaves identically on a monorepo
and a translated text. Standard library only: the analyzer has to run inside
any corpus checkout, where there is no ``uv``, no third-party packages, and no
marketplace harness to import.

It proposes; it never decides. Every finding is a candidate for a human or an
agent to judge in ``contest``.

Examples
--------
Two sibling terms whose definitions say the same thing:

>>> terms = [
...     {"term": "update-action", "parent": "raise",
...      "definition": "update one named action to its current version"},
...     {"term": "update-actions", "parent": "raise",
...      "definition": "update every outdated action to its current version"},
...     {"term": "cut", "parent": "release",
...      "definition": "tag a release at an explicit version"},
... ]
>>> [(a, b) for a, b, _ in synonymy(terms, threshold=0.5)]
[('update-action', 'update-actions')]

One term standing for two unrelated things:

>>> rows = [
...     {"term": "bump", "parent": "raise", "definition": "raise a dependency pin"},
...     {"term": "bump", "parent": "release", "definition": "choose the next version number"},
... ]
>>> [term for term, _ in polysemy(rows)]
['bump']

A term whose parent is not in the table:

>>> orphans([{"term": "probe", "parent": "spike", "definition": "one path"}])
['probe']

A citation that quotes the term it is meant to support:

>>> circular([{"term": "ratchet", "definition": "converges",
...            "cites": [{"quote": "the ratchet stops advancing"}]}])
['ratchet']

The brief may not carry citations, permalinks, or bare numbers:

>>> check_brief("Names split three ways.")
[]
>>> check_brief("See https://example.com/x for detail.")
['line 1: URL belongs in evidence/, not the brief']
>>> check_brief("Twelve plugins, 0.575 similar.")
['line 1: bare number belongs in evidence/, not the brief']
>>> check_brief("Similarity is [0.575](evidence/metrics.md).")
[]
"""

from __future__ import annotations

import json
import math
import re
import sys

SYNONYMY_THRESHOLD = 0.5
"""Sibling definitions at or above this are candidates for one term, not two."""

POLYSEMY_THRESHOLD = 0.3
"""Two rows sharing a term whose definitions fall below this mean two concepts."""

_WORD = re.compile(r"[a-z0-9]+")
_URL = re.compile(r"https?://")
_ANCHOR = re.compile(r"#L\d")
_EVIDENCE_LINK = re.compile(r"\[[^\]]*\]\(evidence/[^)]*\)")
_DIGIT = re.compile(r"\d")


def tokenize(text):
    """Lowercase, split on non-alphanumerics, drop one-character tokens.

    >>> tokenize("Update-Action, v2!")
    ['update', 'action', 'v2']
    """
    return [tok for tok in _WORD.findall(str(text).lower()) if len(tok) > 1]


def idf(docs):
    """Smoothed inverse document frequency per token across *docs*.

    Smoothed as ``log((N + 1) / (1 + df)) + 1`` rather than the textbook
    ``log(N / df)``. A term table is a small corpus — a dozen rows, not a
    million documents — and unsmoothed weights go to zero for a token in most
    rows and negative for a token in every row. Definitions in one ontology
    share their vocabulary by design, so the textbook form cancels out exactly
    the words that make two siblings look alike.

    >>> round(idf([["a", "b"], ["a"]])["a"], 3)
    1.0
    >>> round(idf([["a", "b"], ["a"]])["b"], 3)
    1.405
    """
    total = len(docs)
    df = {}
    for doc in docs:
        for token in set(doc):
            df[token] = df.get(token, 0) + 1
    return {tok: math.log((total + 1) / (1 + n)) + 1 for tok, n in df.items()}


def cosine(a, b):
    """Cosine similarity of two token-weight maps.

    >>> cosine({"a": 1.0}, {"a": 1.0})
    1.0
    >>> cosine({"a": 1.0}, {})
    0.0
    """
    shared = set(a) & set(b)
    dot = sum(a[tok] * b[tok] for tok in shared)
    norm_a = math.sqrt(sum(val * val for val in a.values()))
    norm_b = math.sqrt(sum(val * val for val in b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _vectors(terms):
    """Map each row index to its tf-idf weighted definition vector."""
    docs = [tokenize(row.get("definition", "")) for row in terms]
    weights = idf(docs)
    out = []
    for doc in docs:
        vec = {}
        for token in doc:
            vec[token] = vec.get(token, 0.0) + weights.get(token, 1.0)
        out.append(vec)
    return out


def synonymy(terms, threshold=SYNONYMY_THRESHOLD):
    """Sibling pairs whose definitions score at or above *threshold*.

    Only rows sharing a parent are compared. Two terms under different parents
    are expected to differ, so a high score there is not evidence of one
    concept wearing two names.
    """
    vecs = _vectors(terms)
    hits = []
    for i, left in enumerate(terms):
        for j in range(i + 1, len(terms)):
            right = terms[j]
            if left.get("parent") != right.get("parent"):
                continue
            score = cosine(vecs[i], vecs[j])
            if score >= threshold:
                hits.append((left["term"], right["term"], score))
    hits.sort(key=lambda hit: -hit[2])
    return hits


def polysemy(terms):
    """Terms appearing more than once with definitions that do not match.

    Two rows sharing a term whose definitions score alike are a duplicate
    entry, not polysemy. The finding is one term standing for two concepts.
    """
    vecs = _vectors(terms)
    by_term = {}
    for index, row in enumerate(terms):
        by_term.setdefault(row["term"], []).append(index)
    hits = []
    for term, indexes in by_term.items():
        if len(indexes) < 2:
            continue
        distant = any(
            cosine(vecs[a], vecs[b]) < POLYSEMY_THRESHOLD
            for pos, a in enumerate(indexes)
            for b in indexes[pos + 1 :]
        )
        if distant:
            hits.append((term, [terms[i].get("definition", "") for i in indexes]))
    hits.sort()
    return hits


def orphans(terms):
    """Terms whose parent is neither another term nor ``root``."""
    known = {row["term"] for row in terms} | {"root", ""}
    return [row["term"] for row in terms if row.get("parent", "") not in known]


def fan_out(terms):
    """Child count per parent.

    >>> fan_out([{"term": "a", "parent": "t"}, {"term": "b", "parent": "t"}])
    {'t': 2}
    """
    counts = {}
    for row in terms:
        parent = row.get("parent", "")
        if parent:
            counts[parent] = counts.get(parent, 0) + 1
    return counts


def circular(terms):
    """Terms whose own token appears in the text of a citation supporting them.

    Evidence that quotes the term it is meant to support proves nothing. This
    is not theoretical: routing eval prompts that contained their own skill's
    name made every rename candidate look expensive until the self-reference
    was noticed.
    """
    hits = []
    for row in terms:
        own = set(tokenize(row["term"]))
        for cite in row.get("cites", []):
            quoted = set(tokenize(cite.get("quote", "")))
            if own & quoted:
                hits.append(row["term"])
                break
    return hits


def check_brief(text):
    """Findings for a brief that carries a citation, a permalink, or a bare number.

    The brief is the one file meant to be read start to finish. Where it wants
    a number or a source it links into ``evidence/`` instead.
    """
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        bare = _EVIDENCE_LINK.sub("", line)
        if _URL.search(bare):
            findings.append(f"line {number}: URL belongs in evidence/, not the brief")
        if _ANCHOR.search(bare):
            findings.append(f"line {number}: line anchor belongs in evidence/, not the brief")
        if _DIGIT.search(bare):
            findings.append(f"line {number}: bare number belongs in evidence/, not the brief")
    return findings


def _load(path):
    """Read a JSON-lines file, skipping blank lines."""
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main(argv):
    """Report every finding for the study directory named in *argv*."""
    args = [arg for arg in argv if not arg.startswith("--")]
    brief_only = "--check-brief" in argv
    if not args:
        print("usage: term-metrics.py <study-dir> [--check-brief]", file=sys.stderr)
        return 2
    study = args[0].rstrip("/")

    if brief_only:
        findings = check_brief(open(f"{study}/brief.md", encoding="utf-8").read())
        for finding in findings:
            print(finding)
        return 1 if findings else 0

    terms = _load(f"{study}/terms.jsonl")
    sections = [
        ("synonymy", [f"{a} / {b} at {score:.3f}" for a, b, score in synonymy(terms)]),
        ("polysemy", [f"{term}: {len(defs)} definitions" for term, defs in polysemy(terms)]),
        ("orphans", orphans(terms)),
        ("circular evidence", circular(terms)),
        ("fan-out", [f"{p}: {n}" for p, n in sorted(fan_out(terms).items())]),
    ]
    for title, rows in sections:
        print(f"== {title} ==")
        for row in rows or ["(none)"]:
            print(f"  {row}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
