---
description: >-
  Use when the user wants to prove out a feature or fix fast before
  committing to an implementation — a spike, probe, blitz, sprint,
  bolt, speedrun, MVP pass, or proof-of-concept that mutates the
  working tree but must not land as commits. Triggers on phrases like
  "probe it", "quick probe", "spike into", "do a spike", "blitz it",
  "bolt through it", "speedrun the fix", "do a sprint to handle this
  without committing", "take a stab at it", "prove it works, then
  plan", "MVP this then clean it up", "probe those review items", or
  "get it working before my meeting". The goal may be typed or
  inferred from conversation context (review findings, a failing
  test under discussion). Ends with the working tree stashed and a
  commit-by-commit plan to land the work through the project's
  quality gates.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[<goal>] [--branch=<name>] [--keep-tree] [--replay]"
---

# `/spike:probe`

Rapid spike harness. Probe the goal in the working tree with the
lightest verification that proves the path, exit through the project's
fast quality gates, stash everything with a recovery ref, and hand back
a neat commit-by-commit plan — optionally replaying it immediately.

A probe **mutates the working tree freely** — mutation is the point;
the code is the sensing instrument. What it never touches is history:
like an attached kprobe, it patches the live system to take its
measurement and detaches without a trace in `git log`.

This is a slash command, not a model-invocable skill: it mutates the
working tree and (in `--replay`) creates commits, so it must be
user-explicit, not router-inferred.

## Core thesis

A spike answers "does this path work?" — it is **evidence, not a
deliverable**. The probe's value survives as (a) a stash you can
reapply and (b) decisions the plan records. Committing spike code
converts unreviewed exploration into history.

Three disciplines:

1. **Zero commits during the spike.** The probe ends in a stash and a
   plan, never in `git commit`.
2. **Right-sized verification.** During the probe, run only what
   proves the path (a smoke test, a scoped test run). At spike exit,
   run the project's fast gates once so the plan starts from
   known-green knowledge. Defer what CI covers to CI.
3. **The plan is the product.** Every probe ends with a numbered
   commit sequence mapping stash contents to commits, with the
   discovered gate commands attached to each.

## The Iron Rule

```
A SPIKE PRODUCES ZERO COMMITS
```

Not on trunk, not on the feature branch, not on a scratch branch,
not "just to checkpoint". The exit paths are: stash (default),
`--keep-tree` (leave changes unstaged), or `--replay` (commits happen
only *after* the plan is presented and approved, one plan item at a
time, each behind a green gate).

| Rationalization | Reality |
|---|---|
| "The owner said 'we'll clean it up later' — commit now, clean later" | "Later" is this command's Phase 5. A commit *is* the cleanup being deferred; stash instead. |
| "They need it before a meeting — a commit is the fastest handoff" | A stash plus the plan is the same speed and leaves history clean. Show the demo from the working tree. |
| "It's all green, so it's safe to commit" | Green ≠ reviewed. The probe skipped naming, API, and scope decisions on purpose; the plan surfaces them first. |
| "One commit is easier to undo than a stash" | A stash with a recorded ref is exactly as recoverable and never entangles trunk or the branch. |
| "I'll commit on a scratch branch, that doesn't count" | It counts. Scratch branches leak into PRs and get merged. Stash. |

**Red flags — STOP, you are about to violate the Iron Rule:**
typing `git commit` in any form; "checkpoint commit"; "WIP commit";
"temporary commit"; "I'll squash it later"; creating a branch in order
to commit to it. All of these mean: stash and write the plan.

## `$ARGUMENTS` contract

Non-flag text is the probe goal. Resolve the goal by this ladder:

1. **Typed goal wins.** Non-flag `$ARGUMENTS` text is the goal,
   verbatim. Conversation context may enrich it (file paths, error
   messages already discussed) but never overrides it.
2. **Empty → mine the conversation.** Candidate goals are review
   findings just presented, a failing test under discussion, a pasted
   stack trace, or a suggestion the user agreed with.
   - Exactly one strong candidate: adopt it and proceed to Phase 1 —
     the brief there is the confirmation gate.
   - Several candidates: `AskUserQuestion` (multi-select), one option
     per candidate plus "all of them".
   - None: ask what to probe before touching anything.
3. **Record provenance.** The Phase 1 brief states where the goal
   came from — typed, or inferred from which part of the
   conversation.

When the inferred goal is a set of review findings, note the boundary
in the brief: a probe explores fixes with zero commits; landing fixes
commit-by-commit is `/review:address`.

| Flag | Default | Effect |
|---|---|---|
| `--branch=<name>` | off | Run the probe on a new scratch branch from the current HEAD instead of the current branch's tree. Still zero commits; the branch only isolates the working tree. |
| `--keep-tree` | off | Skip the stash at spike exit; leave changes in the working tree for the user to inspect. The plan is still produced. |
| `--replay` | off | After the plan is approved, immediately implement it: apply the stash, land plan items one commit at a time, each behind a green gate. |

## Phase 0: Situational awareness

Before writing any code:

1. Read `AGENTS.md` / `CLAUDE.md` / `.github/CONTRIBUTING.md` for
   quality checks, commit format, and test conventions.
