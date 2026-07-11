---
description: >-
  Use when the user wants to fan several tickets out into parallel
  branches and git worktrees — one worktree per ticket by default,
  tickets grouped onto a shared branch when they clearly overlap.
  Triggers on phrases like "set up worktrees for these tickets", "fan
  out my Linear queue", "work these three issues in parallel", "a
  worktree per ticket", or "batch these bugs into branches". Discovers
  and groups tickets strictly read-only, confirms the grouping at a
  plan gate, then drives each unit through /action:worktree's
  procedure — one subagent per worktree where the host supports it,
  sequential otherwise.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[<ticket>...] [--groups=\"a b; c\"] [--sequential] [--local|--temp] [--push|--pr|--setup-only]"
---

# `/action:worktrees`

Fan several tickets out into branches and worktrees. This command
owns exactly three things: **discovery** (which tickets),
**grouping** (which tickets share a branch), and **fan-out**
(parallel subagents or a sequential loop). Everything per-unit —
ticket resolution detail, branch naming, worktree creation,
implementation, gates, commits, the exit axis — is
`/action:worktree`'s procedure, followed by reference, never
restated here.

This is a slash command, not a model-invocable skill: it creates
worktrees and branches, modifies files, and creates commits, so it
must be user-explicit, not router-inferred.

## Core thesis

N tickets rarely need N decisions — they need one plan and N
executions. The plural command's value is the plan: the right ticket
set, the right grouping (1:1 by default, shared branches only on
clear overlap), and a fan-out that parallelizes the safe part
(implementation inside isolated worktrees) while serializing the
unsafe part (mutation of shared git state).

Three disciplines:

1. **Delegate, don't duplicate.** The per-unit procedure lives in
   `${CLAUDE_PLUGIN_ROOT}/commands/worktree.md` and the shared
   references — this file never paraphrases it. If the two files ever
   disagree, `worktree.md` wins; if `worktree.md` cannot be read at
   runtime, stop and say so — never reconstruct its procedure from
   memory.
2. **Group by evidence, confirm at the gate.** Default 1:1
   ticket-to-branch; propose a group only when tickets clearly
   overlap; every grouping is confirmed at the plan gate.
3. **Shared git state mutates only in the main loop** (see The Iron
   Rule).

## The Iron Rule

```
SHARED GIT STATE MUTATES ONLY IN THE MAIN LOOP
```

`git worktree add` / `remove`, branch creation, and any stash or
index operation on the shared repository happen **serially, in the
main loop**, before or after fan-out — never inside parallel units.
A parallel unit touches only files inside its own worktree and
commits only on its own branch. The tickets themselves stay
read-only throughout, per ticket-detection.md § The read-only
invariant — discovery queries included.

| Rationalization | Reality |
|---|---|
| "Each subagent can create its own worktree — it's faster" | `git worktree add` writes shared `.git` state (refs, the worktree registry); concurrent adds race. Creation costs seconds; untangling a corrupted registry costs the afternoon. |
| "Two small units can share a worktree" | A worktree serves one branch. Two units in one tree overwrite each other's diffs and commit each other's files. |
| "Stash the main checkout so units start clean" | The main checkout's uncommitted work belongs to the user, and worktrees already isolate units from it. If a stash is ever genuinely needed, it happens in the main loop with the user's consent — never from a unit. |

**Red flags — STOP:** a `git worktree` or `git stash` command inside
a subagent prompt; two units whose worktree paths collide; a unit
whose branch name matches another unit's.

## `$ARGUMENTS` contract

Non-flag text: any number of ticket references (IDs, URLs, `#123`).
Empty → Phase 1 discovers candidates and asks.

| Flag | Default | Effect |
|---|---|---|
| `--groups="a b; c"` | off | Explicit grouping: semicolon-separated groups, whitespace-separated tickets within a group. Skips overlap proposals; still confirmed at the plan gate. |
| `--sequential` | off | Force sequential execution even where subagents are available. |
| `--local` / `--temp` | `--local` | Placement axis, forwarded to every unit (see `/action:worktree`). |
| `--push` / `--pr` / `--setup-only` | commit only | Exit axis, forwarded to every unit (see `/action:worktree`). |

Placement and exit flags apply uniformly to every unit; there is no
per-unit override — run `/action:worktree` separately for a unit
that needs different axes.

## Phase 0: Situational awareness

As `/action:worktree` Phase 0 (Situational awareness) — conventions
files, the five gate
buckets and CI split per
`${CLAUDE_PLUGIN_ROOT}/references/verification-gates.md`, ticket
tooling inventory, trunk and remote detection — plus plural-specific
checks:

1. Confirm `git worktree` is usable and there is disk headroom for N
   checkouts.
2. Note any setup a fresh checkout needs before gates can run
   (dependency install, codegen) — every unit must be able to
   verify.
3. Detect subagent support (Task tool or host equivalent); without
   it, plan for sequential main-loop execution.
4. More than 4 units → flag the fan-out size for explicit
   confirmation at the plan gate; a dozen worktrees is rarely what
   anyone wants.

## Phase 1: Ticket discovery

Resolve the ticket set:

1. **Explicit references in `$ARGUMENTS`** — resolve each per
   ticket-detection.md (detection source ladder; read-only fetch of
   title, description, acceptance criteria, branch-name field).
2. **Empty → mine the conversation** — tickets under discussion, a
   pasted list, a triage the user just agreed to.
3. **Still empty → query, read-only** — the tracker reached by the
   detection ladder: assigned-to-me or current-cycle issues via
   tracker MCP reads, or:

```
gh issue list --assignee @me
```

   Present the candidates via `AskUserQuestion` (multi-select) —
   never auto-select a whole backlog.

## Phase 2: Grouping

Default: **1:1** — one ticket, one branch, one worktree.

Propose a group (several tickets, one branch) only on clear overlap
evidence:

- The tickets name the same component, files, or surface.
- One ticket's acceptance criteria cannot be met without another's
  change.
- The tracker marks them as sub-issues or duplicates of one story.

`--groups` replaces proposals with the user's own grouping. Grouped
units are crosscutting branches: naming skips the ticket-system rung
and proposes a theme slug (ticket-detection.md § Branch-name
precedence ladder), and every ticket's ID rides in the unit's
commits and PR per § Server-side linking. Every grouping — proposed
or explicit — is confirmed at the Phase 3 plan gate.

## Phase 3: Orchestration plan

Enter plan mode if the host supports it (Claude Code:
`EnterPlanMode`; Cursor / Codex / Gemini: `/plan` or `Shift+Tab`) and
present:

1. The unit table: unit → ticket(s) → branch name (with its ladder
   rung) → worktree path → exit axis.
2. Grouping rationale, one line per proposed group (or "1:1
   throughout").
3. Execution mode: parallel (one subagent per unit) or sequential,
   and why (host support, `--sequential`).
4. Discovered gate commands and the local-vs-CI split (shared by all
   units).
5. The serialization boundary: worktree/branch creation in the main
   loop; implement → gates → commit → exit per unit.

Wait for approval, then exit plan mode. This gate also stands in for
each unit's own plan gate (`/action:worktree` Phase 2, Orchestration
plan): units run non-interactively and must not re-prompt. If plan mode is
unavailable, present the plan inline and proceed on confirmation. In
a non-interactive run, record the plan in the report and proceed
with **1:1 grouping only** — never apply inferred groups without a
human at the gate.

## Phase 4: Fan-out

1. **Serialize setup (main loop).** For each unit in plan order,
   perform `/action:worktree` Phase 3 (Worktree & branch) exactly as
   written there — start point, idempotency ladder, collision halt,
   primer assembly. One unit at a time; never a parallel
   `git worktree add`. With `--setup-only`, all units stop here.
2. **Delegate the work.** For each unit, hand the executor — a
   subagent (Task) where supported, the main loop otherwise — the
   unit's parameters (tickets and primer content, branch, worktree
   path, exit axis, resolved gate commands) plus the per-unit
   procedure: `/action:worktree` Phases 4–5 (Implement; Gates &
   commit) and its Iron Rule, read from
   `${CLAUDE_PLUGIN_ROOT}/commands/worktree.md` and quoted to the
   executor — not paraphrased from memory — with this standing
   instruction: *work inside your assigned worktree only; never run
   `git fetch`, `git stash`, or `git worktree` subcommands; never
   touch paths outside your worktree.*
