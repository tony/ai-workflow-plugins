# situate

Gain situational awareness before touching a repository. Read the
branch against trunk, its diff, its pull request and review threads,
its linked tickets, and the project's own conventions — then report
where the work stands and what is unresolved.

Three depths, for three different moments. `/situate` is the full sweep,
for opening a session on work you do not know. `/situate:what` answers a
mid-session "huh" in five lines. `/situate:refocus` asks the separate
question of whether the work still serves what it was started for.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install situate@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/situate` | Sweep the current branch, its pull request, its tickets, and the project's conventions, and report the situation |
| `/situate:what` | Say what is going on in five lines or less, with numbered options when there is a real choice |
| `/situate:refocus` | Re-derive what the work is for, sort the commits against it, and name both the drift and the gap |

`/situate` defaults to the current branch measured against trunk.
`--pr <number|url>` switches the subject to another pull request without
checking it out. `--with-agentgrep [terms]` adds a search of local AI
transcripts for decisions the repository never recorded.

`/situate:what` takes an optional subject to narrow to — `/situate:what
the test failure` spends no lines on branch position.

`/situate:refocus` takes an optional goal, for when the repository does
not record one anywhere.

## Layers

Six, gathered in order, each degrading on its own:

1. **Position** — branch, trunk resolved from the remote's own HEAD,
   ahead/behind, uncommitted work, stashes
2. **Change** — commits since the merge-base and what they were
   building toward, grouped by area
3. **Pull request** — state, checks by job name, unresolved review
   threads and what they ask for
4. **Tickets** — issue IDs found in commits, branch name, and PR body,
   resolved through `gh` or a connected MCP server
5. **Conventions** — the AGENTS.md / CLAUDE.md rules that bear on this
   change, and the quality gates it must pass
6. **Prior conversations** — opt-in, via `agentgrep`

A layer that cannot be gathered is reported unavailable. A layer that
found nothing says so. A section that silently disappears is
indistinguishable from one that was never checked.

## Read-only

No commits, no pushes, no edits, no stashes, no branch switches.

No `git fetch` either. Fetching rewrites remote-tracking refs, which
changes what every later command in the session sees — a mutation
dressed as a read. The sweep works from the refs already present and
reports how old they are, leaving the decision to fetch with the user.

The same reasoning covers the rest: this runs before the user has
decided anything, so it surfaces the failing check and the half-finished
edit rather than repairing them.

## Prior conversations

Off by default. The repository layers read a bounded, current, shared
artifact; `agentgrep` reads local transcripts from every AI CLI on the
machine, including other projects and material the repository never
agreed to hold.

It earns its place when the repository does not explain itself — an
approach with no recorded rationale, work resumed after a gap, a
decision that left no artifact. When it runs, findings are scoped to
this project, capped, and checked against the repository before they
are reported.

A prior conversation is evidence of intent, not of state. A plan
discussed weeks ago may have shipped, been abandoned, or been reversed,
and the transcript reads identically in all three cases. Where the
transcript and the repository disagree, the repository wins — and the
disagreement is usually the most useful thing in the report.

## The brief

`/situate:what` inverts the sweep's contract. The sweep is exhaustive
because its reader is about to touch the code; the brief is ruthless
because its reader has just said "huh", and every line they read before
the confusion ends is a cost.

Five lines is a ceiling, not a target, filled in a fixed order of value
— the blocker, where the work sits, what just happened, what it is for,
what is outstanding — and stopping as soon as the situation runs out.
Slots with nothing real in them are dropped rather than filled, which is
the opposite of the sweep's rule that absence is always reported. On a
five-line budget, "no stashes, no open threads" costs two fifths of the
answer to say nothing happened.

Numbered single-line options follow the body, and only when there is a
real fork. They do not count against the five. There is deliberately no
question panel: a modal is heavier than the answer it would follow, and
this runs ambiently, mid-thought.

Staying cheap enough to ask casually is a design constraint, so evidence
comes in tiers. What the session already knows is free and is tried
first. Local git is cheap and runs when the session's own memory is
thin. `gh` is paid and runs only when a pull request or ticket actually
exists. Fetching, full diffs, and transcript search never run.

## Goal and drift

`/situate:refocus` answers a question the sweep does not ask: not where
the work stands, but whether it still serves what it was started for.

The goal is re-derived on every run and never stored. A stored goal goes
stale the moment scope is renegotiated in a comment, and a stale goal is
confidently wrong in exactly the situation this exists for — resuming
after a gap, where the user has no memory to check it against. It comes
from the first source that yields one: what the user said this session,
then the ticket's acceptance criteria, then the pull request body, then
the branch name and first commit. Which source it came from is reported,
because a goal from acceptance criteria and a goal from a branch name
are not equally trustworthy.

Drift has two sides. Work the goal never asked for is the obvious half.
Work the goal asked for that has not happened is the half that hides —
on a resumed ticket the branch looks busy either way, and only checking
the criteria one at a time surfaces it.

Not everything off-topic is drift. Commits sort three ways, and the
middle one is why this cannot be a keyword match: work that serves the
goal, load-bearing detours the goal could not land without, and genuine
excursions. A fixture repair that unblocked the feature is correct work.

Which commits count is decided before any of that, and not by assuming
trunk. A branch stacked over another branch takes its parent as the
base; measured from trunk instead, the range carries the parent's
commits and the assessment reports work someone else already landed as
this branch's drift. So the base is resolved through the sweep's rules
rather than precomputed cheaply — a wrong base does not produce a
slightly worse answer here, it produces a confidently wrong one.

The goal does not automatically win. Sometimes the excursion was the
better instinct and the ticket was scoped too narrowly — then the
correction is to update the ticket, not to revert good work for
disagreeing with a stale description.

## Shared references

The commands and the skills read the same files at runtime, so the
explicit and ambient paths cannot drift:

- `references/situation-sweep.md` — the six layers, the commands behind
  each, how they degrade, and the evidence discipline separating what
  was read from what was inferred
- `references/prior-conversations.md` — when transcript search is
  warranted, how to scope and cap it, how to reconcile it against the
  repository, and what may not appear in the report
- `references/brief.md` — the five-line budget, the ranking that decides
  what earns a line, the option-line format, and the evidence tiers
- `references/goal-derivation.md` — goal precedence, why nothing is
  stored, the three-way classification, and the four correctives

## Skills

Both trigger on their own and have an explicit command as an entry
point.

`situational-awareness` runs the full sweep when a session opens on
unfamiliar or resumed work — being asked to catch up, to get oriented,
or to say where things left off. `/situate` is its explicit form.

`brief` runs on disorientation rather than on a question: a bare "huh",
"wait, what?", "you lost me", "no idea". The distinction that keeps it
from firing constantly is whether the question names its own subject —
"what does this function do" is an ordinary question and gets an
ordinary answer. `/situate:what` is its explicit form.

Their descriptions are kept vocabulary-disjoint on purpose. Routing
scores terms, so writing "not for catching up on a branch" into the
brief's description would make it match the very prompts it disclaims
and take them from the sweep that should own them. The boundary lives in
each skill's body instead, which is read only after routing has already
chosen.

## Prerequisites

- **git** — every repository layer
- **gh** — pull requests, checks, review threads, and GitHub issues;
  without it the sweep reports those layers unavailable and continues
- **uvx** — only for `--with-agentgrep`, which runs
  [agentgrep](https://pypi.org/project/agentgrep/) without installing it
