---
description: Move one repo or a whole fleet onto a new ruff release — predict which rules can fire against each repo's own select list, gate on the resolver seeing the version, then land one reviewed commit per rule
argument-hint: "[version] [--root <dir>] [--repo <path|slug>...] [--owner <name>...] [--branch <name>] [--audit-only] [--no-pr] [--no-changelog]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "WebSearch", "WebFetch", "Task", "AskUserQuestion"]
---

# Bump ruff

Raise the ruff version floor across the repositories in scope and absorb everything the new release surfaces — one commit per rule, each justified against the rule's own documentation, behind the project's own quality gates.

Two references carry the parts that are easy to get wrong. Read both before acting on anything.

- `${CLAUDE_PLUGIN_ROOT}/references/release-triage.md` — how to work out what a release actually does to a specific repo, and how much care each class of fix needs.
- `${CLAUDE_PLUGIN_ROOT}/references/pin-sites-and-gating.md` — every file a version can be pinned in, and what to do when the resolver refuses to see the release.

User arguments: $ARGUMENTS

## Context

Repository:
`!git remote get-url origin 2>/dev/null || echo "(not a git repository)"`

Default branch:
`!git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || git ls-remote --symref origin HEAD 2>/dev/null | sed -n 's|^ref: refs/heads/\([^[:space:]]*\).*|\1|p' || echo "(unknown)"`

Currently resolved version:
`!command -v ruff >/dev/null 2>&1 && ruff --version || echo "(not on PATH — resolve through the project's environment)"`

Where ruff is pinned here:
`!git grep -nI -- 'ruff' -- ':(glob)**/pyproject.toml' ':(glob)**/requirements*.txt' ':(glob)**/.pre-commit-config.yaml' ':(glob)**/*.tool-versions' ':(glob)**/mise*.toml' ':(glob)**/package.json' ':(glob).github/workflows/*' 2>/dev/null | grep -iv 'tool\.ruff\|ruff\.lint\|# ' | head -40 || echo "(no pins found)"`

Effective rule selection:
`!git grep -A40 -- '\[tool\.ruff\.lint\]' -- ':(glob)**/pyproject.toml' 2>/dev/null | head -60 || echo "(no explicit lint configuration — this repo relies on the defaults, so default-set changes DO apply)"`

Resolver cooldown settings that could hide a fresh release:
`!{ cat "${UV_CONFIG_FILE:-$HOME/.config/uv/uv.toml}" 2>/dev/null; cat uv.toml 2>/dev/null; } | grep -i 'exclude-newer' || echo "(no cooldown configured)"`

## Procedure

### 1. Resolve the target version and its publication time

If the user named a version, use it. Otherwise take the latest stable release. Either way, confirm the version exists on the package index and record its publication timestamp — you need it in phase 3, and a version string written before it is confirmed to exist is the expensive failure this ordering prevents.

### 2. Establish scope

Default scope is the current repository. `--root` walks a directory for git repositories; `--repo` names individual ones; `--owner` keeps only those whose remote belongs to the given accounts or organisations. Exclude forks — check the fork flag, not the owner name — and exclude repositories you cannot push to. Say plainly which repositories were excluded and why.

Within scope, drop repositories that have no ruff configuration at all, and repositories that already satisfy the target floor. If a branch or worktree of the intended name already exists somewhere in scope, skip that repository rather than clobbering it, and list it as skipped.

### 3. Research the release once, then intersect it per repository

Follow the triage reference. Read the release's own changelog at its tag, sort every change into the five buckets, then — separately for each repository — intersect those buckets with that repository's effective rule selection to predict exactly which diagnostics it can produce. Repositories that share a configuration share a prediction; do the research once and reuse it.

The intersection is the point of this phase. A release that expands the default rule set is inert for a repository with an explicit `select`, and reporting it as a risk there is noise. A formatter change that widens which *file types* are covered applies everywhere regardless of rule selection, and is usually the largest single source of diff.

Dispatch a subagent per repository where the host supports it, since the repositories are independent.

### 4. Present the plan and wait

Show the predicted work per repository: the rules expected to fire, whether the formatter's scope widens, which pin sites need editing, and whether a resolver gate is needed. With `--audit-only`, stop here — nothing is written.

### 5. Isolate

