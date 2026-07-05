---
description: >-
  Use when the user wants to act on code-review feedback on the
  current branch — review comments, findings, PR feedback, or a
  reviewer's punch list. Triggers on phrases like "address the review
  items", "respond to the review", "fix the review findings", "handle
  the PR comments", "action the reviewer feedback", or "address each
  issue in separate commits". Fixes only what the branch introduced,
  one finding per commit, behind the project's quality gates; anything
  pre-existing or history-rewriting is surfaced for a decision instead
  of silently done.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[findings text] [--pr=<num>] [--base=<ref>] [--no-fixup] [--on-fail=skip|stop|ask]"
---

# `/review:address`

Address code-review findings on the current branch. Each finding is
triaged for **provenance** (did this branch introduce it?), fixed in
the **simplest pragmatic way**, and landed as **its own commit** behind
the project's discovered quality gates. History rewrites (fixup +
autosquash) happen only with explicit consent.

This is a slash command, not a model-invocable skill: it modifies files
and creates commits, so it must be user-explicit, not router-inferred.

## Core thesis

A reviewer flags; the branch owner scopes. Review findings are claims
about the diff under review, and the correct response set is exactly:
fix it (if this branch caused it), defer it (if it pre-dates the
branch), or decline it with a reason (if it is wrong). Anything else
is scope creep wearing a compliance costume.

Three disciplines:

1. **Provenance before fixes.** No finding is touched until it is
   classified `in-branch`, `pre-existing`, or `disputed` against the
   merge-base with trunk.
2. **One finding, one commit, simplest fix.** Minimal diffs, pragmatic
   over perfect, gates green before every commit.
3. **History rewrites are opt-in.** `fixup!` + autosquash is offered,
   never assumed — and always prompted when the rewrite is non-trivial.

## The Provenance Gate

```
NO FIX WITHOUT PROVENANCE
```

For every finding, before editing anything:

1. Resolve the base: `--base=<ref>` if given, else the merge-base with
   the remote trunk:

```
git merge-base origin/<trunk> HEAD
```

   When no remote exists, fall back to the local trunk branch
   (`main` or `master`); when neither can be resolved, ask for the
   base rather than guessing.

2. Locate the flagged code and test whether this branch introduced or
   last modified it — `git diff <base>...HEAD -- <file>` for the
   region, `git log -L<range>:<file> <base>..HEAD` or blame when the
   diff is ambiguous.
3. Classify: `in-branch` (this branch added/changed it), `pre-existing`
   (present at the base), `mixed` (branch touched some of it), or
   `disputed` (the finding is factually wrong).

Only `in-branch` findings proceed to fixes by default. `pre-existing`
and `disputed` findings go in the report with a recommendation, and the
plan's `AskUserQuestion` panel offers per-finding choices: fix at
branch tip anyway (explicit opt-in), file a follow-up, or leave it.

| Rationalization | Reality |
|---|---|
| "The reviewer asked for it, so I should fix it" | The reviewer flags; the owner scopes. A pre-existing bug fixed on this branch bloats the diff and hides the fix from its own review. |
| "It's a real bug, ignoring it feels wrong" | Deferring is not ignoring: it lands in the report with a follow-up recommendation. Real bugs deserve their own branch and review. |
| "It's a one-line guard, scope barely grows" | The line is one; the regression test, docs, and review surface are not. Small out-of-scope fixes are how branches sprawl. |
| "Provenance is obvious, no need to check" | The baseline for this skill fixed trunk code *because it skipped this exact check*. Run the diff. |

**Red flags — STOP, you are about to violate the gate:** editing a
file the branch never touched; "while I'm here"; fixing a finding you
never classified; a commit that mixes two findings "because they're
related".

## `$ARGUMENTS` contract

If `$ARGUMENTS` is empty and `--pr` is absent, ask for the findings
(pasted text, a file path, or a PR number) before doing anything.

