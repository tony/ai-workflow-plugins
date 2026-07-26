---
description: Audit every GitHub Action across one repo or a whole fleet and update the out-of-date ones — one researched commit per action, then close dependabot's PRs by citing them
argument-hint: "[--root <dir>] [--owner <name>...] [--repo <path|slug>...] [--audit-only] [--pr] [--no-push]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "WebSearch", "WebFetch", "Task", "AskUserQuestion"]
---

# Update All GitHub Actions

Audit every `uses:` pin across the repositories in scope, then bring
the out-of-date ones current — one commit per repository and action,
each justified against the vendor's own release notes.

Use `${CLAUDE_PLUGIN_ROOT}/skills/bumping-github-actions/SKILL.md` for
the phase structure. It reads the same two references this command
does, so the audit and the single-action path cannot drift:
`${CLAUDE_PLUGIN_ROOT}/references/action-pinning.md` and
`${CLAUDE_PLUGIN_ROOT}/references/dependabot-closeout.md`.

For a single named action, use `/github-actions:update-action` instead.

User arguments: $ARGUMENTS

## Context

Repository:
`!git remote get-url origin 2>/dev/null || echo "(not a git repository)"`

Default branch:
`!git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo "(unknown)"`

Pins on this branch:
`!git grep -hoE 'uses:[[:space:]]*[^[:space:]]+' "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo HEAD)" -- '.github/workflows/*' '.github/actions/*' 2>/dev/null | sed -E 's/uses:[[:space:]]*//' | sort | uniq -c | sort -rn || echo "(no workflows found)"`

Open dependabot pull requests here:
`!gh pr list --author app/dependabot --state open --limit 50 --json number,title --jq '.[] | "#\(.number) \(.title)"' 2>/dev/null || echo "(none, or gh unavailable)"`

## Procedure

Follow the skill's phases. This command supplies the scope and the
fan-out.

### 1. Scope

Default scope is the current repository. `--root` audits every git
repository beneath a directory; `--owner` keeps only those whose remote
belongs to the given accounts or organisations; `--repo` names
individual ones. Exclude forks — check the fork flag, not the owner
name — and say which were excluded.

### 2. Inventory and verify

Run the skill's inventory and verification phases across the whole
scope before touching anything. Every target tag is confirmed to exist
first; a dangling ref written fleet-wide is the expensive failure this
sequencing prevents.

### 3. Research, one chain per distinct upgrade

Group the work by upgrade chain rather than by repository — twenty
repositories moving `actions/checkout` from the same major share one
piece of research. Dispatch a subagent per chain where the host
supports it. Validate every release URL before it reaches a commit
message.

### 4. Orchestration plan

Present the plan the skill defines and wait for approval. With
`--audit-only`, stop here and report; nothing is written.

### 5. Commit and push

One commit per repository and action. Work through repositories one at
a time, pushing as each completes, so an interrupted run resumes
cleanly. Repositories parked on a feature branch get a throwaway
worktree based on the remote default branch.

### 6. Verify and close out

Watch CI per repository. Attribute failures before blaming the bumps.
Close every dependabot pull request whose action was bumped, citing the
commit that superseded it; close as obsolete any whose action no longer
appears in a workflow.

## Rules

- No version string is written before its tag is confirmed to exist.
- One commit per repository and action — never bundle actions.
- Commit messages never cite dependabot; the pull request cites the
  commit.
- A fleet-wide claim is verified per repository before it enters that
  repository's commit body.
- Report unrelated breakage; fix it only when a bump caused it.
- Forks and upstream projects are out of scope.

## Output

Open with a one-line hero (`✓ N commits across M repos` or
`⚠ Audit only: N pins out of date`), then exactly these sections:

1. `## Audit` — every action in scope with its current pins and the
   latest version, and what was excluded as fork, upstream, or already
   current.
2. `## Upgrades` — one entry per distinct chain: what changed, release
   links, and which repositories the breaking changes reach.
3. `## Commits` — per repository, the commits made and whether they
   were pushed.
4. `## Close-out` — CI results, dependabot pull requests closed with
   the commit each cited, and any failure shown to predate the bumps.
5. `## Drift` — repositories with no dependabot configuration, and
   actions pinned to a moving branch.

End with an `AskUserQuestion` panel offering next steps (for example:
add dependabot configuration to the repos lacking it, pin the moving
branches, stop here) — skip the panel only in plan mode.
