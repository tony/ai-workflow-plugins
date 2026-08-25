---
name: action
description: "Use when screened review findings should be fixed on the current branch, usually as one verified commit per finding."
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[findings text] [--pr=<num>] [--base=<ref>] [--no-fixup] [--on-fail=skip|stop|ask] [--reply]"
user-invocable: true
disable-model-invocation: true
---


# `/respond:action`

Land the review findings that survived screening. Each accepted finding
is fixed in the simplest way that works and committed on its own,
behind the project's discovered quality gates.

Invoked by name, never routed to on the model's initiative: it modifies
files and creates commits.

## Core thesis

Screening already decided *what* is worth doing and why. This skill
decides *how little* it takes to do it.

That framing matters because the review loop runs on every branch,
forever. Each round leaves behind guards, tests, and comments that were
individually defensible, and their sum is how a readable codebase
becomes an unreadable one without anyone ever writing anything bad. The
discipline that prevents it is `../../references/bloat-discipline.md`,
and it binds every fix here: why now, why this, and what does the next
reader inherit.

Three rules:

1. **No fix without a verdict.** The ledger from `/respond:check` is
   the input. Findings not in it do not get fixed here.
2. **One finding, one commit, smallest fix.** Gates green before every
   commit.
3. **History rewrites are opt-in.** `fixup!` + autosquash is offered,
   never assumed.

## The screening gate

```
NO FIX WITHOUT A VERDICT
```

This skill does not triage. Before any edit, resolve a ledger:

- **A ledger exists for this branch, this `HEAD`, and this feedback** —
  use it. Its verdicts are settled; do not re-argue them.
- **No ledger, or a stale one** — `HEAD` moved, or feedback arrived
  that it never screened. Run `/respond:check` now with the same
  arguments and use its ledger. When the host cannot invoke it, follow
  `../../references/screening-rubric.md` end to end first, and say in
  the report that screening ran inline.

Skipping screening because the findings "look obviously right" is the
failure this gate exists for. Obvious-looking findings are exactly the
ones that turn out to be pre-existing, already fixed, or a fix costing
ten times the defect.

## `$ARGUMENTS` contract

| Flag | Default | Effect |
|---|---|---|
| `--pr=<num>` | current branch's PR when one exists | Passed through to screening: collect findings from the PR. |
| `--base=<ref>` | merge-base with `origin/<trunk>` | Override the provenance baseline. |
| `--no-fixup` | off | Never propose `fixup!` commits; everything lands as a forward commit. |
| `--on-fail=<mode>` | `ask` | Per-finding gate failure: `skip` (revert that fix, continue), `stop` (revert, halt), `ask` (surface via `AskUserQuestion`). |
| `--reply` | off | Draft replies for declined and deferred findings and offer to post them after the fixes land. |

Non-flag text is the findings list, handed to screening.

## Fix shapes

The ledger says what to fix; these say what the fix looks like.

**Behavioral bugs** get the smallest change that removes the defect,
plus a regression test only when the bloat discipline's two-part test
passes: the branch could plausibly break this again, and no existing
test would catch it.

**Comment and docstring findings** are addressed with maximum
concision. The rewrite is shorter than what it replaced; a finding that
grows the comment block was misread. The three-year test governs what
survives at all.

**Typos** are fixed. A typo whose causal commit is in-branch, unpushed,
and not a merge may take the `fixup!` shape; anything else is a forward
commit. A typo sharing a commit with a non-typo finding takes the
forward shape.

**Findings whose only available fix is a defensive wrapper, a
single-caller abstraction, or a guard against a state the caller
already excludes** should not have reached here. If one did, stop and
return it to screening's cost gate rather than building it.

## History rewrites: always prompted when non-trivial

`fixup!` commits target the causal commit and are squashed
non-interactively:

```console
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <base>
```

`<base>` is the resolved provenance base — the merge-base, or
`--base=<ref>` when given.

This rewrites history, so:

- **Trivial and safe** (typo-class fix whose causal commit is
  in-branch, unpushed, and not a merge): offer fixup as the plan's
  default.
