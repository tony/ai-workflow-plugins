# Not losing the user's work

A recut rewrites history that may already be published and may be the
only copy of a day's work. Every gate here exists because skipping it
loses something silently. Verified against git 2.43.

## Refuse before starting

Each of these halts the run with a report, not a warning:

- **A dirty working tree.** Check it yourself with
  `git status --porcelain` — do not rely on git refusing, because
  `rebase.autoStash=true` makes it stash and proceed instead.
- **An operation already in progress.** Probe the git dir for
  `rebase-merge`, `rebase-apply`, `MERGE_HEAD`, `CHERRY_PICK_HEAD`,
  `REVERT_HEAD`, `BISECT_LOG`, `sequencer`, each resolved through
  `git rev-parse --git-path`. During a rebase HEAD reads as detached
  with no indication anything is underway, so HEAD is not the test.
- **Merge commits in the range.** See the collapse section of
  `split-mechanics.md`: collapsing across one erases another author's
  commits from history while keeping their content.
- **The branch checked out in another worktree.** It cannot be
  rewritten in place; `git worktree list --porcelain` names the
  holder.
- **A shallow clone**, which cannot be reasoned about historically.

Report but do not necessarily halt on: a stale submodule pointer,
which survives a rewrite untouched but gets baked in by any later
`git add -A`; an active sparse checkout, which makes a file listing an
incomplete view; and signed commits, which a rebase strips unless
signing is explicitly re-enabled.

```
git log --format='%h %G? %s' <base>..HEAD
```

## The pushed-branch gate

Rewriting a branch someone else may have checked out is a decision for
the user, not the skill. Detect it and require explicit consent.

```
git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
```

No upstream means local-only; proceed. With an upstream, read the
remote's true tip **without** `git fetch`:

```
git ls-remote --heads origin <branch>
```

`fetch` answers the question and simultaneously destroys the
`--force-with-lease` protection you are about to rely on, by
refreshing the remote-tracking ref.

Then decide whether rewriting drops commits that exist only on the
remote:

```
git merge-base --is-ancestor <remote-tip> HEAD
```

A non-zero exit means someone else pushed. Halt and report who:

```
git log --format='%h %an %s' HEAD..origin/<branch>
```

## Back up before touching anything

A reflog entry is not a backup. Unreachable entries expire after 30
days by default and nothing warns anyone.

Use a branch, not a raw ref. All of a branch, a tag, and a
`git update-ref` ref survive gc, but only a branch is discoverable
through the commands a user actually runs, and only a branch gets a
reflog of its own so that overwriting it is recoverable.

```
git branch "backup/<branch>-$(date -u +%Y%m%dT%H%M%SZ)" <branch>
```

Keep the name to a single flat segment after `backup/`. Git refuses to
create a branch whose name is a path prefix of an existing one, so
`backup/x` and `backup/x/<timestamp>` cannot coexist and the second
run hard-fails.

Do not rely on `ORIG_HEAD`. It is one slot, overwritten by the next
reset, merge, or pull — including the user's first recovery attempt.

Report the backup branch name in the final output. It is the whole
recovery story, and the user needs it in front of them.

## Recovery

Undo the most recent rewrite of the checked-out branch:

```
git reset --hard <branch>@{1}
```

Restore a branch that is not checked out:

```
git branch --force <branch> <backup-sha>
```

Never delete and recreate a branch to move it — that destroys its
reflog and throws away the `<branch>@{1}` handle.

When no ref or reflog points at the work any more:

```
git fsck --unreachable --no-reflogs
```

Never run `git reflog expire --expire-unreachable=now --all` as
cleanup. It destroys the user's entire stash list.

## Pushing the result

Pushing is always an explicit, separate decision. The recut itself
stops at the local branch.

```
git push --force-with-lease --force-if-includes origin <branch>
```

Bare `--force-with-lease` is not protection on its own. It compares
the remote against your remote-tracking ref, so a single `git fetch`
from any source between the rewrite and the push — an editor, a
background job, another agent — refreshes that ref, the lease passes,
and a colleague's commit is destroyed. `--force-if-includes` closes
exactly that hole by additionally requiring that the remote tip was
integrated locally.

`--force-if-includes` is a documented no-op unless paired with *bare*
`--force-with-lease`. Adding it to `--force` or to
`--force-with-lease=<ref>:<sha>` buys nothing.

The alternative, immune to background fetches, is to capture the lease
SHA before rewriting:

```
git push --force-with-lease=<branch>:<captured-sha> origin <branch>
```

Never bare `--force`. It disables the fast-forward check on every ref
being pushed, not just this one, so with `push.default=matching` or a
configured `remote.*.push` it can overwrite refs nobody intended to
touch.
