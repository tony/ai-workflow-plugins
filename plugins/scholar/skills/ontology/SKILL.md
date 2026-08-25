---
name: ontology
description: "Use when distilling an ontology, controlled vocabulary, or glossary of what a codebase, a repository set, or a written corpus calls things."
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task", "WebFetch"]
argument-hint: "[<target>...] [--kind=code|prose|fleet] [--out=<dir>] [--resume=<stage>]"
user-invocable: true
---


# /scholar:ontology

Distil what a corpus calls things into a type hierarchy, a controlled
vocabulary, and an evidence layer. The product is a study directory, not a
document, and every claim in it either cites a pinned source or carries a
command that reproduces its number.

Read `../../references/evidence-tiers.md` before starting; it decides what
each claim must carry. `../../references/citation.md` governs every pin.
`../../references/stage-gates.md` states each stage's exit condition.

User arguments: $ARGUMENTS

## Core thesis

An agent that has read a corpus usually returns a summary. A summary cannot be
checked, does not compose, and rots without saying so.

The test this pipeline is built against:

```
CAN A READER WHO WAS NOT PRESENT DISAGREE WITH A CLAIM,
FIND WHAT IT RESTS ON, AND RE-DERIVE IT?
```

A study that fails that test is a summary with more sections.

## Context

Repository:
`!git remote get-url origin 2>/dev/null || echo "(not a git repository)"`

Current ref:
`!git rev-parse --short HEAD 2>/dev/null || echo "(unknown)"`

Existing studies:
`!ls notes/ontology/ 2>/dev/null || echo "(none)"`

## Stages

Five stages, run in order. Each is separately invocable, so a study resumes
where it stopped rather than restarting.

1. `/scholar:gather` — resolve and pin the corpus, inventory it, and record
   what was read and what was skipped, into `sources.jsonl`.
2. `/scholar:extract` — harvest the terms the corpus uses, with a citation and
   a locator each, into `terms.jsonl`.
3. `/scholar:distill` — build the three layers: types, members with
   discriminators, and the controlled vocabulary.
4. `/scholar:contest` — judge the ontology adversarially, one candidate at a
   time, recording the kills.
5. `/scholar:render` — write `brief.md` and the evidence documents, and gate
   the brief.

For prose, run `/scholar:annotate` before `extract` to produce quotations with
stable locators.

`--resume=<stage>` starts at that stage against an existing study directory.

## Orchestration Plan

Enter plan mode before touching anything — `EnterPlanMode` in Claude Code,
`/plan` or Shift+Tab in Cursor, Codex, and Gemini. Where plan mode is
unavailable, present the same plan in chat and wait.

The plan states:

- The corpus: each target, its resolved ref, and how it was resolved.
- The kind — code, prose, or fleet — and what that changes about stages 1 and 2.
- The output directory, and confirmation that it is not inside the corpus.
- Which stages will run, and which are being skipped because a prior study
  already satisfies them.
- The coverage boundary: what will deliberately not be read, and why.

Present it, wait for approval, then exit plan mode and run stage 1.

## Rules

- Never write into the corpus being studied. Output lands under `--out`,
  defaulting to `notes/ontology/<subject>/` in the current repository.
- Every claim carries a tier. A claim that fits neither tier does not go in
  the brief.
- The brief carries no citation, no permalink, and no bare number. Where it
  wants one, it links into `evidence/`.
- A stage may not hand off until its gate passes. Report a failed gate; do not
  work around it.
- Terms are recorded as the corpus spells them. Variants are the evidence, not
  noise to normalize away.
- The analyzer proposes; it never decides. Every finding gets a human or agent
  verdict recorded in `evidence/contested.md`.

## Output

Open with a one-line hero (`✓ <subject>: <n> terms, <n> types, <n> contested`
or `⚠ Blocked: <reason>`), then exactly these sections:

1. `## Corpus` — each source, its resolved ref, and what was deliberately not
   read, with the reason.
2. `## Ontology` — the type hierarchy in prose, each type with its
   discriminator, and the vocabulary's preferred terms.
3. `## Contested` — what was challenged and how it resolved, including what
   was killed and what the kill revealed.
4. `## Where it lives` — the study directory path and which stages ran.

End with an `AskUserQuestion` panel offering next steps (for example: contest
another round, compare against another study, publish the brief, stop here) —
skip the panel only in plan mode.
