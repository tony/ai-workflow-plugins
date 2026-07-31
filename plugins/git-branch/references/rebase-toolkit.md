# Interactive rebase without an editor

`git rebase -i` is built around two editor invocations: one for the
todo list, one per reworded message. An agent has no editor and no
TTY, so both must be replaced before any of it is usable.

Everything here is verified against git 2.43. Where a behavior depends
on the user's config rather than git's default, the config is named.

## The two hooks

`GIT_SEQUENCE_EDITOR` is invoked with the path to the todo list.
`GIT_EDITOR` is invoked with the path to a commit message.

Git runs each through the shell, appending the file path as the last
argument. So a sequence editor of `cp -- plan.txt` becomes
`cp -- plan.txt <todo-path>` — which overwrites the todo with your
plan. That one substitution is the whole mechanism.

Set `GIT_EDITOR=false`, never `true`, for any step that should not
need a message editor. `false` turns a step that would have blocked
into an immediate, loud failure; `true` silently accepts an empty
message.

## The toolkit script

`${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh` wraps the idioms
below with a preflight and a consistent exit code. It refuses to run
on a dirty tree or over an operation already in progress, and it
reports rather than hides a rebase it left stopped.

Report any operation in progress, so a later command does not fail
mysteriously:

```
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh status
```

Print the todo list for a range:

```
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh show <base>
```

Replay the range using an edited plan as the todo list:

```
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh apply <base> plan.txt
```

Run a command after every commit, in place:

```
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh verify <base> 'make test'
```

Fold every pending `fixup!` and `amend!` commit:

```
sh ${CLAUDE_PLUGIN_ROOT}/references/rebase-todo.sh squash <base>
```

Exit 0 is success, 1 means git failed and may have left a rebase
stopped (the message says so and prints the abort command), 2 is a
usage error or a preflight refusal.

`RECUT_UPDATE_REFS=1` adds `--update-refs` so local branches pointing
into the range move with it. `RECUT_SIGN=1` re-signs the rewritten
commits.

## Reading the todo without side effects

Driving a real `git rebase -i` just to capture its todo list replays
every commit in the range and changes their SHAs. Generate the list
instead — for a plain pick list this is exactly what git would write:

```
git log --reverse --no-merges --format='pick %h %s' <base>..HEAD
```

## Config that changes the rules

Three user settings silently change what a scripted rebase does. Pin
all three rather than reading them.

`rebase.rebaseMerges=true` turns the todo from a flat pick list into
one containing `label`, `reset`, and `merge` lines. Code that assumes
every line is a `pick` will corrupt the rebase.

`rebase.missingCommitsCheck` defaults to `ignore`, so a commit whose
todo line goes missing disappears with exit 0 and no warning. Set it
to `error` for any generated plan.

`rebase.autoStash=true` suppresses git's own refusal to rebase a dirty
tree — it stashes, rebases, and pops. Worse, a conflict while
reapplying the autostash still reports success and exits 0, leaving
conflict markers behind. Check `git status --porcelain` yourself.

```
git -c rebase.rebaseMerges=false -c rebase.missingCommitsCheck=error -c rebase.autoStash=false rebase -i <base>
```

## Verifying every commit

`--exec` runs a command after each commit and stops the rebase at the
first failure, with no editor involved. It is the per-commit quality
gate.

```
git rebase --keep-base --exec 'make test' <base>
```

`--keep-base` is not optional. Without it, `git rebase --exec <cmd>
<upstream>` rebases the branch onto upstream as a side effect and
silently drops any commit that becomes empty, while still exiting 0.
With it, the tip SHA is unchanged and the run is a true in-place
check.

Two further cautions. The command runs against the worktree as of each
commit, so a relative path like `./run-tests.sh` resolves to that
commit's version of the script — copy the harness outside the repo and
call it by absolute path. And a harness must tolerate the early states
of the series: a runner that fails when no tests exist yet reports
every early commit as broken.

## Rewriting a message with no editor

`git commit --fixup=reword:<sha>` requires an editor and is unusable
headless. Write the `amend!` commit by hand instead; `--autosquash`
treats it identically.

```
git commit --allow-empty -m "amend! <original subject>" -F new-message.txt
```

Then fold it:

```
GIT_SEQUENCE_EDITOR=true GIT_EDITOR=false git rebase -i --autosquash <base>
```

## Recovering

A failed `--exec` or a conflict leaves the rebase in progress on a
detached HEAD, which poisons every later git command until it is
cleared.

`git rebase --abort` restores the branch. `git rebase --quit` clears
the state and leaves HEAD detached at the half-rewritten result,
restoring nothing — it never fails, which makes it tempting and wrong.

Detect an in-progress operation by probing the git dir, never by
inspecting HEAD: during a rebase `git symbolic-ref -q HEAD` fails and
`git status` reports a detached HEAD with no indication that anything
is underway.

```
git rev-parse --git-path rebase-merge
```

The names worth probing are `rebase-merge`, `rebase-apply`,
`MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, `BISECT_LOG`, and
`sequencer`. Resolve each through `git rev-parse --git-path` — in a
linked worktree `.git` is a file and the state lives elsewhere.

## Things that eat commits

- A plain rebase drops commits that are patch-identical to something
  already upstream. Keeping them needs both `--reapply-cherry-picks`
  and `--empty=keep`.
- Rewriting without `--update-refs` strands any other local branch
  that pointed into the range on the orphaned history. Check with
  `git branch --contains` first.
- A rebase strips GPG and SSH signatures from every commit it
  rewrites unless `commit.gpgSign` is set or `-S` is passed.
- Piping `git rebase` into a truncating command such as `head` kills
  it mid-rebase and leaves stale state. Redirect to a file instead.
