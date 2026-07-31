---
name: git-branch-soft-reset-and-recommit
description: >-
  Use when a commit history needs rebuilding rather than the code it
  contains — `wip` commits to squash, one commit doing five unrelated
  things, or a history no reviewer can follow. Collapses everything with a
  soft reset and rebuilds it as atomic commits in the project's own message
  format, preserving authorship, proving the resulting tree is
  byte-identical to what it replaced, and gating each commit through the
  project's checks. Ships an editor-free interactive rebase toolkit for
  reordering, squashing, and verifying from an agent shell with no TTY.
allowed-tools: ["Bash", "Read", "Write", "Grep", "Glob", "AskUserQuestion", "WebFetch"]
metadata:
  argument-hint: "[PR number, base ref, or a hint like 'split the auth work out']"
  source: "plugins/git-branch/skills/soft-reset-and-recommit/SKILL.md"
---

# Soft reset and recommit

Rebuild a branch's history so the commits explain the change, without
changing a byte of the result.

Argument: $ARGUMENTS — a PR number, a base ref, a hint about how to
split, or nothing.

Four references carry the parts that must not drift:

- `references/branch-safety.md` — the gates, the
  backup, recovery, and the push.
- `references/split-mechanics.md` — base
  resolution, the collapse, staging, splitting, verification.
- `references/commit-messages.md` — style
  discovery, intent recovery, and the privacy gate.
- `references/rebase-toolkit.md` — interactive
  rebase with no editor, plus `references/rebase-todo.sh`.

## Core principle

The tree is the invariant. The history is the deliverable.

A recommit that changes what the branch produces is a bug, no matter how
good the commits look. Every decision below is subordinate to proving
the final tree is identical to the one it replaced.

## Phase 1 — Gather intent, before anything destructive

The collapse destroys the original commit boundaries. Everything worth
knowing has to be read first.

Read every original message whole, the trailers, the pull request body
and its review threads, the linked tickets, and — when the repository
does not explain itself — the session that wrote the code. Follow
`commit-messages.md` Part 2, including its privacy gate: extract
claims and re-state them, never copy a span out of a transcript.

Record what each original commit was *for*. That mapping is the raw
material for every message written later.

## Phase 2 — Resolve the base and run the gates

Resolve the base to a SHA once, per `split-mechanics.md`: fork point
first, plain merge-base as fallback, and refuse unless exactly one
merge base exists. On a stacked branch the base is the parent branch
tip, never trunk.

Then run every refusal in `branch-safety.md`: dirty tree, operation in
progress, merge commits in the range, branch held by another worktree,
shallow clone. Detect a pushed branch and whether anyone else has
pushed to it — without `git fetch`.

A refusal is a report and a stop, not a warning to proceed past.

## Phase 3 — Discover the conventions

The commit format, per `commit-messages.md` Part 1: declared first,
mined from history at the fork point otherwise, and reported as
`mixed` with a question when the repository has no single style.

The project's quality gates, from `AGENTS.md`, `CLAUDE.md`, or
`CONTRIBUTING.md` — the format, lint, typecheck, and test commands as
the project defines them. Never invent one. These become the
per-commit gate in Phase 6, so copy any harness outside the repository
and call it by absolute path.

## Phase 4 — Plan the series, and get it approved

Enter plan mode before any destructive step. In Claude Code that is
`EnterPlanMode`; in other hosts `/plan` or Shift+Tab. If plan mode is
unavailable, present the same plan as text and wait for an explicit
go-ahead.

The plan states:

- The resolved base SHA and how it was resolved.
- The backup branch name.
- The proposed commit series, in order: for each, its subject, the
  paths or hunks it takes, and the intent it came from.
- Which commits are split out of a single original, and which
  originals are merged together.
- The discovered commit format and the gate commands.
- Anything the gates flagged but did not halt on.

Order the series so it builds: a refactor before the behavior that
depends on it, a fixture before the test that uses it. Declare any
dependency between commits.

Split when a commit does two things. The signal is the message — if
the body needs to describe two concerns, it is two commits.

Wait for approval. Exit plan mode before executing.

## Phase 5 — Back up, then collapse

Create the backup branch first, and report its name:

```
git branch "backup/<branch>-$(date -u +%Y%m%dT%H%M%SZ)" <branch>
```

Then collapse:

```
git reset --soft <base-sha>
```

## Phase 6 — Rebuild, one commit at a time

Per `split-mechanics.md`: whole files with `git commit -m "..." --only
-- <paths>` (message flags before the `--`), a single file split
across commits through the regenerate-filter-apply loop, and the
staged set asserted before every commit.

Write each message from the intent gathered in Phase 1, in the format
discovered in Phase 3, preserving the original author identity and
date. Carry `Co-authored-by` and ticket trailers forward.

Then gate the whole series in place:

```
sh references/rebase-todo.sh verify <base-sha> '<test command>'
```

A failure stops the rebase and leaves it in progress; the script says
so and prints the abort command. Fix the offending commit and re-run
rather than pressing on.

## Phase 7 — Prove it, then hand back

The gate, not a formality:

```
git diff --quiet backup/<branch>-<ts> HEAD
```

A non-zero exit means the recommit changed the result. Restore from the
backup and report — do not try to patch the difference.

Then show the user how the history was regrouped:

```
git range-diff <base-sha> backup/<branch>-<ts> HEAD
```

Report the new series, the backup branch name, the gate results, and
what was deferred.

## Phase 8 — Pushing is a separate decision

Never push as part of the recommit. Offer it, with the flags from
`branch-safety.md`, and let the user decide:

```
git push --force-with-lease --force-if-includes origin <branch>
```

## Rules

- Prove tree equality before reporting success. Without it there is no
  claim to make.
- Never rewrite a pushed branch without explicit consent, and never
  when someone else has pushed to it.
- Never `git add -A` or `git add .` — explicit paths only.
- Never delete the backup branch. The user does that when they are
  satisfied.
- Never bare `--force`, and never `git fetch` while a lease is being
  relied on.
- Never invent a test command, a version, or a ticket ID.
- Language-agnostic: every gate command comes from the project's own
  conventions files.

## Common mistakes

**Collapsing before reading the original messages.** They are the
primary evidence of intent, and after the soft reset they are only
reachable through the backup ref.

**Recutting a stacked branch against trunk.** It absorbs the entire
parent pull request into the child. The base is the parent tip.

**Trusting a clean `git rebase --exec` run that had no `--keep-base`.**
Without it the "verification" rebases onto upstream and silently drops
commits that became empty, exiting 0.

**Putting `-m` after the `--` in `git commit --only`.** Everything
after `--` is a pathspec, so git looks for a file named `-m`.

**Gating on `git range-diff` being clean.** Heavy regrouping shows as
drop-and-add pairs. It explains the recommit; tree equality gates it.

**Leaving a stopped rebase in place.** A failed `--exec` leaves a
detached HEAD that poisons every later git command.

**Copying a span out of a transcript into a message.** Transcripts are
unredacted. Re-state the claim in your own words.

**Adding a `(#N)` suffix because the merge commits have one.** Merge
style and branch style legitimately differ in the same repository.


## Portability notes

- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
