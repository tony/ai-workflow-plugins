---
name: pytest-optimizer-00-scan
description: >-
  Phase 1 of the pytest-optimizer pipeline. Profile the suite and emit
  hypotheses without editing any test. Detects pytest + plugin versions and
  gates capabilities, establishes a reproducible timing baseline with a
  measured noise band, ranks the slowest test bodies and the slowest fixture
  setup/teardown separately, and runs the static detectors
  (unused/mis-scoped/ duplicate fixtures, mark-on-fixture, typing and
  parametrize gaps). Writes baseline.json, capabilities.json, and
  hypotheses.json to the memory directory. Read-only on the test suite. Use
  when starting a pytest optimization pass or re-baselining after changes.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "AskUserQuestion"]
metadata:
  argument-hint: "[test-path-or-marker] [--force] [--runs=N] [--memory-dir=<path>]"
  source: "plugins/pytest-optimizer/commands/00-scan.md"
---

# 00-scan

Profile, detect, hypothesize. This phase **only reads** the suite and **only
writes** JSON to the memory directory. No test is edited here.

`$ARGUMENTS` may scope the run to a path or marker, set `--runs=N` (baseline
sample count, default 5), `--force` to ignore the idempotency token, and
`--memory-dir` to override the memory location.

## Step 1: Preflight

Detect preferred tools (`rg`/`ag`/`fd`/`jq`/`uv`/`uvx`) and read the project's
**own** test command from `AGENTS.md`, `CLAUDE.md`, `justfile`, `tox.ini`, or
`pyproject.toml`. Do not hardcode a runner. Record the resolved command; every
later phase reuses it. Substitute it wherever this file writes `pytest`.

## Step 2: Resolve memory and check idempotency

Resolve the memory directory per `references/memory-schema.md`
(repo-root `.pytest-optimizer/`, gitignored; XDG fallback). Compute the
idempotency token (git HEAD + collection node-ids + pytest/plugin versions +
environment fingerprint). If `state.json` shows `scan` completed with an unchanged
token and
`hypotheses.json` exists, report "already scanned" and stop — unless `--force`.

## Step 3: Detect capabilities

Probe the installed pytest and plugins against
`references/version-matrix.md`. Write
`capabilities.json`. Use only available features below; fall back as the matrix
directs (e.g. no `--durations-min` pre-6.1 → post-filter rows).

## Step 4: Establish the baseline and noise band

Run the suite serially, cache disabled, `--runs` times, and record total
wall-time each run:

```bash
pytest -p no:cacheprovider -p no:randomly -q
```

Compute the median and MAD of the per-run totals; set the noise band
(`median + k·MAD`, default `k = 3`) and the ~50ms trust floor. Write the env
fingerprint, versions, capabilities, and the band to `baseline.json`. See
`references/durations-parsing.md`.

## Step 5: Profile slowest tests and fixtures

Capture per-phase timings and bucket rows by the `when` token (`call` vs
`setup`/`teardown`), de-duplicating by `(nodeid, when)`:

```bash
pytest --durations=0 --durations-min=0.005 -p no:cacheprovider -p no:randomly
```

Rank slowest **test bodies** (`call`, H01) and slowest **fixture
setup/teardown** (`setup`/`teardown`, H02). For shared higher-scope fixtures whose
cost is billed to one nodeid (H03), note the attribution; offer the opt-in timing
plugin if precise per-fixture cost is needed. Persist the timings to
`baseline.json`.

## Step 6: Run the static detectors

Work through `references/heuristic-catalog.md`, using
`references/fixture-analysis.md` for the fixture recipes and
`references/parametrize-convention.md` for the typing/
parametrize gaps:

- Fixtures: unused (H08/H09/H41), mis-scoped (H10/H13), duplicate (H11), autouse
  (H12/H15), mark-on-fixture (H43), empty conftest (H42).
- Collection/capability errors (H14/H22/H44).
- Typing and parametrize gaps (H26–H32).
- I/O, sleep, markers, timeouts (H15/H33/H37/H39/H40).
- Recomputation and duplication (H24/H25/H34/H35/H36/H38).

Apply the `getfixturevalue` guard (H09) before proposing any fixture deletion.

## Step 7: Emit hypotheses

Write `hypotheses.json`: one entry per firing detector, each tagged with its
heuristic id, the goal(s) it addresses, the raw evidence, and prior risk/effort.
Do **not** estimate impact here — `01-benchmark` measures it. Update `state.json`
(`phase=scan`, `completed.scan=true`, token).

## Step 8: Report

Emit the `00-scan` sections from
`references/output-contract.md`: a hero block, then
`## Environment`, `## Baseline`, `## Slowest tests`, `## Slowest fixtures`,
`## Hypotheses`. Close with an `ask-user-choice` panel offering to benchmark the
hypotheses, narrow scope, or stop.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
