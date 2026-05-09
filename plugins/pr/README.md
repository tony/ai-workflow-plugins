# pr

Generate and review gold-standard pull request descriptions with structured headings, tables, and test plans. Audit branch commits for AI slop, brittle counts, and verbose messages, then resolve via fixup commits and autosquash with quality-gate checks.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install pr@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/pr` | Generate a gold-standard PR description from branch diff |
| `/pr:merge-commit` | Generate a gold-standard merge commit message from branch diff |
| `/pr:review` | Review an existing PR description against gold-standard patterns |
| `/pr:deslop` | Audit branch commits for AI slop / brittle counts / verbose messages and resolve via fixup commits with optional autosquash |

## How It Works

### `/pr` — Generate PR description

1. **Gather context** — collect branch diff, commit log, and file change summary
2. **Read conventions** — check AGENTS.md/CLAUDE.md for PR description conventions and `.github/pull_request_template.md` for templates
3. **Draft description** — apply gold-standard patterns: bold impact labels, structured headings, comparison tables, verification commands, test plan checklists
4. **Present and create** — show the proposed title and body, then optionally create the PR via `gh pr create`

### `/pr:merge-commit` — Generate merge commit message

1. **Gather context** — collect branch diff, commit log, and file change summary
2. **Read conventions** — check AGENTS.md/CLAUDE.md for merge commit format preferences
3. **Draft message** — apply proportional patterns: title-only for small fixes, structured body with bold labels, arrow notation, breaking change sections, and cross-references for larger changes
4. **Present message** — show the complete merge commit message for the user to copy/paste into their merge workflow (GitHub merge button, `git merge --edit`, etc.)

### `/pr:review` — Review PR description

1. **Fetch the PR** — parse the argument for PR number/URL, or detect the current branch's PR
2. **Fetch the diff** — get the PR diff to judge proportionality
3. **Evaluate** — check structure, bold labels, tables, code blocks, test plan, design decisions, verification, before/after, and negative assertions
4. **Report** — list strengths, list specific improvements with concrete markdown suggestions

### `/pr:deslop` — Audit branch commits for slop and resolve

1. **Detect trunk and lock baseline** — resolve trunk to an absolute SHA, snapshot branch state, refuse on dirty tree / detached HEAD / in-progress rebase / merge commits with `--apply-rebase`
2. **Refuse pushed branches by default** — require `--force-rewrite-pushed` to rewrite published history
3. **Discover quality gates** — read `AGENTS.md` / `CLAUDE.md` / `.github/CONTRIBUTING.md` and merge formatter / linter / type-checker / test commands across files
4. **Calibrate tone against trunk** — read the last 50 commits on `origin/<trunk>` to demote false-positive Tier C signals
5. **Detect** — hybrid pass: regex first (deterministic), semantic sub-agent on flagged hunks (precise; skip with `--no-semantic`)
6. **Materialize a patch series** — write numbered patches plus `apply.sh` under `.git/deslop/<ts>-<pid>/` for review before any history rewrite
7. **Apply with confirmation** — backup branch + checkpointed `apply.sh` for fixup commits; with `--apply-rebase`, run `git rebase -i --autosquash` and run quality gates on touched files at each conflict pause

## Arguments

Generate a PR description with an optional hint:

```
/pr
/pr fixes the race condition in new_session
```

Generate a merge commit message with an optional hint:

```
/pr:merge-commit
/pr:merge-commit version bump
/pr:merge-commit breaking change in the session API
```

Review an existing PR:

```
/pr:review
/pr:review #42
/pr:review https://github.com/owner/repo/pull/42
```

Audit branch commits for slop:

```
/pr:deslop
/pr:deslop --apply-patches
/pr:deslop --apply-rebase --run-tests
/pr:deslop --message-only --budget=strict
/pr:deslop --force-rewrite-pushed --apply-rebase
```

The default mode is **audit-only** — patches are written under
`.git/deslop/<ts>-<pid>/` for review; nothing is applied. Use
`--apply-patches` to create fixup commits without rebasing, or
`--apply-rebase` to also run autosquash. See
`plugins/pr/skills/deslop/SKILL.md` for the full flag reference and
edge cases.

## Gold-Standard Patterns

The generated PR descriptions follow patterns extracted from high-quality open-source PRs:

- **`## Summary`** with bold impact labels opening each bullet
- **`## Changes by area`** with `###` sub-headings for multi-module changes
- **`## Design decisions`** with trade-off rationale
- **`## Verification`** with copyable `rg`/`grep` commands proving completeness
- **`## Test plan`** with `- [x]` checklists describing what is validated
- **Comparison tables** for renames, parameter maps, API pairs, environment matrices
- **Before/After** code blocks for behavioral changes
- **Negative assertions** proving unwanted patterns are fully removed

## Safety

- Never force-pushes or runs destructive git commands
- Never pushes to main/master
- Always presents the description before creating the PR
- Review command never modifies the PR — only reports findings

## Prerequisites

- **git** — for diff and log operations
- **gh** — GitHub CLI for PR creation and fetching
