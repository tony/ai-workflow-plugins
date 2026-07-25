# Safety gates

Parallelism and reordering are the biggest speedups and the biggest correctness
risks. A candidate that touches execution order (`-n auto`, `--dist`, `--ff`,
random order) must pass these gates in `01-benchmark` before `02-plan` will score
it — and a failure drops it at the rubric's hard safety gate.

## Gate 1 — order independence (H17)

A suite is order-independent when every test passes regardless of what ran before
it. Hidden coupling (a module-global mutated by one test and read by another) is
invisible until the order changes.

```bash
uvx --with pytest-randomly --from pytest pytest -p randomly
```

- Run **≥ 3 seeds**. Reproduce a failure with `--randomly-seed=last`, then
  `--randomly-seed=<n>`.
- Run any suspect nodeid **in isolation**: if it fails alone but passes in the
  full run, it depends on another test's side effect.
- Without `pytest-randomly`, approximate: run a single test alone, run a module in
  reverse (`pytest tests/test_x.py::test_b tests/test_x.py::test_a`), and run
  subsets.

**Fix the coupling, do not hide it:** reset the mutated global in a fixture
teardown (or make it function-scoped). Only then is a parallel/reorder speedup
eligible.

## Gate 2 — collection determinism (H18)

xdist distributes tests by collection order; workers must collect the **same** set
in the **same** order.

```bash
pytest --co -q | sort > /tmp/co-a.txt
pytest --co -q | sort > /tmp/co-b.txt
diff /tmp/co-a.txt /tmp/co-b.txt
```

A non-empty diff is a hard xdist blocker. Causes and fixes:

- `parametrize` over a `set` or unordered dict → list-ify the values.
- Collection that branches on the clock, `random`, or environment → make it
  deterministic.

## Gate 3 — green re-run

The change must leave the suite green on a clean serial re-run (cache disabled)
before its delta is even measured. A change that "speeds up" by skipping or
breaking tests scores nothing.

## Parallelism decision tree

Only after gates 1–3 pass:

1. **Is collection fast?** `time pytest --co -q`. If collection is a large fraction
   of wall-time (H22), do **not** xdist — each worker re-collects. Fix collection
   first (narrow `testpaths`, disable unused autoload plugins, reduce parametrize
   explosion, defer heavy imports).
2. **Enable parallelism** (H19): `-n auto`. Cap `--maxprocesses` when the suite is
   I/O-bound on one shared resource.
3. **Flaky under `-n auto`?** (H20) Run it 5–10×; if failures move between workers,
   co-locate stateful tests with `--dist=loadscope` (group by module/class) or
   `--dist=loadfile`, and/or mark groups with `@pytest.mark.xdist_group`. Refactor
   the shared state only if grouping is insufficient.
4. **Session fixture per worker?** (H21) A session fixture runs once **per worker**.
   For a single shared resource use the `FileLock` single-exec pattern or a
   `testrun_uid`-keyed resource.

## What makes a speedup "safe"

Map directly to the rubric's `safety` dimension:

- `safety ≈ 0.9` — pure config/selection, or widening the scope of **read-only**
  setup that passed gates 1–2.
- `safety ≈ 0.5` — scope change on a possibly-mutated resource, autouse removal, or
  xdist **with** grouping.
- `safety ≈ 0.1` — parallelizing across known shared mutable state, or deleting a
  fixture reachable only via `getfixturevalue`. These fall below the `0.4` gate and
  are never auto-applied; the prerequisite refactor is surfaced as its own
  hypothesis instead.

## Measurement hygiene (so the gates' verdicts are trustworthy)

- Measure serially, cache disabled (`-p no:cacheprovider`), N ≥ 3 runs.
- Never compare a parallel run's wall-time to a serial baseline as "the speedup" —
  benchmark the *change*, holding the run mode fixed, then evaluate parallelism as
  its own separate candidate.
- Treat rows below the ~50ms trust floor as noise.