2. Resolve the five gate buckets (`format`, `lint`, `typecheck`,
   `test`, `build`) and the CI-coverage split per
   `${CLAUDE_PLUGIN_ROOT}/references/verification-gates.md`.
3. Record the working tree state. A dirty tree halts here: ask the
   user whether to stash their work first, probe on top of it, or
   abort — never mix the probe with uncommitted user work silently.
4. Locate the code the goal touches (existing modules, tests,
   fixtures) — enough to work in the project's idiom, no more.

## Phase 1: Orchestration plan

Enter plan mode if the host supports it (Claude Code: `EnterPlanMode`;
Cursor / Codex / Gemini: `/plan` or `Shift+Tab`) and present a
**short** spike brief — the full brief format is defined right here;
no external convention document is required:

1. The goal, restated in one line, with its provenance (typed, or
   inferred from what).
2. What "proven" means — the demo command or smoke check that ends
   the probe.
3. Files expected to change; scratch branch name if `--branch`.
4. Discovered gate commands (per bucket: command or `unset`) and the
   local-vs-CI split.
5. The exit path: stash / `--keep-tree` / `--replay`.

Wait for approval, then exit plan mode. If plan mode is unavailable,
present the same brief inline and proceed on confirmation. In a
non-interactive run (CI, subagent), record the brief in the report
and proceed. Keep this to seconds, not minutes — it is a probe.

## Phase 2: The probe

Code the shortest path to "proven". During this phase:

- Verify with the **cheapest signal that moves you forward**: run the
  one test file or smoke command that exercises the new code. Do not
  run the full suite, the build, or repeated broad test passes while
  iterating.
- Mark shortcuts as you take them (a `SPIKE:` comment on hardcoded
  values, skipped edge cases, undecided semantics). These become plan
  items, not debt to fix during the probe.
- Stay inside the goal. Adjacent problems you notice go in the plan's
  "observed, not addressed" list.

## Phase 3: Spike exit gate

Once proven, run the fast local buckets exactly as discovered —
`format`, `lint`, `typecheck`, and the scoped `test` command. Run
`build` only if the change plausibly affects build output; otherwise
note it as CI-deferred.

Gate failures here are **information, not work**: fix trivial ones
(formatting), and record non-trivial ones as plan items. The point is
that the plan below describes code whose gate status is *known*, not
guessed.

Gate commands run **as discovered**, including mutating ones
(`--fix`-style linters, formatters). If a gate changes any file,
re-run the proving smoke check from Phase 2 once before moving on —
the stash must contain code that was proven *after* its last
modification.

## Phase 4: Stash with a recovery ref

Unless `--keep-tree`:

1. Stash everything, including untracked files, with a descriptive
   message:

```
git stash push -u -m "spike: <goal> (<what passed, what's undecided>)"
```

2. **Record the stash's immutable SHA** and put it in the plan output:

```
git rev-parse stash@{0}
```

   A dropped or popped stash is otherwise unrecoverable; with the SHA
   it can always be restored via `git stash apply <sha>`.

3. Verify the tree is back to its pre-spike state (`git status`).

## Phase 5: The replay plan

Produce the commit-by-commit plan. For each planned commit:

- **Subject** in the project's commit format (from Phase 0).
- **Contents**: which files/hunks from the stash it takes, and what
  gets rewritten rather than replayed (e.g. test-first where the
  project's conventions demand it).
- **Decisions to resolve**: every `SPIKE:` marker that lands in this
  commit, stated as a question with a recommendation.
- **Gates**: the per-commit gate commands (fast buckets, scoped
  tests), per verification-gates.md right-sizing.

Close the plan with the local-vs-CI table and the post-push watch
command when one is observable — `gh pr checks --watch` for a PR,
`gh run watch` when no PR exists yet, or an explicit "none (no
remote)" so the deferral is visible rather than implied.

## Phase 6: Replay (only with `--replay`, after approval)

1. `git stash apply <sha>` (apply, not pop — the stash stays until the
   replay finishes green).
2. Land plan items in order: stage only that item's changes, run its
   gates, commit with the planned message. A red gate stops the
   replay; report and hand back. Prefer plan items that split at
   **file level**; when one file must split across commits,
   materialize per-commit patch slices (`git diff` the relevant
   hunks to a file, then `git apply --cached <patch>`) — interactive
   staging (`git add -p`) is not available to an agent.
3. After the final item: run any end-of-run `build` bucket, drop the
   stash, and if the branch has a remote counterpart offer to push
   and watch CI.

## Output contract

1. Hero block (1–3 lines): `✓ spike proven` / `⚠ spike blocked` +
   goal + exit path taken.
2. `## Spike findings` — what was proven, `SPIKE:` markers, observed-
   not-addressed list.
3. `## Verification` — gate commands run and their results; the
   local-vs-CI split; what was deferred and why.
4. `## Stash` — stash ref, message, **SHA**, restore command (omit
   with `--keep-tree`).
5. `## Replay plan` — the numbered commit sequence from Phase 5.
6. End with an `AskUserQuestion` panel: replay now / keep stash and
   stop / discard spike — unless already running inside plan mode or
   `--replay` was given. In a non-interactive run (CI, subagent),
   record the panel's question and options in the report instead of
   asking, and default to keeping the stash.
