# The rebuild contract

What replaces tree equality when the implementation is thrown away and
written again.

the `git-branch-soft-reset-and-recommit` skill can promise the result is
byte-identical, and gates on it. A redo cannot: a ground-up rebuild
that produced an identical tree would just be a recommit. Something
weaker has to carry the guarantee, and it has to be named before any
code is written — otherwise "it still works" means whatever the person
looking at it wants it to mean.

## The contract

**The tests are the specification.** Three sets, and they are not
equivalent:

- **Trunk's tests.** They encode behavior the branch was never
  supposed to change. Any failure is a regression, full stop.
- **The tests the branch added or changed.** These are the branch's
  own statement of what it set out to do. They are the spec the
  rebuild is written against.
- **Tests the rebuild wants to change.** Every one of these is a
  decision surfaced to the user, never a silent edit. A rebuild that
  may rewrite its own spec has no spec.

That last rule is the whole contract. It is easy to make any rebuild
pass by adjusting the assertions, and an agent that is allowed to do
so will, without noticing.

## Run the spec before trusting it

A failing or skipped test is not a specification. Before the rebuild
starts, run the branch's tests against the branch and record the
result. What passes now is the contract; what is already failing or
skipped is a finding to raise, not a target to hit.

## When the branch has no tests

Say so plainly, and stop before rebuilding.

An untested branch has no mechanical invariant at all, which makes a
redo a rewrite with human review as the only safety net. The useful
move is to offer to write characterization tests **against the
existing implementation first** — landing them on the old branch, or
as the rebuild's first commit — so that a spec exists before anything
is thrown away.

A characterization test does not assert what the code *should* do; it
pins what it *currently* does, including behavior nobody chose. That
is exactly what a redo needs to avoid losing.

## The coverage ledger

Built before any code is written, from the original branch. It is the
list the rebuild is checked against, and it exists because a fresh
implementation will not rediscover the things that made the original
messy.

Every entry records what it is, where the evidence is, and whether the
rebuild addressed it. Gather:

- **Behavior changes** — every observable difference from trunk, from
  the diff and the commit messages.
- **Tests** — each test the branch added or changed, and what it pins.
- **Edge cases and workarounds** — a fix in a later commit for a case
  the first commit missed, a guard for a platform quirk, a retry, a
  defensive branch. These are the highest-risk entries: they usually
  have no comment explaining them and a clean rewrite drops them.
- **Review requests** — anything a reviewer asked for on the pull
  request, resolved or not.
- **Ticket acceptance criteria** — what the work was for.
- **Public surface** — exports, CLI flags, config keys, migrations,
  schema changes.
- **Dependencies** — anything added, removed, or pinned.

`commit-messages.md` Part 2 already covers how to mine commits,
trailers, review threads, tickets, and session transcripts, along with
the privacy rules for the last of those. The difference here is what
the material is for: a recommit uses it to write messages, a redo
uses it to reconstruct requirements.

## Reconciling

Two passes, in this order.

**Ledger walk.** Every entry is marked addressed, deliberately
dropped, or missed. A deliberate drop is a decision the user makes,
with the reason recorded in the commit message that drops it. A miss
is a defect in the rebuild.

**Diff as review material.** Then compare the implementations:

```
git diff <old-branch> <new-branch>
```

This is not a gate and must not be treated as one — the whole point
was to write different code. Read it as a list of questions. Every
hunk where the old branch did something the new one does not is a
prompt: was that deliberate?

## What counts as done

All of these, together:

- Trunk's tests pass.
- The branch's tests pass, unmodified, or every modification was
  approved.
- Every ledger entry is addressed or explicitly dropped.
- The project's own gates pass on every commit of the new series.
- The old branch still exists.

## Failure modes

**Silently editing a spec test.** The single most likely way a redo
produces a green, wrong result.

**Rebuilding from the diff instead of the ledger.** Reading the old
implementation line by line and retyping it is not a redo; it
reproduces the structure that motivated the rewrite. Work from the
requirements, and consult the old code when the ledger is ambiguous.

**Losing an unexplained workaround.** A guard with no test and no
comment looks like noise and is usually a scar. Treat every one as
load-bearing until its ledger entry says otherwise.

**Deleting the old branch.** It is the reference, the fallback, and
the evidence. It outlives the rebuild.

**Calling it done because the tests pass.** The tests are the spec
only to the extent the branch wrote them. The ledger covers what they
missed.
