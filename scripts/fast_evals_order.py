#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Order pending fast-suite cases longest-first, and remember how long they took.

A pass is dominated by its slowest case, so starting the ten-minute ensemble
case before the forty-second ones keeps it from straggling alone after every
worker has gone idle.

Durations have to be cached separately from results. A completed case is skipped
on the next pass and an incomplete one is deleted before it runs again, so by
the time ordering happens no pending case has an aggregate left to read.

Reads specs on stdin, one ``plugin|case`` per line, and writes them reordered.
With ``--record SPEC AGGREGATE`` it instead files that run's duration away for
next time.
"""

from __future__ import annotations

import json
import os
import sys
import typing as t
from pathlib import Path

UNKNOWN = float("inf")


def _duration(aggregate: Path) -> float | None:
    """Return the duration recorded in ``aggregate``, or None when unreadable."""
    try:
        with aggregate.open(encoding="utf-8") as handle:
            report = t.cast("object", json.load(handle))
    except (OSError, ValueError):
        return None
    if not isinstance(report, dict):
        return None
    seconds = t.cast("dict[str, object]", report).get("durationSeconds")
    return float(seconds) if isinstance(seconds, (int, float)) else None


def _load_cache(path: Path) -> dict[str, float]:
    """Return the spec-to-seconds cache at ``path``, empty when unreadable."""
    try:
        with path.open(encoding="utf-8") as handle:
            loaded = t.cast("object", json.load(handle))
    except (OSError, ValueError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    return {
        key: float(value)
        for key, value in t.cast("dict[str, object]", loaded).items()
        if isinstance(value, (int, float))
    }


def record(cache_path: Path, spec: str, aggregate: Path) -> int:
    """Store ``aggregate``'s duration against ``spec``, leaving the cache intact on failure."""
    seconds = _duration(aggregate)
    if seconds is None:
        return 0
    cache = _load_cache(cache_path)
    cache[spec] = seconds
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as handle:
        json.dump(cache, handle, indent=1, sort_keys=True)
    return 0


def order(specs: list[str], out: Path, cache_path: Path) -> list[str]:
    """Sort ``specs`` longest-first, preferring a live aggregate over the cache.

    A case nobody has timed sorts first, because its cost is unknown and
    assuming it cheap is the expensive mistake:

    >>> order(["a|slow", "a|quick", "a|new"], Path("/nonexistent"), Path("/nonexistent"))
    ['a|slow', 'a|quick', 'a|new']
    """
    cache = _load_cache(cache_path)

    def seconds(spec: str) -> float:
        plugin, _, case = spec.partition("|")
        live = _duration(out / f"{plugin}--{case}" / "aggregate-result.json")
        return live if live is not None else cache.get(spec, UNKNOWN)

    return sorted(specs, key=lambda spec: -seconds(spec))


def main() -> int:
    """Reorder stdin, or record one duration when called with ``--record``."""
    out = Path(os.environ.get("FAST_EVAL_OUT", "evals/results/fast"))
    cache_path = Path(os.environ.get("FAST_EVAL_TIMINGS", str(out / ".timings.json")))
    if len(sys.argv) > 1 and sys.argv[1] == "--record":
        return record(cache_path, sys.argv[2], Path(sys.argv[3]))
    specs = [line.strip() for line in sys.stdin if line.strip()]
    print("\n".join(order(specs, out, cache_path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
