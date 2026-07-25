---
name: pytest-optimizer-01-benchmark
description: >-
  Phase 2 of the pytest-optimizer pipeline. Test each hypothesis from
  00-scan in isolation on a throwaway working copy and re-measure its
  wall-clock delta against the project's noise band. Runs the safety gates
  (order independence, collection determinism, green re-run) per candidate,
  rejects anything within noise or failing a gate, and records the measured
  delta, confidence, and observed risk to benchmarks.json. Never mutates
  committed history. Idempotent per hypothesis id. Use after 00-scan to find
  out which proposed speedups are real.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit", "AskUserQuestion"]
metadata:
  argument-hint: "[--only=<heuristic-id>] [--runs=N] [--force] [--memory-dir=<path>]"
  source: "plugins/pytest-optimizer/commands/01-benchmark.md"
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
the user to run the `pytest-optimizer-00-scan` skill first. Substitute that resolved test
command wherever this file writes `pytest`. Skip any hypothesis whose
(content-derived) id already has a benchmark recorded **against the current
baseline token**, unless `--force`; a re-baseline after `03-execute` re-opens all
candidates for fresh measurement.

## Step 2: Per hypothesis — apply, measure, gate

For each open hypothesis, in isolation:

1. **Isolate.** Create a scratch worktree (or snapshot the working tree) so the
   change can be applied and discarded without touching history.
2. **Apply** the single change the heuristic prescribes
   (`references/heuristic-catalog.md`).
3. **Measure.** Run the suite serially, cache disabled, `--runs` times, recording
   total wall-time:

   ```bash
   pytest -p no:cacheprovider -p no:randomly -q
   ```

   Compute the median delta (`baseline_median − candidate_median`) vs
   `baseline.json`. It is a **real** speedup only if `median_delta > k·MAD`
   (default `k = 3`) — i.e. the saving exceeds the noise band's half-width.
   Within-noise → `impact = 0`, rejected.
4. **Safety gates** (`references/safety-gates.md`), required
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
`references/output-contract.md`: hero block, then
`## Validated`, `## Rejected`, `## Safety-gate results`. Close with an
`ask-user-choice` panel offering to build the plan, re-benchmark a subset, or stop.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
