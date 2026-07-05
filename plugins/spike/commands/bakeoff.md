---
description: >-
  Use when the user wants to try 2–4 different strategies for the
  same goal in parallel and pick a winner — a bakeoff, arena,
  tournament, gauntlet, shootout, or head-to-head where each
  contender is built for real in its own git worktree, adversarially
  judged, and none of it lands as commits. Triggers on phrases like
  "bakeoff", "bake off two approaches", "arena them", "run the
  gauntlet", "hold a tournament", "fan out different approaches",
  "try it three different ways", "competing implementations",
  "head-to-head", or "which approach wins". Varies the strategy, not
  the model — for running one prompt across different AI models
  (Claude, Antigravity, GPT), use the weave plugin instead. Ends
  with every contender stashed with a recovery SHA, a judged
  verdict, and a commit-by-commit plan to land the winner through
  the project's quality gates.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[<goal>] [--strategies=\"a; b; c\"] [--prongs=<2-4>] [--keep-trees] [--replay]"
---

# `/spike:bakeoff`

Multi-strategy spike harness. Where `/spike:probe` sends one
instrument down one path, a bakeoff enters 2–4 **deliberately
different strategies** for the same goal, builds each one for real in
its own git worktree, judges them adversarially, and hands back a
verdict plus a commit-by-commit plan for the winner.

Every contender **mutates its worktree freely** — real code, real
gates, full bakes. What no contender ever touches is history: the
kitchens are torn down after judging, and only stashes (all
recoverable by SHA) and the verdict survive.

This is a slash command, not a model-invocable skill: it creates
worktrees, mutates them, and (in `--replay`) creates commits, so it
must be user-explicit, not router-inferred.

## Core thesis

One spike answers "does this path work?" — it cannot answer "which
path is best?". When the approach is genuinely uncertain, arguing
about strategies in the abstract is slower and less reliable than
building each one small and comparing **real, judgeable evidence**:
diffs, gate results, blast radius, idiom fit.

A bakeoff is N probes plus a judgment. Each contender follows the
probe discipline (cheapest verification, `SPIKE:` markers, stay in
goal); the bakeoff adds isolation (worktrees), blindness (contenders
do not see each other), and adversarial judging.

**Bakeoff vs weave**: a bakeoff varies the *strategy* with one model;
the weave plugin varies the *model* with one prompt. Reaching for
"three models, one approach" → weave. "One model, three approaches"
→ bakeoff.

## The Iron Rule

```
A BAKEOFF PRODUCES ZERO COMMITS
```

Inherited from `/spike:probe`, and worktrees change nothing: not in
any worktree, not on any contender branch, not "just to snapshot a
contender". Worktrees isolate contenders; they do not license
commits.

| Rationalization | Reality |
|---|---|
| "It's a throwaway worktree — a commit there is harmless" | Worktree branches outlive worktrees and leak into PRs. Stash, then prune. |
| "Committing each contender makes them easier to diff" | `git stash show -p <sha>` and `git diff` across stash SHAs diff fine. Stash. |
| "The winner is decided — commit it straight from its worktree" | The winner exits as a stash and a plan; commits happen in `--replay`, one gated plan item at a time, from the main checkout. |
| "The losers don't matter — force-remove their worktrees" | Losers are graft material for the synthesis. Stash every contender with a SHA before any teardown. |

**Red flags — STOP:** `git commit` anywhere; `git worktree remove
--force` on a tree that has not been stashed; "snapshot commit";
merging a contender branch. All of these mean: stash with a SHA,
prune, and write the verdict.

## `$ARGUMENTS` contract

Non-flag text is the goal. Resolve it by the same ladder as
`/spike:probe`:

1. **Typed goal wins** — non-flag `$ARGUMENTS` text, verbatim.
2. **Empty → mine the conversation** — review findings, a failing
   test under discussion, a problem the user agreed needs handling.
   One strong candidate: adopt it (the Phase 1 brief is the
   confirmation gate). Several: `AskUserQuestion`. None: ask.
3. **Record provenance** in the Phase 1 brief.

**Strategies** resolve by their own ladder:

1. `--strategies="a; b; c"` — semicolon-separated, verbatim, one
   contender each.
2. Otherwise, mine the conversation: a bakeoff is usually reached
   for right after a discussion that surfaced competing options
   ("we could do A or B"). Those options become the contenders —
   listed in the brief with provenance.
3. Otherwise, propose 2–4 genuinely distinct strategies yourself in
   the brief (different architecture, different layer, different
   dependency posture — not cosmetic variants of one idea).

`--prongs=<2-4>` caps the contender count (default: however many
distinct strategies survive the brief, minimum 2, maximum 4).

| Flag | Default | Effect |
|---|---|---|
| `--strategies="a; b; c"` | off | Explicit contender list; skips strategy mining. |
| `--prongs=<2-4>` | auto | Cap the number of contenders. |
| `--keep-trees` | off | Skip teardown; leave all worktrees in place for manual inspection. Stashes are still created and SHAs recorded. |
| `--replay` | off | After the verdict and plan are approved, land the winner immediately: apply its stash, one gated commit per plan item. |

## Phase 0: Situational awareness

As `/spike:probe` Phase 0 — conventions files, the five gate buckets
and CI split per
`${CLAUDE_PLUGIN_ROOT}/references/verification-gates.md`, dirty-tree
halt — plus bakeoff-specific checks:

1. Confirm `git worktree` is usable and there is disk headroom for N
   checkouts.
2. Choose a worktree root outside the repo (e.g. a sibling temp
   directory) and contender names: `bakeoff/<n>-<slug>`.
3. Note any setup a fresh checkout needs to run gates (dependency
   install, codegen) — each kitchen must be able to bake.

