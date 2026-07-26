# situate

Gain situational awareness before touching a repository. Read the
branch against trunk, its diff, its pull request and review threads,
its linked tickets, and the project's own conventions — then report
where the work stands and what is unresolved.

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

Defaults to the current branch measured against trunk. `--pr <number|url>`
switches the subject to another pull request without checking it out.
`--with-agentgrep [terms]` adds a search of local AI transcripts for
decisions the repository never recorded.

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

## Shared references

The command and the skill read the same files at runtime, so the
explicit and ambient paths cannot drift:

- `references/situation-sweep.md` — the six layers, the commands behind
  each, how they degrade, and the evidence discipline separating what
  was read from what was inferred
- `references/prior-conversations.md` — when transcript search is
  warranted, how to scope and cap it, how to reconcile it against the
  repository, and what may not appear in the report

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
