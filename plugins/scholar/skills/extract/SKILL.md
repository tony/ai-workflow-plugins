---
name: extract
description: "Harvest terms and their definitions from a gathered corpus into terms.jsonl, each with the citation that supports it"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Task"]
argument-hint: "[--out=<dir>] [--from=<sources.jsonl>]"
user-invocable: true
disable-model-invocation: true
---


# /scholar:extract

Stage 2. Harvest the terms the corpus uses for its own things, each with a
citation that shows the term in use.

Read `../../references/citation.md` for what a citation must carry and
`../../references/stage-gates.md` for this stage's exit condition.

User arguments: $ARGUMENTS

## What counts as a term

A term is a word the corpus uses for one of its own concepts. In code that is
the names it gives things: type and class names, module and package names,
recurring verbs in function names and commit subjects, the roles in its
configuration, the nouns in its error messages. In prose it is the author's
own vocabulary, taken from `annotate`'s quotation set.

A term is not a word that merely appears. `handler` is a term where the
project distinguishes handlers from services; it is noise where it is just
what someone called a function once.

## Procedure

### 1. Read the source list

Take `sources.jsonl` from `gather`. Harvest only from sources marked
`"read": true`.

### 2. Harvest

For code, the cheapest high-yield passes, all portable:

```console
$ rg -o --no-filename -r '$1' '\b(?:class|struct|interface|type)\s+(\w+)' | sort | uniq -c | sort -rn
```

```console
$ git log --format=%s | rg -o '^\w+' | sort | uniq -c | sort -rn
```

Read the results; do not paste them into the table. Frequency proposes a
candidate, the corpus's own definition confirms it.

### 3. Write terms.jsonl

One row per term as the corpus spells it:

```
{"schema": 1, "term": "adapter", "definition": "wraps a third-party client behind the port interface", "parent": "", "kind": "role", "tier": "structural", "cites": [{"url": "https://github.com/OWNER/REPO/blob/v2.40.0/src/ports.py#L12-L18", "locator": "src/ports.py:12-18", "quote": "every third-party client enters through a port"}]}
```

`parent` stays empty here. `distill` assigns it.

`schema` is the row format's version. It costs one integer now and cannot be
added later without guessing what unversioned rows meant.

`definition` is drawn from the corpus, not composed. Where the corpus never
defines the term, record the definition its usage implies and say so in the
citation's quote by choosing a passage that shows the usage.

## Rules

- Do not invent a term the corpus does not use.
- Do not normalize spellings. `bump` and `update` staying separate is what
  lets `contest` find the synonymy; merging them here destroys the evidence.
- Every row has a non-empty definition and at least one citation with a
  locator, or this stage does not hand off.
- A citation whose quoted text contains the term it supports is circular and
  does not count. Pick a passage that shows the term in use instead.
- Set `tier` to `structural`. Distributional claims are `contest`'s to make,
  and they go in `evidence/metrics.md`, not on a term row.

## Output

Open with a one-line hero (`✓ <n> terms extracted from <n> sources` or
`⚠ Blocked: <reason>`), then exactly these sections:

1. `## Terms` — count by `kind`, and the ten most frequent with their
   definitions.
2. `## Rejected` — candidates that looked like terms and were not, with why.
   This section is the one that shows the harvest was judged rather than
   scraped.
3. `## Gate` — confirmation that every row has a definition and a citation.

End with an `AskUserQuestion` panel offering next steps (for example: run
distill, harvest another source, stop here) — skip the panel only in plan mode.
