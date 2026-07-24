---
description: Rewrite an existing PR description from scratch against the branch's current net change, carrying forward context that still matters
argument-hint: "[PR number or URL, and/or a template path or hint]"
allowed-tools: ["Bash", "Read", "Write", "AskUserQuestion"]
---

# Recut PR Description

Regenerate an existing PR's description from scratch. Where
`/pr:refresh` patches stale content inside the existing structure,
recut discards the old structure and drafts a fresh gold-standard
description of the branch's current net change — after mining the old
description for context worth carrying forward.

User input: $ARGUMENTS

## Context

Current branch:
`!git branch --show-current`

PR for current branch (if any):
`!gh pr view --json number,title,url,baseRefName 2>/dev/null || echo "(no PR for current branch — expect a PR number/URL in the argument)"`

---

## Procedure

### 1. Resolve the PR and its target

- If `$ARGUMENTS` contains a PR number or URL, use it; otherwise use
  the current branch's PR. No PR found → report that and stop
  (`/pr` handles branches without a PR).
- Fetch the full PR:
  ```
  gh pr view <number> --json number,title,body,url,baseRefName,headRefName,state
  ```
- The diff base is the PR's **`baseRefName`** — stack-aware, never an
  assumed trunk. Gather the net change:
  ```
  git fetch origin <baseRefName>
  ```
  ```
  git log origin/<baseRefName>..HEAD --oneline
  ```
  ```
  git diff origin/<baseRefName>...HEAD --stat
  ```
  ```
  git diff origin/<baseRefName>...HEAD
  ```

### 2. Back up the current description

Save the existing body and title verbatim before drafting:

```
mkdir -p .git/pr-backups/$(date -u +%Y%m%d-%H%M%SZ)-pr<number>
```

Write `body.md` and `title.txt` there and tell the user the path. The
old description can be restored with
`gh pr edit <number> --body-file <backup>/body.md`.

### 3. Mine the old description for context

Read the existing body and inventory everything that is **not**
derivable from the diff:

- Issue keywords and links (`Fixes #N`, `Closes #N`), companion PR
  links, tracking issues
- Setup-required steps, deployment or rollout notes
- Screenshots, recordings, benchmark numbers, external links
- Reviewer commitments and @-mentions, unchecked test-plan items
- Hand-written rationale or "why" context absent from commit messages

Classify each item: **carry forward** (still applies), **drop**
(obsolete given the current diff), or **unclear**. For unclear items,
ask the user via `AskUserQuestion` — quote the item and offer carry /
drop. If an item is dropped, it survives in the backup.

### 4. Resolve the template

Follow `${CLAUDE_PLUGIN_ROOT}/references/template-resolution.md`: a
template mentioned in the user's message wins; otherwise the
repository's PR template; otherwise the gold-standard structure. Ask
when multiple candidate templates are in play — never guess between
them.

### 5. Draft the new description

Apply the drafting rules from the `/pr` command — read
`${CLAUDE_PLUGIN_ROOT}/commands/pr.md`, section *Draft PR Description*,
and follow its title, section, table, and proportionality patterns,
including *What NOT to include* and the whole-branch perspective. Then:

- Weave every carry-forward item from step 3 into the appropriate
  place in the new structure.
- Describe the branch's **current net change** only — the old
  description's framing of superseded approaches does not carry over.

### 6. Present and apply

- Show the proposed title and full body.
- Summarize what was carried forward from the old description and what
  was dropped (with one-line reasons), so the user can veto drops.
- Ask whether to apply. On approval, write the body to
  `body.new.md` in the backup directory and run:
  ```
  gh pr edit <number> --title "..." --body-file <file>
  ```
- Confirm with the PR URL and repeat the backup path.

---

## Rules

- **Backed up before rewritten**: never call `gh pr edit` before the
  old body is on disk and its path reported.
- **Stack-aware**: the diff base is the PR's `baseRefName`.
- **Context is preserved or surfaced, never silently lost**: every
  non-diff-derivable item from the old description is carried, asked
  about, or listed as dropped at the presentation gate.
- **Template ambiguity → ask**; an explicitly mentioned template wins
  without asking.
- **Whole-branch perspective**: describe the net result against the
  base, not the branch's internal evolution.
- **No brittle details**: no test counts, SHAs, line numbers, or
  file-changed counts.
- **Never** force-push, push, or run destructive git commands; the only
  write is `gh pr edit` after approval.
