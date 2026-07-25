#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0",
#     "typer>=0.15",
#     "pyyaml>=6.0",
# ]
# ///
"""Routing-quality checks for the skill catalog.

A skill reaches a model through its ``description`` alone: hosts inject only
the name and description, then load the body once the skill is chosen. Two
skills whose descriptions read alike are unroutable however good their bodies
are, and a description with no trigger clause never fires at all.

These checks therefore score the *catalog*, not any single skill. Prompts are
ranked against every description with a small TF-IDF model, and the catalog
fails when two descriptions sit above a similarity threshold. That is the
failure a per-skill test cannot see.

The model is deliberately crude. It is a proxy for a router, not a router, and
its value is regression detection: a description edit that makes two skills
converge shows up as a number that moved.

Examples
--------
Rank a prompt against a small catalog:

>>> corpus = build_corpus(
...     [
...         SkillDoc("commit", "Use when the user wants to create a git commit"),
...         SkillDoc("rebase", "Use when rebasing a branch onto trunk"),
...     ]
... )
>>> rank_skills("create a git commit", corpus)[0].name
'commit'

Descriptions must say when to use the skill:

>>> lint_description(SkillDoc("demo", "Formats source files."))
['demo: description has no trigger clause (add "Use when ...")']
>>> lint_description(SkillDoc("demo", "Use when the user wants formatting."))
[]
"""

from __future__ import annotations

import dataclasses
import json
import math
import re
import typing as t
from pathlib import Path

import rich.console
import typer
import yaml

if t.TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
CASES_DIR = REPO_ROOT / "evals" / "cases"

MAX_DESCRIPTION_CHARS = 1024
"""Hosts inject the description into the system prompt; keep it bounded."""

COLLISION_WARN = 0.5
COLLISION_ERROR = 0.75
"""Cosine similarity between two descriptions. Above the error bound the two
skills compete for the same prompts and the router cannot separate them."""

NAME_TOKEN_WEIGHT = 2
"""A skill's own name is its strongest routing signal, so it counts twice."""

TOP_N = 5

NEGATIVE_MIN_SCORE = 0.2
"""A negative prompt only fails when the skill ranks first *and* clears this
score. Not every prompt has an owner in the catalog, and ranking first at 0.13
out of a field of near-zeros is noise, not a mis-route."""

_WHEN = r"(?:when(?:ever)?|while|before|after|during)"

_TRIGGER_FORMS = (
    # "Use when", "Use whenever", "Use this skill when", "should be used when"
    rf"\buse[ds]?\b(?:\s+\S+){{0,3}}?\s+{_WHEN}\b",
    # "Triggers on phrases like ...", the other convention in this repo
    r"\btriggers?\s+on\b",
    r"\bapplies\s+when\b",
)
_TRIGGER = re.compile("|".join(_TRIGGER_FORMS), re.IGNORECASE)
_TRIGGER_NEGATED = re.compile(
    rf"\b(?:do not|don't|never)\s+use\b(?:\s+\S+){{0,3}}?\s+{_WHEN}\b", re.IGNORECASE
)
_WORD = re.compile(r"[a-z0-9]+")

console = rich.console.Console()

app = typer.Typer(help="Routing-quality checks for the skill catalog.")


@dataclasses.dataclass(frozen=True)
class SkillDoc:
    """A skill reduced to the two fields a router actually sees."""

    name: str
    description: str


@dataclasses.dataclass(frozen=True)
class Ranking:
    """One skill's similarity to a prompt."""

    name: str
    score: float


@dataclasses.dataclass(frozen=True)
class Corpus:
    """Term frequencies per skill plus the catalog-wide inverse document frequency."""

    docs: dict[str, dict[str, int]]
    idf: dict[str, float]


