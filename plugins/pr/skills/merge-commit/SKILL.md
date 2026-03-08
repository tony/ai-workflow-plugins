---
name: merge-commit
description: >
  Generate a gold-standard merge commit message from branch diff. Use
  when the user asks to write a merge commit message, prepare a merge
  message, or create a squash-and-merge summary. Produces a
  product-level summary proportional to the change size.
---

# Generate Merge Commit Message

Create a gold-standard merge commit message for the current branch. Merge commits are the **user-facing, product-level** summary that appears in `git log --merges` on the main branch.

If the user provided a hint (e.g., "version bump" or "breaking change"),
use it to inform the message.

## Context

Gather the following git context before proceeding:

Current branch:

```bash
git branch --show-current
```

Base branch detection:

```bash
git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master
```

Commits on this branch:

```bash
BASE=$(git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master); git log "origin/$BASE..HEAD" --oneline 2>/dev/null || echo "(no commits ahead of base)"
```

Files changed (stat):

```bash
BASE=$(git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master); git diff "origin/$BASE...HEAD" --stat 2>/dev/null || echo "(no diff)"
```

Full diff:

```bash
BASE=$(git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master); git diff "origin/$BASE...HEAD" 2>/dev/null || echo "(no diff)"
```

---

## Procedure

### 1. Analyze Changes

- Review the full diff and **all commits** on the branch -- not just the latest
- Determine the nature: feature, bug fix, refactor, version bump, CI/infra, docs, breaking change, Python/runtime version drop, etc.
- Assess scope: is this a small targeted fix or a large multi-module change?
- Note any PR number visible in branch name or commits (e.g., `feature-name` with PR `#42`)
- **Whole-branch perspective**: describe the net shipped result -- collapse fixup
  commits, reverts-then-re-adds, and WIP states. The merge commit is a product
  summary, not a commit diary.

### 2. Read Project Conventions

- Read AGENTS.md and/or CLAUDE.md for any merge commit or commit message format preferences
- If the project uses a scope format (e.g., `scope(type[detail])`), match it in the title

### 3. Draft Merge Commit Message

#### Title Line

- Under 70 characters
- Ends with ` (#N)` if the PR number is known
- Match the project's commit scope format if one exists
- Descriptive of the **impact** -- what changed for the user, not implementation details

#### Body -- Proportional to the Change

#### Line wrapping

Wrap commit message body lines at **72 characters**. This is the git
convention and ensures readable output in `git log`, terminals, and
email-based review.

**Overflow exceptions** -- do NOT break these tokens across lines;
place them at the end of a line or on their own line:

- URLs
- commit hashes
- stack traces
- file paths
- long identifiers (class names, function signatures)

If a bullet point exceeds 72 characters due to an overflow token,
let the line run long rather than wrapping mid-token.

**Small changes** (1-3 file fix, simple bump): title line only, no body needed.

**Medium changes** (feature, targeted refactor, bug fix with root cause):

Opening narrative paragraph (2-4 sentences) explaining what changed and why, followed by bullet points for specific changes with **bold labels**.

**Large changes** (multi-module feature, major refactor, migration):

Full structured body with relevant sections from the patterns below.

#### Body Patterns -- Use Only What Applies

**For features, refactors, and bug fixes:**
- Opening narrative paragraph: what and why (2-4 sentences)
- Bullet points with **bold labels** for specific changes
- `Breaking changes:` section if applicable, with migration guidance
- Cross-references: `Fixes #N`, `See also:`, companion PR links
- Version compatibility notes if applicable (environment tables, test matrices)

**For bug fixes with non-obvious root cause:**
- Narrative root-cause explanation
- Numbered reproduction steps if helpful
- Environment/version tables when the bug is version-specific

**For API refactors with migration paths:**
- Old/new tables showing renamed methods, parameters, or modules
- Deprecation notices with timeline
- `Breaking changes:` section

**For version bumps:**
- Arrow notation: `v1.2.3 -> v1.3.0` or `v1.2.3 -> v1.3.0`
- Release tag URL and changelog URL per package
- Release date if known
- Per-file scope annotations when multiple files change different dependencies

**For Python/runtime version drops:**
- EOL date
- Links to PEP and devguide references

**For build/infra migrations:**
- Before/after tooling description
- Summary of what changed and why the migration was needed

**For multi-module sync results:**
- Companion PR links
- Design decisions and trade-offs
- Test coverage summary (qualitative, not counts)

#### What NOT to Include

- Test counts or passing numbers ("875 tests pass")
- Git SHAs or commit hashes
- File-level line numbers
- Number of files changed
- Details the reviewer can see in the diff
- Redundant context already visible in `git log`

### 4. Present the Message

- Show the complete merge commit message in a single fenced code block
- **Do NOT run any git commands** -- the message is for the user to copy/paste into their merge workflow (GitHub merge button, `git merge --edit`, squash-and-merge dialog, etc.)
- If the PR number is unknown, note where `(#N)` should be inserted

---

## Rules

- **Never** run git merge, git commit, or any write operation -- output only
- **Never** force-push or run destructive git commands
- **Proportional**: a 1-line fix = subject line only; a large feature = structured body
- **Product-level focus**: describe what changed for the user, not file-level diffs
- **Language-agnostic**: discover conventions from AGENTS.md/CLAUDE.md -- never hardcode specific tool commands
- **Arrow notation** for version bumps: `old -> new`
- **No brittle details**: no test counts, no SHAs, no line numbers, no file-changed counts
