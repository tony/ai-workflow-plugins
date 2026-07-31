# Splitting a collapsed branch into atomic commits

The mechanics of the recommit motion: resolve the base, collapse the
branch into the index, then carve the index up one logical change at a
time. Verified against git 2.43.

The whole motion happens in the index. The working tree stays pinned
at the branch's final content from start to finish, so it never
matches any intermediate commit — which is why intermediate commits
are tested in a separate worktree, not this one.

## Resolve the base first, once, to a SHA

Every later command depends on it, and every way of getting it wrong
is silent.

Two-dot `git diff <base-branch>..HEAD` against a *moving ref* invents
deletions of files the base branch added after the fork. Resolve the
base to a SHA once, then two-dot against that SHA forever after.

Refuse to continue unless exactly one merge base exists. With two,
`git diff A...B` warns on stderr and picks one; `git merge-base` picks
one with no warning at all.

```
git merge-base --all <base-ref> HEAD | wc -l
```

Prefer the fork point, which consults the base ref's reflog and
survives a force-updated base branch:

```
git merge-base --fork-point <base-ref> HEAD
```

It prints nothing and exits 1 when the reflog is empty — the normal
state in a fresh clone or CI. Treat empty output as "no answer" and
fall back to plain `git merge-base`; never let it become an empty
string that flows into `git reset --soft`.

**On a stacked branch the base is the parent branch tip, never
trunk.** Recutting a child against trunk absorbs the entire parent
pull request into it. Once the parent has itself been recommit, plain
`merge-base` for the child collapses back to trunk — recommit stacks
bottom-up and re-derive each child's base afterward.

## Refuse before collapsing

- Merge commits in the range. `git rev-list --merges <base>..HEAD`
  must be empty. Collapsing across a merge succeeds silently and
  produces a single-parent commit: work reachable only through the
  second parent is erased from history while its content survives in
  the tree, so the branch quietly claims another author's commits and
  every content check still passes.
- A dirty tree, or any operation in progress.
- `git reset --soft` is fatal mid-merge; check for `MERGE_HEAD`.

## Collapse

```
git reset --soft <base-sha>
```

HEAD and the branch ref move to the base. The index and working tree
are untouched — the index tree object is literally unchanged, which is
worth asserting with `git write-tree` before and after.

Untracked files are unaffected and stay untracked throughout. Use
`--soft`, never `--mixed`: mixed drops gitignored-but-force-added
files out of the index entirely, after which `git add` on them fails
without `-f`.

Take the inventory of what is now staged:

```
git diff --cached --name-status -M -z
```

```
git diff --cached --summary
```

The summary matters because `--stat` renders a pure mode change or
rename as a bare `| 0`.

## Commit whole files

When a logical change is entirely whole files, commit them directly
and leave everything else staged:

```
git commit -m "subject" --only -- path/one path/two
```

**Message flags must come before the `--`.** Everything after `--` is
a pathspec, so `git commit --only -- file.txt -m "msg"` makes git
look for files named `-m` and `msg`.

`--only` records the *working tree* content of those paths, not the
index. Right after a soft reset the two are identical so this is safe
— but it stops being safe the moment a file is being split, because
splitting is precisely the state where the index differs from the
working tree.

A rename is a delete plus an add in the index; the `R` in status is
diff-time detection. Name both sides or you get a half-rename:

```
git add -A -- old-name new-name
```

## Split one file across several commits

Unstage the file once, then loop. Regenerate the patch from the
*current* index every round — replaying pre-generated patches lets
context drift.

```
git restore --staged -- path/to/file
```

For a file the branch *added*, unstaging makes it untracked and
`git diff` then shows nothing. Restore its visibility first:

```
git add -N -- path/to/file
```

Each round, generate, filter, apply to the index only, and commit:

```
git diff --binary -- path/to/file > /tmp/round.patch
```

```
awk 'BEGIN{w[1]=1} /^@@/{n++;k=(n in w);if(k)print;next} n==0{print;next} k' /tmp/round.patch > /tmp/part.patch
```

```
git apply --cached --recount --whitespace=nowarn /tmp/part.patch
```

The last round needs no patch at all — `git add -- path/to/file`
takes the remainder.

Notes on the patch step:

- Dropping *whole* hunks needs no `--recount`; git locates each hunk
  by its pre-image side. Editing *inside* a hunk body without fixing
  the header counts is a hard failure, and `--3way` does not rescue it
  because parsing happens first. `--recount` does.
- `--cached` is required. `git apply --index` refuses whenever the
  index and working tree differ, which is the recommit's steady state.
- Never pass `--whitespace=fix`; it rewrites content and breaks the
  content-identity guarantee.
- Binary paths need `git diff --binary`, or applying fails with
  `cannot apply binary patch ... without full index line`.
- Write patches outside the repository. A `.patch` file dropped in the
  working tree shows up as untracked and pollutes the final check.

Assert the staged set immediately before every commit — a bare
`git commit` after `git apply --cached` commits the *entire* index,
including everything still staged from the collapse:

```
git diff --cached --name-only
```

## Preserve authorship

The committer is always whoever runs the recommit, stamped now; that
cannot be preserved and should not be faked. The author can be:

```
GIT_AUTHOR_NAME="$AN" GIT_AUTHOR_EMAIL="$AE" GIT_AUTHOR_DATE="$AD" git commit -F /tmp/msg.txt
```

Prefer the environment variables over `--author`. An `--author` value
without angle brackets is silently reinterpreted as a search pattern
over history: it copies the matched author's identity but not their
date, and it is fatal when nothing matches.

Harvest the identities before collapsing, since afterward the commits
are gone from the branch:

```
git log --no-merges --format='%H %an <%ae> %aI' <base>..HEAD
```

## Prove the recommit changed nothing

Tree equality against the pre-recommit backup is the definitive check.
Exit 0 means the two trees are identical:

```
git diff --quiet <backup-branch> HEAD
```

`git range-diff` explains *how* the commits were regrouped, which an
endpoint diff cannot:

```
git range-diff <base-sha> <backup-branch> HEAD
```

Read it as an explanation, not a gate. It ignores merge commits, and
its `<` and `>` lines are expected noise on a real recommit — heavy
regrouping is reported as unrelated drop-and-add pairs rather than as
matched edits.

Then check that each commit stands on its own, in a worktree that is
not pinned to the final content:

```
git worktree add --detach /tmp/recommit-check <sha>
```
