---
name: 01-benchmark
description: "Use when benchmarking pytest optimization hypotheses from 00-scan in isolation to identify speedups that beat measured noise."
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit", "AskUserQuestion"]
argument-hint: "[--only=<heuristic-id>] [--runs=N] [--force] [--memory-dir=<path>]"
user-invocable: true
disable-model-invocation: true
---


# 01-benchmark

Prove or disprove each hypothesis by measurement. This phase applies candidates on
a **throwaway copy** (a scratch git worktree or a stash-guarded working tree),
never on committed history.

`$ARGUMENTS` may pass `--only=<heuristic-id>` to benchmark a subset, `--runs=N`
(measurement runs per candidate, default matches the baseline), and `--force` to
re-benchmark ids already recorded.

## Step 1: Load inputs

Read `baseline.json` (noise band, test command, capabilities) and
`hypotheses.json` from the resolved memory directory. If either is missing, tell
the user to run `/pytest-optimizer:00-scan` first. Substitute that resolved test
command wherever this file writes `pytest`. Skip any hypothesis whose
(content-derived) id already has a benchmark recorded **against the current
baseline token**, unless `--force`; a re-baseline after `03-execute` re-opens all
candidates for fresh measurement.

## Step 2: Per hypothesis — apply, measure, gate

For each open hypothesis, in isolation:

1. **Isolate.** Create a scratch worktree (or snapshot the working tree) so the
   change can be applied and discarded without touching history.
2. **Apply** the single change the heuristic prescribes
   (`../../references/heuristic-catalog.md`).
3. **Measure.** Run the suite serially, cache disabled, `--runs` times, recording
   total wall-time:

   ```bash
   pytest -p no:cacheprovider -p no:randomly -q
   ```

   Compute the median delta (`baseline_median − candidate_median`) vs
   `baseline.json`. It is a **real** speedup only if `median_delta > k·MAD`
   (default `k = 3`) — i.e. the saving exceeds the noise band's half-width.
   Within-noise → `impact = 0`, rejected.
4. **Safety gates** (`../../references/safety-gates.md`), required
   for any change touching order/scope/parallelism:
   - order independence (H17) across ≥ 3 seeds and in isolation;
   - collection determinism (H18);
   - green serial re-run.
   A gate failure rejects the candidate and surfaces the prerequisite refactor as
   its own follow-up hypothesis.
5. **Discard** the change and restore the clean state.

## Step 3: Record

Write `benchmarks.json`: per id, the applied-diff summary, run count, median
delta, `clears_noise`, gate results, a `confidence` score (serial + repeated
+ delta-above-floor → high), the observed risk, and a `verdict`
(`validated`/`rejected` + reason). Update `state.json`
(`phase=benchmark`, benchmarked ids). The phase is idempotent per id.

## Step 4: Report

Emit the `01-benchmark` sections from
`../../references/output-contract.md`: hero block, then
`## Validated`, `## Rejected`, `## Safety-gate results`. Close with an
`AskUserQuestion` panel offering to build the plan, re-benchmark a subset, or stop.
