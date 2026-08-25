---
name: compare
description: "Set two term tables against each other — same concept different term, same term different concept, and what each covers that the other lacks"
allowed-tools: ["Bash", "Read", "Glob", "Write"]
argument-hint: "<study-dir> <study-dir> [--out=<file>]"
user-invocable: true
disable-model-invocation: true
---


# /scholar:compare

Two studies, one question: where do these vocabularies agree, where do they
collide, and what does each one know that the other does not.

This is what makes studying many projects pay off rather than producing many
unrelated studies.

User arguments: $ARGUMENTS

## Two shapes of comparison

**Across projects.** What does tokio call the thing asyncio calls a task. Two
communities solving one problem rarely name it the same way, and the mapping
is most of what it costs to move between them.

**Across time.** One project's vocabulary at v1 against the same project at
v4. Drift that nobody announced is the drift that breaks readers of the old
documentation.

## Procedure

### 1. Load both tables

Take `terms.jsonl` from each study directory. Both must have passed
`distill`'s gate, or the `parent` fields are empty and the sibling comparison
is meaningless.

### 2. Report three sections

**Same concept, different term.** Definitions that score high against each
other while the terms differ. These are the translation table.

**Same term, different concept.** Identical terms whose definitions score low.
These are the traps — the reader who knows one project will be confidently
wrong about the other.

**Coverage.** What each table has that the other has no counterpart for. A
concept present in one and absent in the other is either a genuine difference
in what the projects do, or a gap in one of the studies. Say which you think
it is and why.

### 3. Record the numbers

Every score is a distributional claim, so it carries the command that produced
it. Run the analyzer at `../../references/term-metrics.py` against each table
rather than eyeballing the definitions:

```console
$ <analyzer> <study-dir>
```

## Rules

- Do not merge the tables. A comparison is a third document; the two studies
  stay as they are.
- A high similarity between two terms is a candidate mapping, not a mapping.
  Say what the definitions have in common and where they part.
- Where the two studies read corpora at different depths, say so. A coverage
  gap between an exhaustive study and a shallow one is a fact about the
  studies, not about the projects.

## Output

Open with a one-line hero (`✓ <n> mappings, <n> collisions, <n> uncovered` or
`⚠ Blocked: <reason>`), then exactly these sections:

1. `## Mappings` — same concept, different term, with both definitions.
2. `## Collisions` — same term, different concept, and what a reader moving
   between the two would get wrong.
3. `## Coverage` — what each side has that the other lacks, and whether that
   is a difference or a gap.

End with an `AskUserQuestion` panel offering next steps (for example: study
the uncovered area, publish the mapping, stop here) — skip the panel only in
plan mode.
