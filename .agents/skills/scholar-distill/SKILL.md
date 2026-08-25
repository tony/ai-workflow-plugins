---
name: scholar-distill
description: >-
  Build the three ontology layers from a term table — types, members with
  discriminators, and the controlled vocabulary
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write"]
metadata:
  argument-hint: "[--out=<dir>]"
  source: "plugins/scholar/skills/distill/SKILL.md"
---

# this skill

Stage 3. Turn a flat term table into an ontology. Three layers, in order. Any
one of them alone is not an ontology.

Read `references/evidence-tiers.md` for what each claim must carry and
`references/stage-gates.md` for this stage's exit condition. The orphan
gate below runs `references/term-metrics.py`.

User arguments: $ARGUMENTS

## Layer 1 — types

The is-a hierarchy. What kinds of thing the corpus contains.

Write it to `evidence/hierarchy.md`, one citation per is-a claim, and write
each type back onto its members' rows in `terms.jsonl` as `parent`. A root
type's `parent` is the literal string `root`.

Types come from the corpus's own distinctions. If a project separates ports
from adapters everywhere, those are types. If the analyst finds it tidy to
group four things, that is not a type.

## Layer 2 — members with discriminators

For each type, the test that decides membership. Write it into
`evidence/hierarchy.md` beside the type.

This is what separates an ontology from a labelled list:

- A discriminator: *a plugin is an agent domain iff its name denotes a doer
  rather than the thing acted on.*
- Not a discriminator: *these four feel similar.*

A type whose discriminator you cannot write is not a type yet. Either find the
test, or dissolve the type and return its members to their parent.

## Layer 3 — the controlled vocabulary

Write `evidence/vocabulary.md`: per act or relation the corpus performs, the
preferred term, its deprecated variants, and the disjointness constraints
between siblings.

Three properties, all checkable by `contest`:

- **One term, one referent.** No polysemy. A term standing for two concepts is
  the failure that makes a vocabulary unusable.
- **One referent, one term.** No synonymy. Four names for one act is four
  chances to miss the fourth.
- **Siblings disjoint.** No two sibling terms both correctly describe one
  instance.

The preferred term is the one the corpus already uses most, not the one that
reads best. A vocabulary that renames what the corpus says has stopped
describing it.

## Prohibitions

```
NEVER INVENT A TYPE TO HOUSE AN ORPHAN
NEVER SPLIT A TYPE TO TIDY ITS FAN-OUT
```

Both produce a hierarchy that describes the analyst's sense of order rather
than the corpus. An orphan is a finding: either the corpus has a concept the
hierarchy has not named, or the term does not belong in the table.

## Rules

- Every type has a discriminator before this stage hands off.
- `references/term-metrics.py` reports no orphans before this stage
  hands off.
- A term keeps the spelling `extract` recorded. The vocabulary names a
  preferred term; it does not rewrite the rows.
- Deprecated variants stay in the table. They are what a reader of the corpus
  will actually encounter.

## Output

Open with a one-line hero (`✓ <n> types, <n> terms, <n> preferred terms` or
`⚠ Blocked: <reason>`), then exactly these sections:

1. `## Types` — the hierarchy, each type with its discriminator.
2. `## Vocabulary` — preferred terms with their deprecated variants.
3. `## Unresolved` — terms that resisted placement, and what that suggests
   about the corpus rather than about the table.

End with an `ask-user-choice` panel offering next steps (for example: run
contest, revisit a type, stop here) — skip the panel only in plan mode.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
