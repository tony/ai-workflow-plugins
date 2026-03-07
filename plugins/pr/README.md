# pr

Generate and review gold-standard pull request descriptions with structured headings, tables, and test plans.

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
| `/pr:review` | Review an existing PR description against gold-standard patterns |

## How It Works

### `/pr` — Generate PR description

1. **Gather context** — collect branch diff, commit log, and file change summary
2. **Read conventions** — check AGENTS.md/CLAUDE.md for PR description conventions and `.github/pull_request_template.md` for templates
3. **Draft description** — apply gold-standard patterns: bold impact labels, structured headings, comparison tables, verification commands, test plan checklists
4. **Present and create** — show the proposed title and body, then optionally create the PR via `gh pr create`

### `/pr:review` — Review PR description

1. **Fetch the PR** — parse the argument for PR number/URL, or detect the current branch's PR
2. **Fetch the diff** — get the PR diff to judge proportionality
3. **Evaluate** — check structure, bold labels, tables, code blocks, test plan, design decisions, verification, before/after, and negative assertions
4. **Report** — list strengths, list specific improvements with concrete markdown suggestions

## Arguments

Generate a PR description with an optional hint:

```
/pr
/pr fixes the race condition in new_session
```

Review an existing PR:

```
/pr:review
/pr:review #42
/pr:review https://github.com/owner/repo/pull/42
```

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
