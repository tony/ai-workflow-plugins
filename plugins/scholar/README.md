# scholar

Distil a checkable ontology from a codebase, a repository set, or a written
corpus. The product is a type hierarchy plus a controlled vocabulary, a short
human-readable brief, and an evidence layer that lets a third party check
every claim.

An agent that has read a corpus usually returns a summary. A summary cannot be
checked, does not compose, and rots without saying so. The test this plugin is
built against: can a reader who was not present disagree with a specific
claim, find what it rests on, and re-derive it?

## Installation

In Claude Code, add the marketplace:

```console
$ /plugin marketplace add tony/skills
```

Install the plugin:

```console
$ /plugin install scholar@skills
```

In Codex, add the marketplace:

```console
$ codex plugin marketplace add tony/skills
```

Install the plugin:

```console
$ codex plugin add scholar@skills
```

## Skills

| Claude Code | Codex | Description |
|---|---|---|
| `/scholar:ontology [<target>...]` | `scholar:ontology` | Distil an ontology, controlled vocabulary, or glossary of what a codebase, a repository set, or a written corpus calls things |
| `/scholar:gather <target>...` | `scholar:gather` | Resolve and pin a corpus, inventory it, and record what was read and what was deliberately skipped |
| `/scholar:extract` | `scholar:extract` | Harvest terms and their definitions into a term table, each with the citation that supports it |
| `/scholar:distill` | `scholar:distill` | Build the three layers — types, members with discriminators, and the controlled vocabulary |
| `/scholar:contest` | `scholar:contest` | Adversarially judge the ontology one candidate at a time, recording the kills |
| `/scholar:render` | `scholar:render` | Write the brief and the evidence documents, then enforce the brief's citation prohibition |
| `/scholar:annotate <source>` | `scholar:annotate` | Reading notes on prose — quotations with stable locators, as a term source for extract |
| `/scholar:ask <question>` | `scholar:ask` | Answer from a finished study, citing its evidence, and name the gap when there is one |
| `/scholar:compare <dir> <dir>` | `scholar:compare` | Set two term tables against each other — shared concepts, clashing terms, and coverage |
| `/scholar:revise <claim>` | `scholar:revise` | Record a correction: what was believed, what it rested on, and why it failed |
| `/scholar:verify [<dir>]` | `scholar:verify` | Re-check a study against the corpus it cites — moved refs, vanished files, misquotes, changed numbers |

`ontology` is the only skill a model routes to on its own. The rest are
invoked by name, so the pipeline can be resumed at any stage.

## Artifacts

A study is a directory, not a document:

```
notes/ontology/<subject>/
├── brief.md              the only file meant to be read start to finish
├── terms.jsonl           interchange: {term, definition, parent, kind, cites, tier}
├── sources.jsonl         {source, ref, scope, read, why}
└── evidence/
    ├── hierarchy.md      the type hierarchy, one citation per is-a claim
    ├── vocabulary.md     preferred and deprecated terms, disjointness constraints
    ├── metrics.md        distributional claims, each with its command and output
    ├── contested.md      claim, objection, verdict — including the kills
    └── corrections.md    retractions: what was believed, and why it failed
```

`terms.jsonl` is the seam everything composes on. Stages do not call each
other; they read and write these files. A term table written by hand, or by a
different tool entirely, is a valid input to `contest` and `render`.

`brief.md` may not contain a citation, a permalink, or a bare number. Where it
wants one it links into `evidence/`. `render` enforces this with
`references/term-metrics.py --check-brief`, so the top layer stays readable by
construction rather than by discipline.

## Composition

Every one of these is optional. `scholar` works standalone.

`weave` — `contest --panel` hands one contested claim to independent
adversarial participants and records their verdicts beside the serial one.

`research:deps` — pinned worktrees at an installed version, when the corpus is
a dependency of the current project.

`gh` — the rendered-markdown and source-link disciplines when a study is
published as an issue or a comment.

`spike:ratchet` — the convergence rule `contest`'s stop condition names.

## Prerequisites

- **git** — resolving and pinning a corpus to a ref
- **rg** — inventorying a corpus without reading all of it
- **Python 3.12** — `references/term-metrics.py`, standard library only, so it
  runs inside any corpus checkout with no package manager present
