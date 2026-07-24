---
description: Render the tier-1 org-wide projection — explicit adoption and realization inputs, scenario spread, sensitivity ranking, plain-language company close
argument-hint: "[run directory]"
allowed-tools: ["Bash", "Read", "Write", "Grep", "AskUserQuestion"]
---

# Org-Wide Report (tier 1)

Project a measured per-instance saving across the organization and
close with a summary the whole company can read. Tier 1: team-level
aggregates only, no individual names anywhere. Value is
engineer-hours and capacity; never money.

Read `${CLAUDE_PLUGIN_ROOT}/references/interim-format.md` first — it
defines run location and the completeness gate. Defer these rendering
references until the gate passes; a refused render never loads them:

- `${CLAUDE_PLUGIN_ROOT}/references/provenance.md` — tag rendering,
  anti-inflation rules, the no-currency contract.
- `${CLAUDE_PLUGIN_ROOT}/references/measurement.md` — the
  projection chain `V * F * t * s * a * r`, the population segments,
  and the rule refusing 1.0 defaults.
- `${CLAUDE_PLUGIN_ROOT}/references/audiences.md` — the tier-1
  contract.

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

### 3. Secure the multipliers

Read the deferred references above. Then read adoption `a` and
realization `r` from `assumptions.yaml`. If
either is absent, ask the user via `AskUserQuestion` — explain what
each means per `measurement.md` — and append the answer to the
register as an ESTIMATED entry with rationale and owner. Both are
strictly below 1.0. Refuse to proceed with a default of 1.0 for
either.

### 4. Render the report

Write `<run>/reports/org-wide.md` with this fixed structure:

1. **Bottom-up build** — the full chain
   `Annual_hours_saved = V * F * t * s * a * r`, every factor shown
   with its own tag; the population segmented addressable ⊃ served ⊃
   realized, all three reported.
2. **Scenarios** — conservative, base, upside, with the differing
   assumptions listed per scenario.
3. **Sensitivity** — one-way ranking: which single input moves the
   outcome most, in order.
4. **What has to be true** — break-even framing: the values the
   inputs must reach for the projection to hold.
5. **Plain-language summary** — for the whole company: no
   methodology jargon, no formula notation; figures still tagged and
   true.

Team-level aggregates only. If any measurement is per-person, roll
it up before it appears here.

## Output

Open with a one-line hero (`✓ Org-wide projection: <conservative
figure with tag>`, `✓ Evidence report: <supported claim, unknowns
named>`, or `⚠ Refused: <reason>`), then exactly these sections:

1. `## Run` — the run chosen and its pinned window.
2. `## Gate` — the completeness result and the `a`/`r` values used,
   with their register ids.
3. `## Report` — where it was written, the conservative projection,
   and the most sensitive input.

End with an `AskUserQuestion` panel: write an internal case study
next, revisit an assumption, or stop. Skip the panel in plan mode or
when running non-interactively.
