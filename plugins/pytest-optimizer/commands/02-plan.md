---
description: >-
  Phase 3 of the pytest-optimizer pipeline. Rank the validated speedups from
  01-benchmark into an ordered commit plan. Scores each candidate with the
  weighted rubric (safety, impact, effort, confidence,
  reversibility), drops anything below the hard safety gate, orders the survivors
  (safety-gate fixes and typings first; scope and consolidation before
  parallelism), and drafts one why/what commit per speedup with its verify
  command. Runs inside plan mode and presents the plan for approval. Writes
  plan.json. Use after 01-benchmark to decide what to apply and in what order.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "AskUserQuestion"]
argument-hint: "[--max-commits=N] [--min-score=<0..1>] [--force] [--memory-dir=<path>]"
---

# 02-plan

Turn measured candidates into a reviewable commit plan. This phase **only reads**
the suite and writes `plan.json`; it makes no code changes.

`$ARGUMENTS` may pass `--max-commits=N` to cap the plan, `--min-score` to raise the
inclusion threshold, and `--force` to recompute.

## Step 1: Load and score

Read `benchmarks.json` and `baseline.json`. Score every `validated` candidate with
`${CLAUDE_PLUGIN_ROOT}/references/scoring-rubric.md`:

```
total = 0.35*safety + 0.30*impact + 0.15*effort
      + 0.12*confidence + 0.08*reversibility
```

Apply the **hard gates** first: drop any candidate with `safety < 0.4` or
`impact == 0`. For each dropped item, capture the prerequisite refactor (if any)
as a separate, clearly-labeled follow-up — not as an auto-applied commit.

## Step 2: Order

Score sets priority; these constraints override it where they apply:

1. Safety-gate fixes first (make collection deterministic, prove order
   independence) before any parallel/reorder speedup.
2. Typing and parametrize migrations early (low-risk, readable diffs).
3. Scope and consolidation before parallelism.
4. One speedup per commit — never bundle.

Honor `--max-commits` / `--min-score`.

## Step 3: Draft commits

For each planned item, draft a commit from
`${CLAUDE_PLUGIN_ROOT}/templates/commit-message.tmpl`, adapting the
`type(scope)` prefix to the **target project's** convention (read from its
`AGENTS.md`/`CLAUDE.md`). Each entry records: order, heuristic id, the score
breakdown, target files, the draft subject/body, the verify command (the project
test + quality checks), and any `depends_on`. Write `plan.json` and update
`state.json` (`phase=plan`, plan hash).

## Step 4: Present for approval (plan mode)

This phase is a decision point. Enter plan mode (Claude Code: `EnterPlanMode`;
others: `/plan` or `Shift+Tab`). Present the `02-plan` sections from
`${CLAUDE_PLUGIN_ROOT}/references/output-contract.md`: `## Ranked plan`,
`## Dropped at the gate`, `## Ordering rationale`. Let the user reorder, drop
items, or cap the count. Because plan mode is the decision point, omit the
`AskUserQuestion` panel here. Exit plan mode once approved; `plan.json` is the
contract `/pytest-optimizer:03-execute` consumes.
