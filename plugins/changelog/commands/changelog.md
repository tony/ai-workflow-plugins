---
description: Generate CHANGES entries from branch commits and PR context
argument-hint: "[optional additional context about the changes]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit"]
---

# Changelog Entry Generator

Generate well-formatted changelog entries from the current branch's commits and PR context. This command analyzes commits, categorizes them, and inserts entries into the changelog file after user review.

Additional context from user: $ARGUMENTS

---

## Phase 1: Gather Context

**Goal**: Collect all information needed to generate changelog entries.

**Actions**:

1. **Detect project name** — search for project metadata in order of precedence:
   - `pyproject.toml` → `[project] name`
   - `package.json` → `name`
   - `Cargo.toml` → `[package] name`
   - `go.mod` → module path (last segment)
   - Fall back to the repository directory name

2. **Detect trunk branch**:
   ```
   git symbolic-ref refs/remotes/origin/HEAD
   ```
   - Strip `refs/remotes/origin/` prefix to get branch name
   - Fall back to `master` if the above fails

3. **Verify not on trunk**:
   - Check current branch: `git branch --show-current`
   - If on trunk, report "Already on trunk branch — nothing to generate" and stop

4. **Find and read the changelog file** — scan the repo root for common changelog filenames:
   - `CHANGES`, `CHANGES.md`
   - `CHANGELOG`, `CHANGELOG.md`
   - `HISTORY`, `HISTORY.md`
   - `NEWS`, `NEWS.md`
   - If multiple exist, prefer the one with the most content
   - If none exist, report "No changelog file found" and ask the user which filename to create

5. **Analyze the changelog format**:
   - **Heading format**: Detect the pattern used for release headings (e.g., `## v1.2.3`, `## [1.2.3]`, `## project v1.2.3`, `## 1.2.3 (YYYY-MM-DD)`)
   - **Unreleased section**: Look for an "unreleased" heading or a placeholder comment (e.g., `<!-- END PLACEHOLDER`, `## [Unreleased]`, `## Unreleased`)
   - **Insertion point**: Determine where new entries go — after a placeholder comment, under an unreleased heading, or at the top of the file
   - **Section headings**: Note existing section headings (e.g., `### Bug fixes`, `### Features`) and their capitalization style
   - Record this format to match it exactly when generating entries

6. **Check for PR**:
   ```
   gh pr view --json number,title,body,labels 2>/dev/null
   ```
   - If a PR exists, extract the number, title, body, and labels
   - If no PR exists, note that `(#???)` placeholders will be used

7. **Get commits**:
   ```
   git log <trunk>..HEAD --oneline
   ```
   - Also get full commit details for body parsing:
   ```
   git log <trunk>..HEAD --format='%H %s%n%b---'
   ```
   - If no commits ahead of trunk, report "No commits ahead of trunk" and stop

---

## Phase 2: Categorize Commits

**Goal**: Parse commits into changelog categories and group related ones.

### Commit type mapping

Parse the commit type from the commit subject. Adapt to the project's commit convention (detected from AGENTS.md/CLAUDE.md or from existing commit history):

| Commit type | CHANGES section | Notes |
|---|---|---|
| `feat` | What's new | New functionality (formerly "Features" / "New features") |
| `fix` | Bug fixes | Bug fixes |
| `docs` | Documentation | Doc changes |
| `test` | Tests | Test additions/changes |
| `refactor` | (only if user-visible) | Skip internal-only refactors |
| `chore`, `deps` | Development (only if consumer-visible) | e.g., minimum version bumps, build system changes that alter installation; skip CI, linter, editor, dev-tooling, and test-infrastructure changes |
| `style` | (skip) | Formatting-only changes |

### Grouping rules

