# Choosing which repositories are in scope

Shared by every command in this plugin. Run this before any sweep that
walks a directory rather than acting on one named repository.

A dependency sweep is exactly the kind of run that quietly widens. A
directory of checkouts holds worktrees, forks, vendored clones and
upstream projects read for reference, and every one of them looks like a
git repository. Committing to somebody else's project because it
happened to sit under the same root is not a recoverable mistake — it
lands in a colleague's history, under your name, unasked.

**When ownership is unclear, stop and ask.** A skipped repository costs
one question. A wrong commit costs someone else's review time and your
standing with them.

## Skip worktrees

A linked worktree shares its history with a canonical clone, so updating
both produces the same commit twice, or a conflict. Detect one by `.git`
being a file rather than a directory:

```console
test -d <repo>/.git || echo "worktree or submodule — skip"
```

Map a worktree back to its clone when you need to, and act on the clone:

```console
git -C <repo> rev-parse --path-format=absolute --git-common-dir
```

A directory sweep also picks up several clones of one repository under
different names. Deduplicate by remote URL and keep one.

## Ask the forge first

`gh` answers the question directly, and its answer beats every
inference below:

```console
gh repo view <owner>/<name> --json isFork,viewerPermission
```

**`isFork: true`** — out of scope. A fork you own is still someone
else's project, and its dependencies belong upstream. Owning the fork
does not make the dependency decision yours.

**`viewerPermission: ADMIN` or `MAINTAIN`** — in scope, provided it is
not a fork.

**`viewerPermission: READ` or `TRIAGE`** — out of scope.

**`viewerPermission: WRITE`** — ask. Write access makes you a
contributor, which is not the same as being the person who decides when
this project takes a new version of a dependency.

## When the forge cannot answer

No `gh`, no network, a non-GitHub remote, or no remote at all. Fall back
to two weaker signals and require them to agree.

**The owner segment of the remote.** Necessary but not sufficient: an
organisation you maintain and an organisation you merely contribute to
are indistinguishable by name. `tmux-python/libtmux` and
`pytest-dev/pytest-django` look alike and are not.

**Authorship of the default branch.** Read the last ten commits on
trunk, not on the working tree's branch:

```console
git -C <repo> log "$(git -C <repo> symbolic-ref --short refs/remotes/origin/HEAD)" -10 --format='%an <%ae>'
```

Match on the email domain rather than one exact address — the same
person commits as more than one identity, and a project run under an
organisation's own address is still theirs.

Agreeing signals decide it. **Disagreeing signals mean ask**, and so
does either of these on its own:

- Trunk's recent commits are entirely from bots or coding agents. A repo
  whose last ten commits are all `Gemini Agent <gemini@google.com>` says
  nothing about who owns it — this is a real case, and the forge
  reported ADMIN for it.
- The remote's owner is an organisation and nothing else corroborates
  maintainership.

## What to report

Say which repositories were excluded and under which rule — fork,
permission, worktree, duplicate clone. A sweep that silently drops
repositories reads as a sweep that found them all current.

List the ones you stopped to ask about separately from the ones you
excluded outright. Those are a decision waiting on the user, not a
finding.