- **Non-trivial** (the causal commit is pushed or shared, merge
  topology sits in between, the fix spans commits, or the causal commit
  is large enough that rebasing risks conflicts): **always prompt** via
  `AskUserQuestion` before rewriting. Losing or garbling history is
  worse than an extra forward commit.
- `--no-fixup` disables all of it.

## Phase 0: Situational awareness

1. Read `AGENTS.md` / `CLAUDE.md` / `.github/CONTRIBUTING.md` for the
   commit format and conventions.
2. Resolve the five gate buckets and the CI-coverage split per
   `../../references/verification-gates.md`.
3. Confirm a clean working tree — a dirty tree halts: ask to stash,
   proceed on top, or abort — and detect trunk and push state with
   `git status -sb`.

## Phase 1: Resolve the ledger

Apply the screening gate above. Report which path was taken: an
existing ledger, a fresh screening run, or inline screening.

## Phase 2: Orchestration plan

Enter plan mode if the host supports it (Claude Code: `EnterPlanMode`;
Cursor / Codex / Gemini: `/plan` or `Shift+Tab`) and present:

1. The accepted findings with their verdicts and provenance, and the
   count of deferred and declined ones (not their detail — screening
   already reported that).
2. Per finding: the planned minimal fix, its commit subject in the
   project's format, and forward-vs-`fixup!` shape. Two findings share
   a commit **only** when they edit the same lines, and the plan says
   so explicitly.
3. Anything the fix adds beyond the fix — a new test, a new comment, a
   new code path — named per finding, with why it is warranted. A fix
   that adds nothing says so; that is the good case.
4. The prompts that will fire: non-trivial rewrite consent, reply
   posting.
5. The discovered gate commands and the local-versus-CI split.
6. The `--on-fail` mode in effect.

Wait for approval, then exit plan mode. Without plan mode, present the
same plan inline and proceed on confirmation. In a non-interactive run,
record the plan in the report and proceed with the stated defaults.

## Phase 3: Execute per finding

For each accepted finding, in plan order:

1. Apply the minimal fix.
2. Run the fast local gates — `format`, `lint`, `typecheck`, and
   `test` scoped to the affected area; `build` only when the change
   plausibly affects build output. Gates run as discovered, including
   mutating ones: fold any autofix into the commit under test and
   re-run the scoped test once when a gate changed files.
3. Green → commit. The message uses the project's format and describes
   the defect and the fix in the project's own terms — not the finding
   id, not the reviewer, not the review. A `fixup!` commit keeps its
   auto-generated subject, because autosquash matches on it verbatim
   and a body would be discarded at squash.
4. Red → revert that fix and follow `--on-fail`.

After all findings: run the consented autosquash if any `fixup!`
commits exist, then re-run the fast gates once.

## Phase 4: Replies

With `--reply`, take the drafted replies from the ledger for declined
and deferred findings, show them in full, and post them on one
confirmation — replying to the originating thread where the source was
a thread, otherwise as a single pull-request comment. Never post
without that confirmation, and never resolve a thread on the reviewer's
behalf: the reviewer decides whether the answer settled it.

Without `--reply`, the replies stay in the report for the user to send.

## Phase 5: Report — the output contract

1. Hero block (1–3 lines): `✓ N fixed, M deferred, K declined` plus the
   branch name.
2. `## Commits` — one row per landed commit: finding → SHA → subject →
   gate result.
3. `## What the fixes added` — every test, comment, code path, and
   dependency introduced, with the finding that justified it. An empty
   section is the good outcome and is shown as empty, not omitted.
4. `## Deferred & declined` — the follow-up recommendations and the
   replies, marked as posted or not.
5. `## Verification` — the gate commands run, what was deferred to CI,
   and the watch command when a remote exists.
6. End with an `AskUserQuestion` panel (skip inside plan mode): push
   and watch CI, hand the branch to `/respond:goal` to run the loop to
   completion, run deferred opt-ins, or stop. In a non-interactive run,
   record the options and default to stopping.
