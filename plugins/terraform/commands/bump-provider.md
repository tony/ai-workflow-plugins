---
description: Move a Terraform or OpenTofu provider to a new version across every module that declares it, then refresh each root module's lock file without narrowing its platform coverage
argument-hint: "<provider> [version] [--root-module <dir>...] [--audit-only] [--no-lock] [--no-commit]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "WebSearch", "WebFetch", "AskUserQuestion"]
---

# Bump a Terraform provider

Raise a provider's version across every module that declares it, in one
commit, then refresh the lock file of every affected root module.

Use `${CLAUDE_PLUGIN_ROOT}/skills/bumping-terraform/SKILL.md` for the
phase structure. It reads the same three references this command does,
so the two cannot drift:
`${CLAUDE_PLUGIN_ROOT}/references/layout-discovery.md`,
`${CLAUDE_PLUGIN_ROOT}/references/pin-sites.md`, and
`${CLAUDE_PLUGIN_ROOT}/references/lock-and-init.md`.

To move the CLI itself, use `/terraform:bump-terraform`. To refresh
locks within the constraints already written, use
`/terraform:refresh-lock`.

User arguments: $ARGUMENTS

## Context

Repository:
`!git remote get-url origin 2>/dev/null || echo "(not a git repository)"`

Directories holding a committed lock file or a backend block:
`!{ git ls-files -- '*.terraform.lock.hcl' 2>/dev/null | sed -E 's|\.terraform\.lock\.hcl$||; s|/$||; s|^$|.|'; git grep -lE '^[[:space:]]*(backend[[:space:]]+"|cloud[[:space:]]*\{)' -- '*.tf' '*.tofu' 2>/dev/null | xargs -r -n1 dirname; } 2>/dev/null | sort -u | grep . || echo "(none — no root module found)"`

Source addresses declared in tracked configuration, provider and module alike:
`!git grep -hE '^[[:space:]]*source[[:space:]]*=' -- '*.tf' '*.tofu' 2>/dev/null | sed -E 's/.*"([^"]*)".*/\1/' | grep -vE '^\.{1,2}/' | sort | uniq -c | sort -rn | head -30 | grep . || echo "(none)"`

Version constraints declared:
`!git grep -hE '^[[:space:]]*version[[:space:]]*=[[:space:]]*"' -- '*.tf' '*.tofu' 2>/dev/null | sed -E 's/^[[:space:]]*//' | sort | uniq -c | sort -rn | head -30 | grep . || echo "(none)"`

Tooling available:
`!{ command -v terraform >/dev/null 2>&1 && terraform -version | head -1; command -v tofu >/dev/null 2>&1 && tofu -version | head -1; command -v terragrunt >/dev/null 2>&1 && terragrunt --version | head -1; } 2>/dev/null | grep . || echo "(no terraform, tofu, or terragrunt on PATH)"`

## Procedure

Follow the skill's phases. This command supplies the target and the
scope.

### 1. Resolve which provider

The argument may be a full source address or a bare name. Resolve it
against the addresses the repository actually declares, inside
`required_providers` blocks — the context above cannot tell a provider
source from a module source, and only the block it sits in can. If more
than one declared address matches, ask which.

A name that matches nothing declared is a finding, not a typo to
correct silently: say so and stop.

### 2. Discover the layout and settle the ambiguities

Run the skill's discovery phase. `--root-module` limits the run to the
named directories; without it, discover them and confirm the set when
there is more than one.

### 3. Resolve the target version

If the user named a version, confirm it is published. Otherwise take
the latest stable release. Either way, record the tag and the source
repository the registry reports, and derive the changelog link from
that source rather than from a table of providers somebody remembered.

### 4. Inventory the sites and predict the edits

Every module declaring this provider, root and child, per the pin-sites
reference. Decide per site whether it needs editing at all: a
constraint that already admits the target does not, and rewriting it
anyway narrows what the module accepts.

### 5. Present the plan and wait

Show the sites to be edited with the operator each keeps, the sites
left alone with the reason, the lock files to be refreshed with how
many platforms each currently tracks, and any drift found. With
`--audit-only`, stop here — nothing is written.

### 6. Edit and commit

All constraint edits in one commit. Then, unless `--no-lock`, refresh
each affected root module's lock and commit those separately, checking
each lock's per-provider platform count against what it was. With
`--no-commit`, leave everything in the working tree and say what would
have been committed.

### 7. Verify

Read the selected version back out of each lock file and compare it to
the target. Run the repository's own gates. Report root modules that
did not move, and why.

## Rules

- No version string is written before the release is confirmed to exist.
- Every declaration of the provider moves in the same commit, or none
  does.
- Constraint edits and lock files are separate commits.
- Each site keeps its existing operator; a bump never normalises
  operators repository-wide.
- A lock file never comes back tracking fewer platforms than it had.
- Report drift and unrelated breakage; fix neither as a side effect.
- Untracked files are never edited, and `.terraform/` is never searched.

## Output

Open with a one-line hero (`✓ <provider> <old> -> <new> across N root
modules` or `⚠ Audit only: N sites behind`), then exactly these
sections:

1. `## Target` — the provider's resolved source address, the target
   version, its publication date, and the changelog link derived from
   the registry.
2. `## Layout` — root modules and child modules discovered, which tool
   drives the repository, and any classification the user settled.
3. `## Sites` — every declaration found, whether it was edited or
   deliberately left alone, and the operator each kept.
4. `## Locks` — per root module: the version selected before and after,
   and the platform count tracked before and after.
5. `## Verification` — the gates run and their real results, with any
   pre-existing failure named as pre-existing.
6. `## Drift` — pin sites that disagreed with each other before the
   bump, root modules that did not move and why, and modules whose
   constraints already admitted the target.

End with an `AskUserQuestion` panel offering next steps — for example:
converge the pin sites that disagree, refresh the lock files this run
left alone, restore multi-platform coverage to a lock that only ever
tracked one, or stop here. Skip the panel only in plan mode.
