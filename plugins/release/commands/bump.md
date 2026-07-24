---
description: Discover what version comes next — enumerate candidates from the project's own scheme (a1→a2, 0.1.9→0.1.10, 0.2.0, 0.2.0a0), confirm with the user, then cut the release with the same safe defaults as /release:cut.
argument-hint: "[patch|minor|major|prerelease|final|<version>] [--push] [--tag] [--push-tag]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "AskUserQuestion"]
---

# Bump to the Next Version

Discover the project's current version and versioning scheme, work out
what "next" means, get the user's explicit choice, then run the full
`/release:cut` procedure at the chosen version.

Arguments: $ARGUMENTS

First, read `${CLAUDE_PLUGIN_ROOT}/references/release-conventions.md`.
The safety contract in `${CLAUDE_PLUGIN_ROOT}/commands/cut.md` applies
here unchanged: no push, no tag, no tag push without the explicit
flags.

---

## Phase 1: Discover the Current Position

Gather three signals and check they agree:

1. **Manifest version** — from the version-bearing files (conventions
   reference).
2. **Latest tag** — `git tag --sort=-creatordate | head -20`, noting
   the prefix convention and the increment vocabulary the project has
   actually used (aN, bN, rcN, postN, devN, `-next.N`, plain semver).
3. **CHANGES unreleased header** — the version it already targets.
   A stable-track header like `## <project> 0.63.x (unreleased)`
   constrains the next release to the `0.63` series unless the user
   overrides; a prerelease-track header names the next version
   outright.

If the signals disagree (manifest ahead of tags, CHANGES targeting a
different series), surface the discrepancy before proposing anything.

## Phase 2: Enumerate Candidates

Build the candidate list from the project's scheme — concrete
versions, not abstract bump names:

- **Prerelease track** (e.g. current `0.1.9a1`):
  - Next prerelease: `0.1.9a2` — the routine increment
  - Graduate to final: `0.1.9`
  - Promote the segment (`a` → `b` → `rc`) — only if the project's
    tag history uses those segments
- **Stable track** (e.g. current `0.1.9`):
  - Patch: `0.1.10`
  - Minor: `0.2.0`
  - Major: `1.0.0`
  - Start a prerelease series: `0.2.0a0` (PEP 440) or the npm
    equivalent (`0.2.0-next.0`) — matching the project's vocabulary
- **npm prerelease track** (e.g. `0.1.0-next.11`): next prerelease
  `0.1.0-next.12`, or graduate to `0.1.0`.

Do not offer `post`/`dev` releases unless the user asks or the
argument names one.

## Phase 3: Resolve the Version

- **Explicit version argument** (e.g. `0.2.0a0`) — validate it sorts
  after the current version and fits the scheme, then proceed. If it
  breaks the scheme (a `-next.N` version in a PEP 440 project),
  stop and ask.
- **Bump-type argument** (`patch`, `minor`, `major`, `prerelease`,
  `final`) — map it to the concrete candidate. If the mapping is
  ambiguous for this scheme (`prerelease` on a stable track could
  mean `0.1.10a0` or `0.2.0a0`; `patch` on a prerelease track could
  mean the next prerelease or the graduated final), do not guess —
  present the interpretations via `AskUserQuestion`.
- **No argument** — present the Phase 2 candidates via
  `AskUserQuestion`. Recommend the increment the project performed
  most recently (its last two tags show the habitual step). Label
  each option with the concrete version and a one-line description of
  when it is the right choice.

Never proceed on an inferred version. The user picks; the panel
selection is the confirmation.

## Phase 4: Cut

Run the complete `/release:cut` procedure
(`${CLAUDE_PLUGIN_ROOT}/commands/cut.md`, Phase 1 onward) with the
chosen version, forwarding any `--push` / `--tag` / `--push-tag`
flags the user passed.

The CHANGES step must leave the **next** unreleased header in
`MAJOR.MINOR.x` form on stable-track projects. The typical precedent
is the next minor series — after cutting `1.70.1` the fresh
placeholder reads `## <project> 1.71.x (unreleased)` — but the file's
own past release-to-placeholder transitions are the specification;
mirror them. Prerelease-track projects instead name the full next
prerelease (after `0.0.1a35`, the placeholder is
`## <project> 0.0.1a36 (unreleased)`).
