---
name: situate
description: >-
  Gain situational awareness — read the branch, its diff, its PR, its
  tickets, and the project's own conventions, and report where the work
  stands
allowed-tools: ["Bash", "Read", "Grep", "Glob", "AskUserQuestion"]
metadata:
  argument-hint: "[--pr <number|url>] [--with-agentgrep [terms]]"
  source: "plugins/situate/commands/situate.md"
---

# Situate

Answer one question: what is going on here, right now, and what would
someone picking this up need to know before touching anything.

Read `references/situation-sweep.md` first; it
defines the six evidence layers, how each degrades, and the read-only
contract. Read
`references/prior-conversations.md` before using
`--with-agentgrep`.

User arguments: $ARGUMENTS

## Context

Repository — run this command and read the output:

```bash
git remote get-url origin 2>/dev/null || echo "(no remote)"
```

Current branch — run this command and read the output:

```bash
git branch --show-current 2>/dev/null || echo "(detached HEAD)"
```

Trunk — run this command and read the output:

```bash
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo "(origin/HEAD unset)"
```

Ahead / behind trunk — run this command and read the output:

```bash
git rev-list --left-right --count "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)"...HEAD 2>/dev/null || echo "(no comparison available)"
```

Working tree — run this command and read the output:

```bash
git status --short 2>/dev/null | head -20 || echo "(unavailable)"
```

Trunk ref last updated — run this command and read the output:

```bash
git log -1 --format='%cr' "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)" 2>/dev/null || echo "(unknown)"
```

## Procedure

### 1. Fix the scope

Default scope is the current branch measured against trunk, plus its
pull request if one is open.

`--pr <number|url>` switches the subject to that pull request and its
head branch instead — for reviewing someone else's work, or returning
to a branch not currently checked out. Read it through `gh`; do not
check it out.

On trunk with nothing ahead and a clean tree, there is no branch story.
Report recent trunk activity and the open pull requests, and say that
is what happened.

### 2. Sweep the layers

Work through the five repository layers in the order the sweep
reference sets out: position, change, pull request, tickets,
conventions. Gather all of them before writing anything — a finding in
one layer changes what matters in another, and a ticket's acceptance
criteria reframe the diff that implements them.

### 3. Search prior conversations

Only with `--with-agentgrep`, and only under the rules in the
prior-conversations reference: scoped to this project, capped, checked
against the repository, and reported without local paths.

Derive the search terms from what the first four layers found unless
the user supplied them.

### 4. Report

Write the sections below, in order. Then hand back — this command ends
at understanding.

## Rules

- Read-only. No commits, no pushes, no edits, no stashes, no branch
  switches, and no `git fetch`.
- Report absence explicitly. "No pull request open" is a finding; a
  missing section reads as a layer that was never checked.
- Separate what was read from what was inferred, and mark the
  inferences.
- Cite only ticket IDs found in the commits, the branch name, or the
  pull request body. Never invent a reference.
- Prior conversations are evidence of intent; the repository is the
  evidence of state. When they disagree, the repository wins and the
  disagreement is worth reporting.
- Orient, do not fix. Failing checks, review threads, and dirty files
  get surfaced, not repaired.
- No local absolute paths and no third-party personal details in the
  report.

## Output

Open with a one-line hero — `✓ <branch>: <what it does> · <n> commits ·
PR #<n> <state>`, or `⚠ <what is blocking or unclear>` — then exactly
these sections:

1. `## Position` — branch, trunk, ahead/behind, uncommitted work,
   stashes, and how stale the trunk ref is.
2. `## Change` — what the branch does and how far along it is, grouped
   by area, with the commit sequence's shape.
3. `## Pull request` — state, checks by job name, unresolved review
   threads and what they ask for; or that none is open.
4. `## Tickets` — each linked issue with its state and what it asks
   for; or that none is referenced.
5. `## Conventions` — the rules from AGENTS.md / CLAUDE.md that bear on
   this change, and the quality gates it must pass.
6. `## Prior work` — only when `--with-agentgrep` ran: what was decided
   earlier, when, and whether the repository agrees.
7. `## Open questions` — what is unresolved, mid-flight, or
   contradictory, and what a resumed session would most likely get
   wrong.

End with an `ask-user-choice` panel offering next steps (for example:
continue the branch's work, address the review threads, open a pull
request, widen the sweep to prior conversations) — skip the panel only
in plan mode.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
