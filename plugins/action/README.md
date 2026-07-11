# action

Take tickets to branches in isolated git worktrees — resolve Linear /
GitHub issues strictly read-only, name branches the way the team
already does, implement through the project's discovered quality
gates, and fan out multiple tickets in parallel.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install action@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/action:worktree [<ticket>...]` | One branch + worktree for one or more tickets: resolve read-only, name by convention, implement, land gated commits; push or PR only on request |
| `/action:worktrees [<ticket>...]` | Discover and group several tickets, then fan out one worktree per unit — parallel subagents where the host supports them, sequential otherwise |

One ticket (or a few that share one change) → `worktree`. A queue of
independent tickets → `worktrees`. To land review findings on the
current branch, use the review plugin instead — this plugin starts
ticket work on new branches.

Both commands share two flag axes:

- **Placement** — `--local` (default): a visible sibling worktree at
  `{repo_path}-{branch-with-slashes-flattened}/`; `--temp`: the
  host's native temp-worktree mechanism, else a temp root outside the
  repo.
- **Exit** — default: implement and commit through the project's
  gates, no push; `--push`: also push the branch; `--pr`: also open a
  PR with the tickets linked; `--setup-only`: stop after worktree +
  branch + a ticket primer.

`/action:worktree` also takes `--branch=<name>` (use a name
verbatim). `/action:worktrees` also takes `--groups="a b; c"`
(explicit grouping) and `--sequential` (no parallel fan-out).

## Workflow

1. **Situational awareness** — read AGENTS.md / CLAUDE.md, discover
   the project's format / lint / typecheck / test / build commands
   and what CI covers post-push
2. **Ticket resolution** — detect the tracker (prompt > conversation
   > MCP tools > CLIs > repo heuristics), fetch title, description,
   and acceptance criteria read-only
3. **Branch naming** — precedence ladder: explicit ask > project
   conventions > ticket-system default (Linear `gitBranchName`,
   GitHub `<num>-<slug>`) > observed repo norms mined from history >
   kebab-slug fallback
4. **Plan gate** — tickets, branch name, worktree path, grouping (for
   the plural), gates, and exit axis, confirmed before any mutation
5. **Worktree & branch** — idempotent: re-running with the same
   ticket resumes the existing worktree; an unexpected directory
   collision halts with a question
6. **Implement, gates, commit** — inside the worktree only, gated by
   the discovered commands, ticket IDs in every commit body
7. **Exit** — stop local by default; push, PR, or setup-only per the
   flags

A multi-ticket branch is first-class: crosscutting tickets share one
branch under a theme slug confirmed at the plan gate, and every
ticket ID still rides in commits and the PR for server-side linking.

## Zero ticket write-back

The plugin never assigns, comments, transitions, or otherwise mutates
tickets — all reads, no writes, in every tracker. Linking happens
server-side from naming alone: Linear auto-attaches branches and PRs
whose names carry the issue ID; GitHub links issues from closing
keywords in the PR body. An abandoned branch therefore unwinds with
zero blowback — nothing on the ticket to undo.

## Shared references

Both commands read the same reference files at runtime, so the
singular and plural procedures cannot drift:

- `references/ticket-detection.md` — tracker detection, ticket
  resolution, the branch-name precedence ladder, worktree path
  sanitization, and server-side linking
- `references/verification-gates.md` — quality-gate and CI discovery
  (lockstep copy shared with the spike and review plugins)

The plural command delegates all per-unit work to
`/action:worktree`'s phases by reference rather than duplicating the
procedure.

## Verification discovery

Both commands read AGENTS.md / CLAUDE.md / CONTRIBUTING.md to
discover which quality checks the project requires, and read the CI
definitions to learn what a push verifies for free (see
`references/verification-gates.md`). They do **not** hardcode any
test runner, linter, or build tool — and they run no more
verification than the change needs, deferring CI-covered work to
`gh pr checks --watch` after a push.

## Prerequisites

- **git** — worktree-based workflow uses `git worktree`
- **gh** (optional) — first-class GitHub issue resolution, PR
  creation, and CI watching
- **Tracker MCP server** (optional) — e.g. Linear's, for real
  `gitBranchName` resolution and read-only issue lookups
