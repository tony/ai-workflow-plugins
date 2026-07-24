---
description: Roll a newly published package release out to every consumer repo you maintain — discover consumers under your workspace roots, bump pins, re-lock, commit, push, and verify CI with gh.
argument-hint: "<package> [<version>] [--roots <glob>...] [--no-push]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "AskUserQuestion", "Task"]
---

# Update Downstream Packages

A release of one of the user's packages just published. Find every
repo of theirs that consumes it, bump the pin (and sibling workspace
packages released together with it), refresh lockfiles, commit, push
to trunk, and verify CI end to end.

Arguments: $ARGUMENTS

This command **pushes to trunk of many repos**. Nothing is mutated
before the Phase 3 confirmation gate. `--no-push` runs the whole
procedure but leaves commits local.

---

## Phase 1: Inputs and Pre-flight

1. **Package** — the first non-flag argument. If missing, ask.
2. **Version** — the second non-flag argument, or discover the latest
   published version from the package index (for PyPI:
   `https://pypi.org/pypi/<package>/json`; for npm:
   `npm view <package> version`). Confirm the version actually exists
   on the index before touching anything — locking against an
   unpublished version fails everywhere at once.
3. **Workspace roots** — from `--roots` globs. If not given, ask the
   user which directories hold their open-source checkouts (e.g.
   glob patterns two levels deep under a work directory). Do not
   assume a layout.
4. **Sibling packages** — if the package is developed in a workspace
   repo that publishes several packages versioned together, list the
   siblings (from the source repo's `packages/*` manifests or the
   index). They bump together.
5. **Fresh resolver cache** — for Python consumers, run
   `uv cache clean --force` once before any locking, so every lock
   resolves against the newly published files rather than a stale
   cached index.

## Phase 2: Discover Consumers

Scan the workspace roots for repos whose manifest depends on the
package:

```
rg -l '<package>' <root>/*/pyproject.toml <root>/*/package.json
```

For each hit, record:

- **Worktree?** If `.git` is a file rather than a directory, it is a
  linked worktree — skip it; the primary checkout will be found on
  its own.
- **Trunk** — `git symbolic-ref refs/remotes/origin/HEAD`, falling
  back to whichever of `main`/`master` exists.
- **Owner** — from `git remote get-url origin`. Group repos by owner
  org; the user confirms which orgs are in scope at the gate.
- **Current pin(s)** — the pinned version(s) of the package and any
  siblings in the manifest.
- **Source overrides** — dependency sources that shadow the index
  (`[tool.uv.sources]` entries, npm `file:`/`link:`/`git:` specs).
  These repos need the override removed and the published index
  package used instead — as its own commit, before the bump.
- **Resolver cutoffs** — for uv consumers, whether
  `[tool.uv.exclude-newer]` is set and whether the package and every
  sibling appear under `[tool.uv.exclude-newer-package]`. A missing
  entry blocks the fresh release at lock time; add the missing
  entries as their own commit, before the bump.
- **Dirty?** Repos with uncommitted changes get reported and skipped
  unless the user says otherwise.

## Phase 3: Confirmation Gate (mandatory)

Present the plan before mutating anything:

- Per repo: path, owner, branch to update, current pin → new version,
  and any prep commits needed (source-override removal,
  `exclude-newer-package` additions).
- Skipped repos with reasons (worktree, dirty, org out of scope).
- Whether pushes will happen (`--no-push` inverts the default).

Ask the user to confirm scope via `AskUserQuestion` — which owner
orgs are in scope, and whether any repo needs a branch override or an
**additional** branch beyond trunk (some projects maintain a
long-lived second branch that also consumes the package; the user
names it, the same per-repo procedure runs on it). Do not proceed
without confirmation.

## Phase 4: Per-Repo Procedure

Repos are independent — parallelize with background agents batched by
owner org (up to 4 batches), or run sequentially if agents are
unavailable. Each repo, on each of its confirmed branches:

1. **Sync** — `git checkout <branch> && git pull --ff-only`.
2. **Prep commits** (each on its own, only if discovery flagged it):
   - Remove the source override so the repo consumes the published
     index package. Commit it alone, e.g.
     `py(deps[docs]) Use published <package> from PyPI` with a
     why/what body.
   - Add missing entries to `[tool.uv.exclude-newer-package]`
     (`<name> = false`, alphabetical order). Commit alone; wrap
     `exclude-newer-package` in backticks in the subject:
     ``py(deps[uv]) Add <name> to `exclude-newer-package` whitelist``
     with a why/what body noting the cooldown would otherwise block
     the fresh release.
3. **Bump pins** — replace the pinned version for the package and all
   siblings in the manifest. A pattern replacement across the shared
   version series catches every sibling at once, e.g.:

   ```
   sed -i 's/==0\.0\.1a[0-9]\+/==0.0.1a<N>/g' pyproject.toml
   ```

4. **Re-lock** — the ecosystem's lock command (`uv lock`,
   `npm install --package-lock-only`, ...). On a resolution failure,
   `uv cache clean --force` and retry once.
5. **Prerelease warnings mean stop.** If locking warns about
   prerelease resolution or would need `--prerelease` flags or
   config to accept the version, do not add flags, pins, or config
   to force it through — halt this repo and report. A correctly
   published release resolves without coaxing; a warning means
   something upstream is wrong (stale cache, missing
   `exclude-newer-package` entry, or a bad publish).
6. **Commit** — mirror the repo's own previous bump commits for this
   package (`git log --oneline --grep '<package>'`). Fallback
   subject, version-arrow form:

   ```
   py(deps[docs]) <package> <old> → <new>
   ```

   Body: why/what summarizing what the new release ships — read the
   package's CHANGES entry for the version, do not invent.
7. **Push** — `git push` (skip with `--no-push`). Never force.

## Phase 5: Verify with gh

For every pushed repo:

1. Clear stale Actions caches so CI resolves fresh:

   ```
   gh cache delete --all --repo <owner>/<repo>
   ```

2. Watch the run for the pushed commit:

   ```
   gh run list --repo <owner>/<repo> --branch <branch> --limit 1
   ```

3. On failure: clear the cache again and
   `gh run rerun <run-id> --failed`. If it still fails, compare with
   the run before the bump — a pre-existing failure is reported as
   such, not retried forever.
4. Where the repo deploys docs from CI, confirm the docs job/workflow
   succeeded too — a docs-dependency bump that breaks the docs build
   defeats the point.

## Output

1. Hero line: `✓ <package> <old> → <new> across N repos` (or `⚠` with
   the failure count).
2. **Rollout summary** — per repo: branch, prep commits, bump commit,
   pushed or local, CI status.
3. **Stopped repos** — any halted on prerelease warnings, dirty
   trees, or persistent CI failures, each with what the user should
   look at.
4. Next-step `AskUserQuestion` panel: rerun failed CI checks / retry
   stopped repos / push the `--no-push` commits / done.