Work on a branch off the remote default branch, in a throwaway worktree, never in the primary checkout and never on the default branch. `--branch` overrides the branch name. This matters most for repositories that are parked mid-feature; a worktree leaves that work untouched.

### 6. Gate the resolver, if and only if it is blocked

Only when the resolver genuinely cannot see the target version. Follow the gating reference: narrow to the one package, temporary, marked as such in the file with its removal condition, and landed as its own first commit so it reverts cleanly. Skip this phase entirely when the resolver can already see the release — an exemption nobody needs is a permanent hole in a supply-chain guard.

### 7. Raise the floor and refresh the lockfile

Edit every pin site the reference enumerates, in one commit. Prefer a floor over an exact pin, except in pre-commit configuration where the tag is exact by design. Refresh the lockfile with the project's own resolver, and confirm the lock actually moved to the target version rather than assuming the constraint was enough. Cite the release notes in the commit body.

### 8. One rule, one commit

Enumerate the distinct rule codes the linter now reports. For each, in its own commit: apply that rule's safe fixes alone, hand-fix what the autofix leaves, re-run the project's quality checks, and commit with a body that explains why the rule exists, what changed, and — for behavior-changing rules — what the behavior delta is. Close each body with the rule's documentation URL.

A rule that produces a large mechanical diff across many files is still one commit; it is still one rule. Run the formatter last, as its own commit, and if it rewrote file types it never previously covered, say so explicitly — the reviewer needs to know that churn is mechanical rather than authored.

Do not add code comments explaining a lint fix. The commit message carries the rationale, and a comment naming a linter rule ages into noise the moment the rule is renamed or removed. Configuration files are the exception: a temporary resolver exemption must be annotated where it lives.

### 9. Verify before claiming anything

Run the project's own quality checks — lint, format check, type check, tests — as defined in its `AGENTS.md`/`CLAUDE.md` or its CI workflow. Never substitute assumed commands for the ones the project actually runs.

If tests fail, establish whether they fail on the default branch too before attributing the failure to the bump. Pre-existing failures are reported, not fixed and not concealed. Never report green without having read the output that says so.

### 10. Push, open, watch, record

Push the branch and open a pull request unless `--no-pr`. The body states which rules moved and links each to its documentation, and — when phase 6 applied — carries an explicit pre-merge instruction to drop the exemption and re-resolve, with the time the block lapses.

Watch CI to a conclusion. Attribute failures before blaming the bump. Then, unless `--no-changelog` or the repository keeps no changelog, add an entry following that repository's own changelog conventions; a linter floor is development tooling, so it belongs wherever that repository files development-tooling changes, and only if that repository documents such changes at all.

## Rules

- No version string is written before the release is confirmed to exist on the index.
- Every pin site in a repository moves in the same commit, or none does.
- One commit per rule. Never bundle rules, and never bundle a rule with the floor bump.
- Unsafe fixes are applied one at a time and reviewed individually, never in bulk.
- A resolver exemption is temporary, narrow, annotated, separately committed, and called out as a pre-merge blocker.
- Suppressions require a stated reason in the commit body; a rule that is broadly wrong for a project belongs in that project's ignore configuration, not scattered inline.
- Report unrelated breakage; fix it only when the bump caused it.
- Repositories you do not own, forks, and existing branches of the target name are out of scope.

## Output

Open with a one-line hero (`✓ N repos on ruff X.Y.Z` or `⚠ Audit only: N repos behind`), then exactly these sections:

1. `## Release` — what the target version changes, sorted into the triage buckets, with the formatter's scope change called out separately if there is one.
2. `## Scope` — repositories in scope with their current and target versions, and what was excluded as fork, unowned, already-current, or already-branched.
3. `## Per repo` — for each: the rules that fired against its selection, the commits made, and the pull request.
4. `## Verification` — the quality checks run per repository and their real results, with any pre-existing failure named as pre-existing.
5. `## Pre-merge` — every repository carrying a temporary resolver exemption, and when its block lapses.
6. `## Drift` — pin sites found disagreeing with each other before the bump, repositories with no lint configuration, and repositories relying on the default rule set.

End with an `AskUserQuestion` panel offering next steps — for example: drop the resolver exemptions now that the block has lapsed, merge the green pull requests, adopt a newly stabilized rule that is currently unselected, or stop here. Skip the panel only in plan mode.
