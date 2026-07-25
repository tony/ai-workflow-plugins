---
name: business-case-study-internal
description: >-
  Write the tier-2 internal case study — situation, what was built, tagged
  outcomes with denominators, lessons, replication guide for other teams
allowed-tools: ["Bash", "Read", "Write", "Grep", "AskUserQuestion"]
metadata:
  argument-hint: "[run directory]"
  source: "plugins/business/commands/case-study-internal.md"
---

# Internal Case Study (tier 2)

Turn a run package into a narrative case study for internal
circulation: what happened, what it measured, what other teams can
take from it. Tier 2: internal team and repo names allowed;
individuals anonymized to roles. Value is engineer-hours, cycle
time, and capacity; never money.

Read `references/interim-format.md` first — it
defines run location and the completeness gate. Defer these rendering
references until the gate passes; a refused render never loads them:

- `references/provenance.md` — tag rendering,
  anti-inflation rules, the no-currency contract.
- `references/audiences.md` — the tier-2
  contract.

User arguments: $ARGUMENTS

## Context

Recent runs — run this command and read the output:

```bash
sh -c 'ls -dt "$HOME"/Documents/*/business/ /mnt/c/Users/*/Documents/*/business/ 2>/dev/null' | head -5 | grep . || echo "(no runs found)"
```

## Procedure

### 1. Locate the run

Use the `$ARGUMENTS` path if given, else the newest run per
`interim-format.md`. Confirm the choice with the user.

### 2. Completeness gate

Run the completeness gate from `interim-format.md`. Refuse to render
from an incomplete package; list what is missing and stop.

### 3. Render the case study

Read the deferred references above, then write
`<run>/reports/case-study-internal.md` as a narrative in this
fixed order:

1. **Situation** — the team, the recurring task, why it cost enough
   to act on.
2. **What was built** — the skill or workflow, its build time
   (tagged), and who maintains it.
3. **Measured outcomes** — every figure tagged, denominator stated,
   window pinned. Include the costs: verification time, failed
   runs, maintenance.
4. **Lessons** — what worked, what did not, what the team would do
   differently.
5. **How other teams can replicate** — prerequisites, the expected
   ramp (and the excluded novelty window), and where results are
   likely to differ.

Anonymize individuals to roles. Team and repo names stay.

## Output

Open with a one-line hero (`✓ Case study: <one-line outcome with
tag>`, `✓ Evidence report: <supported claim, unknowns named>`, or
`⚠ Refused: <reason>`), then exactly these sections:

1. `## Run` — the run chosen and its pinned window.
2. `## Gate` — the completeness result.
3. `## Report` — where it was written and the headline outcome.

End with an `ask-user-choice` panel: write the public case study
next, adjust the narrative, or stop. Skip the panel in plan mode or
when running non-interactively.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
