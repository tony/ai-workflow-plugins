#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Decide whether one fast-suite result counts as a pass.

A score alone is not enough. A routing case usually pairs a grader asserting the
Skill invocation with one grading the answer, so at a 0.5 threshold the answer
keeps a broken route green. An interrupted run also writes an aggregate, and
reusing that verdict reports a suite green on grading that never finished.
"""

from __future__ import annotations

import json
import os
import sys
import typing as t
from pathlib import Path


def _mapping(value: object) -> dict[str, object]:
    """Return ``value`` as a mapping, or an empty one when it is not."""
    return t.cast("dict[str, object]", value) if isinstance(value, dict) else {}


def _sequence(value: object) -> list[object]:
    """Return ``value`` as a list, or an empty one when it is not."""
    return t.cast("list[object]", value) if isinstance(value, list) else []


def _routing_graders(case: dict[str, object]) -> set[str]:
    """Name every grader in ``case`` that asserts a Skill invocation."""
    names: set[str] = set()
    for grader in _sequence(case.get("graders")):
        entry = _mapping(grader)
        name = entry.get("name")
        if (
            entry.get("type") == "tool_used"
            and _mapping(entry.get("config")).get("tool") == "Skill"
            and isinstance(name, str)
        ):
            names.add(name)
    return names


def classify(report: dict[str, object], threshold: float) -> str:
    """Return ``pass``, ``fail: <reason>``, or ``incomplete: <reason>``.

    A run that was cut short is incomplete rather than failed, so the caller
    reruns it instead of caching a verdict for grading that never finished:

    >>> classify({"partial": True, "partialReason": "interrupted"}, 0.5)
    'incomplete: interrupted'

    A routing grader carries its own veto, whatever the aggregate score:

    >>> routing = {"name": "skill-fired", "type": "tool_used", "config": {"tool": "Skill"}}
    >>> run = {"graders": [{"name": "skill-fired", "passed": False}]}
    >>> classify(
    ...     {
    ...         "cases": [{"graders": [routing], "arms": {"with": [run]}}],
    ...         "aggregates": {"overallScore": 1.0},
    ...     },
    ...     0.5,
    ... )
    'fail: routing grader skill-fired did not pass'

    Otherwise the score decides:

    >>> classify({"cases": [], "aggregates": {"overallScore": 0.75}}, 0.5)
    'pass'
    >>> classify({"cases": [], "aggregates": {"overallScore": 0.25}}, 0.5)
    'fail: score 0.25 below 0.5'
    """
    if report.get("partial"):
        reason = report.get("partialReason")
        return f"incomplete: {reason if isinstance(reason, str) and reason else 'partial'}"

    for case in _sequence(report.get("cases")):
        case_map = _mapping(case)
        routing = _routing_graders(case_map)
        for run in _sequence(_mapping(case_map.get("arms")).get("with")):
            run_map = _mapping(run)
            error = run_map.get("error")
            if error:
                return f"incomplete: run error ({str(error)[:40]})"
            for grader in _sequence(run_map.get("graders")):
                entry = _mapping(grader)
                name = entry.get("name")
                if isinstance(name, str) and name in routing and not entry.get("passed"):
                    return f"fail: routing grader {name} did not pass"

    raw = _mapping(report.get("aggregates")).get("overallScore")
    score = float(raw) if isinstance(raw, (int, float)) else 0.0
    if score < threshold:
        return f"fail: score {score} below {threshold}"
    return "pass"


def verdict(path: Path, threshold: float) -> str:
    """Classify the aggregate at ``path``, treating an unreadable one as incomplete."""
    try:
        with path.open(encoding="utf-8") as handle:
            loaded = t.cast("object", json.load(handle))
    except (OSError, ValueError) as exc:
        return f"incomplete: unreadable ({exc.__class__.__name__})"
    return classify(_mapping(loaded), threshold)


def main() -> int:
    """Print the verdict for the aggregate named by the single argument."""
    threshold = float(os.environ.get("FAST_EVAL_THRESHOLD", "0.5"))
    print(verdict(Path(sys.argv[1]), threshold))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
