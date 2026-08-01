---
description: Find every outdated dependency and toolchain pin across one repo or a fleet and bring them current — toolchain, named bumps, bulk refresh and fallout as separate researched commits
argument-hint: "[--root <dir>] [--repo <path|slug>...] [--owner <name>...] [--audit-only] [--branch <name>] [--pr] [--issue github|linear] [--no-push]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "WebSearch", "WebFetch", "Task", "AskUserQuestion"]
---

# Update packages

Bring the repositories in scope up to date — one researched commit per
toolchain pin and per named package, a bulk refresh for the rest, and
each follow-up as its own commit.

Use `${CLAUDE_PLUGIN_ROOT}/skills/updating-packages/SKILL.md` for the
phase structure. It reads the same references this command does, so
the sweep and the single-package path cannot drift:
`${CLAUDE_PLUGIN_ROOT}/references/repo-scope.md`,
`${CLAUDE_PLUGIN_ROOT}/references/ecosystems.md`,
`${CLAUDE_PLUGIN_ROOT}/references/commit-conventions.md`,
`${CLAUDE_PLUGIN_ROOT}/references/upstream-links.md`, and
`${CLAUDE_PLUGIN_ROOT}/references/follow-ups.md`.

For one named package, use `/package-updater:update-package`. For
`.tool-versions`, `.nvmrc`, `packageManager` or `engines`, use
`/package-updater:update-toolchain`.

User arguments: $ARGUMENTS

## Context

Repository:
`!git remote get-url origin 2>/dev/null || echo "(not a git repository)"`

Default branch:
`!git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo "(unknown)"`

Manifests, lockfiles and toolchain pins here:
`!git ls-files -- 'pyproject.toml' '**/pyproject.toml' 'uv.lock' '**/uv.lock' 'poetry.lock' 'requirements*.txt' 'package.json' '**/package.json' 'pnpm-lock.yaml' 'package-lock.json' 'yarn.lock' 'Cargo.toml' 'Cargo.lock' 'go.mod' '.tool-versions' '.nvmrc' '.python-version' 'mise.toml' '.mise.toml' 2>/dev/null | grep -v node_modules | head -40 || echo "(none found)"`

Toolchain pins on this branch:
`!for f in .tool-versions .nvmrc .python-version; do [ -f "$f" ] && { echo "--- $f"; cat "$f"; }; done 2>/dev/null || echo "(no toolchain pin files)"`

Package manager and engines:
`!grep -hE '"(packageManager|node|npm|pnpm)"[[:space:]]*:' package.json 2>/dev/null || echo "(none declared)"`

Cooldown configuration that can hide a fresh release:
`!{ grep -hi 'minimumReleaseAge\|min-release-age' pnpm-workspace.yaml .npmrc 2>/dev/null; grep -hi 'exclude-newer' uv.toml pyproject.toml "${UV_CONFIG_FILE:-$HOME/.config/uv/uv.toml}" 2>/dev/null; } || echo "(no cooldown configured)"`

Project quality checks:
`!grep -hiE '^(test|lint|format|check|type-?check)[[:space:]]*:' justfile Justfile Makefile 2>/dev/null | head -12; grep -A12 '"scripts"' package.json 2>/dev/null | head -14 || echo "(read AGENTS.md/CLAUDE.md or CI for the real commands)"`

## Procedure

Follow the skill's phases. This command supplies the scope and the
fan-out.

### 1. Scope

Default scope is the current repository. `--root` walks a directory for
git repositories; `--repo` names individual ones; `--owner` keeps only
those whose remote belongs to the given accounts or organisations.

Follow the repo-scope reference for every repository a `--root` sweep
turns up. Skip worktrees and duplicate clones, ask the forge for
`isFork` and `viewerPermission`, and treat a fork as out of scope no
matter who owns it. Where the signals disagree — or trunk's recent
commits are all from bots and coding agents — **stop and ask the user
rather than guessing**. Say plainly what was excluded and under which
rule, and list what you asked about separately.

### 2. Inventory and discover

Run the skill's inventory and discovery phases across the whole scope
before touching anything. Detect ecosystems by files present, read pins
from the default branch, and check for a cooldown before calling
anything current.

Sort what you find into the four commit tracks now. A move sorted wrong
here produces a commit that cannot be reverted independently later.

### 3. Research, one chain per distinct move

Group by upgrade chain rather than by repository — twenty repositories
taking the same uv release share one piece of research. Dispatch a
subagent per chain where the host supports it. Verify every release URL
before it reaches a commit body, and intersect each finding with the
repository it lands in.

The bulk refresh needs no research and carries no claims.

### 4. Orchestration plan

Present the plan the skill defines and wait for approval. With
`--audit-only`, stop here and report; nothing is written.

### 5. Land and push

Work through repositories one at a time in the skill's commit order,
pushing as each completes so an interrupted run resumes cleanly.
Repositories parked on a feature branch get a throwaway worktree based
on the remote default branch.

Commits land on the default branch by default. `--branch <name>` works
on a branch instead; `--pr` opens a pull request from it; `--no-push`
commits locally and stops.

With `--issue`, the audit is filed before the work starts: create the
issue or Linear card listing what is outstanding, derive the branch name
from it, then work on that branch. Linear supplies its own branch name —
use it verbatim. The pull request references the issue; the commits do
not.

### 6. Verify and report

Run the project's own quality checks per repository, per the skill's
verification phase. Attribute failures against the default branch before
blaming a bump.

## Rules

- Toolchain, package manager, named bumps, bulk refresh and follow-ups
  are five separate commits. Never bundle across tracks.
- One tool per commit in `.tool-versions`, even when one edit moves
  several.
- The bulk refresh body is empty.
- No version is written before it is confirmed to exist, and no URL
  before it is confirmed to resolve.
- A bump left knowingly red says so in its body and its follow-up lands
  in the same run.
- A fleet-wide claim is verified per repository before entering that
  repository's history.
- Report unrelated breakage; fix it only when a bump caused it.
- GitHub Actions, ruff floors and Terraform belong to sibling plugins —
  report them, do not do them.
- Forks and repositories you cannot push to are out of scope.

## Output

Open with a one-line hero (`✓ N commits across M repos` or
`⚠ Audit only: N packages outdated`), then exactly these sections:

1. `## Audit` — per repository, the ecosystems found and what is
   outdated in each, separated into what moves in-range and what needs a
   manifest edit. Note what was excluded as fork, unowned, or already
   current.
2. `## Gated` — releases the cooldown currently hides, with the date each
   becomes visible. Omit when no cooldown is configured.
3. `## Moves` — one entry per distinct chain: what changed upstream,
   verified links, and which repositories it reaches.
4. `## Commits` — per repository, the commits made in landing order and
   whether they were pushed.
5. `## Follow-ups` — config, snapshot and migration commits, and any bump
   that was red until its follow-up landed.
6. `## Verification` — the quality checks run per repository and their
   real results, with any pre-existing failure named as pre-existing.
7. `## Handoff` — stale GitHub Actions, ruff floors and Terraform
   versions found, each with the sibling command that handles it.
8. `## Holds` — every `reject` entry across the tree with its recorded
   condition, which conditions are now met, and which holds have no
   recoverable reason. Omit when nothing is held.
9. `## Drift` — pins disagreeing across a workspace, and holds applied
   unevenly across workspace members.

End with an `AskUserQuestion` panel offering next steps — for example:
run the sibling command for the handoff items, drop a cooldown exemption
whose block has lapsed, take a gated release once it ages out, or stop
here. Skip the panel only in plan mode.
