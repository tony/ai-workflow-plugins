---
name: check
description: "Use when screening or replying to pull-request review comments and bot findings; decide if each comment is real, worth fixing, deferred, or declined."
allowed-tools: ["Bash", "Read", "Grep", "Glob", "AskUserQuestion", "Task"]
argument-hint: "[findings text] [--pr=<num>] [--base=<ref>] [--include-resolved]"
user-invocable: true
---


# `/respond:check`

Screen review feedback and decide what deserves a fix. Every claim —
from a colleague, from a bot, from a review command run earlier in this
session — is tested against six gates and leaves with a verdict, its
evidence, and a reply the reviewer can argue with.

**This skill changes nothing.** No edits, no commits, no comments
posted, no threads resolved. Its entire output is a ledger and a
recommendation; acting on it is `/respond:action`'s job.

That is also why this skill can be routed to on the model's initiative
while `/respond:action` and `/respond:goal` cannot: reaching for
screening when someone pastes a review costs a report and nothing else.

## Core thesis

A review is a set of claims, and a claim is not a work order. The
expensive mistakes are symmetrical: a branch that fixes everything a
reviewer says grows tests, guards, and comments that nobody can later
justify; a branch that dismisses what a reviewer says ships the bug.

Screening separates the two before any code moves, and it separates
them *on the record* — every verdict carries the evidence that produced
it, so a reviewer who disagrees can attack the evidence instead of the
judgment.

The screening question is never only "is this correct?" It is:

1. Is it **true** of the code as written?
2. Did **this branch** cause it?
3. Is it right **for this project**, against the decisions the project
   has already made and written down?
4. How **often** does the scenario it describes actually fire, and what
   happens when it does?
5. What would the fix **cost** everyone who reads the file afterward?

The rubric that answers these is `../../references/screening-rubric.md`
and it is the authority; this skill collects the inputs and reports the
outputs.

## `$ARGUMENTS` contract

Non-flag text is the findings list. With no arguments and no `--pr`,
look for review output already in this session; if there is none, ask
for the feedback rather than inventing a review.

| Flag | Default | Effect |
|---|---|---|
| `--pr=<num>` | current branch's PR when one exists | Collect from the PR's reviews, inline comments, and threads. |
| `--base=<ref>` | merge-base with `origin/<trunk>` | Override the provenance baseline (a stacked branch's parent, for instance). |
| `--include-resolved` | off | Screen resolved and outdated threads too, instead of treating them as already settled. |

## Phase 0: What this project has already decided

The alignment gate needs citations, so gather them before reading a
single finding: `AGENTS.md` / `CLAUDE.md` and any nested equivalents
covering the touched directories, `.github/CONTRIBUTING.md`, and the
branch's own stated purpose — its pull request body, its commit
messages, its ticket.

Resolve the provenance base here too (see the rubric's Provenance
gate), and note the branch's push state with `git status -sb`.

A project with nothing written down has made no decisions to cite,
which means the alignment gate will rarely fire. That is the correct
outcome, not a reason to substitute a preference for a citation.

## Phase 1: Collect

Gather from every channel `../../references/feedback-sources.md`
describes that applies to this run: pasted text, this session's earlier
review output, the pull request's three comment surfaces, and failing
CI.

Normalize each claim into a finding record, split multi-claim comments
into separate findings, drop the approvals and summaries that assert
nothing, and merge duplicates — the same defect from four reviewers is
one finding with four sources.

Carry forward the declines from any previous round in this session: a
bot re-posting a finding that was already declined, against code that
has not changed since, does not get screened twice.

## Phase 2: Screen

Run the six gates on every finding, in the rubric's order, stopping at
the first gate that settles it. Record each gate's evidence as you go —
the diff that settled provenance, the citation that settled alignment,
the trigger that settled odds. A verdict with no evidence behind it is
not a verdict, and the report must not contain one.

Two disciplines while screening:

- **Read the code, do not trust the claim.** Automated reviewers assert
  with total confidence regardless of whether they are right, and three
  bots agreeing is one opinion repeated, not corroboration.
- **Cost the smallest fix that works**, not the one the reviewer
  proposed. Reviewers routinely propose a mechanism where a condition
  would do, and the cost gate should judge the cheaper option.

Use `AskUserQuestion` for `ask` verdicts only — findings where the
truth depends on intent only the author has, or where the alignment
citation is genuinely contested. Everything else is decided here.

## Phase 3: Report — the output contract

1. Hero block (1–3 lines): `N to fix, M deferred, K declined` plus the
   branch name and the feedback sources screened.
2. `## Ledger` — one entry per finding: id, source (author, and whether
   it is a bot), the claim quoted, location, the gate results with
   their evidence, and the verdict with its reason. Merged duplicates
   list all their sources on one entry.
3. `## To fix` — the accepted findings in the order they should land,
   each with the minimal fix and whether it wants a forward commit or a
   `fixup!`.
4. `## Deferred & declined` — with the follow-up recommendation or the
   drafted reply. A declined `improbable` reply states the trigger the
   scenario needs, so a reviewer who knows a caller that produces it
   can say so.
5. `## Ledger key` — branch, `HEAD` SHA, and the feedback digest. This
   is what `/respond:action` checks to know the screening still
   describes the current tree.
6. End with an `AskUserQuestion` panel: run `/respond:action` on the
   accepted findings, run it with `--reply` so the drafted replies get
   posted too, re-screen with the deferred findings opted in, or stop.
   In a non-interactive run (CI, subagent) record the panel's options
   in the report and stop.

Nothing in this phase edits, commits, or posts. If the run reaches a
point where a fix seems obvious enough to just do, that is the failure
mode this skill exists to prevent — write it in `## To fix` and hand
off.
