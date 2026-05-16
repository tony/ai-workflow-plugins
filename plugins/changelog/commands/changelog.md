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

2. **Read project conventions** — check the repo root for convention files and record what they prescribe. Look at `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/*`, `.github/AGENTS.md`, and any equivalent. Extract:
   - **Commit message format** — scope/type pattern (e.g., `Scope(type[detail]) subject`), body structure (e.g., `why:` / `what:` blocks), line-wrap budget (e.g., 72 chars), component-naming conventions
   - **Any prescribed CHANGES/release-notes format or voice**
   - **Any project-specific section names** (e.g., the project might use `Features` instead of `What's new`)

   These conventions **outrank** the defaults later in this command. If a project convention conflicts with a fallback rule below, the project convention wins.

3. **Detect trunk branch**:
   ```
   git symbolic-ref refs/remotes/origin/HEAD
   ```
   - Strip `refs/remotes/origin/` prefix to get branch name
   - Fall back to `master` if the above fails

4. **Verify not on trunk**:
   - Check current branch: `git branch --show-current`
   - If on trunk, report "Already on trunk branch — nothing to generate" and stop

5. **Find and read the changelog file** — scan the repo root for common changelog filenames:
   - `CHANGES`, `CHANGES.md`
   - `CHANGELOG`, `CHANGELOG.md`
   - `HISTORY`, `HISTORY.md`
   - `NEWS`, `NEWS.md`
   - If multiple exist, prefer the one with the most content
   - If none exist, report "No changelog file found" and ask the user which filename to create

6. **Analyze the changelog format** — this is the homogeneity step; the existing file is the source of truth for shape:
   - **Heading format**: Detect the pattern used for release headings (e.g., `## v1.2.3`, `## [1.2.3]`, `## project v1.2.3`, `## 1.2.3 (YYYY-MM-DD)`)
   - **Unreleased section**: Look for an "unreleased" heading or a placeholder comment (e.g., `<!-- END PLACEHOLDER`, `## [Unreleased]`, `## Unreleased`)
   - **Insertion point**: Determine where new entries go — after a placeholder comment, under an unreleased heading, or at the top of the file
   - **Section headings, order, and capitalization**: Look at the most recent populated release. Record the exact section names (`Features` vs. `What's new`, `Bug fixes` vs. `Bug Fixes`), their sequence, and any sections the project uses that aren't in the default list. Mirror this exactly when generating new entries.
   - **Entry shape and proportionality**: Note whether the project uses plain bullets, `####` sub-section headings, paragraph-per-entry, etc., and the typical entry length. Match it.

7. **Check for PR**:
   ```
   gh pr view --json number,title,body,labels 2>/dev/null
   ```
   - If a PR exists, extract the number, title, body, and labels
   - If no PR exists, note that `(#???)` placeholders will be used

8. **Get commits**:
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

