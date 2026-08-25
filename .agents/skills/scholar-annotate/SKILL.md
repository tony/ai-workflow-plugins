---
name: scholar-annotate
description: >-
  Take reading notes on a prose corpus — quotations with stable locators and
  margin notes, as a term source for extract
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write"]
metadata:
  argument-hint: "<source> [--locator=chapter|section|page|line] [--out=<dir>]"
  source: "plugins/scholar/skills/annotate/SKILL.md"
---

# this skill

The prose path. Without it, a written corpus enters the pipeline as
unstructured text and its citations degrade to "somewhere in chapter 3".

Read `references/citation.md` for the locator rules this stage
implements.

User arguments: $ARGUMENTS

## Locator precedence

Take the most stable locator the source actually supports. In order:

**A pinned line anchor** — where the source is a text file in version control.
Most stable, and `verify` can check it mechanically.

**Chapter and section** — where the work is structured. Survives repagination
and translation between print and digital.

**Page** — only where `sources.jsonl` records the edition. A page number
without an edition is not a locator; it is a number that happens to be true of
one printing.

**A search string** — where the source has no stable anchor at all: a PDF
without pagination, an audio transcript, a scanned document. Quote enough
unique text to be found by search, and record in `sources.jsonl` that this
source's locator is a search string rather than a position, so `verify` checks
it by search rather than by position.

Never invent a position the source does not have. A confident wrong locator
costs a reader more than an honest search string.

## Procedure

### 1. Confirm the edition

Read the source's row in `sources.jsonl`. If the locator scheme is `page` and
the edition is unrecorded, stop and record the edition first.

### 2. Extract quotations

One quotation per concept the author names, long enough to stand on its own
when read out of context. A quotation that only makes sense beside the
sentence before it is too short.

### 3. Attach margin notes

The note says what the quotation is evidence *for* — which is the analyst's
judgement and must stay visibly separate from the author's words. Never blend
the two into a paraphrase; `extract` needs to know which is which.

### 4. Write the quotation set

```
{"source": "<source id from sources.jsonl>", "locator": "ch.3 §2", "quote": "...", "note": "the author's own term for the boundary"}
```

## Rules

- The quotation is verbatim. An ellipsis marks every omission.
- The note is the analyst's; the quote is the author's. They never merge.
- A term the author uses without defining is still a term. Quote a passage
  showing the usage rather than skipping it.
- Where the author defines a term explicitly, quote the definition and mark it,
  so `extract` can use it directly rather than inferring one.

## Output

Open with a one-line hero (`✓ <n> quotations from <source>` or `⚠ Blocked:
<reason>`), then exactly these sections:

1. `## Quotations` — count by locator kind, and the concepts they name.
2. `## Locator` — which scheme this source uses and why, including any
   fallback to a search string.
3. `## Undefined` — terms the author uses without defining, which `extract`
   will have to infer from usage.

End with an `ask-user-choice` panel offering next steps (for example: run
extract, annotate another source, stop here) — skip the panel only in plan
mode.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
