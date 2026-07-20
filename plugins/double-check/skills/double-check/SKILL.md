---
name: double-check
description: >-
  Use whenever the user asks to double-check, cross-check, verify,
  recheck, sanity-check, or confirm prior analysis or results —
  including "are you sure", "are you confident", "is this true",
  "still true?", "prove it", "triple check", "check against" some
  artifact, "look again", "repeat the analysis", or "repeat your
  findings in full". Re-derives the answer from source artifacts and
  returns it standalone in the original request's structure — never
  a revision log of the prior turn. Also invoke before re-running
  any analysis whose output the user has already seen once. To
  repair a chat where a diff-shaped answer already happened, use
  /double-check:align.
user-invocable: true
---

# Double-check

Re-verify by re-deriving. The deliverable is the verified answer,
not a record of how it differs from your last one.

Read `${CLAUDE_PLUGIN_ROOT}/references/verification-contract.md`
before responding — it is the contract this skill enforces.

## Why the obvious response is wrong

Your prior answer sits in the transcript, so re-checking it feels
like editing it: keep the numbering, mark each item *holds* /
*overstated*, report what changed. But transcript order is not
user-adopted state. The user usually has not internalized the prior
answer — often the double-check request is itself the signal that
they never committed to it. A verdict list against text they never
held is unreadable, and inherited scaffolding hides whatever the
first pass missed entirely.

## Steps

1. **Recover the request, not the answer.** From the conversation,
   take the original question, its constraints, and any narrowing the
   user added since. Prior answers of yours are untrusted scratch —
   good for recalling which sources exist, never citable as evidence.
2. **Re-derive from source.** Re-open the artifacts — files, issues,
   specs, data — and rebuild each claim from what they actually say.
   Verification is performed, not asserted: cite what you re-opened
   and what it said, or the command you ran and its output. "Verified
   earlier in this conversation" anchors a claim to transcript
   position and does not count.
3. **Rebuild the structure.** Outline from the source material and
   the request, not from your prior answer's item numbers. A claim
   that no longer earns a place simply does not appear; a missing
   area simply appears.
4. **State confidence on claims.** "Weak evidence — X only follows
   if Y", never "X was overstated".
5. **Check for adopted state.** If the user acted on a prior claim —
   committed, filed, sent, built on it — name that correction
   explicitly, once, briefly. Otherwise the prior turn is not a
   baseline and does not exist in your output.

## Output shape

Same shape the original request implied, as if answering for the
first time. No "what changed" section, no verdict legend, no
*as noted above*. A reader who never saw the first answer must lose
nothing.
