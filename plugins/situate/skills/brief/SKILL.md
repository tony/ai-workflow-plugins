---
name: brief
description: >-
  Use when the user signals confusion without naming a subject —
  "huh", "huh?", "wait, what?", "sorry, you lost me", "no idea",
  "slow down", "explain simply", "keep it short". Answers in five
  lines or less, followed by numbered single-line options. Not for a
  question that names its own subject.
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
---

# Brief

Someone just said "huh". Give them five lines and get out of the way.

Read `${CLAUDE_PLUGIN_ROOT}/references/brief.md` before answering — it
carries the five-line budget, the ranking that decides what earns a
line, the option-line format, and the evidence tiers. `/situate:what` is
the explicit entry point to this same contract.

## Recognizing the trigger

The signal is a question with no subject. "What does the parser do" names
what it wants and is an ordinary question. "What" on its own names
nothing, because the user cannot yet articulate what they are missing —
that inability is the thing to fix.

Treat these as the same ask: a bare interrogative, a request to back up,
or an admission of being lost. Treat anything with a stated object as a
normal question and answer it normally.

When genuinely unsure, answer briefly rather than asking which they
meant. A five-line answer to the wrong reading costs less than a
clarifying round-trip, and it usually reveals the right reading.

A request to be caught up is not this skill, even though it overlaps.
"Bring me up to speed on this branch", "what is this pull request
waiting on", "where did this work leave off" all name what they want and
want it in full — that is `situational-awareness`, and `/situate` is its
explicit form. This skill is for the moment before someone can phrase
that request.

The description above deliberately carries none of that vocabulary — no
branch, pull request, ticket, or catching up. Routing scores terms, so
naming those here to disclaim them makes this skill match the prompts it
is disclaiming, and it takes them from the sweep that should own them.
The boundary belongs in this body, which is read only after the skill is
already chosen.

## What "huh" is usually about

Rank by how recently the confusion could have started.

Most often it is the last thing that happened in the session — a command
that ran, a decision taken, a direction changed without being announced.
That answer is already in context and needs no tools.

Less often it is the repository: what branch this is, what is
uncommitted, what the pull request or ticket is waiting on. Reach for
the cheap git tier then, and the paid `gh` tier only when a pull request
or ticket ID actually exists.

Often it is both, and both fit — the session in one line, the repository
in another.

## Answering

Five lines maximum, ordered by the ranking in the brief reference:
blocker, position, what just happened, what it is for, what is
outstanding. Drop any slot with nothing real in it rather than filling
it.

Then numbered single-line options, but only when there is an actual
fork. No panel, no dialog — plain numbered lines the user can answer
with a digit.

## Read-only

No commits, no edits, no branch switches, no `git fetch`. Disorientation
is the worst possible moment to change the thing being described.

## Common mistakes

**Answering with a wall.** The trigger for this skill is that the user
is overloaded. A thorough answer is the failure mode, not a generous
one.

**Preamble.** "Let me get you oriented — here's where things stand" is
two lines spent announcing that the next lines exist.

**Re-reading what is already known.** If a sweep already ran this
session, or the work is in context, that is the evidence. Re-running
`git log` to look diligent is pure latency.

**Reporting quiet layers.** "No stashes, no uncommitted changes, no open
review threads" spends three fifths of the answer on nothing happening.

**Apologizing for the confusion.** It attributes the confusion to the
user and delays the fix.

**Diagnosing drift here.** If the work has wandered from what it was
for, say it in one line and offer `/situate:refocus`. The full
goal-versus-drift assessment does not fit and does not belong.
