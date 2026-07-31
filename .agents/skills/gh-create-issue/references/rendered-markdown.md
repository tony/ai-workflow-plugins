# Rendered markdown

The writing rules for text a renderer will show a human: issue, pull
request, discussion and review-comment bodies, release notes, tracker
tickets, and a repository's own markdown files.

Shared by the `rendered-markdown` skill and this skill so the
rules cannot drift between them. Linking mechanics live in
`references/source-links.md`.

## The test

Will a maintainer three years from now find this helpful?

They will not have the conversation that produced the text, the tab
that was open, or the branch it was written on. What survives is what
was written down and what it links to. Everything below follows from
that: pin the links, name the symbols exactly, show the command that
was actually run, and cut the sentences that only made sense on the
day.

For a pull request, the same test picks the subject: describe the
branch's **net** change, not the route it took. Intermediate renames,
reverted attempts, and fixups are history the commits already carry.

## Two surfaces, one difference

In issue, pull request, discussion, and comment bodies GitHub renders
a single newline inside a paragraph as a line break. In a markdown
file it renders as a space.

That difference decides wrapping. Three rules below are body-only and
say so — heading level, table of contents, and mentions. Everything
else applies to both surfaces.

### Comment bodies are never hard-wrapped

Write each paragraph as one long line and separate paragraphs with a
blank line. A body wrapped at 72 or 80 columns renders as a column of
ragged short lines, and every later edit re-wraps a whole paragraph
into unreadable diffs.

### Repository files follow the repository

Wrapping a `.md` file is safe and most repositories do it — this file
is wrapped at 72. Match whatever the repository already does; never
re-wrap a file just because a body nearby is unwrapped.

### Commit messages wrap

They are not rendered markdown at all. The project's own commit
convention governs.

## Symbols

Wrap every symbol in backticks: function and method names, flags, CLI
subcommands, environment variables, file paths, package names, type
names, config keys, and verbatim error strings. In the title too.

Backticks are also the escape hatch: text inside a code span is never
autolinked, so `` `#123` `` and `` `@import` `` stay literal. An
unescaped `@` in a body has linked to a stranger's GitHub account
before.

## Nothing local, nothing personal

Strip before publishing, every time:

- Absolute local paths. Rewrite `/home/<you>/work/api/src/db.py` as
  `src/db.py`, relative to the repository root.
- Machine names, internal hostnames, LAN addresses, and container ids.
- Email addresses, real names of people who did not consent to be
  named, and account handles used as attribution.
- Tokens, keys, cookies, session ids, and signed URLs — including
  inside pasted logs and stack traces.
- Internal-only URLs a reader outside the org cannot open. Say what
  they contain instead of linking them.

Pasted output is where these leak. Read every line of a log before it
goes into a body, not just the first and last.

## Code blocks

Reach for a fenced block whenever the text is something a reader would
otherwise have to retype.

- One command per block. Two commands in one fence cannot be copied
  independently, and the reader cannot tell which one failed.
- No comments inside a fence. Explanation goes above the block as
  ordinary prose.
- A single long command may span lines with a trailing `\`, and a
  multi-statement one-liner may use `\;` — that is still one command.
- Tag the language when highlighting earns it — `python`, `ts`, `rust`
  for source. Use `console` for a transcript that shows a `$` prompt
  with its output; it is the only hint that tokenizes the two apart. A
  lone command needs no tag.
- To show triple backticks inside a block, fence it with four.

## Long output goes in `<details>`

Logs, stack traces, full diffs, dependency trees, JSON dumps, version
matrices, and anything else a reader scrolls past to reach the point.

```
<details>
<summary>Full stack trace</summary>

...

</details>
```

- The blank line after `</summary>` is required. Without it the body
  is raw HTML and every fence, list, and `**bold**` renders literally.
  This is the single most common way a body ships broken.
- No markdown inside `<summary>` — asterisks and backticks render as
  themselves there. Use `<b>` or `<code>`, or plain text.
- `<details open>` works, and blocks nest, each level needing its own
  blank line after its `</summary>`.
- Indenting a `<details>` four or more spaces past its container's
  content column turns it into a code block. Under a numbered step,
  three spaces is right.

## Structure

### No tables

Rendered tables are `width: max-content` with `overflow: auto` — they
scroll sideways instead of reflowing, so a narrow viewport silently
hides the right-hand columns. Use nested sections, or a list with a
repeated leading label. Both reflow, diff cleanly, and survive being
quoted in a reply.

### Start a body's headings at `###`

In an issue the title is a separate field, so a `#` in the body
duplicates it. `##` draws a full-width horizontal rule; `###` does
not. GitHub's own templates and issue forms emit `###` per section,
so it is what readers expect. A repository file has no title field
and keeps its `#`.

### No table of contents in a body

Headings in an issue body receive no anchor ids, so a `[jump](#repro)`
link is dead on arrival. Link to another issue or a pinned file
instead. A repository file's headings do get ids, and a table of
contents there resolves.

### Alerts stay at the top level

`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`,
`> [!CAUTION]` — and no others. Inside a `<details>` block or a list
item they degrade silently to a plain blockquote showing the literal
`[!NOTE]`. The marker must sit alone on its blockquote line. One per
body, at most.

## In a body, mentions are notifications

`@person` and `@org/team` send mail. They are not a way to attribute
work or decorate a body. Name someone only when you are asking them
for something.

Every rendered issue reference also writes a backlink onto the target
issue. Citing twenty related issues notifies twenty threads.

Neither fires from a repository file, where `@name` and `#123` are
plain text.

## What to leave out

- Preamble and sign-off. Start at the finding.
- Test counts, file counts, line counts, and "as of" dates. They are
  wrong within a week and nobody updates them.
- Line numbers in prose. Pin a permalink instead.
- Narration of the draft itself — "I have updated the section above".
- `comprehensive`, `robust`, `seamless`, `production-ready`,
  `leverage`, `delve`. Say what the thing does.
- Coded labels (`[R1]`, `Option B`) in text a human reads.
- For a pull request: renames of symbols that never shipped,
  "previously X" framing for behavior no released user saw, and any
  paraphrase of the diff.

## Preview before publishing

GitHub's own renderer will tell you whether the body works:

```
gh api --method POST /markdown -f mode=gfm -f context=OWNER/REPO -f text="$(cat body.md)"
```

Literal `**` or ``` ``` ``` in that output means a `<details>` block
is missing its blank line. A `<br>` inside a prose paragraph means the
body is hard-wrapped.

Both `mode=gfm` and `context` are required — with the default mode,
`context` is ignored and every reference renders inert, which reads as
a false negative. The preview is also not faithful for label chips,
reference unfurling in lists, team mentions, or cross-repo references,
and it renders with your permissions, so a private reference that
links for you can be inert for everyone else.

## Primary sources

- [Basic writing and formatting syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
- [Organized with collapsed sections](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-collapsed-sections)
- [Autolinked references and URLs](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls)
- [The GitHub Flavored Markdown spec](https://github.github.com/gfm/)
