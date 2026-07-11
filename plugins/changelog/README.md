# changelog

Generate categorized changelog entries from branch commits and PR context.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install changelog@ai-workflow-plugins
```

## Command

| Command | Description |
|---------|-------------|
| `/changelog` | Analyze commits, categorize changes, and insert entries into the changelog |

## 5-Phase Workflow

1. **Gather context** — Detect project name, read project conventions (AGENTS.md/CLAUDE.md), find changelog file, analyze its format, check for PR, collect commits
2. **Categorize commits** — Parse commit types, group related commits (e.g., TDD sequences collapse into one entry)
3. **Generate entries** — Write markdown matching the existing changelog style
4. **Present for review** — Show proposed entries and insertion point, wait for user approval
5. **Insert** — Apply approved entries to the changelog file

## A Branch Is Not a Release

Entries always land in the unreleased section. The command will not create or date
a version heading, guess which version the work ships in, reason about SemVer from
the commits, edit version files, or create tags — a release-shaped branch name,
milestone, or version bump in the diff changes none of this.

Cutting a release is a separate, explicit act: the command does it only when you ask
for it and name the version ("cut v1.53.0", "this is the release branch for 0.9.4").
Ambiguous asks get a clarifying question, not a guess.

## Supported Changelog Formats

The command auto-detects the changelog format from the existing file:

| File names | `CHANGES`, `CHANGES.md`, `CHANGELOG`, `CHANGELOG.md`, `HISTORY.md`, `NEWS.md` |
|------------|--------------------------------------------------------------------------------|
| Heading styles | `## v1.2.3`, `## [1.2.3]`, `## project v1.2.3`, `## 1.2.3 (YYYY-MM-DD)` |
| Insertion points | Placeholder comments, `## [Unreleased]` headings, top of file |

## Commit Categorization

Commits are mapped to changelog sections based on their type prefix. **Section names mirror the existing CHANGES file when one exists** — the table below lists fallback names used only when the file has no precedent:

| Commit type | Fallback section |
|-------------|------------------|
| `feat` | What's new (or `Features`, if the project uses that) |
| `fix` | Bug fixes |
| `docs` | Documentation |
| `test` | Tests |
| `chore`, `deps` | Development |

Related commits are grouped automatically:
- TDD sequences (xfail → fix → remove xfail) collapse into a single bug fix entry
- Sequential feature commits on the same component merge into one entry
- Merge commits and formatting-only changes are skipped

## Project Conventions

The command reads `AGENTS.md`, `CLAUDE.md`, and similar convention files at the repo root in Phase 1, and applies them with this priority:

1. **AGENTS.md / CLAUDE.md** (explicit project rules) — wins over everything else
2. **Existing CHANGES file** (implicit homogeneity) — section order, heading capitalization, entry shape, and proportionality are mirrored from the most recent populated release
3. **Command defaults** — used only when neither source has precedent

This applies to both the changelog entries themselves and the commit message used when the CHANGES update is committed. If the project's AGENTS.md prescribes a commit format (e.g., `Scope(type[detail])` with `why:` / `what:` body), the command follows it instead of its fallback `docs(CHANGES) <description>` form.

## Prerequisites

- **git** — for commit history analysis
- **gh** (optional) — for PR number and label detection

## Language-Agnostic Design

Project name detection works across ecosystems: `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, or the repository directory name. The changelog format is detected from the existing file — no format is assumed.
