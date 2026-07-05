# spike

Prove a path fast in a no-commit spike — a single probe, or a bakeoff
of 2–4 competing strategies in git worktrees — exit through the
project's quality gates into stashes, and hand back a neat
commit-by-commit implementation plan.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install spike@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/spike:probe [<goal>]` | Probe the goal with zero commits, stash with a recovery ref, propose a commit-by-commit landing plan |
| `/spike:bakeoff [<goal>]` | Build 2–4 competing strategies in isolated git worktrees, judge them adversarially, stash every contender, propose a landing plan for the winner |

The goal can be typed or inferred from conversation context (review
findings just presented, a failing test under discussion) — the
plan-mode brief confirms it either way.

`/spike:probe` flags: `--branch=<name>` (spike on a scratch branch),
`--keep-tree` (skip the stash, leave changes for inspection),
`--replay` (implement the approved plan immediately, one gated commit
per plan item).

`/spike:bakeoff` flags: `--strategies="a; b; c"` (explicit contender
list), `--prongs=<2-4>` (cap contender count), `--keep-trees` (leave
worktrees for inspection), `--replay` (land the winner immediately).

One approach in mind → `probe`. Genuinely uncertain between
approaches → `bakeoff`. To vary the *model* rather than the strategy,
use the weave plugin instead.

## Workflow

1. **Situational awareness** — read AGENTS.md / CLAUDE.md, discover the
   project's format / lint / typecheck / test / build commands and what
   CI covers post-push
2. **Spike brief** — short plan-mode confirmation of goal (with its
   provenance), "proven" criterion, and exit path
3. **Probe** — shortest path to proven; cheapest verification signal
   only; shortcuts marked `SPIKE:`
4. **Exit gate** — one pass of the fast local gates so the plan starts
   from known state
5. **Stash** — `git stash push -u` with a descriptive message and a
   recorded immutable SHA for recovery
6. **Replay plan** — numbered commit sequence mapping stash hunks to
   commits, decisions to resolve, per-commit gates, local-vs-CI split

A bakeoff runs steps 3–5 once per contender, each in its own git
worktree with contenders blind to each other, then adds an
adversarial judging pass (correctness, blast radius, idiom fit, gate
status) before the replay plan. Every contender is stashed with a
recovery SHA — losers included, as graft material — before its
worktree is removed.

The spike itself never commits — not in the working tree, not in any
worktree. Commits only happen in `--replay`, after the plan is
approved, one plan item at a time, each behind a green gate.

## Verification discovery

Both commands read AGENTS.md / CLAUDE.md / CONTRIBUTING.md to discover
which quality checks the project requires, and reads the CI definitions
to learn what a push verifies for free (see
`references/verification-gates.md`). It does **not** hardcode any test
runner, linter, or build tool — and it deliberately runs no more
verification than the change needs, deferring CI-covered work to
`gh pr checks --watch` after a push.

## Prerequisites

- **git** — stash-based workflow uses standard git operations;
  `/spike:bakeoff` additionally uses `git worktree`
- **gh** (optional) — enables watching CI checks after a push
