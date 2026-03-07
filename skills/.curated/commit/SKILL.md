---
name: commit
description: Create git commits following project conventions with format enforcement and safety checks. Use when asked to commit changes, create a commit message, or stage and commit files.
---

# Git Commit

Create a well-formatted git commit using the project's commit conventions.

## Context

Gather the following information before proceeding:

Run `git branch --show-current` to determine the current branch.

Run `git status --short` to see the working tree status.

Run `git diff --cached --stat` to see staged changes.

Run `git diff --stat` to see unstaged changes.

Run `git diff HEAD` to see the full diff against HEAD.

Run `git log --oneline -10` to see recent commits for style matching.

---

## Commit Convention

Read the project's AGENTS.md / CLAUDE.md to discover the commit message format. Look for:
- Subject line format (e.g., `Scope(type[detail]) description`, Conventional Commits `type(scope): description`, or other patterns)
- Body structure (e.g., `why:/what:` sections)
- Component naming conventions

If no project convention is found, fall back to Conventional Commits: `type(scope): description`.

Match the style of the recent commits shown above — capitalization, tense, level of detail.

---

## Procedure

### 1. Analyze Changes

- Review the full diff to understand what changed
- Determine the commit type (`feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `style`, etc.)
- Determine the scope/component from the files and modules touched
- Check topic coherence: if the changes span unrelated topics, warn the user and suggest splitting into separate commits

### 2. Determine Staging

- **If files are already staged** (`git diff --cached` is non-empty): respect the user's staging — only commit what is staged
- **If nothing is staged**: auto-stage changed files, but:
  - **Never stage sensitive files**: `.env`, `.env.*`, `*.pem`, `*.key`, `*credentials*`, `*secret*`, `*.p12`, `*.pfx`, `id_rsa*`, `*.keystore`
  - Use `git add <specific-files>` — never `git add -A` or `git add .`
  - Tell the user which files are being staged

### 3. Draft Commit Message

- Follow the project's commit format discovered above
- If the user provided context, use it as a hint for the description — but always enforce the project's format
- Include a body (`why:/what:` or equivalent) when:
  - Multiple files are changed
  - The change is non-trivial
  - The diff is not self-explanatory
- **Show the proposed commit message** to the user before executing

#### Line wrapping

Wrap commit message body lines at **72 characters**. This is the git
convention and ensures readable output in `git log`, terminals, and
email-based review.

**Overflow exceptions** — do NOT break these tokens across lines;
place them at the end of a line or on their own line:

- URLs
- commit hashes
- stack traces
- file paths
- long identifiers (class names, function signatures)

If a bullet point exceeds 72 characters due to an overflow token,
let the line run long rather than wrapping mid-token.

### 3a. Version & Dependency Bump Commits

When the changes are version bumps or dependency updates, use this specialized format:

**Single package** — compact subject with body:
```
scope(tool) old_version -> new_version
```
Body: link the release tag and changelog:
```
- https://github.com/owner/repo/releases/tag/vX.Y.Z
- https://github.com/owner/repo/blob/vX.Y.Z/CHANGELOG.md
```

**Multiple packages** — list each in the body:
```
scope(chore) Bump tool1, tool2, tool3

- tool1 1.2.0 -> 1.3.0 (March 5, 2026)
  - https://github.com/owner/tool1/releases/tag/v1.3.0
  - https://github.com/owner/tool1/blob/v1.3.0/CHANGELOG.md
- tool2 0.9.1 -> 0.10.0 (February 28, 2026)
  - https://github.com/owner/tool2/releases/tag/v0.10.0
  - https://github.com/owner/tool2/blob/v0.10.0/CHANGELOG.md
```

URL guidelines:
- Use `/releases/tag/` for release pages
- Use `/blob/<tag>/CHANGELOG.md` for changelogs pinned to the release tag — not `/blob/main/` unless no tags exist
- Use arrow notation for version transitions: `v1.2.0 → v1.3.0` or `1.2.0 -> 1.3.0`

### 4. Commit

- For single-line messages:
  ```
  git commit -m "the message"
  ```
- For messages with a body, use heredoc to preserve formatting:
  ```
  git commit -m "$(cat <<'EOF'
  subject line

  why: ...
  what:
  - ...
  EOF
  )"
  ```
- **If a pre-commit hook fails**:
  - Read the hook output to understand the failure
  - Fix the issue (formatting, lint, etc.)
  - Re-stage the fixed files
  - Create a **new** commit — never use `--amend` (the failed commit does not exist)

### 5. Confirm Result

Run `git log --oneline -1` to show the created commit.

Run `git status` to show the remaining working tree state.

Report success to the user.

---

## Commit Quality Guide

### Do

- **Proportional detail** — small fix gets a concise body; large feature gets structured sub-sections (Changes, Test coverage)
- **`why:` explains motivation; `what:` lists specific technical changes** — reader understands the reason before the implementation
- **Quantify impact** for performance changes — include before/after numbers and percentages
- **Before/after examples** for bug fixes — show broken vs fixed behavior inline when helpful
- **Cross-reference** related PRs/issues with `Fixes #N` or `See also: <URL>`
- **List specific files** changed when multiple modules are touched
- **Version bumps** — include release date, release tag URL, and changelog URL
- **Arrow notation** for version transitions: `v1.2.0 → v1.3.0` or `1.2.0 -> 1.3.0`
- **Wrap body at 72 characters** — the git convention; let URLs, paths,
  hashes, and identifiers overflow rather than breaking mid-token

### Don't

- **Vague subjects**: "update code", "fix bug", "misc changes"
- **Redundant type-in-description**: "feat: add new feature" — the type already says feat
- **`#PR_NUMBER` in commit messages** — PR numbers belong in CHANGES entries, not commits; git merge history already tracks PR association
- **Bodies longer than the change warrants** — a one-line typo fix doesn't need 10 bullets
- **Omitting the body** when changes span multiple files or the diff is non-obvious
- **Counts of files, lines, or tests changed** — these duplicate `git diff --stat` and become stale; describe *what* changed, not *how many*

---

## Rules

- **Never** run `git push`, `git push --force`, `git reset --hard`, or any destructive git command
- **Never** use `--amend` — always create new commits
- **Never** use `--no-verify` or `--no-gpg-sign`
- **Never** create empty commits
- **Never** use `git add -A` or `git add .`
- **Never** commit files that likely contain secrets (`.env`, credentials, keys)
- Always use heredoc when the commit message has a body (multi-line)
- Always present the proposed commit message before executing `git commit`
- If there are no changes to commit, report "Nothing to commit" and stop
