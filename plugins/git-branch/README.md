# git-branch

Rebuild a branch's commit history so the commits explain the change,
without changing a byte of what the branch produces.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install git-branch@ai-workflow-plugins
```

## Components

### `/git-branch:soft-reset-and-recommit` (skill)

Takes a branch of `wip` commits, or one commit doing five things, and
turns it into a series a reviewer can read.

1. **Gathers intent first** — the original commit messages, trailers,
   the pull request body and its review threads, linked tickets, and
   optionally the session that wrote the code. The collapse destroys
   the original boundaries, so everything is read before anything is
   touched.
2. **Resolves the base and refuses** — one merge base or stop; the
   parent tip for a stacked branch, never trunk; and a halt on a dirty
   tree, an operation in progress, merge commits in the range, or a
   branch someone else has pushed to.
3. **Discovers the commit format** — declared in `AGENTS.md`,
   `CONTRIBUTING.md`, or a commitlint config, otherwise mined from the
   project's own history at the fork point. Reports `mixed` and asks
   rather than guessing.
4. **Plans the series and waits** — every proposed commit, its
   contents, and the intent behind it, presented in plan mode for
   approval before anything destructive happens.
5. **Backs up, collapses, rebuilds** — a backup branch, then
   `git reset --soft`, then one atomic commit at a time, preserving
   original authorship and carrying trailers forward.
6. **Proves it** — `git diff --quiet` against the backup must exit 0,
   and every commit is gated in place through the project's own
   checks.

Pushing is always a separate decision the user makes.

### The interactive-rebase toolkit

`references/rebase-todo.sh` drives `git rebase -i` from a shell with
no editor and no TTY. Both skills use it, and it works standalone.

Run it from anywhere — the examples below spell the path in full so
they can be pasted as-is. Inside a session `${CLAUDE_PLUGIN_ROOT}`
resolves to this plugin's directory; from a plain shell, substitute
wherever the plugin is installed.

Report any git operation in progress:

```console
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh status
```

Print the todo list for a range:

```console
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh show <base>
```

Replay the range from an edited plan:

```console
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh apply <base> plan.txt
```

Run a command after every commit, in place:

```console
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh verify <base> 'make test'
```

Fold pending `fixup!` and `amend!` commits:

```console
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh squash <base>
```

It refuses to run on a dirty tree or over an operation already in
progress, pins the three config settings that otherwise change the
todo format or hide dropped commits, and reports rather than hides a
rebase it left stopped.

## Relationship to the other git plugins

### Reach for `/git-branch:soft-reset-and-recommit` when

The branch's *content* is right and its *history* is wrong — commits
that mix concerns, say nothing, or do not survive review.

### Reach for `/pr:deslop` when

The commit messages need cleaning but the commit boundaries are fine.
It fixes messages through fixup commits and autosquash, and explicitly
does not split multi-topic commits — that gap is what this plugin
fills.

### Reach for `/rebase` when

The branch needs to move onto current trunk. That is a different
operation: neither skill here changes the base a branch sits on.

### Reach for `/commit` when

You are creating a new commit rather than rebuilding existing ones.

## Prerequisites

- **git** — 2.43 or newer for the verified behavior of `--keep-base`,
  `git restore`, and `--force-if-includes`.
- **gh** — to read the pull request, its review threads, and linked
  issues. Optional; the skill degrades to git-only sources.
- **uvx** — only for the optional prior-conversation layer.
