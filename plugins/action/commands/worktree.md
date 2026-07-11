---
description: >-
  Use when the user wants to take a ticket — or several tickets that
  share one change — into its own branch and git worktree and drive it
  to gated commits. Triggers on phrases like "work TEA-123 in a
  worktree", "spin up a worktree for issue #45", "start on this
  ticket", "branch for the Linear ticket", "put these two tickets on
  one branch", or "prep a worktree, I'll take it from there". Resolves
  the ticket strictly read-only (never assigns, comments, or
  transitions), names the branch by the team's own conventions,
  implements through the project's discovered quality gates, and never
  pushes or opens a PR unless the flags say so. Mutates the repo —
  invoke explicitly.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[<ticket>...] [--branch=<name>] [--local|--temp] [--push|--pr|--setup-only]"
---

# `/action:worktree`

Take one or more tickets to a working branch in its own git worktree.
Resolve the ticket(s) read-only, name the branch the way the team
actually names branches, create the worktree beside the repo (or in a
temp root), implement, and land gated commits — pushing or opening a
PR only when asked.

One worktree, one branch, one deliverable — carrying one ticket by
default, and several when they genuinely share a change. Crosscutting
is first-class, not an error.

This is a slash command, not a model-invocable skill: it creates
worktrees and branches, modifies files, and creates commits, so it
must be user-explicit, not router-inferred. To land review findings
on the *current* branch, use `/review:address`; this command starts
ticket work on a *new* branch.

## Core thesis

A ticket describes an outcome; a branch is the unit of delivery. This
command is the plumbing between the two, done the way the tracker and
the team already expect: the branch name carries the ticket ID so
linking happens server-side, the worktree keeps the main checkout
untouched, and the gates keep every commit green.

Three disciplines:

1. **Tickets are read-only.** Resolution pulls title, description,
   acceptance criteria, and the branch-name field — and writes
   nothing back (see The Iron Rule).
2. **Names follow the precedence ladder.** Explicit ask > project
   conventions > ticket-system default > observed repo norms > slug
   fallback — per
   `${CLAUDE_PLUGIN_ROOT}/references/ticket-detection.md`.
3. **The main checkout is never disturbed.** All work happens in the
   worktree; the default exit is a gated commit, not a push.

## The Iron Rule

```
TICKETS ARE READ-ONLY
```

The full invariant — forbidden operations and the zero-blowback
rationale — lives in
`${CLAUDE_PLUGIN_ROOT}/references/ticket-detection.md` § The
read-only invariant. Short form: no assign, no comment, no state
transition, no `gh issue develop`. Linking rides on names,
server-side, so an abandoned branch unwinds with nothing to undo.

| Rationalization | Reality |
|---|---|
| "Assigning it to me signals the work started" | The branch name carries the ID; the tracker shows the attached branch. Assignment is a team decision, not plumbing. |
| "One comment with the branch link helps reviewers" | Linear auto-attaches from the name; GitHub links from the PR body. The comment is redundant now and stale the moment the branch is renamed or dropped. |
| "Move it to In Progress — that's what the column is for" | If the branch is abandoned, someone must move it back and explain why. Zero write-back means zero cleanup. |
| "`gh issue develop` is the official way to make the branch" | It writes a linked-branch record onto the issue — ticket state. Construct the same name locally instead. |

**Red flags — STOP, you are about to violate the rule:** any tracker
mutation verb (assign, comment, transition, label, close);
`gh issue develop`; an MCP tool call whose name is not read-shaped.

## `$ARGUMENTS` contract

Non-flag text is the ticket reference(s): IDs (`TEA-123`, `#45`),
URLs, or free text describing the goal. Several references in one
invocation mean **one branch carrying all of them** (crosscutting).
With no references at all, resolve per the detection source ladder in
ticket-detection.md (conversation context before lookups) and ask
rather than invent.

| Flag | Default | Effect |
|---|---|---|
| `--branch=<name>` | off | Use this branch name verbatim (rung 1 of the precedence ladder). |
| `--local` | **on** | Placement: visible sibling worktree at `{repo_path}-{sanitized_branch}/`. |
| `--temp` | off | Placement: the host's native temp-worktree mechanism when one exists, else a temp root outside the repo. |
| `--push` | off | Exit: after the gated commit(s), push the branch to the remote. |
| `--pr` | off | Exit: push, then open a PR whose title/body link the tickets. Implies `--push`. |
| `--setup-only` | off | Exit: stop after worktree + branch + the ticket primer — no implementation. |

Two axes: placement is `--local` xor `--temp`; exit escalates
(commit only → `--push` → `--pr`), and `--setup-only` short-circuits
the exit axis entirely. Path derivations for both placements are in
ticket-detection.md § Worktree placement & path sanitization.

## Phase 0: Situational awareness

1. Read `AGENTS.md` / `CLAUDE.md` / `.github/CONTRIBUTING.md` for
   quality checks, commit format, and any branch-naming conventions
   (these feed rung 2 of the ladder).
2. Resolve the five gate buckets and the CI-coverage split per
   `${CLAUDE_PLUGIN_ROOT}/references/verification-gates.md`.
3. Inventory ticket tooling: tracker MCP tools, the `gh` CLI. Detect
   the trunk branch and remotes (`git remote -v`,
   `git symbolic-ref refs/remotes/origin/HEAD`).
4. Record main-checkout state (`git status -sb`). A dirty main tree
   is **not** a blocker — the worktree isolates the work — but note
   it, and never stash or otherwise touch the user's uncommitted
   work.

## Phase 1: Ticket resolution

Per `${CLAUDE_PLUGIN_ROOT}/references/ticket-detection.md`:

