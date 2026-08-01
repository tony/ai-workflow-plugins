---
name: package-updater-update-package
description: >-
  Take one named package to a target version everywhere it is pinned —
  research the span, land one commit per repo with a why/what body and
  verified links, then its follow-up
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "WebSearch", "WebFetch", "Task", "AskUserQuestion"]
metadata:
  argument-hint: "<package> [version] [--root <dir>] [--repo <path|slug>...] [--owner <name>...] [--audit-only] [--branch <name>] [--pr] [--no-push]"
  source: "plugins/package-updater/commands/update-package.md"
---

# Update one package

Move one named package to a target version wherever it is pinned, with a
body that says what the release means for each repository it lands in.

Use the `package-updater-updating-packages` skill for the
phase structure, and its references:
`references/ecosystems.md`,
`references/commit-conventions.md`,
`references/upstream-links.md`, and
`references/follow-ups.md`.

For a full sweep, use the `package-updater-update` skill. For a runtime or
toolchain pin, use the `package-updater-update-toolchain` skill.

User arguments: $ARGUMENTS

## Context

Repository — run this command and read the output:

```bash
git remote get-url origin 2>/dev/null || echo "(not a git repository)"
```

Default branch — run this command and read the output:

```bash
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo "(unknown)"
```

Manifests that could pin it — run this command and read the output:

```bash
out=$(git ls-files -- 'pyproject.toml' '**/pyproject.toml' 'requirements*.txt' 'package.json' '**/package.json' 'Cargo.toml' 'go.mod' 2>/dev/null | grep -v node_modules | head -30); if [ -n "$out" ]; then echo "$out"; else echo "(none found)"; fi
```

Cooldown configuration — run this command and read the output:

```bash
out=$({ grep -hi 'minimumReleaseAge\|min-release-age' pnpm-workspace.yaml .npmrc; grep -hi 'exclude-newer' uv.toml pyproject.toml "${UV_CONFIG_FILE:-$HOME/.config/uv/uv.toml}"; } 2>/dev/null); if [ -n "$out" ]; then echo "$out"; else echo "(no cooldown configured)"; fi
```

## Procedure

### 1. Resolve the target and confirm it exists

If the user named a version, use it. Otherwise take the latest stable
release. Either way confirm it is published and record its publication
timestamp — you need it to reason about the cooldown, and a version
written before it is confirmed to exist is the expensive failure this
ordering prevents.

If the cooldown currently hides it, say when it becomes visible and stop
rather than exempting it. Exempt only when the release is needed now,
and then per the exemption protocol in the ecosystems reference: narrow,
annotated, its own commit, reverted when the block lapses.

### 2. Find every pin site

The package can be pinned in more than one place in one repository —
several workspace members, a dependency group, a lockfile, a
pre-commit configuration, a CI workflow. Enumerate them all. Every pin
site in a repository moves in the same commit, or none does.

Note where the pin shapes disagree — an exact pin in one package and a
caret range in another is drift worth reporting even when both resolve
to the same version.

### 3. Establish scope

Default scope is the current repository. `--root`, `--repo` and
`--owner` widen it as in the `package-updater-update` skill. Drop repositories
that do not pin the package and those already at the target.

A widened scope goes through the repo-scope reference first: worktrees
and forks are out, and a repository whose ownership is unclear is a
question for the user, not a guess.

### 4. Research the span once

Read the release notes for every version between the current pin and the
target, not just the endpoint. Collect links per the upstream-links
reference and verify each resolves.

Then, separately per repository, work out what the release actually
reaches. A release note describes the package; only the repository can
say whether the change applies. Where the general claim does not hold,
the body says something different in that repository.

Predict the follow-up now — a formatter, compiler or framework bump
usually needs one, per the follow-ups reference.

### 5. Present the plan and wait

Show the pin sites per repository, the target, the verified links, the
follow-up expected, and whether any repository will be red between the
bump and its follow-up. With `--audit-only`, stop here.

### 6. Land

One commit per repository, subject and body per the commit-conventions
reference — `why:` then `what:`, written through a heredoc or a file.
The follow-up lands immediately after as its own commit.

Commits land on the default branch by default. `--branch` works on a
branch; `--pr` opens a pull request; `--no-push` stops after committing.

### 7. Verify

Run the project's own quality checks. Attribute failures against the
default branch before blaming the bump. A knowingly-red bump is only
acceptable when its body said so and its follow-up lands in the same
run.

## Rules

- No version is written before it is confirmed published; no URL before
  it is confirmed to resolve.
- Every pin site in a repository moves in one commit, or none does.
- The body says what the release means for *this* repository, never a
  generalization that does not hold here.
- A follow-up is its own commit, never folded into the bump.
- Waiting out a cooldown is the default; an exemption is narrow,
  annotated, separately committed and reverted.
- Report unrelated breakage; fix it only when the bump caused it.
- ruff belongs to the `ruff-bump` skill; action pins to
  the `github-actions-update-action` skill; Terraform providers to
  the `terraform-bump-provider` skill.

## Output

Open with a one-line hero (`✓ <package> <old> -> <new> across N repos`
or `⚠ Gated: <package> <version> visible <date>`), then exactly these
sections:

1. `## Release` — what the span changes, with verified links to every
   version in it.
2. `## Pin sites` — per repository, every place the package is pinned
   and its current shape, plus what was excluded as not pinning it or
   already current.
3. `## Impact` — per repository, what the release actually reaches
   there, and where the general claim does not apply.
4. `## Commits` — the commits made, their follow-ups, and whether they
   were pushed.
5. `## Verification` — the quality checks run and their real results,
   with any pre-existing failure named as pre-existing.
6. `## Drift` — pin shapes disagreeing across a workspace or a fleet.

End with an `ask-user-choice` panel offering next steps — for example:
run the sweep for the rest of the tree, take a gated release once it
ages out, land the follow-up separately, or stop here. Skip the panel
only in plan mode.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