3. **Contain failures.** A unit that cannot reach green exits with a
   failure note (`/action:worktree` Phase 5, Gates & commit — red
   path): it never blocks other units, and its worktree stays in
   place for inspection.
4. **Serialize the exit axis.** Remote operations are excluded from
   subagent scope: after the units report, run each green unit's
   `/action:worktree` Phase 6 (Exit axis — push, PR) one unit at a
   time in the main loop. In sequential degradation, Phase 6 folds
   into each unit's turn instead — nothing is concurrent there.
5. **Serialize teardown decisions.** No worktree is removed in this
   phase; removal is offered in the closing panel and executed in
   the main loop.

## Output contract

1. Hero block (1–4 lines): `✓ N units done, M blocked` + execution
   mode + exit axis.
2. `## Units` — one row per unit: ticket(s) → branch → worktree path
   → created/resumed → commits landed → gate status → exit taken.
3. `## Grouping` — the final grouping and its rationale (or "1:1").
4. `## Verification` — shared gate commands, per-unit results
   summarized, the local-vs-CI split, deferred work named.
5. `## Blocked` — failed units with the failure verbatim and the
   worktree path to inspect. Omit when none.
6. End with an `AskUserQuestion` panel (skip when already in plan
   mode): push all green units / open PRs for green units / retry
   blocked units / remove finished worktrees / stop. In a
   non-interactive run, record the question and options in the
   report instead of asking, and default to stopping with all
   worktrees kept.
