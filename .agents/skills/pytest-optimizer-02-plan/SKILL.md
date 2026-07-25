---
name: pytest-optimizer-02-plan
description: >-
  Phase 3 of the pytest-optimizer pipeline. Rank the validated speedups from
  01-benchmark into an ordered commit plan. Scores each candidate with the
  weighted rubric (safety, impact, effort, confidence, reversibility), drops
  anything below the hard safety gate, orders the survivors (safety-gate
  fixes and typings first; scope and consolidation before parallelism), and
  drafts one why/what commit per speedup with its verify command. Runs
  inside plan mode and presents the plan for approval. Writes plan.json. Use
  after 01-benchmark to decide what to apply and in what order.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "AskUserQuestion"]
metadata:
  argument-hint: "[--max-commits=N] [--min-score=<0..1>] [--force] [--memory-dir=<path>]"
  source: "plugins/pytest-optimizer/commands/02-plan.md"
---

# 02-plan

Turn measured candidates into a reviewable commit plan. This phase **only reads**
the suite and writes `plan.json`; it makes no code changes.

`$ARGUMENTS` may pass `--max-commits=N` to cap the plan, `--min-score` to raise the
inclusion threshold, and `--force` to recompute.

## Step 1: Load and score

Read `benchmarks.json` and `baseline.json`. Score every `validated` candidate with
`references/scoring-rubric.md`:

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
`templates/commit-message.tmpl`, adapting the
`type(scope)` prefix to the **target project's** convention (read from its
`AGENTS.md`/`CLAUDE.md`). Each entry records: order, heuristic id, the score
breakdown, target files, the draft subject/body, the verify command (the project
test + quality checks), and any `depends_on`. Write `plan.json` and update
`state.json` (`phase=plan`, plan hash).

## Step 4: Present for approval (plan mode)

This phase is a decision point. Enter plan mode (Claude Code: `EnterPlanMode`;
others: `/plan` or `Shift+Tab`). Present the `02-plan` sections from
`references/output-contract.md`: `## Ranked plan`,
`## Dropped at the gate`, `## Ordering rationale`. Let the user reorder, drop
items, or cap the count. Because plan mode is the decision point, omit the
`ask-user-choice` panel here. Exit plan mode once approved; `plan.json` is the
contract the `pytest-optimizer-03-execute` skill consumes.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
