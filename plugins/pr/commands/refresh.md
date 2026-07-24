---
description: Refresh an existing PR description to match the branch's current net change, preserving structure and customizations
argument-hint: "[PR number or URL, and/or a hint, e.g. 'the retry logic was dropped']"
allowed-tools: ["Bash", "Read", "Write"]
---

# Refresh PR Description

Bring an existing PR description back in sync with what the branch
**currently** does — non-destructively. The description's structure,
formatting, links, and hand-written customizations are preserved; only
content that the branch's evolution has made stale is updated.

This command is **content-only**. It never restructures the
description, never applies a template, and never discusses structure or
templates. If the user asks for a different structure or mentions a
template, reply in one line that restructuring is `/pr:recut`'s job,
then continue with the content-only refresh (or stop, if restructuring
was the sole request).

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
  the current branch's PR. No PR found → report that and stop.
- Fetch the full PR:
  ```
  gh pr view <number> --json number,title,body,url,baseRefName,headRefName,state
  ```
- The diff base is the PR's **`baseRefName`** — this is what makes the
  command stack-aware. A PR targeting a sibling branch in a stack is
  diffed against that branch, never against trunk.
- Gather the net change:
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

Before any analysis, save the existing body verbatim:

```
mkdir -p .git/pr-backups/$(date -u +%Y%m%d-%H%M%SZ)-pr<number>
```

Write the fetched body to `body.md` and the title to `title.txt` inside
that directory, and tell the user the backup path. If the edit is later
regretted, the old description can be restored with
`gh pr edit <number> --body-file <backup>/body.md`.

### 3. Map the description against the current diff

Read the existing body section by section and classify every claim:

- **Still accurate** — describes something the net diff still does.
  Leave it byte-for-byte untouched, including phrasing you'd have
  written differently. Refresh fixes staleness, not style.
- **Stale** — describes behavior, files, flags, or approaches the
  branch no longer contains, or understates/misstates what it now
  does. Rewrite minimally, in the section's existing voice and format.
- **Missing** — a change in the net diff that the description doesn't
  cover. Add it to the existing section where it belongs, matching
  that section's format (bullet style, bold-label pattern, table
  shape). Never create a new section for it.
- **Unverifiable** — hand-written content whose accuracy can't be
  judged from the diff: reviewer commitments, deployment notes,
  screenshots, benchmark numbers, external links, checked task-list
  items. **Preserve by default.** If the diff suggests one of these is
  now wrong (e.g., a screenshot of a UI the branch since changed), ask
  the user before touching it — never silently drop or edit it.

Preserve throughout: section order and headings, link targets and link
text, images, badges, HTML comments, task-list check states, issue
keywords (`Fixes #N`), and @-mentions.

### 4. Ambiguity gate

When it is unclear whether a piece of existing content is stale or
load-bearing, ask via `AskUserQuestion` with the specific text quoted
and the options: keep as-is, update (showing the proposed replacement),
or remove. Batch related uncertainties into one question set rather
than asking serially. Never resolve ambiguity by guessing.

### 5. Present and apply

- Show the proposed edit as an old → new comparison, quoting only the
  sections that change; state explicitly which sections are untouched.
- Update the title only if it is factually stale; keep its style.
- Ask whether to apply. On approval:
  ```
  gh pr edit <number> --body-file <file>
  ```
  Write the new body to a file first (in the backup directory, as
  `body.new.md`) so formatting survives shell quoting.
- Confirm with the PR URL and repeat the backup path.

---

## Rules

- **Non-destructive**: every run backs up the existing body before
  editing; the smallest edit that restores accuracy wins.
- **Content-only**: never add, remove, rename, or reorder sections;
  never discuss structure or templates.
- **Stack-aware**: the diff base is the PR's `baseRefName`, never an
  assumed trunk.
- **Ask on ambiguity**: unverifiable or uncertain content is kept
  unless the user says otherwise.
- **Whole-branch perspective**: refreshed content describes the net
  result against the base, not the branch's internal history.
- **No brittle details**: don't introduce test counts, SHAs, line
  numbers, or file-changed counts while refreshing.
- **Never** force-push, push, or run destructive git commands; the only
  write is `gh pr edit` after approval.
