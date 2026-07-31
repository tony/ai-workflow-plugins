---
description: Move runtime and toolchain pins — .tool-versions, .nvmrc, .python-version, packageManager, engines — one tool per commit, each release in the span linked
argument-hint: "[tool] [version] [--root <dir>] [--repo <path|slug>...] [--owner <name>...] [--audit-only] [--branch <name>] [--pr] [--no-push]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "WebSearch", "WebFetch", "Task", "AskUserQuestion"]
---

# Update the toolchain

Move the pins that select the tools everything else resolves through —
one tool per commit, with every release in the span linked.

Use `${CLAUDE_PLUGIN_ROOT}/skills/updating-packages/SKILL.md` for the
phase structure, and in particular
`${CLAUDE_PLUGIN_ROOT}/references/upstream-links.md`, which carries the
per-tool link taxonomy this command depends on. Also read
`${CLAUDE_PLUGIN_ROOT}/references/commit-conventions.md` and
`${CLAUDE_PLUGIN_ROOT}/references/ecosystems.md`.

For dependencies rather than tools, use `/package-updater:update` or
`/package-updater:update-package`.

User arguments: $ARGUMENTS

## Context

Repository:
`!git remote get-url origin 2>/dev/null || echo "(not a git repository)"`

Default branch:
`!git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo "(unknown)"`

Pin files on this branch:
`!for f in .tool-versions .nvmrc .python-version mise.toml .mise.toml; do [ -f "$f" ] && { echo "--- $f"; cat "$f"; }; done 2>/dev/null || echo "(no toolchain pin files)"`

Package manager and engines:
`!grep -hE '"(packageManager|engines|node|npm|pnpm)"[[:space:]]*:' package.json 2>/dev/null || echo "(none declared)"`

What the version manager reports as outdated:
`!command -v mise >/dev/null 2>&1 && mise outdated 2>/dev/null || echo "(mise not on PATH — resolve each tool against its own release feed)"`

Installed versions, for comparison:
`!for c in uv just node python go pnpm; do command -v "$c" >/dev/null 2>&1 && printf '%s: %s\n' "$c" "$($c --version 2>&1 | head -1)"; done 2>/dev/null || echo "(none on PATH)"`

## Procedure

### 1. Resolve targets

If the user named a tool, work on that one. Otherwise take every tool in
the pin files. For each, resolve the latest release from the vendor's
own feed rather than memory, and confirm it exists before writing it.

Prefer the pin granularity the repository already uses. A repository
pinning `3.14` rather than `3.14.2` has chosen to track the latest patch
deliberately — do not "fix" it to an exact version.

### 2. Establish scope

Default scope is the current repository. `--root`, `--repo` and
`--owner` widen it as in `/package-updater:update`. Drop repositories
that do not pin the tool and those already at the target.

A toolchain sweep is where pins most often disagree across a fleet.
Record the current version per repository before changing anything; the
spread is a finding.

### 3. Research each span

For each tool, collect the release notes for **every version between the
current pin and the target**, not just the endpoint. The intermediate
releases are where a regression usually entered, and a reader has no
other way to find them.

Take the URLs from the upstream-links reference — each tool has its own
shape, and Node, Go and pnpm publish per minor rather than per patch.
Verify each resolves.

For a runtime, check what the repository claims to support before
moving its floor. Dropping a version that is still declared supported in
a manifest, a CI matrix, or classifiers is a separate decision and a
separate commit.

### 4. Present the plan and wait

Show, per repository and per tool: current pin, target, the versions in
the span, and the verified links. Say how many commits this produces —
one per tool per repository. With `--audit-only`, stop here.

### 5. Land, one tool per commit

Even when a single edit to `.tool-versions` moves three tools, that is
three commits. Stage the file, commit one tool's change, then the next.
Each reverts on its own, and a reader bisecting a runtime regression
needs them separated.

Subject names the file and the tool; the body is a link block and
nothing else:

```console
git commit -F - <<'EOF'
.tool-versions(just) just 1.55.1 -> 1.57.0

- just
  - https://github.com/casey/just/blob/1.57.0/CHANGELOG.md
  - https://github.com/casey/just/releases/tag/1.56.0
  - https://github.com/casey/just/releases/tag/1.57.0
EOF
```

`packageManager` and `engines` live in `package.json` but are toolchain
pins, so they land here and never with a dependency bump. An `engines`
floor takes a `why:`/`what:` body instead of a link block, because a
floor exists for a reason the diff does not record.

Commits land on the default branch by default. `--branch` works on a
branch; `--pr` opens a pull request; `--no-push` stops after committing.

### 6. Verify

A toolchain bump changes what resolves, so run the project's own quality
checks after it — including a lockfile check, since a new resolver may
disagree with the committed lock. Attribute failures against the default
branch before blaming the bump.

## Rules

- One tool per commit, always, even from a single file edit.
- Every release in the span is linked, not just the endpoint.
- No version is written before it is confirmed to exist; no URL before
  it is confirmed to resolve.
- Preserve the repository's existing pin granularity.
- `packageManager` and `engines` are toolchain, never dependencies.
- Dropping a supported runtime version is a separate decision and a
  separate commit.
- Report unrelated breakage; fix it only when the bump caused it.

## Output

Open with a one-line hero (`✓ N tools across M repos` or
`⚠ Audit only: N pins behind`), then exactly these sections:

1. `## Pins` — per repository, each tool's current version and target,
   and what was excluded as not pinning it or already current.
2. `## Spans` — per tool, every release between pin and target with
   verified links, and anything in the span worth knowing.
3. `## Commits` — the commits made, one per tool per repository, and
   whether they were pushed.
4. `## Verification` — the quality checks run per repository and their
   real results, including whether the lockfile still resolves.
5. `## Drift` — tools pinned to different versions across the fleet, and
   pins that disagree with what the repository declares it supports.

End with an `AskUserQuestion` panel offering next steps — for example:
align the fleet on one version, refresh lockfiles against the new
toolchain, drop a runtime version the project no longer supports, or
stop here. Skip the panel only in plan mode.
