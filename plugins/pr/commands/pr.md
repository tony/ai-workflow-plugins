---
description: Generate a gold-standard pull request description from branch diff
argument-hint: "[optional hint about the PR, e.g. 'fixes the race condition']"
allowed-tools: ["Bash", "Read"]
---

# Generate PR Description

Create a gold-standard pull request description from the current branch's diff.

User hint: $ARGUMENTS

## Context

Current branch:
`!git branch --show-current`

Base branch detection:
`!git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master`

Commits on this branch:
`!BASE=$(git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master); git log "origin/$BASE..HEAD" --oneline 2>/dev/null || echo "(no commits ahead of base)"`

Files changed (stat):
`!BASE=$(git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master); git diff "origin/$BASE...HEAD" --stat 2>/dev/null || echo "(no diff)"`

Full diff:
`!BASE=$(git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master); git diff "origin/$BASE...HEAD" 2>/dev/null || echo "(no diff)"`

---

## Procedure

### 1. Analyze Changes

- Review the full diff and **all commits** on the branch — not just the latest
- Determine the nature of the change: new feature, bug fix, refactor, CI/infra, docs, etc.
- Identify which modules, files, and areas are affected
- Note the scope: is this a small targeted fix or a large multi-module change?

### 2. Read Project Conventions

- Read AGENTS.md and/or CLAUDE.md for any PR description conventions
- Check for a PR template at `.github/pull_request_template.md`
- If a template exists, use its structure as the starting point and fill it in with the gold-standard patterns below

### 3. Draft PR Description

#### Title

- Short — under 70 characters
- Descriptive of the impact, not the implementation
- Details belong in the body, not the title
- Match the project's commit/PR title style if one exists

#### Body

Use the sections that are **relevant** to the change — not every PR needs every section. A small bug fix needs fewer sections than a large feature.

**`## Summary`** — 3-7 bullet points:
- Each bullet opens with a **bold impact label** (e.g., **Fix**, **Add**, **Remove**, **Replace**, **Migrate**)
- Concise but complete — a reviewer should understand the full scope from just the summary
- For non-trivial changes, include the motivation (why this change is needed)

**`## Changes`** or **`## Changes by area`** — for multi-module changes:
- Group by area with `###` sub-headings
- Use **bold file/module names** with inline descriptions
- Example: **`src/server.py`**: Wrap post-deletion code in `try/finally` for safe env restoration

**`## Design decisions`** — when trade-offs were made:
- Explain rationale with **bold-label** entries
- Include "why not" for alternatives considered
- Example: **Errors as values, not exceptions**: `SyncResult` follows the structured result pattern because...

**`## Verification`** — copyable commands proving completeness:
- Each `rg` or `grep` command on its own line in its own code block
- Commands should return zero matches for removed patterns or expected matches for added patterns
- Example: verify no f-strings remain in log calls

**`## Test plan`** — a `- [x]` checklist:
- Each item describes **what is validated**, not just the command
- Include project test/lint/typecheck commands as discovered from AGENTS.md
- Include specific test names when they exist
- Example: `- [x] test_new_session_empty_stdout — verifies error on empty stdout`

**`## Setup Required`** — pre-merge steps (only when applicable):
- Numbered external URLs
- Specific configuration steps

**`## Companion PR`** — cross-repo links (only when applicable):
- Link to related PRs in other repositories

#### Tables

Use tables when they improve scannability:

| Use case | Format |
|---|---|
| Parameter/flag mappings | `Parameter \| Flag \| Description` |
| Old-to-new renames | `Method \| Old \| New` |
| File inventories | `Path \| Description` |
| Environment matrices | `Environment \| Result` |
| Sync/async API pairs | `Sync \| Async` |
| Before/after comparisons | `Before \| After` |

#### Line wrapping

**Do NOT hard-wrap PR body text.** Unlike commit messages, PR descriptions
are rendered as Markdown on GitHub — long lines reflow into paragraphs.
Hard-wrapping at 72 characters creates jarring mid-sentence line breaks
in the rendered view. Write prose and bullet text as single long lines;
let the editor/renderer handle display wrapping.

#### Code blocks

- One command per code block
- Explanatory text goes outside the block as regular markdown
- Never put `#` comments inside code blocks

#### Before/After

For behavioral or UX changes, show both states in separate labeled code blocks.

#### Negative assertions in test plan

For removal or migration PRs, include "verify zero matches for X" items proving unwanted patterns are fully removed.

#### What NOT to include

- Test counts or passing numbers ("875 tests pass", "42 tests added")
- Git SHAs or commit hashes
- File-level line numbers
- Number of files or lines changed ("updated 12 files", "adds 340 lines")
- Details the reviewer can see in the diff
- Redundant context already visible in `git log`
- `Fixes #N` hardcoded in the body — use `gh pr create` flags or let GitHub auto-link

#### Whole-branch perspective

Describe the branch's **net shipped result**, not its internal evolution. Ignore
fixup commits, reverts-then-re-adds, and intermediate WIP states — the PR
description is a product changelog for reviewers, not a commit-by-commit diary.

### 4. Present and Create

- **Show the proposed title and body** to the user in full
- Ask whether to:
  1. Create the PR via `gh pr create`
  2. Just output the description (user will create manually)
- **If creating the PR:**
  - Check if the branch has been pushed; if not, push it with `git push -u origin <branch>`
  - Never push to `main` or `master`
  - Use heredoc for the body to preserve formatting:
    ```
    gh pr create --title "the title" --body "$(cat <<'EOF'
    ## Summary
    ...
    EOF
    )"
    ```
  - If the user provided `$ARGUMENTS` containing a hint about a linked issue, add `--body` content accordingly
- Return the PR URL when done

---

## Rules

- **Never** force-push or run destructive git commands
- **Never** push to `main` or `master`
- **Always** present the full description before creating the PR
- **Always** use heredoc for `gh pr create --body` to preserve formatting
- **Language-agnostic**: discover test/lint commands from AGENTS.md/CLAUDE.md — never hardcode specific tool commands
- **Proportional**: match the description's detail level to the diff size — a one-file fix doesn't need 20 bullets; a 30-file feature shouldn't be one sentence
- **No brittle details**: no test counts, no SHAs, no line numbers, no file/line-changed counts
- **Whole-branch perspective**: describe the net shipped result, not the branch's internal commit history
