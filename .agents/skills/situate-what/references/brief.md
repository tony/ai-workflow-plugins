# The brief

Shared by this skill and the `what` skill.

Five lines, maximum. The reader is disoriented and wants to stop being
disoriented — every line they have to read before that happens is a
cost, not a service.

This is a different contract from `situation-sweep.md`. The sweep is
exhaustive because its reader is about to touch the code. The brief is
ruthless because its reader has just said "huh".

## The budget

Five lines of body. One sentence each, no sub-clauses stacked to smuggle
a sixth fact into the fifth line. No headings, no bullets, no bold, no
preamble, no closing summary.

Option lines are separate and do not count. Everything else does.

Fewer than five lines is a better brief, not an incomplete one. Three
lines that land beat five that pad. There is no obligation to fill the
budget and no template to satisfy.

## What earns a line

Fill from the top of this ranking and stop when the situation runs out
or the budget does:

1. **The blocker.** What is stopping progress right now — a failing
   check, an unanswered question, a conflict, a decision waiting on the
   user. If something is blocked, it is line one.
2. **Where the work sits.** Branch against trunk, pull request state,
   uncommitted work. Compress to one line: `feat-x, 4 commits, PR #12
   open, 2 files uncommitted`.
3. **What just happened.** What this session did or was midway through.
   On a resumed session with no history, what the last commits did
   instead.
4. **What it is for.** The goal, when it is not obvious from the branch
   name or when the work has wandered from it.
5. **What is outstanding.** What remains before this is done.

A fact that fits two slots is stated once, in the higher one.

## Drop, do not pad

The sweep reports absence explicitly, because a missing section there is
indistinguishable from an unchecked one. The brief does the opposite.

Report absence only when it is load-bearing. "No pull request open" on a
finished branch is the finding. "No pull request open" on a branch one
commit old is noise that costs a fifth of the answer.

Never spend a line saying a layer was checked and was boring.

## Options

After the body, optionally offer choices — each exactly one line,
numbered, so the reader can answer with a digit instead of a sentence.

Offer them only when there is a real fork. A brief whose next step is
obvious ends at the body; appending three choices to a situation with
one path is the bloat this command exists to avoid.

Two to four options. Each names an action, not a topic: `2. Resolve the
three review threads on PR #12`, never `2. Review feedback`.

Do not use `ask-user-choice` here. A modal panel is heavier than the
five lines it follows, and the brief is often produced ambiently, mid
thought, where interrupting with a dialog is worse than the confusion it
answers.

## Evidence budget

The brief is asked casually and must stay cheap enough to answer that
way. Work outward in tiers and stop as soon as the five lines are
earned.

**Free — always.** What this session already knows. If a sweep already
ran, or the session has been working in this repo, that is the evidence.
Re-reading what is already in context to look thorough is the most
common way this command gets slow.

**Cheap — run when the session's own memory is thin.** Current branch,
trunk from `refs/remotes/origin/HEAD`, ahead/behind, `git status
--short`, and the branch's commit subjects. These are local and fast.

**Paid — only on an existing reference.** `gh pr view` when the branch
actually has a pull request, `gh issue view` when a ticket ID appears in
the branch name, a commit, or the pull request body. Skip both when the
session already knows their state.

**Never.** `git fetch`, full diff reads, transcript search, convention
files. Nothing here writes, switches branches, or stages anything — the
read-only contract in `situation-sweep.md` applies unchanged.

When a paid layer is unreachable — no `gh`, no network — say so inside
an existing line rather than spending a line on the tooling.

## Confidence

Five lines leave no room to separate what was read from what was
inferred in prose. Use a tighter rule instead: state only what the
evidence supports, and mark at most one inference per brief with a
single hedging word. Two hedges means the brief is guessing and should
say what it does not know instead.

## Banned

- Preamble. Not "Here's what's going on" — just what is going on.
- Restating the question back before answering it.
- File and path inventories. The reader can run `git status`.
- References to earlier turns: "as I mentioned", "as noted above".
- Apology or self-assessment about the confusion that prompted the ask.
- Any line that would be true in every repository on any day.

## When nothing is going on

A clean tree on trunk with nothing in flight is a one-line answer, and
the option lines carry more value than the body: say it is clean and
offer the plausible starts.
