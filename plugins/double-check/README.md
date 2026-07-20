# double-check

Make verification requests return the re-derived answer instead of a
diff against the agent's prior turn.

Ask an agent to "double check" an analysis and it usually replies
with a revision log — *Overstated*, *Does not hold*, *still holds* —
a delta against a message you may never have read. This plugin names
that failure (temporal-baseline misalignment producing
revision-history leakage) and ships both directions of the fix:
prevention when the request arrives, recovery when the diff already
happened.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install double-check@ai-workflow-plugins
```

## Components

### `double-check` (skill)

Loads when you ask to double-check, cross-check, verify, re-examine,
or confirm prior analysis — "are you sure", "check again", "is that
right". The agent re-derives from source artifacts and answers
standalone in the original request's structure: no verdicts about
its own prior claims, no "what changed" section, no inherited
numbering that hides omissions.

### `/double-check:align` (command)

Recovery, for when the diff-shaped answer already landed. Restates
the current best analysis whole, rebuilt from source, without
referencing or grading the earlier response. With an argument it
re-anchors on a narrower question and drops the old scaffolding —
which is what lets missing items finally surface.

## The contract

Both components enforce `references/verification-contract.md`:

- The deliverable of a verification request is the re-derived
  answer, not a record of what changed.
- The baseline is the source material, not the transcript.
- Confidence belongs on the claim ("weak evidence — X only follows
  if Y"), never on the revision ("X was overstated").
- One exception: if you acted on a prior claim — committed it, filed
  it, sent it — the correction is stated explicitly, once.

The reference ends with a short fragment you can paste into any
project's AGENTS.md to make the rule ambient without installing the
plugin.

## Relationship to `lean`

`lean` keeps drafts free of journey-narration in artifacts; this
plugin applies the same discipline to conversation turns, where the
"journey" is the agent's own earlier answers. Explicit comparison
requests ("diff your two proposals") are out of scope for both —
those legitimately want a delta.

## Prerequisites

None.
