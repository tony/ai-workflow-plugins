# situate

Gain situational awareness before touching a repository. Read the
branch against trunk, its diff, its pull request and review threads,
its linked tickets, and the project's own conventions — then report
where the work stands and what is unresolved.

`/situate` is the full sweep, for opening a session on work you do not
know. `/situate:refocus` asks the separate question of whether the work
still serves what it was started for.

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
| `/situate:refocus` | Re-derive what the work is for, sort the commits against it, and name both the drift and the gap |

`/situate` defaults to the current branch measured against trunk.
`--pr <number|url>` switches the subject to another pull request without
checking it out. `--with-agentgrep [terms]` adds a search of local AI
transcripts for decisions the repository never recorded.

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

The goal does not automatically win. Sometimes the excursion was the
better instinct and the ticket was scoped too narrowly — then the
correction is to update the ticket, not to revert good work for
disagreeing with a stale description.

## Shared references

The commands and the skill read the same files at runtime, so the
explicit and ambient paths cannot drift:

- `references/situation-sweep.md` — the six layers, the commands behind
  each, how they degrade, and the evidence discipline separating what
  was read from what was inferred
- `references/prior-conversations.md` — when transcript search is
  warranted, how to scope and cap it, how to reconcile it against the
  repository, and what may not appear in the report
- `references/goal-derivation.md` — goal precedence, why nothing is
  stored, the three-way classification, and the four correctives

## Skill

`situational-awareness` carries the same procedure and triggers on its
own when a session opens on unfamiliar or resumed work — being asked to
catch up, to get oriented, or to say where things left off. `/situate`
is the explicit entry point to it.

## Prerequisites

- **git** — every repository layer
- **gh** — pull requests, checks, review threads, and GitHub issues;
  without it the sweep reports those layers unavailable and continues
- **uvx** — only for `--with-agentgrep`, which runs
  [agentgrep](https://pypi.org/project/agentgrep/) without installing it
