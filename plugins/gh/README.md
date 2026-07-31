# gh

File GitHub issues a maintainer can still act on in three years, and
write any rendered body — issue, pull request, comment, ticket — so it
renders correctly and its links keep resolving.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install gh@ai-workflow-plugins
```

## Components

### `/gh:create-issue` (skill)

Files a GitHub issue from a description, a pasted finding, or an
investigation already in the conversation.

1. **Resolves the target repository, then checks it belongs in a
   public issue** — a vulnerability goes down that project's private
   reporting path instead.
2. **Preflights the repository** — issues enabled, contact links,
   issue templates and forms read from the default branch,
   `CONTRIBUTING.md` requirements.
3. **Looks for the issue that already exists** — open and closed, in
   titles and bodies, before writing anything.
4. **Gathers evidence** — reproduces the defect, records exact
   versions, pins the code that causes it, researches every upstream
   project it names.
5. **Drafts** — a fixed section order, `###` headings, long output in
   `<details>`, nested sections instead of tables.
6. **Sanitizes and previews** — strips local paths and PII, then
   renders the body through GitHub's own renderer to catch broken
   markup before it ships.
7. **Files on approval** — shows the full title and body, then opens
   it with `gh issue create --body-file`.

Read-only until that last step.

### `rendered-markdown` (skill)

Loads while you write anything a renderer will show a human: never
hard-wrap a comment body, backtick every symbol, one shell command per
fence, long output in `<details>`, nested sections instead of tables,
no local paths or PII, and every source link pinned to a tag or a
7-character commit. Guidance only — it never edits files.

The rules live in `references/rendered-markdown.md` and
`references/source-links.md`, which `/gh:create-issue` follows too, so
the two cannot drift.

## Why the wrapping rule has an exception

GitHub renders a single newline as a line break in issue, pull
request, discussion, and comment bodies, and as a space in a markdown
file. So a comment body is never hard-wrapped, while a repository's
`.md` files follow whatever convention the repository already uses.
The skills apply that boundary rather than reformatting files to match
bodies.

## Relationship to `pr` and `lean`

### Reach for `gh` when

You are filing an issue, or writing any body GitHub will render and
you want the markup and links to hold up.

### Reach for `pr` when

You need a pull request description generated, refreshed, recut, or
reviewed against gold-standard structure.

### Reach for `lean` when

You want the prose itself tightened — filler, diff narration, and
inflation removed. `lean` governs the sentences; `gh` governs the
markup, structure, and links around them.

## Prerequisites

- **gh** — GitHub CLI, authenticated. Used for every repository read,
  the markdown preview, and creating the issue.
- **git** — for resolving tags and refs when pinning links.
- **curl** and **jq** — for the package-registry lookups and the
  pre-publish link check when an issue names an upstream project.
