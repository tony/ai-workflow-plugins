---
description: Write the tier-3 public case study — hard sanitization, every headline claim triangulated against external evidence, candid limitations mandatory
argument-hint: "[run directory]"
allowed-tools: ["Bash", "Read", "Write", "Grep", "AskUserQuestion"]
---

# Public Case Study (tier 3)

Turn a run package into a case study fit for external publication.
Tier 3 is the hard sanitization tier: no internal identifiers of any
kind, aggregates and ranges only, every headline claim triangulated.
Value is engineer-hours, cycle time, and capacity; never money.

Read `${CLAUDE_PLUGIN_ROOT}/references/interim-format.md` first — it
defines run location and the completeness gate. Defer these rendering
references until the gate passes; a refused render never loads them:

- `${CLAUDE_PLUGIN_ROOT}/references/provenance.md` — tag rendering,
  anti-inflation rules, the no-currency contract.
- `${CLAUDE_PLUGIN_ROOT}/references/evidence.md` — the external
  evidence table and the triangulation procedure.
- `${CLAUDE_PLUGIN_ROOT}/references/audiences.md` — the tier-3
  contract and the final checklist.

User arguments: $ARGUMENTS

## Context

Recent runs:
`!sh -c 'ls -dt "$HOME"/Documents/*/business/ /mnt/c/Users/*/Documents/*/business/ 2>/dev/null' | head -5 | grep . || echo "(no runs found)"`

## Procedure

### 1. Locate the run

Use the `$ARGUMENTS` path if given, else the newest run per
`interim-format.md`. Confirm the choice with the user.

### 2. Completeness gate

Run the completeness gate from `interim-format.md`. Refuse to render
from an incomplete package; list what is missing and stop.

### 3. Draft under the tier-3 contract

Read the deferred references above, then draft the case study in
this order — sanitized from the first word,
not sanitized afterwards:

1. **Context** — the kind of team and the kind of task, described
   without identifying anyone or anything internal.
2. **Approach** — what was built, in transferable terms.
3. **Results** — aggregates and ranges only; every figure tagged as
   tag plus method phrase per `audiences.md`; denominators and
   pinned-window lengths stated; honest rounding.
4. **Limitations** — candid and mandatory: measurement weaknesses,
   the counterfactual rung, what was not measured. Credibility is
   the PR asset.

### 4. Triangulate every headline claim

Apply the triangulation procedure from `evidence.md` to each
headline claim. A claim outside the defensible external range is
removed or kept only with an explicit methodology defense. Record
each outcome.

### 5. Final checklist pass

Run the tier-3 final checklist from `audiences.md` over the finished
draft as an explicit pass, item by item. Fix every hit, then write
`<run>/reports/case-study-public.md`.

## Output

Open with a one-line hero (`✓ Public case study: <headline with
tag>`, `✓ Evidence report: <supported claim, unknowns named>`, or
`⚠ Refused: <reason>`), then exactly these sections:

1. `## Run` — the run chosen and its pinned window.
2. `## Gate` — the completeness result.
3. `## Sanitization` — the checklist results item by item, and the
   triangulation outcome per headline claim.
4. `## Report` — where it was written and the headline.

End with an `AskUserQuestion` panel: derive the PR release next,
tighten a claim, or stop. Skip the panel in plan mode or when
running non-interactively.
