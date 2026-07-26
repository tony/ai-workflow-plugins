---
name: situate-situational-awareness
description: >-
  Use when a session starts on unfamiliar or resumed work — when asked to
  catch up, get oriented, or figure out where things left off, what a branch
  is doing, what a pull request or its review threads are asking for, or
  what the state of this repository is before touching it.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "AskUserQuestion"]
metadata:
  source: "plugins/situate/skills/situational-awareness/SKILL.md"
---

# Situational awareness

Establish what is going on in a repository before acting in it: what
the branch does, how far along it is, what its pull request and tickets
ask for, and what the project's own rules require of the work.

Two reference files carry the parts that must not drift between this
skill and `/situate`:

- `references/situation-sweep.md` — the six
  evidence layers, how each one degrades, and the read-only contract.
- `references/prior-conversations.md` — when
  searching local AI transcripts is warranted, how to scope it, and
  what may not appear in the report.

## Core principle

Read everything before reporting anything.

The layers reinterpret each other. A ticket's acceptance criteria
change what the diff means. An unresolved review thread explains a
commit that otherwise looks like a detour. Reporting each layer as it
arrives produces a list of facts; reading them together produces a
situation.

## Read-only

No commits, no pushes, no edits, no branch switches, no `git fetch`.

This runs at the start of a session, before the user has decided
anything. A command that mutates while claiming to orient is worse than
no command at all — it changes the state being reported on, and it
does so before there is any agreement about what should change.

## Phase 1 — Position

Branch, trunk resolved from `refs/remotes/origin/HEAD` rather than
assumed, merge-base, ahead/behind counts, uncommitted work, stashes.

Uncommitted work is the highest-signal part of this phase. It is the
piece of the situation that no commit, pull request, or ticket records,
and the piece a resumed session is most likely to trample.

## Phase 2 — Change

Commits since the merge-base, and the diff behind them. Report intent —
what behavior changed and what the sequence was building toward — not
an inventory of paths.

The shape of the history is itself evidence: pending fixups, a revert,
a mid-branch merge from trunk. Each says something about where the work
stands.

## Phase 3 — Pull request and review

State, checks by job name, review threads and what they ask for. Verify
that a green check rollup covers the current head rather than an
earlier push.

Review threads are the only layer holding another person's opinion, and
the one a resumed session has least chance of reconstructing on its
own.

## Phase 4 — Tickets

IDs from commits, branch name, and pull request body only. Resolve
GitHub issues through `gh` and other trackers through whatever MCP
server the session has connected. An ID that cannot be resolved is
reported unresolved.

## Phase 5 — Conventions

The rules in `AGENTS.md` and `CLAUDE.md` that bear on this change:
commit format, quality gates, constraints on the files being touched.
Nested files override the root for their subtree. Report the rules that
apply to the work in flight, not the whole document.

## Phase 6 — Prior conversations

Opt-in. Warranted when the repository does not explain itself — an
approach with no recorded rationale, work resumed after a gap, a
decision that left no artifact. Follow the prior-conversations
reference for scoping, capping, reconciliation, and privacy.

## Report

Lead with what is unresolved. Someone asking to be caught up wants the
open questions, the failing check, and the half-finished edit — not a
narration of what already works.

Separate what was read from what was inferred, and say which layers
were unavailable and why.

## Common mistakes

**Acting on the situation instead of reporting it.** Fixing a failing
check mid-sweep changes the state being reported and pre-empts a
decision the user has not made.

**Assuming trunk is `main`.** Resolve it from the remote; the fallback
is a guess and gets labeled as one.

**Fetching to freshen the comparison.** It rewrites remote-tracking
refs and changes what the rest of the session sees. Report the ref's
age instead.

**Reporting a file inventory as the change.** The diff already lists
paths. What is missing is what the branch is for.

**Treating a prior conversation as current state.** A plan discussed
weeks ago may have shipped, been abandoned, or been reversed — and the
transcript reads identically in all three cases.

**Silently omitting an empty layer.** A dropped section and an
unchecked one are indistinguishable to the reader.

**Trusting a stale check rollup.** Green on a run that predates the
last push says nothing about the current head.


## Portability notes

- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
