# spike

Prove a path fast in a no-commit spike/blitz, exit through the project's
quality gates into a stash, and hand back a neat commit-by-commit
implementation plan.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install spike@ai-workflow-plugins
```

## Command

| Command | Description |
|---------|-------------|
| `/spike:blitz <goal>` | Blitz the goal with zero commits, stash with a recovery ref, propose a commit-by-commit landing plan |

Flags: `--branch=<name>` (spike on a scratch branch), `--keep-tree`
(skip the stash, leave changes for inspection), `--replay` (implement
the approved plan immediately, one gated commit per plan item).

## Workflow

1. **Situational awareness** — read AGENTS.md / CLAUDE.md, discover the
   project's format / lint / typecheck / test / build commands and what
   CI covers post-push
2. **Spike brief** — short plan-mode confirmation of goal, "proven"
   criterion, and exit path
3. **Blitz** — shortest path to proven; cheapest verification signal
   only; shortcuts marked `SPIKE:`
4. **Exit gate** — one pass of the fast local gates so the plan starts
   from known state
5. **Stash** — `git stash push -u` with a descriptive message and a
   recorded immutable SHA for recovery
6. **Replay plan** — numbered commit sequence mapping stash hunks to
   commits, decisions to resolve, per-commit gates, local-vs-CI split

The spike itself never commits. Commits only happen in `--replay`,
after the plan is approved, one plan item at a time, each behind a
green gate.

## Verification discovery

The command reads AGENTS.md / CLAUDE.md / CONTRIBUTING.md to discover
which quality checks the project requires, and reads the CI definitions
to learn what a push verifies for free (see
`references/verification-gates.md`). It does **not** hardcode any test
runner, linter, or build tool — and it deliberately runs no more
verification than the change needs, deferring CI-covered work to
`gh pr checks --watch` after a push.

## Prerequisites

- **git** — stash-based workflow uses standard git operations
- **gh** (optional) — enables watching CI checks after a push
