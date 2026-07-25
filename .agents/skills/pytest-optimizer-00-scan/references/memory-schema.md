# Memory schema

The four phases communicate only through durable JSON files. This is what makes
the pipeline **idempotent** (re-running a completed phase is a no-op while inputs
are unchanged) and **resumable** (a crash mid-execute picks up at the next item).

JSON is chosen over pickle on purpose: it is diffable, language-agnostic, and safe
to inspect in a PR.

## Location resolution

Resolve the memory directory **once** and record it in `state.json` so all phases
agree.

1. **Preferred — project-owned, gitignored.** `.pytest-optimizer/` at the repo
   root. Append `.pytest-optimizer/` to `.gitignore` idempotently (check first;
   never duplicate the line). This keeps the durable artifacts next to the code
   they describe and lets the run resume on the same checkout across sessions.
2. **Fallback — per-user cache.** When the tree is read-only, or the user declines
   any in-tree file, use:
   - `$XDG_CACHE_HOME/pytest-optimizer/<repo-id>/` (Linux/macOS; default
     `~/.cache/...` when `XDG_CACHE_HOME` is unset), or
   - `%LOCALAPPDATA%\pytest-optimizer\<repo-id>\` (Windows).
   - `<repo-id>` is a short hash of the repo's absolute path + git remote, so two
     checkouts of the same repo do not collide and two different repos do not
     share state.
3. **Override.** `--memory-dir=<path>` forces a location (useful in CI).

The fallback needs no `.gitignore` edit because it lives outside the tree.

## Idempotency token

Each phase is keyed by:

```
token = hash(git HEAD
             + sorted collection node-ids
             + pytest version + plugin versions
             + environment fingerprint)
```

A phase is a **no-op** on re-run when all three hold:

- `state.json` marks the phase `completed`, **and**
- the token is unchanged, **and**
- the phase's output file exists.

`--force` overrides all three. The environment fingerprint (Python version, OS,
CPU model) is included because the noise band and absolute timings are
machine-specific; moving machines re-baselines automatically. **`git HEAD` is
included so the commits `03-execute` produces change the token** — the next
`00-scan` re-measures a fresh baseline on its own, which is what lets the loop
continue for a second pass instead of short-circuiting as already-completed.

## Baseline-diff strategy

A candidate counts as a real speedup only when its measured median delta
(`baseline_median − candidate_median`, the seconds saved) exceeds the **half-width
of the noise band** (`k · MAD`) recorded in `baseline.json`:

```
real_speedup  <=>  median_delta > k * MAD     (default k = 3)
```

Equivalently, in absolute terms: `candidate_median < baseline_median − k · MAD`.
The `median ± k·MAD` band describes total wall-time jitter; the threshold on the
*improvement* is that band's half-width, `k · MAD` — not the absolute median.

This is the single rule that prevents the loop from committing jitter. The band is
measured per project in `00-scan` (N serial, cache-disabled runs), never quoted as
a fixed number.

## Files

All paths are relative to the resolved memory directory.

| File | Written by | Purpose |
|------|-----------|---------|
| `state.json` | all phases | Phase cursor + idempotency tokens + resolved memory path |
| `baseline.json` | `00-scan` | Env fingerprint, versions, capability gates, per-phase timings, noise band |
| `capabilities.json` | `00-scan` | Resolved version-matrix probes → available features + fallbacks |
| `hypotheses.json` | `00-scan` | Candidate speedups tagged with heuristic id + goals + evidence |
| `benchmarks.json` | `01-benchmark` | Per-hypothesis measured delta vs noise + safety-gate outcomes |
| `plan.json` | `02-plan` | Ranked commit plan: score breakdown, files, draft message, verify |
| `execution-log.json` | `03-execute` | Durable per-item checkpoint: applied/verified/committed or skipped |

The canonical JSON Schema for these lives in `templates/state.schema.json`.

### `state.json`

```json
{
  "phase": "benchmark",
  "run_id": "string",
  "memory_dir": ".pytest-optimizer",
  "collection_hash": "string",
  "env_token": "string",
  "completed": { "scan": true, "benchmark": false, "plan": false, "execute": false },
  "last_applied_index": -1
}
```

### `baseline.json`

```json
{
  "captured_at": "ISO-8601",
  "python": "3.13.x",
  "pytest_version": "9.1.1",
  "plugins": { "pytest-xdist": "3.x", "pytest-randomly": "3.x" },
  "capabilities": { "durations_min": true, "stash": true },
  "runs": [ { "wall_seconds": 12.4 }, { "wall_seconds": 12.6 } ],
  "noise": { "median": 12.5, "mad": 0.15, "floor": 0.05, "k": 3 },
  "timings": [ { "nodeid": "tests/test_x.py::test_a", "phase": "setup", "seconds": 0.42 } ]
}
```

### `hypotheses.json`

Each `id` is **derived from content** — `<heuristic>-<sorted target files>-<short
evidence digest>` — not a sequential counter. So an unchanged candidate keeps the
same id across re-scans (and `01-benchmark` can correctly skip it), while a
genuinely new candidate gets a new id. Benchmarks are scoped to the baseline
token: a re-baseline after `03-execute` re-opens all candidates for fresh
measurement.

```json
[
  {
    "id": "H10-conftest-make_config",
    "heuristic": "H10",
    "addresses": [5, 6],
    "evidence": "make_config SETUP runs 40x at function scope, body ~0.3s",
    "est_risk": "medium",
    "est_effort": "small",
    "status": "open"
  }
]
```

### `benchmarks.json`

```json
[
  {
    "id": "H10-conftest-make_config",
    "runs": 5,
    "median_delta": 2.7,
    "clears_noise": true,
    "gates": { "order_indep": true, "collection_det": true, "green": true },
    "confidence": 0.9,
    "observed_risk": "low",
    "verdict": "validated"
  }
]
```

### `plan.json`

```json
[
  {
    "order": 1,
    "id": "H10-conftest-make_config",
    "score": { "safety": 0.9, "impact": 0.7, "effort": 1.0, "confidence": 0.9, "reversibility": 0.9, "total": 0.855 },
    "files": ["tests/conftest.py"],
    "commit": { "subject": "test(fixtures) widen make_config to session scope", "body": "why: ...\n\nwhat:\n- ..." },
    "verify": "<project test command>",
    "depends_on": []
  }
]
```

### `execution-log.json`

```json
[
  {
    "order": 1,
    "id": "H10-conftest-make_config",
    "applied": true,
    "verify": { "passed": true, "output_ref": "checkpoint-1.txt" },
    "commit_sha": "abc1234",
    "skip_reason": null,
    "ts": "ISO-8601"
  }
]
```

## gitignore handling

- Append `.pytest-optimizer/` to `.gitignore` only if not already present.
- The opt-in project-owned pytest plugin/cache scaffold (`templates/`) is also
  gitignored by default; the user may choose to commit it instead.
- When the XDG/LOCALAPPDATA fallback is used, no `.gitignore` edit happens.
