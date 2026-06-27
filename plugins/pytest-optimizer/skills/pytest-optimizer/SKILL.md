---
name: pytest-optimizer
description: >-
  Use when the user wants to make a pytest suite faster, profile slow tests or
  fixtures, find unused or mis-scoped fixtures, consolidate duplicate test
  tracks, migrate to typed parametrize, or apply safe test speedups. Triggers on
  phrases like "speed up my tests", "why are my tests slow", "profile pytest",
  "optimize the test suite", "find slow fixtures", "my fixtures are slow", "which
  fixtures are unused", "the test suite takes too long", or "parallelize my
  tests". Runs a resumable four-phase pipeline (scan, benchmark, plan, execute)
  that measures before it mutates and applies each speedup as its own verified
  commit. Does not edit the suite until a speedup clears the noise band and a
  safety gate.
user-invocable: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[test-path-or-marker] [--phase=scan|benchmark|plan|execute] [--force] [--memory-dir=<path>]"
---

# pytest-optimizer

Profile a pytest suite, find **safe** speedups, and apply each one as its own
verified commit — through a resumable, idempotent four-phase loop.

The core discipline: **measure before you mutate, and prove a speedup against the
project's own timing noise before you trust it.** A theoretically great change
whose measured delta falls inside the noise band is worth nothing and is never
committed.

`$ARGUMENTS` may name a test path or marker to scope the run, a `--phase` to jump
to, `--force` to ignore idempotency tokens and re-run, and `--memory-dir` to
override where durable state is written.

## The loop

```
00-scan  ->  01-benchmark  ->  02-plan  ->  03-execute  ->  (re-scan)
```

Each phase is a separate command that reads and writes durable JSON under the
resolved memory directory. Re-running the whole skill resumes at the first
incomplete phase. After `03-execute`, re-scanning measures the new baseline and
the loop can continue until no candidate clears the rubric.

| Phase | Command | Reads | Writes |
|-------|---------|-------|--------|
| 1 | `/pytest-optimizer:00-scan` | `AGENTS.md`/`CLAUDE.md`, prior `state.json` | `baseline.json`, `capabilities.json`, `hypotheses.json` |
| 2 | `/pytest-optimizer:01-benchmark` | `baseline.json`, `hypotheses.json` | `benchmarks.json` |
| 3 | `/pytest-optimizer:02-plan` | `benchmarks.json`, `baseline.json` | `plan.json` |
| 4 | `/pytest-optimizer:03-execute` | `plan.json`, `baseline.json` | `execution-log.json` + commits |

## Step 1: Detect preferred tools and the project test command

Check for the user's preferred search tools, then read the project's own test and
quality-check commands. **Never hardcode the runner** — `pytest`, `uv run`, `tox`,
`nox`, and `hatch` are all valid and the project declares which it uses.

```bash
for tool in rg ag fd jq uv uvx; do command -v "$tool" >/dev/null 2>&1 && echo "$tool:available" || echo "$tool:missing"; done
```

Read `AGENTS.md`, `CLAUDE.md`, `justfile`, `tox.ini`, and `pyproject.toml` to
discover the canonical commands for running the suite, the formatter, the linter,
and the type checker. Record the test command verbatim; every phase reuses it.

## Step 2: Detect pytest capabilities (version gating)

The toolbox depends on the installed pytest and plugins. Probe once and persist
the result, so later phases use only features that exist.

```bash
python -c "import pytest; print(pytest.__version__)"
```

```bash
pytest --help 2>/dev/null | rg -- '--durations-min|--import-mode|--dist|--sw-reset' || true
```

Resolve each feature against `${CLAUDE_PLUGIN_ROOT}/references/version-matrix.md`
(min version, detection probe, and graceful fallback). For example: pre-6.1 pytest
has no `--durations-min` (post-filter rows yourself); `--dist=loadgroup` needs
`pytest-xdist >= 2.5`; the `Stash` API needs pytest >= 7.0 (else use
`config.cache`). Write the resolved matrix to `capabilities.json`.

## Step 3: Resolve the memory directory

Follow `${CLAUDE_PLUGIN_ROOT}/references/memory-schema.md`. Prefer
`.pytest-optimizer/` at the repo root and add it to `.gitignore` idempotently. If
the tree is read-only or the user declines an in-tree directory, fall back to the
XDG cache path. Record the chosen path in `state.json` so all four phases agree.

## Orchestration Plan

Before any measurement or edit, present a plan and get approval.

1. **Enter plan mode.** In Claude Code call `EnterPlanMode`. In Cursor/Codex/Gemini
   use `/plan` or `Shift+Tab`. If plan mode is unavailable, the phase structure
   below still forces analysis before any write.
