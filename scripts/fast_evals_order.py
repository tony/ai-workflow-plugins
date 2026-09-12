#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Order pending fast-suite cases longest-first, using previously recorded times.

A pass is dominated by its slowest case. Starting the ten-minute ensemble case
before the forty-second ones keeps it from straggling alone after every worker
has gone idle. A case never run before sorts first, since its cost is unknown
and guessing it cheap is the expensive mistake.

Reads specs on stdin, one ``plugin|case`` per line; writes them back reordered.
"""

from __future__ import annotations

import json
import os
import sys
import typing as t
from pathlib import Path

UNKNOWN = float("inf")


def recorded_seconds(out: Path, spec: str) -> float:
    """Return the duration a previous pass recorded for ``spec``, else infinity."""
    plugin, _, case = spec.partition("|")
    path = out / f"{plugin}--{case}" / "aggregate-result.json"
    try:
        with path.open(encoding="utf-8") as handle:
            report = t.cast("object", json.load(handle))
    except (OSError, ValueError):
        return UNKNOWN
    if not isinstance(report, dict):
        return UNKNOWN
    seconds = t.cast("dict[str, object]", report).get("durationSeconds")
    return float(seconds) if isinstance(seconds, (int, float)) else UNKNOWN


def main() -> int:
    """Reorder the specs on stdin, longest recorded run first."""
    out = Path(os.environ.get("FAST_EVAL_OUT", "evals/results/fast"))
    specs = [line.strip() for line in sys.stdin if line.strip()]
    specs.sort(key=lambda spec: -recorded_seconds(out, spec))
    print("\n".join(specs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