- **TDD workflow sequences**: An xfail commit + a fix commit + an xfail-removal commit should collapse into a **single** bug fix entry. The fix commit's message is the primary source.
- **Dependency bumps**: A deps commit + a changelog doc commit = 1 entry under "Breaking changes" (if it's a minimum version bump) or "Development"
- **Multi-commit features**: Sequential `feat` commits on the same component collapse into one entry
- **Skip entirely**: merge commits, lock-only changes, internal-only refactors

### Output of this phase

A structured list of entries grouped by section, each with:
- Section name (e.g., "Bug fixes")
- Entry text (formatted markdown)
- Source commit(s) for traceability

---

## Phase 3: Generate Entries

**Goal**: Write the exact markdown to be inserted into the changelog.

### Format rules (derived from the existing changelog file)

1. **Section headings**: Match the style found in Phase 1 (e.g., `### Bug fixes`, `### Bug Fixes`)

2. **Section order** (only include sections that have entries — this order is mandatory, never reorder):
   1. Breaking changes
   2. What's new
   3. Bug fixes
   4. Documentation
   5. Tests
   6. Development

   **IMPORTANT**: Always use the exact heading names above. In particular, use `### What's new` (not "Features" or "New features") — this matches the project's established convention in recent releases.

3. **Simple entries** — single bullet for one-line changes:
   ```markdown
   - Brief description of the change (#123)
   ```

4. **Sub-section entries** — `####` heading + 2-4 lines of product-level prose. Use this for new packages, new flags, new behaviours, or notable changes to existing surface — anything a downstream user needs to learn rather than just notice. The heading names the product change; the prose covers usefulness, integration, and trade-offs:

   ```markdown
   #### New package: `<name>`

   One-paragraph description of what the user can do with it, how it
   integrates with what they already have, and any explicit trade-off
   or limitation. Drop-in compatibility statements live here. (#123)

   #### New flag: `--<flag>` for `<command>`

   What the flag enables and the default behaviour without it. Note
   any non-obvious interaction with existing flags. (#123)

   #### `<package>`: <product-level change>

   For changes to existing packages, lead the heading with the package
   name, then the user-visible change. Body explains what the user
   sees differently and why it matters downstream. (#123)
   ```

   Sub-section heading style:
   - `#### New package: \`<name>\`` for new workspace packages.
   - `#### New flag: \`--<flag>\`` for new CLI surface.
   - `#### New <noun>: \`<name>\`` for other additions (config value, directive, hook, etc.).
   - `#### \`<package>\`: <change>` for behavioural changes to existing packages.
   - **Avoid** commit-prefix-style headings like `#### cli(sync): ...` — those describe the commit, not the change. Lead with the product surface the user sees.

   Bulleted detail under a sub-section is permitted but rare. If a sub-section needs more than 4 lines or a bullet list, the change probably warrants splitting into multiple entries — one per shipped surface.

5. **PR references**:
   - If PR number is known: `(#512)`
   - If no PR exists: `(#???)`

6. **Match existing style**:
   - Check whether the project uses "Bug fixes" or "Bug Fixes" (match existing capitalization)
   - This project uses "What's new" (not "Features" or "New features")
   - Match the heading level, bullet style, and overall format of existing entries
   - Preserve the project's conventions

### Entry writing guidelines

- **Product-level perspective.** Lead with what the user GAINS, can now DO, or needs to KNOW — not what code changed internally. A reader skimming the changelog at upgrade time should learn: is there a new affordance, a new default, a behavioural change, or a trade-off they need to plan around?
- **Discuss usefulness and downstream impact.** When a new package or feature has a non-obvious integration story, mention it: drop-in compatibility (`Drop-in for X`), default activation (`Replaces X in DEFAULT_EXTENSIONS`), auto-derivation (`auto-derives X, Y, Z from a single docs_url`), or accepted-but-ignored config keys with a warning. Two short sentences usually do this; rarely more.
- **Brevity.** Aim for 2-4 lines per sub-section entry, 1-2 lines per simple bullet. If an entry is growing past that, the underlying change probably wants to be split into multiple entries (one per shipped surface). Long prose buries the impact.
- **Skip what's not user-visible.** Refactors that don't change behaviour, type-only annotations, internal renames, lint cleanups, CI tweaks, test-infra changes, dev-tooling bumps — none belong in CHANGES. The diff and commit log are the right home for those.
- Use present tense for entry titles ("Add support for..." not "Added support for...").
- Don't repeat the section heading in the entry text.
- Never include numeric tallies — file counts, line counts, test counts, commit counts ("across N commits", "in N changes", "adds N tests"). These are brittle and duplicate the diff.
- Never include git refs — SHAs, commit hashes, branch names, tag names, or line numbers. These break when history is rebased or tags move.

### Good vs. bad framing

| Bad — describes the commit | Good — describes the user-visible change |
|---|---|
| `gp-opengraph: new workspace package providing OpenGraph and Twitter meta-tag emission for Sphinx. Drop-in replacement for the transitive sphinxext-opengraph dep — same ogp_* configuration surface, minus the matplotlib-based social-card generator (which is accepted but ignored, with a one-line warning pointing at the static-image workflow). Replaces sphinxext.opengraph in DEFAULT_EXTENSIONS.` | `#### New package: \`gp-opengraph\`<br><br>OpenGraph meta-tag emission. Drop-in for \`sphinxext-opengraph\`, matplotlib-free; \`ogp_social_cards\` is accepted but ignored with a warning. Replaces \`sphinxext.opengraph\` in \`DEFAULT_EXTENSIONS\`. (#22)` |
| `cli(sync): Add structured error reporting to handler` | `#### \`cli sync\`: Errored items now appear in the summary<br><br>The summary block previously showed only successful and failed counts; errored items were silently dropped. Each errored item is now listed with its failure reason. (#512)` |
| `feat: Add 12 new test cases for parser` | (skip — internal coverage, not user-visible) |

### Whole-branch perspective

Changelog entries describe the **net shipped result** of the branch, not its
internal commit history. Collapse fixup commits, reverts-then-re-adds, and
intermediate states. A TDD sequence (add failing test → fix → clean up) becomes
one bug fix entry, not three.

---

## Phase 4: Present for Review

**CRITICAL**: This is a mandatory confirmation gate. Never skip to Phase 5 without explicit user approval.

**Present to the user**:

1. **Summary line**:
   ```
   Branch: <branch-name> | Commits: <count> | PR: #<number> (or "none")
   ```

2. **Proposed entries** in a fenced code block showing the exact markdown:
   ````
   ```markdown
   ### What's new

   #### New package: `cli-sync`

   Bidirectional config sync between `~/.config/foo` and a remote
   store. Drop-in for the deprecated `foosync` script. (#512)

   ### Bug fixes

   - Fix phantom error when processing edge case input (#513)

   #### `cli sync`: Errored items now appear in the summary

   The summary block previously showed only successful and failed
   counts; errored items were silently dropped. Each errored item is
   now listed with its failure reason. (#514)
   ```
   ````

3. **Insertion point**: Describe where these entries will go:
   ```
   Insert after: <identified insertion point from Phase 1>
   Before: <next section or release heading>
   ```

4. **Ask the user**: "Insert these entries into <changelog-file>? You can also ask me to modify them first."

**Wait for user response.** Do not proceed until they confirm.

---

## Phase 5: Insert into Changelog

**Goal**: Insert the approved entries into the changelog file.

**Only execute after explicit user approval in Phase 4.**

### Insertion logic

1. **Find the insertion point** identified in Phase 1

2. **Check for existing unreleased section headings**:
   - If the changelog already has a matching section heading in the unreleased block, **append** to the existing section rather than creating a duplicate heading
   - If the section doesn't exist yet, insert the full section with heading

3. **Insert the entries**:
   - Use the Edit tool to insert at the identified insertion point
   - Ensure consistent blank line spacing matching the existing file style

4. **Show the result**:
   - After editing, read the modified region of the changelog file and display it so the user can verify
   - Note: this command does NOT commit — the user decides when to stage and commit the changelog update

### Commit message conventions for CHANGES edits

When the user asks to commit the CHANGES update, follow these rules:

1. **`#PRNUM` references belong in CHANGES, never in commit messages.** CHANGES entries reference PRs (e.g., `(#511)`) because they are user-facing and link to GitHub. Commit messages must never contain `#123` — the PR number may not exist yet, and git's merge history already tracks which PR a commit belongs to.

2. **Don't be redundant with the component prefix.** The commit prefix `docs(CHANGES)` already says "this is a changelog edit." The subject line should describe *what the changelog covers*, not that a changelog was added. For example:
   - **Good**: `docs(CHANGES) Help-on-empty CLI and sync --all flag`
   - **Bad**: `docs(CHANGES) Add changelog entry for help-on-empty CLI`
   - **Bad**: `docs(CHANGES[v1.53.x]) ...` — the version is unknown until merge

3. **Use `docs(CHANGES)` as the component.** No sub-component (no `[v1.53.x]` etc.) since the target release version is not known at commit time.

### Edge case: merging with existing entries

If there are already entries in the unreleased section:

- New entries for **existing sections** are appended at the end of that section (before the next `###` heading or the next `## ` release heading)
- New entries for **new sections** follow the section order defined in Phase 3 — insert the new section in the correct position relative to existing sections
- Never duplicate a `###` section heading
