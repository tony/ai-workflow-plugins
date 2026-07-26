---
description: Update one named GitHub Action to its current version — verify the tag exists, research the upgrade, and commit it with release links
argument-hint: "<owner/action> [target version] [--repo <path|slug>...] [--pr] [--no-push]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "WebSearch", "WebFetch", "AskUserQuestion"]
---

# Update One GitHub Action

Take a single action — `actions/checkout`, `astral-sh/setup-uv`,
whatever the user names — from whatever each repository currently pins
to its current version, with one commit per repository explaining the
upgrade.

Read `${CLAUDE_PLUGIN_ROOT}/references/action-pinning.md` first; it
defines how to inventory pins, verify a target tag exists, dereference
annotated tags, and choose the pin shape. Read
`${CLAUDE_PLUGIN_ROOT}/references/dependabot-closeout.md` for the
close-out and CI-attribution rules.

User arguments: $ARGUMENTS

## Context

Repository:
`!git remote get-url origin 2>/dev/null || echo "(not a git repository)"`

Default branch:
`!git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo "(unknown)"`

Current pins for all actions on this branch:
`!git grep -hoE 'uses:[[:space:]]*[^[:space:]]+' "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo HEAD)" -- '.github/workflows/*' '.github/actions/*' 2>/dev/null | sed -E 's/uses:[[:space:]]*//' | sort | uniq -c | sort -rn || echo "(no workflows found)"`

## Procedure

### 1. Identify the action and the scope

The action comes from the argument. Without one, ask via
`AskUserQuestion`, offering the out-of-date pins from the context block
above.

Scope defaults to the current repository. `--repo` may be repeated to
name others by path or slug. Exclude forks unless the user insists —
ownership is not the same as authorship.

### 2. Inventory the current pins

Read every `uses:` line naming this action from each repository's
default branch, per the pinning reference. Note the pin shape per
repository: a major float, an exact patch, or a commit SHA with a
version comment.

### 3. Resolve and verify the target

Resolve the latest version, or take the one the user named. Choose the
target that preserves each repository's existing shape, then confirm
the tag exists and gate on exit status. Stop here if it does not
resolve, and report the shapes that are available instead.

### 4. Research the upgrade

Collect every major release between the oldest pin in scope and the
target, each with a verified release URL, plus the breaking changes.
Then check those claims against the actual workflows — the gates
section of the pinning reference lists the recurring ones.

### 5. Commit

One commit per repository. Subject and body follow the project's own
commit conventions from AGENTS.md or CLAUDE.md; the body says what
changed upstream, what it means for that repository, and links every
major release in the span. Never cite a dependabot pull request.

Push unless `--no-push`. With `--pr`, branch and open a pull request
instead of committing to the default branch.

### 6. Verify and close out

Watch CI. Attribute any failure before blaming the bump. Close any
dependabot pull request for this action by citing the commit that
superseded it.

## Rules

- Never write a version string whose tag has not been confirmed to
  exist.
- One commit per repository, for this action only — no bundling with
  unrelated bumps.
- Preserve each repository's pin shape; move a SHA pin's trailing
  version comment along with the SHA.
- A commit body may not carry a claim that is false for the repository
  it lands in.
- Bump the action; report unrelated breakage rather than fixing it.

## Output

Open with a one-line hero (`✓ <action> <old> → <new> across N repos`
or `⚠ Blocked: <reason>`), then exactly these sections:

1. `## Target` — resolved version, evidence the tag exists, and the
   pin shape chosen per repository.
2. `## Upgrade` — what changed between the pins in scope and the
   target, with release links, and which repositories the breaking
   changes actually reach.
3. `## Commits` — one line per repository: commit subject and whether
   it was pushed, or why it was skipped.
4. `## Close-out` — CI result and any dependabot pull requests closed,
   with the commit each cited.

End with an `AskUserQuestion` panel offering next steps (for example:
update another action, run the full audit, stop here) — skip the panel
only in plan mode.
