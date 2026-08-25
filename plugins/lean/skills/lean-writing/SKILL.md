---
name: lean-writing
description: "Use when commit messages or prose must stay tight: cut filler, padding, preamble, AI fluff, and stories of attempts; lead with current results."
---

# Lean writing

Produce tight, slop-free prose and code the first time, so nothing has
to be cleaned up later.

## Core moves

- Lead with the result. Cut preamble ("Certainly!", "Here is…") and
  postamble ("Let me know if…").
- State current truth, not the journey. No diary of what changed, what
  you tried, or how you got here — the artifact is the freshest take,
  not a log.
- Reuse before you create. Search for an existing file, component,
  helper, API, test, or doc section before adding another.
- Smallest coherent change. Keep unrelated cleanup out of it.
- Preserve references when editing. Never orphan a link, citation,
  anchor, warning, or a comment that documents an invariant or "why".
- Prefer prose and nested sections over tables. Reach for a table only
  when the data is genuinely matrix-shaped and stable.
- One command per code block; keep comments outside the fence.
- No coded rule labels (`[R1]`, `Option B`) in text a human reads.

## Calibrate to the project

Read `./AGENTS.md` and `./CLAUDE.md`. When they define a slop rubric or
a house voice, that governs — match it.

## Comments

Code comments and docstrings answer to
`../../references/comment-policy.md`: one or two lines, only for what
the code cannot say, rationale in the commit message. To trim comments
that already exist, use `/lean:trim-comments`.

## Deeper catalog

See `../../references/lean-rubric.md` for the full
signature list, preservation rules, and the "add a table / file / test"
decision blocks.

## While tightening, don't add slop

Replacements must be concrete and shorter than what they replace. Never
narrate your own edits ("I tightened…", "cleaned up…"). Fix the text,
not a description of the fix.