2. **Section order — mirror the existing CHANGES first.** The homogeneity rule: whatever the project already does wins. Resolve in this priority:

   1. **Project convention from AGENTS.md / CLAUDE.md** (read in Phase 1). If the project's convention files prescribe a release-notes format or section order, follow it exactly. This wins over everything else.
   2. **Existing CHANGES file precedent.** If the most recent populated release in the changelog establishes a section order and naming (e.g., the project uses `### Features` and `### Bug Fixes` in that order), mirror it — same sequence, same heading names, same capitalization. Don't drag `Features` to `What's new`; don't promote `Development` above `Bug fixes` if the project doesn't.
   3. **Fallback (no precedent in either source).** When the CHANGES is empty or has no populated release to mirror, fall back to this default order, including only sections that have entries:

      Breaking changes → What's new → Bug fixes → Documentation → Tests → Development

3. **Simple entries** — single bullet for one-line changes:
   ```markdown
   - Brief description of the change (#123)
   ```

4. **Sub-section entries** — `####` heading + 2-4 lines of product-level prose. Use this for new packages, new flags, new behaviours, or notable changes to existing surface — anything a downstream user needs to learn rather than just notice. The heading names the product change; the prose covers usefulness, integration, and trade-offs.

   **If the existing CHANGES already has a sub-section convention, match it instead.** The shapes below are fallback defaults for projects with no precedent. If the project uses paragraph-only entries, bullet-only entries, or a different heading level for notable changes, mirror that:

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

6. **Match existing style** (the homogeneity rule, applied per-detail):
   - Match heading capitalization exactly — `Bug fixes` vs. `Bug Fixes`, `Features` vs. `What's new`, etc.
   - Match the heading level used for entry groups (`###` vs. `####`)
   - Match bullet style, prose vs. bullet preference, blank-line spacing, and any other shape detail visible in recent populated releases
   - When in doubt, copy the shape of the most recent release verbatim and adapt only the content

### Voice

**Product-facing, 10,000-ft, upgrade-time-decision oriented.** Each entry answers one of four reader questions in its first sentence: *should I upgrade, will my code break, can I drop a workaround / take a new affordance, was my bug just fixed?* Lead with what the user GAINS, can now DO, or needs to KNOW — never with what was implemented.

The changelog is a *"should I care?"* filter, not a manual or a release-notes blog post. Depth lives in autodoc, source, and git history; the PR link in each entry is the doorway for readers who want it.

#### What belongs in an entry

- **Usefulness and downstream impact.** When a new package or feature has a non-obvious integration story, mention it: drop-in compatibility (`Drop-in for X`), default activation (`Replaces X in DEFAULT_EXTENSIONS`), auto-derivation (`auto-derives X, Y, Z from a single docs_url`), or accepted-but-ignored config keys with a warning. Two short sentences usually do this; rarely more.
- **Present-tense entry titles.** "Add support for..." not "Added support for...".
- **PR link.** Every entry closes with `(#123)` or `(#???)`.

#### What to exclude

These patterns belong in autodoc, source, and the linked PR — never in CHANGES. Call them out and rewrite when you see them in a draft entry:

- **Type signatures** — `float | None`, `Optional[X]`, generic params, return types.
- **Signal / syscall / kernel names** — `SIGTERM`, `SIGKILL`, `epoll`, `mmap`, "kernel pipe buffer", "non-blocking fd".
- **Internal mechanics** — selectors, busy-loops, race windows, buffer sizes, lock files, the *cause* of a fix rather than its effect on the user.
- **Dunder / private method names** — `__str__`, `__init__`, `_internal_helper`.
- **Implementation flags or constants** — `_TIMEOUT_GRACE_SECONDS`, internal env vars, feature toggles invisible to consumers.
- **Numeric tallies** — file counts, line counts, test counts, commit counts ("across N commits", "in N changes", "adds N tests"). Brittle, and duplicate the diff.
- **Git refs** — SHAs, commit hashes, branch names, tag names, line numbers. Break when history is rebased or tags move.
- **Non-user-visible work** — refactors that don't change behaviour, type-only annotations, internal renames, lint cleanups, CI tweaks, test-infra changes, dev-tooling bumps. The diff and commit log are the right home.
- **Phantom fixes** — `### Fixes` entries (or "no longer raises / fails / errors / crashes" phrasings) for behavior that did not exist in any published release. Apply the Published-Release Test (`AGENTS.md` § *Shipped vs. Branch-Internal Narrative*): did users of the most recently published release ever experience this bug? If no, the entry belongs in the design-description paragraph of the feature that introduced the contract, not under `### Fixes`.
- **Section-heading repetition.** Don't repeat the section heading in the entry text.

#### Proportionality

- 1-2 lines per simple bullet
- 2-4 lines per `####` sub-section entry
- If an entry grows past that, the underlying change probably wants to be split into multiple entries (one per shipped surface). Long prose buries the impact.
- If a sentence reads like it was lifted from a docstring or a stack trace, cut it — that information has a better home in the linked PR or in autodoc.

When the existing CHANGES file establishes its own proportionality (e.g., one-line bullets only, or paragraph-per-entry), match it.

#### Good vs. bad framing

| Bad — describes the commit, or leaks implementation | Good — describes the user-visible change |
|---|---|
| `gp-opengraph: new workspace package providing OpenGraph and Twitter meta-tag emission for Sphinx. Drop-in replacement for the transitive sphinxext-opengraph dep — same ogp_* configuration surface, minus the matplotlib-based social-card generator (which is accepted but ignored, with a one-line warning pointing at the static-image workflow). Replaces sphinxext.opengraph in DEFAULT_EXTENSIONS.` | `#### New package: \`gp-opengraph\`<br><br>OpenGraph meta-tag emission. Drop-in for \`sphinxext-opengraph\`, matplotlib-free; \`ogp_social_cards\` is accepted but ignored with a warning. Replaces \`sphinxext.opengraph\` in \`DEFAULT_EXTENSIONS\`. (#22)` |
| `cli(sync): Add structured error reporting to handler` | `#### \`cli sync\`: Errored items now appear in the summary<br><br>The summary block previously showed only successful and failed counts; errored items were silently dropped. Each errored item is now listed with its failure reason. (#512)` |
| `#### New \`timeout=\` keyword<br><br>\`Foo.run()\` and \`Bar.run()\` accept \`timeout: float \| None = None\`. When the deadline fires the child is \`SIGTERM\`'d (\`SIGKILL\` after a grace) and \`SomeError\` is raised with the deadline duration in its \`__str__\`. (#42)` | `#### New \`timeout=\` keyword<br><br>\`Foo.run()\` and \`Bar.run()\` now accept a \`timeout\`, with improved cleanup of stuck subprocesses when the deadline fires. (#42)` |
| `#### \`Foo.lookup()\`: read fewer entries<br><br>The previous implementation called \`some-internal --verbose\` whose output enumerates every entry; \`lookup()\` now reads \`some-internal --short\` and falls back to a default value when the optional field is unset, matching upstream behaviour. Subprocess failures still degrade to \`None\`. (#43)` | `#### Improve handling of large datasets<br><br>Lookups against datasets with thousands of entries no longer appear to hang -- the implementation avoids a load-bearing command that walked every entry. (#43)` |
| `feat: Add 12 new test cases for parser` | (skip — internal coverage, not user-visible) |

**The pattern in the last two rows**: the *bad* version reads like a release-notes blog post or an autodoc summary; the *good* version answers *"what's this, why care?"* and stops. Anyone wanting the implementation detail can follow the PR link and read the diff.

#### Whole-branch perspective

Changelog entries describe the **net shipped result** of the branch, not its internal commit history. Collapse fixup commits, reverts-then-re-adds, and intermediate states. A TDD sequence (add failing test → fix → clean up) becomes one bug fix entry, not three.

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

When the user asks to commit the CHANGES update, the commit message follows a tiered rule:

1. **Project convention wins.** If `AGENTS.md` / `CLAUDE.md` (read in Phase 1) prescribes a commit format, use it exactly — including any required subject pattern, body structure, and line-wrap budget. For example, a project might prescribe:

   ```
   Scope(type[detail]) concise description

   why: Explanation of necessity or impact.
   what:
   - Specific technical changes made
   ```

   with 72-character body wrapping. Use the project's `type` for docs edits (typically `docs`), the project's component-detail style (e.g., `docs(CHANGES)`), and the project's body structure. The body should say *why* the changelog was updated (e.g., "Document help-on-empty CLI and sync --all flag for v1.53") and *what* it adds (a bulleted recap of the new sections), wrapped to the prescribed width.

2. **Fallback when no convention is documented.** Use `docs(CHANGES) <description>` as the subject with no body.

3. **Universal rules** (apply regardless of project convention):

   - **`#PRNUM` references belong in CHANGES, never in commit messages.** CHANGES entries reference PRs (e.g., `(#511)`) because they are user-facing and link to GitHub. Commit messages must never contain `#123` — the PR number may not exist yet, and git's merge history already tracks which PR a commit belongs to.
   - **The subject describes *what the changelog covers*, not that a changelog was added.**
     - **Good**: `docs(CHANGES) Help-on-empty CLI and sync --all flag`
     - **Bad**: `docs(CHANGES) Add changelog entry for help-on-empty CLI`
   - **No version sub-component.** Avoid `docs(CHANGES[v1.53.x]) ...` — the target release version isn't known at commit time.

### Edge case: merging with existing entries

If there are already entries in the unreleased section:

- New entries for **existing sections** are appended at the end of that section (before the next `###` heading or the next `## ` release heading)
- New entries for **new sections** follow the section order defined in Phase 3 — insert the new section in the correct position relative to existing sections
- Never duplicate a `###` section heading
