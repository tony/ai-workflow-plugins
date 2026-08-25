---
name: contest
description: "Adversarially judge a distilled ontology one candidate at a time — synonymy, polysemy, orphans, circular evidence, and coverage"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "Task", "AskUserQuestion"]
argument-hint: "[--out=<dir>] [--rounds=<n>] [--panel]"
user-invocable: true
disable-model-invocation: true
---


# /scholar:contest

Stage 4. Attack the ontology. Four passes, serial by default: one judge, one
candidate at a time, every verdict traceable to the evidence that settled it.

Read `../../references/evidence-tiers.md` before recording any number. The
analyzer ships beside it at `../../references/term-metrics.py`; `<analyzer>`
below is that path.

User arguments: $ARGUMENTS

## Pass 1 — mechanical

Run the analyzer:

```console
$ <analyzer> notes/ontology/<subject>/
```

It reports synonymy candidates, polysemy candidates, orphans, circular
evidence, and fan-out per type.

```
THE ANALYZER PROPOSES. IT NEVER DECIDES.
```

A high similarity score is a question — *are these one concept?* — not an
answer. Record the number in `evidence/metrics.md` with the command that
produced it, per the evidence tiers.

## Pass 2 — serial judgment

One candidate at a time. For each, write to `evidence/contested.md`:

- **Claim** — what the ontology currently asserts.
- **Objection** — the strongest case against it, argued properly rather than
  noted.
- **Evidence** — what settles it, cited or measured.
- **Verdict** — upheld, revised, or killed.

```
KILLS ARE RECORDED, NOT DISCARDED
```

A kill often carries more than a survivor, because it names a boundary the
ontology drew in the wrong place. A candidate rejected for the wrong reason
tells you the type above it is mis-specified.

Judge one candidate fully before starting the next. Batching them produces
verdicts that argue with each other.

## Pass 3 — completeness

Read `sources.jsonl` and ask what the study does not know:

- Which sources were never opened, and whether the vocabulary plausibly lives
  in one of them.
- Which terms rest on a single citation.
- Which types have exactly one member. A one-member type is usually a
  description wearing a type's clothes.
- Which terms have no citation that shows them in use, only in definition.

## Pass 4 — stop condition

Stop when a round surfaces no new contested claim, or at `--rounds`
(default 3). The convergence rule is `/spike:ratchet`'s: stop when the design
stops fighting back, not when a counter runs out.

## The circularity check

Runs in every pass. A citation whose quoted text contains the term it supports
proves the corpus uses the word, which was never in question, and hides
whether the corpus uses it the way the definition claims.

This is not theoretical. Routing eval prompts in this repository contained
their own skill's name, which made every rename candidate look expensive until
the self-reference was noticed.

## Panels

`--panel` hands one contested claim to independent adversarial participants
via `/weave:ask`, recording their verdicts in `evidence/contested.md` beside
the serial one. Where `weave` is not installed, say so and continue serially —
the panel is an amplifier, not a dependency.

## Rules

- Every analyzer finding has a recorded verdict before this stage hands off.
- A verdict cites or measures. "On reflection this seems fine" is not a
  verdict.
- Do not edit `terms.jsonl` to make a finding go away. Revise the claim and
  record why.
- A claim raised and not settled goes in `evidence/contested.md` as open, not
  in the brief.

## Output

Open with a one-line hero (`✓ <n> candidates judged, <n> killed, <n> open` or
`⚠ Blocked: <reason>`), then exactly these sections:

1. `## Findings` — what the analyzer proposed, by kind.
2. `## Verdicts` — each candidate, its objection, and how it resolved.
3. `## Kills` — what was killed and what the kill revealed.
4. `## Coverage` — what the study does not know, from pass 3.

End with an `AskUserQuestion` panel offering next steps (for example: another
round, run render, widen the corpus, stop here) — skip the panel only in plan
mode.
