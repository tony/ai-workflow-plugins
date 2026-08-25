---
name: ask
description: "Answer a question from a finished study, citing back into its evidence, and say plainly when the study does not cover it"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
argument-hint: "<question> [--study=<dir>]"
user-invocable: true
disable-model-invocation: true
---


# /scholar:ask

Consult a study instead of re-reading the corpus. Answers come from
`terms.jsonl` and the evidence documents, and they carry the citation the
study already earned.

User arguments: $ARGUMENTS

## The discipline that gives this skill its value

```
ANSWER FROM THE EVIDENCE, OR NAME THE GAP
```

An agent asked a question about a corpus it has partly read will reason from
the parts it has to the parts it has not, and the result is indistinguishable
in tone from an answer it actually knows. This skill does not do that.

Where the study does not cover the question, say so, and say what would have
to be read to cover it. That answer is more useful than a plausible one,
because it can be acted on: `sources.jsonl` already records what was skipped
and why.

## Procedure

### 1. Locate the question in the ontology

Which terms does it touch, and which types do they sit under. A question that
touches no term in the table is a coverage question, not a lookup.

### 2. Answer from the rows

Every claim in the answer names the evidence file and the term row it came
from. An answer with no citations is either trivial or invented.

### 3. Trace on request

"Show me the evidence for X" is a question this skill answers: the term's
definition, every citation with its locator, any measurement that mentions it,
and any verdict `contest` recorded about it. That chain is what lets a reader
check the study rather than trust it.

### 4. Say what is missing

Distinguish three cases, because they mean different things:

- The study covers the question and the answer is here.
- The study read the relevant source and the corpus does not settle the
  question. That is a fact about the corpus.
- The study never read the relevant source. That is a fact about the study,
  and `sources.jsonl` says why it was skipped.

## Rules

- Never answer past the evidence. Plausibility is not coverage.
- Never cite the corpus directly. If the answer needs a source the study did
  not read, that is case three — report it and stop.
- Quote the study's own words for a definition rather than paraphrasing; a
  paraphrase silently drops the distinction the term exists to carry.

## Output

Open with a one-line hero (`✓ answered from <n> terms` or `⚠ Not covered:
<what would have to be read>`), then exactly these sections:

1. `## Answer` — the answer, each claim citing its evidence file and row.
2. `## Evidence` — the chain: definitions, citations with locators, and any
   verdict recorded about the terms involved.
3. `## Gaps` — what the study does not settle, and which of the three cases
   applies.

End with an `AskUserQuestion` panel offering next steps (for example: widen
the study to cover the gap, ask another question, stop here) — skip the panel
only in plan mode.
