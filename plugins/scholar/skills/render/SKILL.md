---
name: render
description: "Write a study's brief and evidence documents, then enforce the brief's citation prohibition with the analyzer"
allowed-tools: ["Bash", "Read", "Glob", "Edit", "Write"]
argument-hint: "[--out=<dir>]"
user-invocable: true
disable-model-invocation: true
---


# /scholar:render

Stage 5. Write the two layers a reader actually meets: a brief they read start
to finish, and the evidence they check it against.

The analyzer ships at `../../references/term-metrics.py`; `<analyzer>` below
is that path.

User arguments: $ARGUMENTS

## The prohibition

```
THE BRIEF CARRIES NO CITATION, NO PERMALINK, AND NO BARE NUMBER
```

Where it wants one, it links into `evidence/`. This is what keeps the top
layer readable: a brief with its appendices inlined is a report, and nobody
reads it start to finish.

The rule is enforced, not hoped for:

```console
$ <analyzer> notes/ontology/<subject>/ --check-brief
```

Non-zero exit means the brief is not renderable yet. Fix the brief, not the
checker.

## What the brief says

Four movements, in prose, each linking to the evidence file that holds its
support:

1. What the corpus is about, and where its vocabulary lives.
2. The type hierarchy, with each type's discriminator stated plainly.
3. The controlled vocabulary: the preferred terms, and the collisions that
   made them necessary.
4. What `contest` overturned, and what the kills revealed.

Write it for a reader who was not present. They do not have the corpus open,
they do not know the analyst, and they will judge the study by whether they
can disagree with it.

## What the evidence documents hold

`evidence/hierarchy.md` — the is-a claims, one citation each, with the
discriminators.

`evidence/vocabulary.md` — preferred and deprecated terms, and the
disjointness constraints.

`evidence/metrics.md` — every distributional claim with the command that
produced it and the output it produced.

`evidence/contested.md` — what `contest` judged, including the kills.

`evidence/corrections.md` — created empty, written by `/scholar:revise`.

## Rules

- Run the brief gate before reporting success. A study whose brief fails the
  gate is not rendered.
- Refresh the evidence documents rather than appending; they describe the
  current state of the study, and `corrections.md` is where history lives.
- Every section of the brief links to the evidence file that supports it.
- Do not restate an evidence document in the brief. If a paragraph would
  survive being replaced by a link, replace it.

## Output

Open with a one-line hero (`✓ rendered <subject>: brief + <n> evidence docs`
or `⚠ Brief gate failed: <n> findings`), then exactly these sections:

1. `## Brief` — the path, and the four movements in one line each.
2. `## Evidence` — each document written and what it holds.
3. `## Gate` — the brief check's output, verbatim.

End with an `AskUserQuestion` panel offering next steps (for example: publish
via gh, compare against another study, stop here) — skip the panel only in
plan mode.
