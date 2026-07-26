# The situation sweep

Shared by `/situate` and the `situational-awareness` skill.

Six layers, gathered in order. Each one degrades on its own — a repo
with no remote still has commits, a branch with no pull request still
has a diff. A layer that cannot be gathered is reported as unavailable,
never dropped.

## Read-only contract

Nothing in this sweep writes. No commits, no pushes, no branch
switches, no file edits, no stash.

Do not `git fetch`. It rewrites remote-tracking refs, which changes
what every other command in the session sees — a mutation dressed as a
read. Work from the refs already in the repository and say how old they
are:

```console
git log -1 --format='%cr' "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)"
```

If that date is old, the comparison against trunk may be stale. Say so
and let the user decide whether to fetch.

## 1. Position

Where the working tree sits relative to trunk.

Resolve trunk from the remote's own HEAD rather than assuming `main`:

```console
git symbolic-ref --short refs/remotes/origin/HEAD
```

When that ref is absent — a fresh clone, a repo cloned with
`--single-branch` — fall back to whichever of `origin/main` or
`origin/master` exists, and say which was assumed.

Then the merge-base, the ahead/behind counts, the uncommitted state,
and any stashes. A dirty tree is part of the situation: work in flight
that no commit records yet is exactly what a new session cannot see.

Detect the degenerate case early. On trunk itself with nothing ahead,
there is no branch story to tell — report recent trunk activity and the
open pull requests instead, and say that is what happened.

## 2. Change

What the branch does, not which files it touched.

```console
git log --no-merges --format='%h %s' "$(git merge-base HEAD @{upstream} 2>/dev/null || git merge-base HEAD origin/HEAD)"..HEAD
```

Read the diff, not just the stat. A file list is an inventory; the
reader wants the intent — what behavior changed, what the commits were
building toward, and whether the sequence tells a coherent story or
shows an approach that was abandoned partway.

Group by area rather than listing every path. Twelve files under one
directory is one fact, not twelve.

Note the shape of the history too: fixup commits pending autosquash, a
revert, a merge from trunk mid-branch. Each says something about where
the work stands.

## 3. Pull request

```console
gh pr view --json number,title,state,isDraft,url,headRefName,body,statusCheckRollup,reviewDecision
```

No pull request for the branch is a finding, not an error — it means
the work has not been proposed yet.

Report failing checks by job name, and unresolved review threads by
what they ask for. A green rollup on a run from before the last push is
not a passing branch; check that the run covers the current head.

Review comments are the highest-value layer here. They are the only
part of the situation containing another person's opinion, and they are
what a resumed session most often has no memory of.

## 4. Tickets

Extract IDs from three places only: commit subjects and bodies on this
branch, the branch name, and the pull request body. Code comments and
documentation are out of scope — a `TODO(#42)` in a file the branch
never touched is not this branch's ticket.

Recognize `#123`, `owner/repo#123`, `Fixes`/`Closes`/`Refs` trailers,
Linear-style keys (`ENG-123`), and full issue URLs.

Resolve GitHub issues:

```console
gh issue view <n> --json number,title,state,labels,body,url
```

Resolve Linear and other trackers through whatever MCP server the
session has connected. When no such server is available, report the ID
unresolved. An unresolved reference is information; a guess at what it
means is not.

Never invent a link. An ID that appears nowhere in the evidence does
not go in the report.

## 5. Conventions

What this project requires of the work in flight. Read `AGENTS.md`,
`CLAUDE.md`, and any nested equivalents that cover the directories the
branch touched — nested files override the root for their subtree.

Report only the rules that bear on the current change: the commit
message format, the quality gates that must pass before a commit,
constraints on the specific files being edited. A branch touching one
plugin does not need the whole document restated.

Note the toolchain the gates actually run through, discovered from the
repo rather than assumed — the lint, format, type-check, and test
commands named in those files or in the project's manifest.

## 6. Prior conversations

Opt-in only. See `prior-conversations.md`.

## Evidence discipline

Distinguish what was read from what was inferred. "Three commits
refactor the parser" is read. "This branch is close to done" is
inferred, and must be marked as such or left out.

Report absence explicitly. A section that silently disappears because
nothing was found is indistinguishable from a section that was never
checked, and the reader has no way to tell which.

Orient, do not fix. The sweep surfaces failing checks, unresolved
threads, and dirty files; it does not repair them, and it does not
propose a plan for them beyond the closing next-step panel. A command
that edits while claiming to be reading is the one failure mode that
makes it unusable as a first move in a session.