2. **The orchestration plan must state:**
   - the resolved test command and quality-check commands (from Step 1);
   - the detected pytest + plugin versions and which capabilities are gated off
     (from Step 2);
   - the resolved memory directory and whether `.gitignore` will be touched;
   - which phase the run will start at (fresh `00-scan`, or resume), and the
     scope (`$ARGUMENTS` path/marker, or the whole suite);
   - that `00-scan` and `02-plan` only read and write JSON memory — no suite edits —
     and that suite edits happen only in `03-execute`, one commit per speedup,
     each green-verified.
3. **Present the plan and wait for approval.** Let the user narrow scope, exclude
   risky heuristics, or cap the number of commits.
4. **Exit plan mode** before running any phase.

## Step 4: Run the phases

Route to the four commands in order, honoring `--phase` and resume state. Each
command embeds its own detailed procedure; this skill only sequences them and
carries the shared context (test command, capabilities, memory dir).

- **`00-scan`** establishes the baseline (median + MAD noise band over N serial,
  cache-disabled runs), profiles slowest tests (`call` rows) and fixture
  setup/teardown (`setup`/`teardown` rows), and runs the static detectors. It
  emits `hypotheses.json`: candidate speedups, each tagged with a heuristic id
  (`H01`–`H44`) and the goal it addresses.
- **`01-benchmark`** applies each hypothesis in isolation on a throwaway working
  copy, re-measures vs the noise band, and runs the safety gates (order
  independence, collection determinism, green re-run). Within-noise or
  gate-failing candidates are rejected with a reason.
- **`02-plan`** scores the survivors with the rubric
  (`${CLAUDE_PLUGIN_ROOT}/references/scoring-rubric.md`), drops anything below the
  safety gate, orders the rest (typing and safety-gate fixes first; scope and
  consolidation before parallelism), and drafts one commit per speedup.
- **`03-execute`** applies the plan one item at a time: edit, run the project
  quality checks + suite, commit alone on green (why/what message), revert and
  skip on failure. It checkpoints after every item and resumes from the last
  applied index.

## Step 5: Report and decide whether to loop again

After `03-execute`, re-measure total wall-time against `baseline.json` and present
the result using the shared output contract
(`${CLAUDE_PLUGIN_ROOT}/references/output-contract.md`): a hero block, the
applied/skipped speedups with their measured deltas, and an `AskUserQuestion`
next-step panel (re-scan for a second pass, scaffold the opt-in cache/plugin, or
stop).

## Opt-in scaffolds

When profiling shows it would help, offer (never impose) to generate a
project-owned, gitignored helper:

- A `pytest11` timing plugin (`templates/pytest_optimizer_plugin.py`) that wraps
  `pytest_fixture_setup` to attribute setup cost to the **individual** fixture —
  the one thing pytest core cannot do, since a `setup` duration row is the whole
  setup chain for an item.
- A `config.cache` memoization snippet (`templates/conftest_cache_snippet.py`)
  with an invalidation token and an xdist write-guard, for expensive build
  artifacts recomputed every run.

Generate only on explicit confirmation; gitignore the output unless the user
chooses to commit it.

## Graceful degradation

- **No plan mode** — keep the phase order; never edit the suite during `00-scan`,
  `01-benchmark`, or `02-plan`.
- **Old pytest** — gate features via the version matrix; widen the noise band when
  duration precision is coarser (pre-6.0 used `time.time()`, not `perf_counter`).
- **No xdist / randomly / deadfixtures** — fall back to serial runs, manual
  reversed-order isolation checks, and the built-in `--fixtures` vs
  `--fixtures-per-test` diff.
- **Dirty working tree** — refuse to run `03-execute` until clean (one commit per
  speedup requires a clean base); `00-scan` and `01-benchmark` are read-only and
  may run anyway.

## References

- `${CLAUDE_PLUGIN_ROOT}/references/scoring-rubric.md` — the weighted rubric and
  the hard safety gate.
- `${CLAUDE_PLUGIN_ROOT}/references/heuristic-catalog.md` — `H01`–`H44` with
  detect/action/risk/effort and the goal each addresses.
- `${CLAUDE_PLUGIN_ROOT}/references/version-matrix.md` — feature → min version →
  probe → fallback.
- `${CLAUDE_PLUGIN_ROOT}/references/memory-schema.md` — memory location, file set,
  idempotency token, baseline-diff.
- `${CLAUDE_PLUGIN_ROOT}/references/durations-parsing.md` — invoking and parsing
  `--durations`, phase bucketing, JUnit XML, the noise band.
- `${CLAUDE_PLUGIN_ROOT}/references/fixture-analysis.md` — scope model and the
  unused/duplicate/mis-scope recipes.
- `${CLAUDE_PLUGIN_ROOT}/references/safety-gates.md` — order independence,
  collection determinism, xdist preconditions.
- `${CLAUDE_PLUGIN_ROOT}/references/parametrize-convention.md` — the typed
  NamedTuple + test_id convention and typed builtins.
- `${CLAUDE_PLUGIN_ROOT}/references/output-contract.md` — the shared output shape.
