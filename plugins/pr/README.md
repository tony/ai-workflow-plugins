# pr

Generate, refresh, recut, and review gold-standard pull request descriptions with structured headings, tables, and test plans. Audit branch commits for AI slop, brittle counts, and verbose messages, then resolve via fixup commits and autosquash with quality-gate checks.

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
| `/pr:refresh` | Update an existing PR description to the branch's current net change, preserving structure and customizations |
| `/pr:recut` | Rewrite an existing PR description from scratch, carrying forward context that still matters |
| `/pr:merge-commit` | Generate a gold-standard merge commit message from branch diff |
| `/pr:review` | Review an existing PR description against gold-standard patterns |
| `/pr:deslop` | Audit branch commits for AI slop / brittle counts / verbose messages and resolve via fixup commits with optional autosquash |

## How It Works

### `/pr` — Generate PR description

1. **Gather context** — collect branch diff, commit log, and file change summary
2. **Read conventions** — check AGENTS.md/CLAUDE.md for PR description conventions and `.github/pull_request_template.md` for templates
3. **Draft description** — apply gold-standard patterns: bold impact labels, structured headings, comparison tables, verification commands, test plan checklists
4. **Present and create** — show the proposed title and body, then optionally create the PR via `gh pr create`

### `/pr:refresh` — Refresh an existing PR description

1. **Resolve the PR** — from the argument or the current branch; diff against the PR's actual base branch (stack-aware)
2. **Back up** — save the current body under `.git/pr-backups/` before any edit
3. **Map claims against the diff** — keep accurate content byte-for-byte, minimally rewrite stale claims, add missing changes to existing sections, ask before touching hand-written content it can't verify
4. **Present and apply** — show an old → new comparison, then apply via `gh pr edit` on approval

Content-only: structure, links, formatting, and customizations are preserved; restructuring is `/pr:recut`'s job.

### `/pr:recut` — Rewrite an existing PR description from scratch

1. **Resolve the PR and back up** — same stack-aware base detection and `.git/pr-backups/` backup as `/pr:refresh`
2. **Mine the old description** — inventory issue links, setup steps, screenshots, reviewer commitments, and other context not derivable from the diff; ask about anything unclear
3. **Resolve the template** — a template named in your message wins; otherwise the repo's PR template; otherwise gold-standard structure; ambiguity between candidates gets a question
4. **Draft, present, apply** — fresh gold-standard description of the current net change with carried-forward context woven in, applied via `gh pr edit` on approval, with dropped items listed for veto

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

Refresh or recut an existing PR (defaults to the current branch's PR):

```
/pr:refresh
/pr:refresh #42
/pr:refresh the retry logic was dropped
/pr:recut
/pr:recut #42 use .github/PULL_REQUEST_TEMPLATE/feature.md
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

## PR Templates

`/pr` and `/pr:recut` resolve which template to draft against: a template named in your message wins, then the repository's PR template (all standard GitHub locations, including `.github/PULL_REQUEST_TEMPLATE/`), then the gold-standard structure. When several candidate templates are in play, they ask instead of guessing. `/pr:review` accepts a template named in your message as its evaluation baseline. `/pr:refresh` never applies templates — it preserves the description's existing structure.

## Safety

- Never force-pushes or runs destructive git commands
- Never pushes to main/master
- Always presents the description before creating the PR
- Review command never modifies the PR — only reports findings
- Refresh and recut back up the existing description under `.git/pr-backups/` before editing, and only edit after approval

## Prerequisites

- **git** — for diff and log operations
- **gh** — GitHub CLI for PR creation and fetching