def stem(token: str) -> str:
    """Strip common English suffixes so inflected forms share a term.

    This is a suffix chopper, not a linguistic stemmer: it collapses
    "rebasing" and "rebased" onto one term without claiming that term is a
    word. Bare stems are left alone, so "format" and "formatting" do not
    meet -- close enough for ranking, and it never invents a match.

    Examples
    --------
    >>> stem("rebasing"), stem("rebased")
    ('rebas', 'rebas')
    >>> stem("branches"), stem("quickly")
    ('branch', 'quick')
    """
    for suffix in ("ing", "edly", "ies", "es", "ed", "ly", "s"):
        if len(token) > len(suffix) + 2 and token.endswith(suffix):
            base = token[: -len(suffix)]
            return f"{base}y" if suffix == "ies" else base
    return token


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, and stem.

    Examples
    --------
    >>> tokenize("Rebasing branches onto trunk")
    ['rebas', 'branch', 'onto', 'trunk']
    """
    words = t.cast("list[str]", _WORD.findall(text.lower()))
    return [stem(word) for word in words]


def term_freq(tokens: Iterable[str]) -> dict[str, int]:
    """Count occurrences of each term.

    Examples
    --------
    >>> term_freq(["a", "b", "a"])
    {'a': 2, 'b': 1}
    """
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def build_corpus(skills: Sequence[SkillDoc]) -> Corpus:
    """Build per-skill term frequencies and catalog-wide IDF weights.

    The skill's name is tokenized and counted ``NAME_TOKEN_WEIGHT`` times,
    because a prompt that echoes a skill's name is the clearest routing
    signal available.

    Examples
    --------
    >>> corpus = build_corpus([SkillDoc("commit", "Use when staging changes")])
    >>> corpus.docs["commit"]["commit"]
    2
    """
    docs: dict[str, dict[str, int]] = {}
    doc_freq: dict[str, int] = {}
    for skill in skills:
        name_tokens = tokenize(skill.name.replace("-", " "))
        tokens = list(name_tokens) * NAME_TOKEN_WEIGHT + tokenize(skill.description)
        counts = term_freq(tokens)
        docs[skill.name] = counts
        for term in counts:
            doc_freq[term] = doc_freq.get(term, 0) + 1

    total = len(docs)
    idf = {term: math.log(1 + total / (1 + freq)) for term, freq in doc_freq.items()}
    return Corpus(docs=docs, idf=idf)


def _vector(counts: dict[str, int], idf: dict[str, float]) -> dict[str, float]:
    """Weight term frequencies by inverse document frequency."""
    return {term: freq * idf.get(term, 0.0) for term, freq in counts.items()}


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors.

    Examples
    --------
    >>> cosine({"a": 1.0}, {"a": 1.0})
    1.0
    >>> cosine({"a": 1.0}, {"b": 1.0})
    0.0
    """
    shared = set(left) & set(right)
    dot = sum(left[term] * right[term] for term in shared)
    if not dot:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot / (left_norm * right_norm)


def rank_skills(prompt: str, corpus: Corpus) -> list[Ranking]:
    """Rank every skill in the corpus against a prompt, best first."""
    prompt_vec = _vector(term_freq(tokenize(prompt)), corpus.idf)
    rankings = [
        Ranking(name=name, score=cosine(prompt_vec, _vector(counts, corpus.idf)))
        for name, counts in corpus.docs.items()
    ]
    rankings.sort(key=lambda item: (-item.score, item.name))
    return rankings


def lint_description(skill: SkillDoc) -> list[str]:
    """Check one description for the properties a router depends on.

    Examples
    --------
    >>> lint_description(SkillDoc("demo", "Use when x. " + "y" * 1100))[0][:20]
    'demo: description is'
    """
    problems: list[str] = []
    if not skill.description:
        problems.append(f"{skill.name}: missing description")
        return problems

    if len(skill.description) > MAX_DESCRIPTION_CHARS:
        detail = f"{len(skill.description)} chars, over the {MAX_DESCRIPTION_CHARS} limit"
        problems.append(f"{skill.name}: description is {detail}")

    has_trigger = _TRIGGER.search(skill.description) is not None
    only_negated = has_trigger and not _TRIGGER.search(_TRIGGER_NEGATED.sub("", skill.description))
    if not has_trigger or only_negated:
        problems.append(f'{skill.name}: description has no trigger clause (add "Use when ...")')

    return problems


def find_collisions(corpus: Corpus, threshold: float) -> list[tuple[str, str, float]]:
    """Find description pairs whose similarity meets or exceeds a threshold."""
    names = sorted(corpus.docs)
    vectors = {name: _vector(corpus.docs[name], corpus.idf) for name in names}
    hits: list[tuple[str, str, float]] = []
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            score = cosine(vectors[left], vectors[right])
            if score >= threshold:
                hits.append((left, right, score))
    hits.sort(key=lambda item: -item[2])
    return hits