| Flag | Default | Effect |
|---|---|---|
| `--pr=<num>` | off | Pull findings from the PR's review comments (`gh pr view <num> --comments` and the review-comment API) instead of pasted text. |
| `--base=<ref>` | merge-base with `origin/<trunk>` | Override the provenance baseline (e.g. a stacked branch's parent). |
| `--no-fixup` | off | Never propose `fixup!` commits; all fixes land as forward commits. |
| `--on-fail=<mode>` | `ask` | Per-finding gate failure: `skip` (revert that fix, continue), `stop` (revert, halt), `ask` (surface via `AskUserQuestion`). |

Non-flag text is treated as the findings list.

## Acceptance policy (which findings get addressed)

| Finding | Policy |
|---|---|
| `in-branch`, legitimate | Address in the **simplest way possible** — pragmatic beats thorough; minimal diff; a regression test only when the finding is a behavioral bug. |
| Code-comment / docstring findings, even low-severity | Address; maximum concision — **the fewer lines the better**. Rewrites shrink comments, never grow them. |
| Typos (code, comments, docs) | Fix. Trivial and causal commit is in-branch and unpushed → offer `fixup!` + autosquash. Anything else → forward commit, or prompt (see below). A typo fix that shares a commit with a non-typo finding takes the **forward-commit** shape — fixup defaults apply only to pure typo-class commits. |
| `pre-existing` | Do not fix by default. Report + per-finding decision panel. |
| `disputed` / factually wrong | Do not fix to appease. Report with the evidence and a suggested reviewer reply. |
| Style opinions contradicting project conventions | The project's AGENTS.md / CLAUDE.md wins; report the conflict rather than churning code. |

## History rewrites: always prompted when non-trivial

`fixup!` commits target the causal commit and are squashed
non-interactively (`GIT_SEQUENCE_EDITOR=:` accepts the auto-generated
todo list):

```
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <base>
```

`<base>` is the same resolved provenance base from the Provenance
Gate (the merge-base, or `--base=<ref>` when given).

This rewrites history, so:

- **Trivial + safe** (typo-class fix; causal commit is in-branch,
  unpushed, and not a merge): offer fixup as the default in the plan.
- **Non-trivial** (causal commit already pushed or shared; merge
  topology in between; the fix spans commits; the causal commit is
  large enough that rebasing risks conflicts): **always prompt** via
  `AskUserQuestion` before any rewrite — losing or garbling history is
  worse than an extra forward commit. Never run the autosquash
  without that explicit consent.
- `--no-fixup` disables all of this; forward commits only.

## Phase 0: Situational awareness

1. Read `AGENTS.md` / `CLAUDE.md` / `.github/CONTRIBUTING.md` for
   quality checks, commit format, and conventions.
2. Resolve the five gate buckets and the CI-coverage split per
   [references/verification-gates.md](../references/verification-gates.md).
3. Confirm a clean working tree (a dirty tree halts: ask to stash,
   proceed on top, or abort) and detect trunk + push state
   (`git status -sb`, `git log origin/<branch>..HEAD` when a remote
   counterpart exists).

## Phase 1: Parse findings

Normalize each finding to: id, severity/score (as given), category
(bug / comment / typo / style / other), file(s), and the reviewer's
claim, quoted. Findings that cannot be located in the code are marked
`unlocatable` and reported, not guessed at.

## Phase 2: Provenance triage

Run the Provenance Gate on every finding. Produce the triage table
(finding → classification → evidence ref) before any editing begins.

## Phase 3: Orchestration plan

Enter plan mode if the host supports it (Claude Code: `EnterPlanMode`;
Cursor / Codex / Gemini: `/plan` or `Shift+Tab`) and present the plan —
its required contents are defined right here; no external convention
document is required:

1. The triage table with each finding's classification.
2. For each `in-branch` finding: the planned minimal fix, its commit
   subject (project format), and forward-vs-`fixup!` shape. Two
   findings share a commit **only** when they edit the same lines;
   the plan must say so explicitly.
3. The prompts that will fire: pre-existing opt-ins, non-trivial
   rewrite consent.
4. Discovered gate commands and the local-vs-CI split.
5. `--on-fail` mode in effect.

Wait for approval; exit plan mode. If plan mode is unavailable,
present the same plan inline and proceed on confirmation. In a
non-interactive run (CI, subagent), record the plan in the report and
proceed with the command's stated defaults.

## Phase 4: Execute per finding

For each approved finding, in plan order:

1. Apply the minimal fix.
2. Run the fast local gates (`format`, `lint`, `typecheck`, scoped
   `test`; `build` only when plausibly affected — per
   verification-gates.md right-sizing). Gates run as discovered, even
   mutating ones (`--fix`-style): fold any gate-applied autofixes into
   the commit under test, and re-run the scoped test once when a gate
   changed files.
3. Green → commit as planned. Forward commits use the project's
   commit format and quote the finding id in the body. A `fixup!`
   commit keeps its auto-generated subject (autosquash matches on it
   verbatim; a body would be discarded at squash) — its finding id
   lives in the report's Commits table instead.
4. Red → revert that fix and follow `--on-fail`.

After all findings: if `fixup!` commits exist, run the consented
non-interactive autosquash (see History rewrites above); re-run the
fast gates once after the rebase.

## Phase 5: Report — the output contract

1. Hero block (1–3 lines): `✓ N addressed, M deferred, K declined` +
   branch name.
2. `## Triage` — the provenance table with evidence refs.
3. `## Commits` — one row per landed commit: finding id → SHA →
   subject → gates result.
4. `## Deferred & declined` — pre-existing findings with follow-up
   recommendations; disputed findings with evidence and a suggested
   reviewer reply.
5. `## Verification` — gate commands run; what was deferred to CI;
   when a remote/PR exists, end by offering `gh pr checks --watch`
   after push.
6. End with an `AskUserQuestion` panel (skip when already in plan
   mode): push now and watch CI / run deferred opt-ins / stop. In a
   non-interactive run (CI, subagent), record the panel's question and
   options in the report instead of asking, and default to stopping.
