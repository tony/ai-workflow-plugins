# Durations parsing

How `00-scan` measures and ranks. pytest's profiler is `--durations`, implemented
in `_pytest/runner.py` over `_pytest/timing.py`. Understanding exactly what it
reports avoids three common mis-reads.

## What pytest measures

Every test item runs **three independently timed phases** — `setup`, `call`,
`teardown` — each wrapped by `CallInfo.from_call`:

- `setup` — the full fixture/collector setup chain for that item, plus every
  active plugin's setup hook work.
- `call` — `item.runtest()`, the test body.
- `teardown` — finalizers for that item.

The ranked `duration` is a single `perf_counter()` delta (pytest ≥ 6.0); it is
**not** warmed or averaged, so fast rows are high-variance.

## Three things the table does *not* do

1. **It does not group by phase.** `pytest_terminal_summary` collects every report
   carrying a `duration`, sorts them all together descending, and prints
   `{duration:02.2f}s {when:<8} {nodeid}`. A `setup` row and a `call` row are
   interleaved purely by magnitude. The only phase discriminator is the middle
   `when` token.
2. **It does not attribute fixture cost per fixture.** A `setup` row is the whole
   setup chain for one item. A shared higher-scope fixture pays its cost once,
   billed to the **first** item that triggers it — so an expensive
   session-scoped fixture appears as one big `setup` row on one nodeid, not spread
   across its consumers. Per-fixture attribution needs the opt-in timing plugin
   (`templates/pytest_optimizer_plugin.py`).
3. **It does not include collection.** `CollectReport` has no `duration`, so
   collection never appears. Profile collection separately with `time pytest --co -q`
   (see H22).

## Invocations

Rank slowest **test bodies** (H01):

```bash
pytest --durations=25 --durations-min=0.005 -p no:randomly -p no:cacheprovider
```

Rank slowest **fixture setup/teardown** (H02) — use `--durations=0` so no phase is
sliced away before you filter:

```bash
pytest --durations=0 --durations-min=0.01 -p no:cacheprovider
```

Capture **everything** on a small suite (H04), including `0.00s` rows:

```bash
pytest --durations=0 --durations-min=0 -p no:cacheprovider
```

`--durations=0` means "no N-slice" (header reads `slowest durations`), but the
`--durations-min` filter still applies — so `--durations=0` alone still hides
sub-5ms phases. Use `--durations-min=0` (or `-vv`) to truly show all.

## Bucketing by phase

Each row is `<float>s <when> <nodeid>`. Split on the **second** token:

- `when == "call"` → test-body ranking (goal 1).
- `when == "setup"` → fixture/setup-chain ranking (goal 2).
- `when == "teardown"` → finalizer ranking (goal 2).

The same nodeid appears up to three times (once per phase), and parametrized
subtests (pytest ≥ 9.0) add extra `call` rows under one nodeid — **de-duplicate by
`(nodeid, when)`** when aggregating.

## Machine-readable timings (H07)

When the output must be parsed reliably, prefer JUnit XML over scraping the table:

```bash
pytest --junit-xml=report.xml -o junit_duration_report=call
```

Read `testcase@time` for per-test `call` time (`junit_duration_report=call`
isolates the body; the default reports setup+call+teardown). Store the structured
result in `baseline.json`.

## Noise band

Fast rows are not benchmarks. To know whether a later change is a real speedup:

1. Run the same durations command serially (no `-n`), cache disabled, **N ≥ 3**
   times.
2. Compute the **median** total wall-time and the **MAD** (median absolute
   deviation) of the per-run totals.
3. The noise band is `median + k * MAD` (default `k = 3`); the **trust floor** is
   ~50ms — rank nothing below it.
4. A candidate's measured delta counts only if it exceeds the band
   (see `memory-schema.md`, baseline-diff).

Why disable cacheprovider while measuring: its `.pytest_cache` writes happen at
session start/finish (outside any item phase), so they do **not** change the
duration rows — but disabling it gives reproducible total wall-time and one fewer
timed hook in each phase. Never measure under xdist: per-worker re-collection and
contention distort both totals and rows.
