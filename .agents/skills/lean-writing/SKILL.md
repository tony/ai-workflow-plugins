---
name: lean-writing
description: >-
  Use while producing or editing any prose or code — commit messages, PR and
  ticket bodies, docs, comments, or implementation — to keep the first draft
  tight and slop-free: lead with the result, state current truth over the
  journey, reuse before creating, and preserve references when editing.
  Guidance only; it never edits files. To clean slop out of existing files
  in place, use the `tighten` skill; for repo-wide or branch-scoped commit
  cleanup, use the `scan` skill or the `deslop` skill.
allowed-tools: ["Read", "Grep", "Glob"]
metadata:
  source: "plugins/lean/skills/lean-writing/SKILL.md"
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

## Deeper catalog

See `references/lean-rubric.md` for the full
signature list, preservation rules, and the "add a table / file / test"
decision blocks.

## While tightening, don't add slop

Replacements must be concrete and shorter than what they replace. Never
narrate your own edits ("I tightened…", "cleaned up…"). Fix the text,
not a description of the fix.


## Portability notes

- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