1. Identify the tracker and ticket(s) via the detection source
   ladder.
2. Fetch each ticket read-only: title, description, acceptance
   criteria, and (Linear) the `gitBranchName` field.
3. Resolve the branch name via the precedence ladder. Record which
   rung produced it and any observed-norms adjustment applied.
4. Multi-ticket: the ladder skips the ticket-system rung — propose a
   theme slug for the plan gate to confirm.
5. Derive the worktree path from the placement axis.

A reference that resolves to nothing (ID matches no issue, URL 404s)
halts with a question — never guess a ticket's content.

## Phase 2: Orchestration plan

Enter plan mode if the host supports it (Claude Code:
`EnterPlanMode`; Cursor / Codex / Gemini: `/plan` or `Shift+Tab`) and
present:

1. Ticket(s): ID, title, source (prompt / conversation / lookup),
   one line each; for multi-ticket, why they share a branch.
2. The branch name and the ladder rung that produced it, naming any
   observed-norms adjustment; the theme slug, for confirmation, when
   multi-ticket.
3. The worktree path, placement axis, and start point (Phase 3).
4. The implementation shape: acceptance criteria restated as the
   definition of done, files expected to change, planned commit
   subject(s) in the project's format.
5. Discovered gate commands and the local-vs-CI split.
6. The exit axis in effect: commit only / `--push` / `--pr` /
   `--setup-only`.

Wait for approval, then exit plan mode. If plan mode is unavailable,
present the same plan inline and proceed on confirmation. In a
non-interactive run (CI, subagent — including `/action:worktrees`
fan-out, which holds its own plan gate), record the plan in the
report and proceed.

## Phase 3: Worktree & branch

Start point: the remote trunk head — `git fetch origin`, then
`origin/<trunk>` — falling back to the local trunk, then `HEAD`; the
plan states which.

Resolve **idempotently**, first match wins:

1. **Branch exists and is checked out in a worktree** — reuse it:
   `git worktree list --porcelain` gives the path. Resume there and
   report "resumed", not "created".
2. **Branch exists, no worktree** — attach one:

```
git worktree add <path> <branch>
```

3. **Path exists and is the expected worktree** (listed in
   `git worktree list` for this repo, on the expected branch) —
   resume there.
4. **Path exists and is anything else** — halt with
   `AskUserQuestion`: pick another path, let the user clear it, or
   abort. Never delete or overwrite a directory this command did not
   create.
5. **Neither exists** — create both:

```
git worktree add -b <branch> <path> <start-point>
```

Then assemble the **ticket primer** — per ticket: ID, title,
description, acceptance criteria, link. The primer lives in this
command's report (`## Primer`), not in files inside the worktree: an
untracked primer file would haunt `git status` and risk riding into
a commit. With `--setup-only`, skip ahead to the output contract now.

## Phase 4: Implement

Inside the worktree only:

1. Work the acceptance criteria in the project's idiom.
2. Verify with the **cheapest signal that moves you forward** — the
   one test file or smoke command exercising the change. Full passes
   wait for Phase 5.
3. Stay in ticket scope. Adjacent problems go in the report's
   "observed, not addressed" list, not in the diff.
4. Multi-ticket: keep each ticket's work separable — every commit in
   Phase 5 must be attributable to its ticket ID(s).

## Phase 5: Gates & commit

1. Run the fast local buckets exactly as discovered — `format`,
   `lint`, `typecheck`, scoped `test`; `build` only when plausibly
   affected — per verification-gates.md right-sizing. Gates run as
   discovered, including mutating ones (`--fix`-style): fold
   autofixes into the commit under test and re-run the scoped test
   once when a gate changed files.
2. Green → commit in the project's format. Each commit body names the
   ticket ID(s) it advances (exact form per project conventions;
   closing keywords are reserved for the PR body — see
   ticket-detection.md § Server-side linking). Multi-ticket branches
   land one commit per separable unit of work where practical.
3. Red → fix and re-run. A gate that cannot be brought green stops
   the exit axis before any push/PR; report the failure verbatim in
   `## Verification`.

## Phase 6: Exit axis

- **Default** — stop after the gated commit(s). No push; the branch
  and worktree stay local for the user.
- **`--push`** — publish with an upstream:

```
git push -u origin <branch>
```

- **`--pr`** — push as above, then open the PR with the tickets
  linked per ticket-detection.md § Server-side linking: GitHub
  closing keywords (`Fixes #123`) in the body; Linear IDs already in
  the branch name and repeated in the PR title for auto-attach:

```
gh pr create --title "<title>" --body "<body linking the tickets>"
```

  On non-GitHub forges use the forge's CLI equivalent when present;
  otherwise report the prepared title and body for manual creation.
  After opening, offer `gh pr checks --watch` when CI is observable.

## Output contract

1. Hero block (1–4 lines): `✓ <branch> ready — N commit(s), <exit>`
   or `⚠ blocked at <phase>`, plus ticket ID(s) and worktree path.
2. `## Tickets` — one row per ticket: ID, title, tracker, source;
   note that nothing was written back.
3. `## Worktree` — path, branch, start point, created vs resumed.
4. `## Primer` — only with `--setup-only`: the ticket context (title,
   description, acceptance criteria, link), ready to hand to the next
   session.
5. `## Commits` — one row per commit: SHA, subject, ticket ID(s),
   gate result. Omitted with `--setup-only`.
6. `## Verification` — gate commands run and results; the local-vs-CI
   split; deferred work named; the watch command when observable.
7. End with an `AskUserQuestion` panel (skip when already in plan
   mode): push now / open a PR / keep it local / remove the worktree.
   In a non-interactive run, record the question and options in the
   report instead of asking, and default to keeping the branch local.
