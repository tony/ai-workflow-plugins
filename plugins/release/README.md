# release

Cut, bump, and roll out releases with safe defaults: nothing leaves
your machine — no push, no tag, no tag push — unless you explicitly
flag it or pick it from the closing prompt.

Release procedures are discovered from the target repo at runtime:
which files carry the version (`pyproject.toml`, `__about__.py`,
`package.json`, ...), which lockfile to refresh, how the changelog
formats its unreleased header, whether a MIGRATION file participates,
and which quality gates AGENTS.md / CLAUDE.md prescribe. Nothing about
language or layout is hardcoded.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install release@ai-workflow-plugins
```

## Components

### `/release:cut <version> [--push] [--tag] [--push-tag]` (command)

Cut a release at an explicit version: bump every version-bearing
file, refresh the lockfile, date the CHANGES section (and MIGRATION
heading, if present), open the next unreleased placeholder, run the
project's quality gates, and commit with a plain `Tag v<version>`
subject.

Safety model — each escalation needs its own flag:

- Default: commit stays local. No push, no tag.
- `--push`: push the release commit. Never implies the tag.
- `--tag`: create `v<version>` locally. Never pushed by itself.
- `--tag --push-tag`: push the tag. In repos where tags trigger the
  publish workflow, this *is* releasing — which is why it takes two
  flags.

Whatever the flags did not authorize is printed as ready-to-run
commands, and offered interactively at the end.

If your repo's AGENTS.md / CLAUDE.md reserves tagging for a human,
scope the rule to unprompted action:

> Never create or push a tag on your own initiative. An explicit
> instruction is the user's call, including a `--tag` or `--push-tag`
> flag; act on it without asking again.

An unscoped "never create tags" reads as outranking a flag the user
just passed, and the agent stops mid-release — commit pushed, tag
missing, publish never triggered.

### `/release:bump [patch|minor|major|prerelease|final|<version>]` (command)

Same procedure as `cut`, but discovers what "next" means first: reads
the current version, tag history, and the CHANGES unreleased header,
then enumerates concrete candidates in the project's own scheme —
`0.1.9a1 → 0.1.9a2`, `0.1.9 → 0.1.10`, `0.2.0`, `1.0.0`, or starting
a prerelease series like `0.2.0a0`. The user picks; ambiguous
arguments get interpretations offered rather than guessed. Stable
projects keep their next unreleased CHANGES header in
`MAJOR.MINOR.x` form; prerelease-track projects name the next
prerelease outright.

### `/release:update-downstream-packages <package> [<version>]` (command)

After a release publishes, roll it out to every consumer repo you
maintain. Discovers consumers under your workspace roots (skipping
git worktrees and dirty checkouts), then per repo: syncs trunk,
removes stale source overrides and maintains uv's
`exclude-newer-package` cutoffs as separate commits, bumps the pin
for the package and its workspace siblings, re-locks with a fresh
resolver cache, commits in the repo's own bump-commit style, pushes,
and verifies CI (and docs deploys) with `gh` — clearing stale Actions
caches and rerunning failures once.

Nothing mutates before a confirmation gate showing every repo,
branch, and planned commit. `--no-push` keeps all commits local.
Prerelease resolution warnings halt that repo and get reported
instead of being forced through with resolver flags.

## Shared reference

`references/release-conventions.md` holds the discovery procedures
and templates both release commands follow: version-file and bump-
tooling discovery, version-scheme vocabulary (PEP 440, semver, npm
prereleases), CHANGES/MIGRATION unreleased-header lifecycle, the
release commit format, and the safety contract.

## Prerequisites

- `git`, and `gh` for the downstream CI verification
- The target project's own toolchain (whatever its AGENTS.md /
  CLAUDE.md quality gates require)
