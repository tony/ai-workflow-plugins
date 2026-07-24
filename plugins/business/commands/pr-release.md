---
description: Write the tier-3 one-page announcement — figures drawn only from the public case study, denominators attached, limitations one-liner included
argument-hint: "[run directory]"
allowed-tools: ["Bash", "Read", "Write", "Grep", "Glob", "AskUserQuestion"]
---

# PR Release (tier 3)

Derive a one-page announcement from the public case study — and only
from it. The public case study is the sanitization firewall: this
command introduces no figure that is not already in it and re-derives
nothing from the interim package. Value is engineer-hours, cycle
time, and capacity; never money.

Read these first; they bind every step:

- `${CLAUDE_PLUGIN_ROOT}/references/interim-format.md` — locating
  the run.
- `${CLAUDE_PLUGIN_ROOT}/references/provenance.md` — tag rendering,
  denominators, the no-currency contract.
- `${CLAUDE_PLUGIN_ROOT}/references/audiences.md` — the tier-3
  contract.

User arguments: $ARGUMENTS

## Context

Recent runs:
`!ls -dt ~/Documents/*/business/ /mnt/c/Users/*/Documents/*/business/ 2>/dev/null | head -5 || echo "(no runs found)"`

## Procedure

### 1. Locate the run

Use the `$ARGUMENTS` path if given, else the newest run per
`interim-format.md`. Confirm the choice with the user.

### 2. Locate the firewall

Check for `<run>/reports/case-study-public.md`. If it is missing,
ask via `AskUserQuestion` whether to run
`/business:case-study-public` now or stop — never draft the release
straight from the interim package.

### 3. Compose one page

From the public case study only:

1. **Headline result** — the case study's headline, with its tag
   and range.
2. **Supporting numbers** — two or three, each with its denominator
   and window length, exactly as they appear in the case study.
3. **Quote placeholder** — clearly marked as a placeholder, with
   attribution left blank for the user to fill.
4. **Limitations one-liner** — a single candid sentence distilled
   from the case study's limitations section.

Write `<run>/reports/pr-release.md`.

## Rules

- Every figure must be traceable to the public case study verbatim
  or by stated rounding; if a wanted figure is not there, the answer
  is to extend the case study first, not to reach into the run.
- The tier-3 contract in `audiences.md` applies in full — no
  internal identifiers, no currency.

## Output

Open with a one-line hero (`✓ PR release: <headline>` or
`⚠ Blocked: <reason>`), then exactly these sections:

1. `## Run` — the run chosen.
2. `## Firewall` — the public case study used, and confirmation
   that every figure traces to it.
3. `## Report` — where it was written and the headline.

End with an `AskUserQuestion` panel: revise the headline, regenerate
after updating the case study, or stop. Skip the panel in plan mode
or when running non-interactively.
