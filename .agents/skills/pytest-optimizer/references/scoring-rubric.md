# Scoring rubric

How `02-plan` ranks benchmarked speedup candidates. The rubric is **safety-first**:
it answers "which changes are worth the risk?", not "which are fastest?".

## Dimensions and weights

Each dimension is scored `0.0`–`1.0`. The total is their weighted sum.

| Dimension | Weight | `1.0` means | `0.0` means |
|-----------|-------:|-------------|-------------|
| `safety` | 0.35 | Behavior-preserving: pure config/selection, or widening the scope of read-only setup that passed the order-independence (H17) and collection-determinism (H18) gates. | Parallelizing across known shared mutable state, or deleting a fixture reachable only via `getfixturevalue`. |
| `impact` | 0.30 | **Measured** in `01-benchmark`: recovers > 40% of suite wall-time, or removes the single dominant test/fixture. | Delta within the noise band (median + k·MAD) — indistinguishable from jitter. |
| `effort` | 0.15 | Trivial: `addopts`/marker/flag, or a one-line scope change. | Restructuring shared global state across modules. |
| `confidence` | 0.12 | Serial, cache-disabled, repeated runs; delta many multiples of the noise floor. | Collection-bound or xdist-contended numbers known to be distorted, or sub-50ms rows. |
| `reversibility` | 0.08 | A single isolated commit, config-only revert. | An entangled multi-file refactor. |

```
total = 0.35*safety + 0.30*impact + 0.15*effort
      + 0.12*confidence + 0.08*reversibility
```

Mid-scale anchors keep scoring consistent:

- `safety = 0.5` — scope change on a possibly-mutated resource, autouse removal,
  or xdist with grouping.
- `impact = 0.5` — recovers 5–15% of suite wall-time.
- `effort = 0.6` — hoist a build into a fixture and add a reset; `0.3` — introduce
  a factory fixture or a filelock single-exec pattern.

## Hard gates (applied before ranking)

A candidate is **dropped from the plan, never auto-applied**, when either holds:

1. **Safety gate:** `safety < 0.4`. Correctness risk outweighs any speed.
2. **Noise gate:** `impact == 0` — the measured delta did not clear the project's
   noise band in `01-benchmark`. A speedup that cannot be distinguished from
   jitter is not a speedup.

Surviving candidates are ordered by `total` descending, then by the ordering
constraints below.

## Ordering constraints

Score sets the priority, but some changes must precede others regardless of score:

1. **Safety-gate fixes first** — make collection deterministic (H18) and prove
   order independence (H17) before any parallel or reorder speedup.
2. **Typing and parametrize migrations early** — they are low-risk, make later
   diffs readable, and rarely conflict (H26–H32).
3. **Scope and consolidation before parallelism** — fix fixture scope (H10) and
   merge duplicates (H11, H25) before introducing `-n auto` (H19), so xdist runs
   over an already-lean suite.
4. **One speedup per commit** — never bundle; `reversibility` exists so a failed
   green-verify reverts exactly one change.

## Worked examples

**Widen a read-only `make_config` fixture from `function` to `session`** (H10):

| Dimension | Score | Reason |
|-----------|------:|--------|
| safety | 0.9 | Setup is read-only; passed H17 across 3 seeds and H18. |
| impact | 0.7 | Measured 22% suite reduction (setup ran 40×, now once). |
| effort | 1.0 | One-line `scope=` change. |
| confidence | 0.9 | Serial, 5 runs, delta ≫ noise floor. |
| reversibility | 0.9 | Single fixture line. |

`total = 0.855` → top of the plan.

**Enable `-n auto` over a suite sharing one on-disk SQLite file** (H19/H16):

| Dimension | Score | Reason |
|-----------|------:|--------|
| safety | 0.1 | Parallel writes to one shared mutable DB file. |

`safety < 0.4` → **dropped at the gate**. The plan instead surfaces the
prerequisite refactor (isolate the DB per worker via `tmp_path_factory` +
`worker_id`, or a transaction-rollback fixture) as a *separate* hypothesis to
benchmark, not as an auto-applied speedup.

## Tunable knobs

These defaults are deliberately conservative; a project may override them in the
orchestration plan:

- **Noise-band multiplier `k`** (default `3`) in `median + k·MAD`. Lower `k`
  credits smaller deltas as real; higher `k` demands a larger, surer win.
- **Safety-gate cutoff** (default `0.4`). Raise it to be stricter about which
  changes may be applied at all.
- **Trust floor** (default `~50ms`). Duration rows below this are too noisy to
  rank; `confidence` is penalized for candidates resting on them.