## Phase 1: Orchestration plan

Enter plan mode if the host supports it (Claude Code:
`EnterPlanMode`; Cursor / Codex / Gemini: `/plan` or `Shift+Tab`) and
present the **bakeoff brief**:

1. The goal, one line, with provenance (typed / inferred from what).
2. The contenders: one line per strategy stating what makes it
   *distinct* from the others. If two entries differ only
   cosmetically, merge them — a bakeoff of near-identical bakes is
   waste.
3. What "proven" means per contender — the shared smoke check every
   contender must pass to reach judging.
4. The judging rubric (Phase 4 lenses, plus any goal-specific
   criteria the user cares about).
5. Discovered gate commands and the local-vs-CI split.
6. Worktree names and root; the exit path: stash-and-teardown /
   `--keep-trees` / `--replay`.

Wait for approval, then exit plan mode. If plan mode is unavailable,
present the brief inline and proceed on confirmation. In a
non-interactive run, record the brief in the report and proceed.

## Phase 2: The bake

For each contender, create its worktree and run it as an independent
sub-agent (Task tool) when the host supports it, or sequentially
otherwise:

```
git worktree add <root>/<n>-<slug> HEAD
```

Each contender follows `/spike:probe` Phase 2 discipline inside its
own worktree: shortest path to the shared "proven" check, cheapest
verification signal while iterating, `SPIKE:` markers on shortcuts,
adjacent problems recorded but not chased.

Contenders are **blind to each other**: no shared scratch files, no
peeking at another kitchen. Convergent shortcuts are signal for the
judges; copied ones are noise.

A contender that cannot reach "proven" is not disqualified silently:
it exits with a failure note (what blocked it), which is itself
evidence for the verdict.

## Phase 3: Contest exit gate

In each worktree, run the fast local buckets exactly as discovered —
`format`, `lint`, `typecheck`, scoped `test` — per
verification-gates.md right-sizing. Gate results here are **judging
inputs, not work**: fix only trivialities (formatting); everything
else is recorded on the contender's scorecard. If a mutating gate
changes files, re-run the shared proving check once, as in probe
Phase 3.

## Phase 4: Judging

Adversarial comparison, one pass per lens, each judge trying to
**refute** the contender's claim to the win rather than admire it:

- **Correctness** — does the proving check really demonstrate the
  goal, or does a `SPIKE:` marker hide the hard part?
- **Blast radius** — diff size and files touched; what does each
  approach entangle?
- **Simplicity / idiom fit** — which reads like the project already
  wrote it?
- **Gate status** — what passed, what failed, what was deferred.
- Any goal-specific lenses from the brief (performance, migration
  cost, dependency posture).

When the host supports sub-agents, run the lenses as independent
judges and aggregate; otherwise evaluate the lenses sequentially.
Produce a scorecard per contender, a **winner**, and a **graft
list** — ideas from runners-up worth carrying into the winner's plan
(a test case, an edge-case guard, a cleaner interface).

A split verdict is a valid verdict: report it as `⚠ inconclusive`
with the scorecards and let the user decide.

## Phase 5: Stash all contenders, then tear down

Teardown order is non-negotiable — **stash first, prune second**,
per contender:

1. In each worktree, stash everything including untracked files:

```
git stash push -u -m "bakeoff/<n>-<slug>: <strategy> (<verdict>)"
```

2. Record the stash's immutable SHA:

```
git rev-parse stash@{0}
```

   Stashes are repo-global — shared across all worktrees — so every
   contender remains recoverable from the main checkout after its
   worktree is gone, via `git stash apply <sha>`.

3. Only after the SHA is recorded, remove the worktree (skip with
   `--keep-trees`):

```
git worktree remove <root>/<n>-<slug>
```

4. After all contenders: `git worktree prune`, and verify the main
   tree is untouched (`git status`).

Losers are stashed too, not just the winner — the graft list points
into their stashes by SHA.

## Phase 6: The verdict and replay plan

Produce the verdict, then a commit-by-commit plan for the **winner's
stash** exactly as `/spike:probe` Phase 5 — subjects in the
project's commit format, contents per commit, `SPIKE:` decisions to
resolve, per-commit gates — plus:

- **Grafts**: plan items that pull specific hunks from runner-up
  stashes (identified by SHA and file), stated as recommendations.
- The losing strategies, one line each: why they lost, and under
  what future conditions they would have won (this is the decision
  record the bakeoff existed to produce).

Close with the local-vs-CI table and the post-push watch command
when observable, as in probe.

## Phase 7: Replay (only with `--replay`, after approval)

As `/spike:probe` Phase 6, from the main checkout: apply the
winner's stash (apply, not pop), land plan items one gated commit at
a time, apply graft hunks from runner-up stashes where the plan says
so, and only after the final green gate drop the contender stashes.

## Output contract

1. Hero block (1–3 lines): `✓ bakeoff judged — <winner>` /
   `⚠ bakeoff inconclusive` + goal + exit path taken.
2. `## Contenders` — one line per strategy: what it tried, proven or
   blocked, headline gate status.
3. `## Verdict` — scorecards per lens, the winner, the graft list,
   and why the losers lost.
4. `## Verification` — gate commands run per contender; local-vs-CI
   split; deferrals.
5. `## Stashes` — table: contender, strategy, stash message, **SHA**,
   restore command. Every contender appears, losers included.
6. `## Replay plan` — the numbered commit sequence for the winner,
   grafts marked.
7. End with an `AskUserQuestion` panel: replay the winner / keep
   stashes and stop / discard all — unless already in plan mode or
   `--replay` was given. In a non-interactive run, record the
   question in the report and default to keeping the stashes.
