---
description: >-
  Use when a verification pass already came back as a diff against
  the agent's prior turn — verdict lists like "overstated" / "still
  holds", "what I changed" sections — and you want the analysis
  restated whole. Triggers on "align", "restate cleanly", "say how it
  is", "stop correcting yourself", "I never read the first version",
  or "give me the final version". Rebuilds the answer from source as
  a standalone artifact; with an argument, re-anchors on a narrower
  question and drops the old scaffolding entirely.
argument-hint: "[topic or question to re-anchor on]"
---

# `/double-check:align`

Recovery for a broken double-check. The chat currently holds a
revision log — verdicts about prior claims, deltas against text the
user never read. Replace it with the analysis itself.

Read `${CLAUDE_PLUGIN_ROOT}/references/verification-contract.md`
first — it is the contract this command restores.

## `$ARGUMENTS`

- Empty — re-anchor on the subject of the most recent analysis
  thread, at its original scope.
- A topic or question — re-anchor on that instead. Narrowing is a
  feature: it discards the earlier answer's scaffolding, which is
  what lets omitted items finally surface.

## Steps

1. **Recover the request.** From the conversation, reconstruct the
   original question and every constraint the user has added since —
   including corrections they made that you agreed with. User turns
   are binding context; your own answer turns are not.
2. **Quarantine prior answers.** Everything you previously concluded
   is untrusted until re-verified against source. Do not reuse prior
   numbering, category names, or verdict framing.
3. **Re-derive and restate.** Re-open the source artifacts and write
   the full analysis, standalone, in the shape the original request
   implied. Every claim stated positively and in full — no verdict
   shorthand, no "as noted above", no delta table.
4. **Weakness inline.** If a claim is weak, say why it is weak.
   Never say it was previously stated differently.

## What this does not do

- Reference, summarize, or grade the earlier response — the user did
  not read it and will not.
- Edit files or commit — output is conversation only.
- Answer a different question than the one recovered or given —
  losing focus is the failure this command repairs.
