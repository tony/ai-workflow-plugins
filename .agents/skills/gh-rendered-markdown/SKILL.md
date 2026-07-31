---
name: gh-rendered-markdown
description: >-
  Use when writing anything a renderer will show a human — a GitHub issue,
  pull request, discussion or review-comment body, release notes, a tracker
  ticket, or a repository markdown file. Governs the markup that decides
  whether it renders and the links that decide whether it survives: never
  hard-wrap a comment body, backtick every symbol, pin source links to a tag
  or a 7-character commit, one shell command per fence, long output folded
  into `<details>`, nested sections instead of tables, and no local paths or
  PII. Guidance only; it never edits files on its own.
allowed-tools: ["Read", "Grep", "Glob", "Bash", "WebSearch", "WebFetch"]
metadata:
  source: "plugins/gh/skills/rendered-markdown/SKILL.md"
---

# Rendered markdown

Write the body so it renders, and link it so it still resolves in
three years.

Two references carry the rules, and they are the same ones
the `gh-create-issue` skill follows:

- `references/rendered-markdown.md` — wrapping,
  symbols, code fences, `<details>`, structure, and what to leave out.
- `references/source-links.md` — pinning,
  autolinking, cross-repo references, and the project link set.

## The test

Will a maintainer three years from now find this helpful? They will
not have the conversation, the open tab, or the branch. What survives
is the text and what it links to.

For a pull request that test also picks the subject: the branch's net
change, not the route it took.

## Core moves

- **Know which surface you are on.** GitHub renders a single newline
  as a line break in issue, pull request, and comment bodies, and as a
  space in a markdown file. So a comment body is never hard-wrapped,
  and a repository file follows the repository's own convention. Do
  not re-wrap a file to match a body.
- **Backtick every symbol** — functions, flags, paths, env vars,
  packages, types, verbatim errors. In the title too. Backticks are
  also how you stop `#123` or `@name` from linking.
- **Strip local paths and PII** before publishing: absolute home
  paths, hostnames, emails, tokens, internal URLs. Pasted logs are
  where they hide.
- **Fence liberally, one command per block**, no comments inside the
  fence, language tagged. A long command may wrap with `\`.
- **Fold long output into `<details>`** with a blank line after
  `</summary>` — without it the whole block renders as raw HTML.
- **Nested sections, not tables.** Rendered tables scroll sideways
  instead of reflowing and hide their right-hand columns.
- **Link at every opportunity, and pin what you link.** A release tag
  first, else a 7-character commit reachable from trunk, never
  `blob/main`. Name an open-source project once with its whole set:
  repository, homepage, docs, the changelog at that release, and its
  registry page.
- **Use the autolinks that already exist.** Bare `#123` and a bare
  7-character ref inside a GitHub body; `[REPO#123](url)` across
  repositories; a bare tracker key only when that repository actually
  resolves it.

## Calibrate to the project

Read `./AGENTS.md` and `./CLAUDE.md`. Where they define a house voice,
a slop rubric, or a wrap convention, that governs.

## Verify before publishing

Render the draft through GitHub's own renderer and read the output —
literal `**` means a `<details>` block lost its blank line, and a
`<br>` inside prose means the body is hard-wrapped.

```
gh api --method POST /markdown -f mode=gfm -f context=OWNER/REPO -f text="$(cat body.md)"
```

## Common mistakes

**Hard-wrapping an issue body at 72 columns.** Correct for a commit
message, correct for most repository files, wrong here — every newline
becomes a line break and the paragraph renders as ragged stubs.

**A `<details>` block with no blank line after `</summary>`.** The
fences, lists, and bold inside it all render as literal text. It is
the most common way a body ships broken.

**An alert inside `<details>` or a list item.** `> [!WARNING]`
degrades silently to a plain blockquote showing the marker.

**Linking `blob/main/…` with a line anchor.** It resolves forever and
points at different code every week.

**A table of contents linking to the body's own headings.** Issue-body
headings get no anchor ids; every one of those links is dead.

**@mentions as attribution.** They send mail. Name someone only when
you are asking them for something.

**Reformatting the repository to match.** This skill governs what you
are writing, not the files around it.


## Portability notes

- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
