# slop

Scan the current repo for AI slop, brittle counts, verbose noise,
and low-value contributions in tracked files. Each finding becomes
its own forward-going commit, after the project's discovered
formatter / linter / type-checker pass. Never rewrites history;
safe on pushed and shared branches.

For branch-scoped slop cleanup that uses fixup commits and
`git rebase -i --autosquash`, see the sibling `pr` plugin's
`/pr:deslop` skill.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install slop@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/slop:scan` | Scan tracked files at HEAD for slop; land one atomic commit per finding with quality-gate verification. |

## How It Works

### `/slop:scan` — Repo-wide slop scanner

1. **Snapshot state and lock baseline** — detect trunk, resolve to
   an absolute SHA (pointer-drift lock), refuse on dirty tree
   (unless `--allow-dirty`), detached HEAD, or in-progress rebase.
2. **Resolve scope** — `git ls-files` filtered by `--paths=<glob>`
   if provided. Optional `--with-history=N` collects the last N
   commits' content for advisory-only historical scanning.
3. **Discover quality gates** — read all of `AGENTS.md` /
   `CLAUDE.md` / `.github/CONTRIBUTING.md` and merge formatter,
   linter, type-checker, and test commands across files.
   Manifest-sniff fallback only with explicit user confirmation.
4. **Calibrate tone against trunk** — read the last 50 commit
   messages on `origin/<trunk>` to demote false-positive Tier C
   signals the project's voice already accepts.
5. **Detect (hybrid)** — Pass A regex on every in-scope file. Pass
   B `Task` sub-agent per file (skip with `--no-semantic`) for
   semantic verification with an anti-slop-on-slop constraint.
6. **Materialize a patch series** — write numbered patches and a
   `commits.json` proposal under `.git/slop-scan/<ts>-<pid>/` for
   review before any commits land.
7. **Per-finding commit loop (with `--apply`)** — for each finding,
   apply the edit, stage explicit paths, run touched-file gates
   (`format` + `lint` + `typecheck`; tests opt-in via `--run-tests`),
   commit with a per-category message from the template registry.
   On gate failure: `git checkout -- <file>` to rollback, mark
   `gate-failed`, continue (configurable via `--on-fail`).

The result: N forward-going commits, one per finding, each
individually reviewable and revertable via `git revert <sha>`.

## Arguments

Audit the repo without applying anything (the default):

```
/slop:scan
```

Scope to a subdirectory:

```
/slop:scan --paths='src/**'
```

Include historical commits in the scan (advisory-only findings):

```
/slop:scan --with-history=50
```

Apply the per-finding commit loop:

```
/slop:scan --apply
```

Apply with the strict budget (only Tier A auto-applies; Tier B
becomes advisory):

```
/slop:scan --apply --budget=strict
```

Stop on the first gate failure instead of skipping:

```
/slop:scan --apply --on-fail=stop
```

Run tests as part of every per-finding commit's gates (slow on
large runs):

```
/slop:scan --apply --run-tests
```

## Safety

- **Never rewrites history.** Every change is a forward-going
  commit; original history is preserved.
- **Never pushes.** The user runs `git push` after reviewing the
  new commits.
- **Never `git add -A` / `git add .`.** Per
  `plugins/commit/commands/commit.md:181-191`, the apply loop
  stages explicit paths only.
- **Never `--no-verify`.** Project pre-commit / commit-msg hooks
  are the project's authority; hook rejection rolls back the
  finding and continues (per `--on-fail`).
- **Gate-failed rollback.** If formatter / linter / type-checker
  rejects a finding's change, `git checkout -- <file>` reverts
  the file to HEAD content and the run continues with the next
  finding.
- **Audit-first default.** Without `--apply`, the skill writes a
  patch series for review and stops. Commits never land
  unexpectedly.
- **Tier C never auto-applies.** Subjective tone is advisory only,
  calibrated against the project's actual voice on trunk.

## Prerequisites

- **git** — for `ls-files`, `log`, `commit`, `checkout`, and
  status operations.
- **The project's formatter / linter / type-checker** — discovered
  at runtime from `AGENTS.md` / `CLAUDE.md`. None are required;
  unset buckets are skipped.

## Boundary with `/pr:deslop`

| Skill | Scope | Action shape |
|---|---|---|
| `/pr:deslop` | Branch commits since trunk (diffs + commit messages) | Fixup commits + autosquash (rewrites history) |
| `/slop:scan` | Tracked files at HEAD (optional advisory history scan) | Forward-going atomic commits, one per finding |

The two skills share the same signature registry, the same
quality-gate discovery procedure, and the same tone-calibration
algorithm. They differ only in how findings get *resolved*.
