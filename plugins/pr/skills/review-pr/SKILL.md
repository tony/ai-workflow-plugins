---
name: review-pr
description: >
  Review a PR description against gold-standard patterns and suggest
  improvements. Use when the user asks to review a PR, check a PR
  description, evaluate PR quality, or improve PR documentation.
  Provides concrete markdown snippets for each suggestion.
---

# Review PR Description

Evaluate an existing PR description against gold-standard patterns and suggest concrete improvements.

If the user provided a PR number or URL, use it. Otherwise, detect the current branch's PR.

---

## Procedure

### 1. Fetch the PR

- If the user provided a PR number (e.g., `#42`, `42`) or URL, use it directly
- If no target was specified, detect the current branch's PR:

  ```bash
  gh pr view --json number,title,body,url
  ```

- Fetch the full PR details:

  ```bash
  gh pr view <number> --json title,body,url
  ```

### 2. Fetch the Diff Context

- Get the PR diff to understand the scope of changes:

  ```bash
  gh pr diff <number>
  ```

- Count files changed and estimate the magnitude (small fix, medium feature, large overhaul)
- This context is needed to judge whether the description is **proportional** to the change

### 3. Evaluate Against Quality Patterns

Check each applicable dimension. Not every dimension applies to every PR -- a one-line typo fix doesn't need a Design Decisions section.

| Dimension | What to check |
|---|---|
| **Structure** | Does it use `## Summary`, `## Changes`, `## Test plan` headings where appropriate for the change size? |
| **Proportionality** | Is the detail level proportional to the diff size? Small fix shouldn't have 20 bullets; large feature shouldn't be one sentence. |
| **Bold impact labels** | Do summary bullets open with **bold verbs** (Fix, Add, Remove, Replace, Migrate)? |
| **Tables** | Are comparison-heavy sections using tables instead of prose? (renames, parameter maps, file inventories, environment matrices) |
| **Code blocks** | One command per block? No comments inside blocks? Explanatory text outside? |
| **Test plan** | Does it have a checklist with `- [x]` or `- [ ]` items? Are items descriptive (what is validated), not just commands? |
| **Design decisions** | For non-trivial changes, are trade-offs explained with rationale? |
| **Verification** | Are there copyable `rg`/`grep` commands proving the change is complete? |
| **Negative assertions** | For removal/migration PRs: "verify zero matches for X" items? |
| **Cross-references** | Companion PRs, related issues, tracking links where relevant? |
| **Before/After** | For behavioral changes, are both states shown in labeled code blocks? |
| **No brittle details** | Does the description avoid test counts, SHAs, line numbers, or file/line-changed counts? These duplicate what the reviewer sees in the diff. |
| **Whole-branch perspective** | Does it describe the net shipped result, or does it narrate the branch's commit-by-commit evolution? |

### 4. Report

Structure the report as:

**What the PR description does well:**
- List specific strengths -- reinforce good patterns so the author knows to keep doing them

**Suggested improvements:**
- List specific improvements with **concrete markdown snippets** -- not vague advice like "add more detail"
- If a section is missing that the diff warrants, draft it as a ready-to-paste suggestion
- If a section exists but could be improved, show the improved version

**Overall assessment:**
- One sentence summary: is this description adequate, good, or gold-standard?
- For "adequate" or "good" descriptions, identify the single highest-impact improvement

---

## Rules

- **Never** modify the PR -- only report findings
- **Never** run destructive git or gh commands
- Suggestions must be **concrete markdown snippets**, not abstract advice
- Evaluate **proportionally** -- don't penalize a one-line fix for missing a Design Decisions section
- Recognize and reinforce good patterns -- the report should be balanced, not just a list of criticisms
- Check for **brittle details** (test counts, SHAs, line numbers, file-changed counts) -- flag them as concrete improvements
- Check for **commit-diary style** -- if the description narrates the branch's internal evolution instead of the net result, suggest rewriting to whole-branch perspective
