# Deriving the goal, and measuring drift against it

Used by `/situate:refocus`.

## The goal is derived, never stored

Every invocation re-reads the goal from the project's own artifacts.
Nothing is written to disk and nothing carries over between sessions.

A stored goal is worse than no goal. It goes stale the moment the ticket
is edited or the scope is renegotiated in a comment, and a stale goal is
confidently wrong in exactly the situation this command exists for —
resuming work after a gap, where the user has no memory to check it
against. Re-deriving costs a few reads and cannot drift.

The cost is real and worth naming: a goal the user only ever said out
loud, in a session that has since ended, is not recoverable. When that
is the case, say the goal came from the branch name and is weak, rather
than presenting a guess as the record.

## Precedence

Take the first source that yields a goal, and say which one it was.
Confidence differs enormously between them.

1. **What the user stated in this session.** Binding, and it beats every
   artifact. If the user said the goal out loud, that is the goal, even
   where the ticket says otherwise — they are allowed to renegotiate
   scope without editing the ticket first.
2. **The linked ticket's acceptance criteria.** The body, not the title.
   A title names a topic; the criteria say what done means. Resolve
   ticket IDs the way `situation-sweep.md` does — from commits, the
   branch name, and the pull request body only.
3. **The pull request body.** What the branch claims to deliver, in the
   author's own words. Fall back to its title only if the body is empty
   or a template.
4. **The branch name and its first commit.** Weak but usually directional:
   the first commit is what the branch set out to do before anything
   else accumulated on top of it.
5. **Nothing.** Say so and ask. Do not synthesize a goal from the diff —
   a goal inferred from the work cannot detect drift in that work, since
   every commit trivially matches it.

## When sources disagree

The ticket and the pull request describing different things is a
finding, not an ambiguity to resolve silently.

The ticket is what was asked for. The pull request is what is being
delivered. A gap between them means either the scope moved without the
ticket being updated, or the branch is solving a different problem than
the one filed. Report both readings and let the user say which is
current.

## Drift has two sides

Most drift-checking catches only the first of these. Both are drift.

**Work the goal never asked for.** Commits and uncommitted changes that
do not serve the stated outcome.

**Work the goal asked for that has not happened.** Acceptance criteria
with nothing on the branch addressing them. On a resumed ticket this is
usually the more useful half — the branch looks busy, and what is
missing is invisible until something checks the criteria one by one.

## Classify, do not just flag

Sort every commit and every uncommitted change into three buckets. The
middle one is why this cannot be a keyword match against the ticket.

**On goal.** Directly serves a stated outcome.

**Load-bearing detour.** Not in the goal, but the goal could not land
without it — a broken fixture that blocked the test, a dependency bump
the new code required, a rename the compiler forced. This is correct
work and must not be reported as drift. Say what it unblocked.

**Off goal.** Neither serves the outcome nor unblocked it. This is the
drift. Name where it started — the first commit that departed — because
that commit usually explains the whole excursion.

## Why it happened

When there is off-goal work, name the pattern. The user recognizes their
own drift faster than they parse a list of commits, and the pattern
predicts whether it will recur:

- Repairing something noticed in passing while touching the file
- A failing check dragging in an unrelated fix to get green
- Review feedback that expanded scope without the ticket following
- Gold-plating a piece that already met the criteria
- A rabbit hole opened by an assumption that turned out wrong

## Realigning

Read-only. Produce the assessment and the corrective options; execute
nothing. Branch surgery, reverts, and scope edits are the user's call,
and this command runs precisely when their judgment of the situation is
the thing in question.

Four correctives, and the last one is not a consolation prize:

- **Finish the gap.** Name the unaddressed criteria in priority order.
- **Defer the off-goal work.** Split it to a follow-up branch or file it
  as its own issue, so it survives without holding this one open.
- **Drop it.** Correct when the excursion produced nothing worth keeping.
- **Widen the goal.** Sometimes the drift was the right instinct and the
  ticket was scoped too narrowly. The fix is then to update the ticket or
  the pull request body to match what is actually being built — not to
  revert good work for conforming to a stale description.

Never assume the goal wins. The goal is evidence of what was intended,
and the user is allowed to have learned something since.
