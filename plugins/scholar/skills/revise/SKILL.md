---
name: revise
description: "Record a correction to a standing claim — what was believed, what it rested on, and why it failed — rather than editing it away"
allowed-tools: ["Bash", "Read", "Glob", "Edit", "Write"]
argument-hint: "<term-or-claim> [--study=<dir>]"
user-invocable: true
disable-model-invocation: true
---


# /scholar:revise

Something the study asserted turned out to be wrong. This records that, rather
than quietly making it true.

User arguments: $ARGUMENTS

## Why a correction is kept

```
A RETRACTED CLAIM IS WORTH MORE WRITTEN DOWN THAN DELETED
```

Deleting it does not delete it from anyone's memory. A figure that circulated
and turned out to measure something else keeps being repeated by everyone who
read it before the fix, and they have no way to learn otherwise unless the
study says so.

The correction also carries information the replacement does not: knowing that
a plausible reading of the evidence was wrong tells the next reader which
plausible readings to distrust.

## Procedure

### 1. Establish what is being overturned

Usually from `/scholar:verify` (a citation that no longer says what it was
quoted as saying) or from `/scholar:contest` (a later round that killed an
earlier verdict). Take the claim as it currently stands, verbatim.

### 2. Append to evidence/corrections.md

```markdown
## <the term or claim>

**Was:** the claim as it stood, quoted exactly.

**Rested on:** the citation or measurement that supported it.

**Failed because:** what overturned it, cited or measured.

**Now:** the replacement claim, or a statement that the question is open.
```

Append. Never rewrite an existing correction — a correction that was itself
wrong gets its own entry beneath.

### 3. Update the study

Change the affected row in `terms.jsonl` and the affected evidence document,
then link the correction from the brief's section so a reader of the brief
meets it.

## Rules

- Quote the old claim exactly. Paraphrasing a retraction is how a retraction
  becomes a second version of the original error.
- A correction states what overturned the claim, with the same evidence tier
  the claim itself required. "This turned out to be wrong" is not a
  correction.
- Where the replacement is "we do not know", say that. An open question is a
  legitimate resting state; a confident replacement invented to fill the hole
  is not.
- Never delete a correction to tidy the document.

## Output

Open with a one-line hero (`✓ corrected <claim>` or `⚠ Blocked: <reason>`),
then exactly these sections:

1. `## Correction` — the four fields, as written to the file.
2. `## Touched` — the rows and evidence documents updated.
3. `## Downstream` — anything else in the study that rested on the same
   evidence and may now be unsupported.

End with an `AskUserQuestion` panel offering next steps (for example: verify
the downstream claims, re-run contest, stop here) — skip the panel only in
plan mode.
