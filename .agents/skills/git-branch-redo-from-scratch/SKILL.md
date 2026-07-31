---
name: git-branch-redo-from-scratch
description: >-
  Use when a branch's code works but its implementation should be replaced
  from scratch rather than tidied — a proof of concept that became the real
  thing, an approach found halfway through that the earlier code does not
  reflect, or a structure that fights the problem. Studies the branch into a
  coverage ledger, treats its tests as the specification, reimplements from
  those requirements instead of copying the old code, then reconciles the
  result against the ledger entry by entry. The net change may legitimately
  differ from the original, which is kept as reference and fallback.
allowed-tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob", "AskUserQuestion", "WebFetch"]
metadata:
  argument-hint: "[PR number, branch, or what should change about the approach]"
  source: "plugins/git-branch/skills/redo-from-scratch/SKILL.md"
---

# Redo from scratch

Throw the implementation away and write it again, without losing what
the original learned.

Argument: $ARGUMENTS — a PR number, a branch, a statement of what
should change about the approach, or nothing.

Four references carry the parts that must not drift:

- `references/rebuild-contract.md` — the
  contract, the coverage ledger, reconciliation, and what counts as
  done.
- `references/branch-safety.md` — the gates, the
  backup, recovery, and the push.
- `references/commit-messages.md` — style
  discovery, intent recovery, and the privacy gate.
- `references/rebase-toolkit.md` — per-commit
  verification with no editor.

## Core principle

The old branch is the specification, not the source.

A redo that reads the old implementation line by line and retypes
it has reproduced the shape it was called in to replace. Work from
what the branch had to *achieve*; consult how it achieved it only when
the requirement is ambiguous.

## Boundary

the `git-branch-soft-reset-and-recommit` skill keeps the net change identical
and rebuilds only the history. Reach for it when the code is right and
the commits are wrong.

This skill is the opposite trade: the history and the code are both
replaced, and the net change may differ. That makes it strictly
riskier, so it earns its safety from the contract rather than from a
tree comparison.

## Phase 1 — Establish the contract before anything else

Per `rebuild-contract.md`. Identify trunk's tests, the tests this
branch added or changed, and run them against the branch now. What
passes is the specification; what is already failing or skipped is a
finding to report, not a target.

**If the branch has no tests, stop here.** An untested branch has no
mechanical invariant, and a redo becomes a rewrite with review as
the only net. Offer to write characterization tests against the
existing implementation first, so a spec exists before anything is
discarded. Proceed without them only if the user says so, and say in
the final report that nothing mechanical was guarding the result.

## Phase 2 — Study the branch into a ledger

Build the coverage ledger from `rebuild-contract.md`: behavior
changes, tests, edge cases and workarounds, review requests, ticket
acceptance criteria, public surface, dependencies.

Mine intent per `commit-messages.md` Part 2 — commits, trailers, the
pull request and its review threads, linked tickets, and optionally
the session that wrote the code, under the privacy rules there.

Give the workarounds disproportionate attention. A guard with no test
and no comment is the single most likely thing a clean rewrite drops,
and the original author usually had a reason they never wrote down.

## Phase 3 — Gate and back up

Every refusal in `branch-safety.md`. Then record the original tip so
it cannot be lost:

```
git branch "backup/<branch>-$(date -u +%Y%m%dT%H%M%SZ)" <branch>
```

The old branch is never deleted, never force-moved, and never the
place the rebuild happens.

## Orchestration Plan

Enter plan mode before writing any code. In Claude Code that is
`EnterPlanMode`; in other hosts `/plan` or Shift+Tab. If plan mode is
unavailable, present the same plan inline and wait for a go-ahead.

The plan states:

- The contract: which tests are the spec, and their current result.
- The ledger, summarized, with the entries judged highest-risk called
  out by name.
- What is being changed about the approach, and why the original shape
  is not being kept.
- Where the rebuild happens — the worktree path and new branch name.
- The gate commands discovered from the project's own conventions.
- Anything the branch does that the rebuild intends to drop, as an
  explicit list to be approved rather than discovered later.

When more than one approach is genuinely in contention, say so and
offer a bakeoff rather than picking silently.

Wait for approval. Exit plan mode before executing.

## Phase 4 — Rebuild

Work in a worktree so the original branch is untouched and remains
runnable for comparison:

```
git worktree add -b <branch>-redo /tmp/redo <base-sha>
```

Rebuild against the ledger, in the project's idiom, with no commits
until the contract is met — the exploration is a spike, and unreviewed
exploration does not belong in history. Mark shortcuts in place as you
take them so they become commits or decisions, not silent debt.

When the plan called for a bakeoff and the `spike` plugin is
installed, the `spike-bakeoff` skill runs the competing strategies in isolated
worktrees and returns a scored comparison. Without it, build the
leading candidate, record what the alternatives were, and say they
were not tried.

## Phase 5 — Verify against the contract

Trunk's tests, then the branch's tests, unmodified.

A test the rebuild cannot pass without editing is a decision, not a
task. Stop and surface it: the choices are to fix the rebuild, or to
agree the test encoded something the new approach deliberately
changes. Never edit a spec test to make a rebuild green.

Then gate every commit of the new series in place:

```
sh references/rebase-todo.sh verify <base-sha> '<test command>'
```

## Phase 6 — Reconcile

Walk the ledger. Every entry is addressed, deliberately dropped, or
missed. A drop is recorded in the commit message that drops it; a miss
is a defect.

Then present the comparison as review material, never as a gate:

```
git diff <backup-branch> <branch>-redo
```

Each hunk where the old branch did something the new one does not is a
question for the user. This is where a lost workaround surfaces.

## Phase 7 — Land, then stop

Commit the rebuild as an atomic series in the project's own format,
per `commit-messages.md`. Report the ledger outcome, the contract
result, the backup branch, and every deliberate drop.

Pushing is a separate decision, with the flags from
`branch-safety.md`. The old branch stays until the user retires it.

## Rules

- Never edit a test the branch added in order to make the rebuild
  pass, without explicit approval.
- Never delete or force-move the original branch.
- Never rebuild in the original branch's worktree.
- Never present a passing test run as proof of completeness; the
  ledger covers what the tests missed.
- Never commit during the rebuild phase.
- Language-agnostic: every gate command comes from the project's own
  conventions files.

## Common mistakes

**Retyping the old implementation.** The result is the same shape with
new commit hashes. Build from the ledger.

**Treating `git diff` against the old branch as a gate.** The code is
supposed to differ. It is a list of questions.

**Dropping a guard that had no test.** It usually marks a bug someone
already hit. Every workaround is load-bearing until its ledger entry
says otherwise.

**Starting without a contract.** On an untested branch this skill's
first job is to create one, not to rebuild.

**Rebuilding a branch that only needed its commits redone.** If the
code is right and the history is wrong, that is
the `git-branch-soft-reset-and-recommit` skill, and it comes with a guarantee
this skill cannot offer.


## Portability notes

- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
