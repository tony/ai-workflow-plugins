# pytest-optimizer

A Claude Code plugin that profiles a pytest suite, finds **safe** speedups, and
applies each one as its own verified commit.

It runs as a **resumable four-phase pipeline**. Measurement and mutation are
separated on purpose: you can re-run any phase without redoing the previous one,
and the suite is never edited until a speedup has been measured against the
project's own timing noise and has cleared a safety gate.

```
00-scan  ->  01-benchmark  ->  02-plan  ->  03-execute
profile      prove each        rank by       apply each speedup
+ detect     hypothesis vs      the safety    as a separate commit,
+ hypothesize  noise band       rubric        verify green, resume
```

## Why four commands instead of one loop

A single autonomous loop cannot be re-entered safely: if it crashes between
"measured" and "applied" you no longer know which is which. Each phase here reads
and writes a durable JSON file under `.pytest-optimizer/`, so the pipeline is:

- **Idempotent** — re-running a completed phase is a no-op while its inputs are
  unchanged (keyed by an idempotency token: collection node-ids + pytest/plugin
  versions + environment fingerprint).
- **Resumable** — `03-execute` checkpoints after every commit and picks up at the
  first un-applied plan item.
- **Auditable** — the plan is a reviewable artifact before any code changes.

## What it looks for

The detection rules live in `references/heuristic-catalog.md` (ids `H01`–`H44`).
Each rule maps to one or more of the goals below.

| Goal | Approach |
|------|----------|
| 1. Slowest tests + root cause | Rank `--durations` rows where the phase is `call`; attribute in-test cost (I/O, bootstrap, sleep). |
| 2. Slowest fixtures + root cause | Rank `setup`/`teardown` rows; an opt-in `pytest11` timing plugin attributes cost to the individual fixture (pytest core cannot). |
| 3. Consolidate duplicate test tracks | Detect in-body data loops and copy-pasted helpers/fixtures; merge into one parametrized track. |
| 4. Detect unused fixtures | Diff defined fixtures (`--fixtures`) against used closures (`--fixtures-per-test`), with a `getfixturevalue` false-positive guard. |
| 5. Proper fixture scope | `--setup-plan` setup-count analysis: an expensive function-scoped fixture re-run N times is a scope candidate. |
| 6. Safe speedups (risk vs refactor vs gain) | Score every candidate with the weighted rubric; drop anything below the hard safety gate. |
| 7. Try ideas + report | `01-benchmark` applies each hypothesis on a throwaway copy and re-measures vs the noise band. |
| 8. Apply each speedup as a separate commit | `03-execute` commits one change at a time with a why/what message and green-verify. |
| 9. Typings | Detect untyped tests/fixtures and legacy `tmpdir`; type pytest builtins. |
| 10. Typed parametrize | Migrate to `class XFixture(t.NamedTuple)` with `test_id` first + `ids=` derived from it. |
| 11. Project-owned cache/plugin | Opt-in scaffold for a gitignored (or XDG) `pytest11` plugin and `config.cache` memoization. |

## The safety rubric

Candidates are ranked by a weighted score and gated, not just sorted by speed.
Full definition in `references/scoring-rubric.md`.

| Dimension | Weight | Meaning |
|-----------|-------:|---------|
| safety | 0.35 | Inverse of correctness risk. **Hard gate: score < 0.4 is dropped, never auto-applied.** |
| impact | 0.30 | **Measured** wall-clock delta vs the noise band — not estimated. Within-noise scores 0. |
| effort | 0.15 | Inverse refactor cost. |
| confidence | 0.12 | Quality of the timing evidence (serial, repeated, well above the noise floor). |
| reversibility | 0.08 | How cleanly the change is undone if green-verify fails. |

## Commands

| Command | Phase | Writes |
|---------|-------|--------|
| `/pytest-optimizer:00-scan` | Profile, detect, hypothesize (plan-mode gated) | `baseline.json`, `capabilities.json`, `hypotheses.json` |
| `/pytest-optimizer:01-benchmark` | Prove each hypothesis vs the noise band | `benchmarks.json` |
| `/pytest-optimizer:02-plan` | Rank into a commit plan (plan-mode gated) | `plan.json` |
| `/pytest-optimizer:03-execute` | Apply each speedup as a commit, verify, resume | `execution-log.json` |

The skill `pytest-optimizer` orchestrates the loop and routes to these commands;
invoke it with phrases like "speed up my tests" or "why is my pytest suite slow".

## Memory

Durable state lives in `.pytest-optimizer/` at the repo root (gitignored by
default). On a read-only tree, or when you opt out of any in-tree file, it falls
back to `$XDG_CACHE_HOME/pytest-optimizer/<repo-id>/` (and
`%LOCALAPPDATA%\pytest-optimizer\<repo-id>\` on Windows). The resolved path is
recorded in `state.json` so all four commands agree. See
`references/memory-schema.md`.

## Prerequisites

- A git repository containing a pytest suite.
- The project's test and quality-check commands are read at runtime from
  `AGENTS.md` / `CLAUDE.md` — the plugin does not hardcode `pytest`, `uv run`,
  `tox`, or any runner.
- Optional, auto-detected and used only when present:
  - `pytest-xdist` — parallelism candidates (`-n auto`, `--dist loadscope`).
  - `pytest-randomly` — order-independence safety gate.
  - `pytest-deadfixtures` (via `uvx`) — dead/duplicate fixture cross-check.
  - `pytest-timeout` — per-test timeout recommendations.

## Component reference

- `commands/` — the four phase commands.
- `skills/pytest-optimizer/SKILL.md` — model-invocable orchestrator with the
  Orchestration Plan and graceful degradation.
- `references/` — rubric, heuristic catalog, version matrix, memory schema, and
  the analysis recipes (durations parsing, fixture analysis, safety gates,
  parametrize convention, output contract).
- `templates/` — opt-in scaffolds: the `pytest11` timing plugin, the
  `config.cache` snippet, the NamedTuple parametrize template, the gitignore and
  commit-message snippets, and the durable-memory JSON schema.

## Scope

The pipeline, rubric, and memory model are **runner-agnostic in shape**, but the
detection and remediation here are **pytest-specific**. The capability matrix
adapts to the installed pytest (degrading gracefully from 9.x back to 6.x). To
ship it in a marketplace, register an entry in `.claude-plugin/marketplace.json`
under category `testing`.
