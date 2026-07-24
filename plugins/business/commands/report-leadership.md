---
description: Render the tier-0 leadership report from a business run — SCQA with the answer first, action-titled exhibits, explicit value build, the conservative number committed
argument-hint: "[run directory]"
allowed-tools: ["Bash", "Read", "Write", "Grep", "Glob", "AskUserQuestion"]
---

# Leadership Report (tier 0)

Render the full-detail leadership report from a run package. Tier 0
withholds nothing: names, raw links, registers inline. It still
never contains money — value is engineer-hours, cycle time, and
capacity.

Read these first; they bind every step:

- `${CLAUDE_PLUGIN_ROOT}/references/interim-format.md` — locating
  the run and the completeness gate.
- `${CLAUDE_PLUGIN_ROOT}/references/provenance.md` — tag rendering,
  anti-inflation rules, the no-currency contract.
- `${CLAUDE_PLUGIN_ROOT}/references/measurement.md` — the value
  build, break-even, guardrails, the counterfactual ladder.
- `${CLAUDE_PLUGIN_ROOT}/references/evidence.md` — external context
  for the pre-answered objections.
- `${CLAUDE_PLUGIN_ROOT}/references/audiences.md` — the tier-0
  contract.

User arguments: $ARGUMENTS

## Context

Recent runs:
`!ls -dt ~/Documents/*/business/ /mnt/c/Users/*/Documents/*/business/ 2>/dev/null | head -5 || echo "(no runs found)"`

## Procedure

### 1. Locate the run

Use the `$ARGUMENTS` path if given, else the newest run per
`interim-format.md`. Confirm the choice with the user before
rendering.

### 2. Completeness gate

Run the completeness gate from `interim-format.md`. Refuse to render
from a package with untagged figures or missing register fields —
list exactly what is missing and stop.

### 3. Render the report

Write `<run>/reports/leadership.md` with this fixed structure:

1. **SCQA opening** — Situation, Complication, Question, Answer,
   with the Answer stated first.
2. **Exhibits** — action titles: every exhibit title is a
   full-sentence takeaway; one message per exhibit; a source, query,
   and date-range note under each.
3. **Value build** — every multiplier explicit, per the chains in
   `measurement.md`; break-even stated.
4. **Scenarios** — the conservative scenario is THE committed
   number; base and upside appear as context, never as the headline.
5. **Assumptions register and data dictionary** — appendix, inline
   from `assumptions.yaml` plus definitions of every metric used.
6. **Known limitations** — each with a confidence label.
7. **What would flip this conclusion** — the input thresholds at
   which the answer changes.
8. **Pre-answered objections** — at minimum: how do you know the
   skill caused this (name the counterfactual rung); does the
   savings rate survive the verification tax; who maintains the
   skill.

## Output

Open with a one-line hero (`✓ Leadership report: <committed figure
with tag>` or `⚠ Refused: <what the gate found>`), then exactly
these sections:

1. `## Run` — the run chosen and its pinned window.
2. `## Gate` — the completeness result.
3. `## Report` — where it was written, the committed number, and the
   strongest limitation.

End with an `AskUserQuestion` panel: render the org-wide projection
next, adjust assumptions and re-render, or stop. Skip the panel in
plan mode or when running non-interactively.
