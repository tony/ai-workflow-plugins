# merge-pr

Merge pull requests via `gh` with merge commits that match the
repository's own `git log --merges` history — never before a
readiness gate confirms the PR is actually mergeable.

Merging is treated as its own provincial act: verify checks, bring
the branch up to date, land it, sync trunk, stand by. It is not a
release — these commands never tag, never edit changelogs, and never
claim a change lands "in vX.Y" unless the PR itself is release work.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install merge-pr@ai-workflow-plugins
```

## Components

### `/merge-pr:this` (command)

Merge one PR — the one under discussion, or the current branch's.
Runs the readiness gate (open, not draft, CI passing via
`gh pr checks`, mergeable, no requested changes), waits on pending
checks with `gh pr checks --watch`, rebases and force-pushes with
`--force-with-lease` if the branch is behind or conflicted, then
merges via `gh pr merge` with a merge commit message derived from
the repo's merge history. Afterwards it checks out trunk, pulls,
and stops.

### `/merge-pr:multiple` (command)

Land a set of PRs one at a time. Detects whether the set is a
**stack** (a PR based on another PR's head branch — merged
bottom-up, children retargeted and rebased with the parent's commits
dropped) or **independent** (merged in the user's order, each
rebased onto the trunk the previous merge produced). Between merges:
rebase, resolve conflicts, force-push, and wait on CI before the
next `gh pr merge`. Halts — preserving everything already merged —
on failing CI, unexpected rebase drift, or a conflict that needs a
product decision.

## Merge strategy and flags

Both commands default to a merge commit. `--squash` and `--rebase`
override the strategy, and every other `gh pr merge` flag passes
through verbatim (`--auto`, `--delete-branch`, `--admin`,
`--match-head-commit`, `--body-file`, `--repo`, ...). `--admin` is
honored only to bypass branch protection when CI is otherwise green
— never to merge over failing or pending checks.

Both commands read `references/merge-readiness.md`, the shared
contract covering the readiness gate, the rebase procedure, the
merge-message derivation, and the do-no-harm rules: discovery before
action, ask on ambiguity, halt on anything surprising.

## Prerequisites

- `gh` CLI, authenticated with permission to merge in the target
  repository.
- `git` with fetch/push access to the PR branches.