def discover_skills() -> list[SkillDoc]:
    """Read every plugin skill's frontmatter name and description."""
    skills: list[SkillDoc] = []
    for skill_file in sorted(PLUGINS_DIR.glob("*/skills/*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if match is None:
            continue
        loaded = t.cast("object", yaml.safe_load(match.group(1)))
        if not isinstance(loaded, dict):
            continue
        data = t.cast("dict[str, object]", loaded)
        name = data.get("name") or skill_file.parent.name
        description = data.get("description") or ""
        skills.append(SkillDoc(name=str(name), description=str(description).strip()))
    return skills


def _load_cases() -> list[dict[str, object]]:
    """Load skill-creator-compatible eval cases, if any are present."""
    if not CASES_DIR.is_dir():
        return []
    cases: list[dict[str, object]] = []
    for path in sorted(CASES_DIR.glob("*.json")):
        loaded = t.cast("object", json.loads(path.read_text(encoding="utf-8")))
        if isinstance(loaded, dict):
            cases.append(t.cast("dict[str, object]", loaded))
    return cases


def _check_triggers(corpus: Corpus) -> tuple[int, int, list[str]]:
    """Rank each case's positive and negative prompts. Returns hits, total, failures."""
    failures: list[str] = []
    hits = 0
    total = 0
    for case in _load_cases():
        skill_name = str(case.get("skill_name", ""))
        trigger = case.get("trigger")
        if not isinstance(trigger, dict):
            continue
        trigger_map = t.cast("dict[str, object]", trigger)

        positives = trigger_map.get("positive")
        if isinstance(positives, list):
            for entry in t.cast("list[object]", positives):
                if not isinstance(entry, dict):
                    continue
                item = t.cast("dict[str, object]", entry)
                prompt = str(item.get("prompt", ""))
                top_k = int(t.cast("int", item.get("top_k", 3)))
                total += 1
                ranked = [row.name for row in rank_skills(prompt, corpus)[:top_k]]
                if skill_name in ranked:
                    hits += 1
                else:
                    failures.append(f"{skill_name}: not in top {top_k} for {prompt!r}")

        negatives = trigger_map.get("negative")
        if isinstance(negatives, list):
            for entry in t.cast("list[object]", negatives):
                if not isinstance(entry, dict):
                    continue
                item = t.cast("dict[str, object]", entry)
                prompt = str(item.get("prompt", ""))
                ranked = rank_skills(prompt, corpus)
                if (
                    ranked
                    and ranked[0].name == skill_name
                    and ranked[0].score >= NEGATIVE_MIN_SCORE
                ):
                    failures.append(f"{skill_name}: ranks first for negative prompt {prompt!r}")

    return hits, total, failures


@app.command()
def check(min_rank1: int = 0) -> None:
    """Lint every description and fail on colliding or unroutable skills."""
    skills = discover_skills()
    if not skills:
        console.print("[red]No skills discovered.[/red]")
        raise typer.Exit(code=1)

    errors: list[str] = []
    for skill in skills:
        errors.extend(lint_description(skill))

    corpus = build_corpus(skills)

    for left, right, score in find_collisions(corpus, COLLISION_ERROR):
        errors.append(f"{left} and {right} descriptions are {score:.2f} similar")
    for left, right, score in find_collisions(corpus, COLLISION_WARN):
        if score < COLLISION_ERROR:
            console.print(f"[yellow]warn[/yellow] {left} / {right} similarity {score:.2f}")

    hits, total, failures = _check_triggers(corpus)
    errors.extend(failures)

    if total and min_rank1:
        rate = hits / total * 100
        if rate < min_rank1:
            errors.append(f"trigger hit rate {rate:.0f}% is below the {min_rank1}% floor")

    for error in errors:
        console.print(f"[red]error[/red] {error}")

    if errors:
        console.print(f"\n{len(errors)} error(s) found.")
        raise typer.Exit(code=1)

    summary = f"{len(skills)} skills checked"
    if total:
        summary += f", {hits}/{total} trigger prompts routed"
    console.print(f"{summary}. 0 errors found.")


@app.command()
def route(prompt: str) -> None:
    """Show how a prompt ranks against the catalog."""
    corpus = build_corpus(discover_skills())
    for ranking in rank_skills(prompt, corpus)[:TOP_N]:
        console.print(f"{ranking.score:.3f}  {ranking.name}")


if __name__ == "__main__":
    app()
