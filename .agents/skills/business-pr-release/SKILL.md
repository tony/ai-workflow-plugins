---
name: business-pr-release
description: >-
  Write the tier-3 one-page announcement — figures drawn only from the
  public case study, denominators attached, limitations one-liner included
allowed-tools: ["Bash", "Read", "Write", "Grep", "AskUserQuestion"]
metadata:
  argument-hint: "[run directory]"
  source: "plugins/business/commands/pr-release.md"
---

# PR Release (tier 3)

Derive a one-page announcement from the public case study — and only
from it. The public case study is the sanitization firewall: this
command introduces no figure that is not already in it and re-derives
nothing from the interim package. Value is engineer-hours, cycle
time, and capacity; never money.

Read `references/interim-format.md` first — it
defines run location. Defer these until the firewall (the public case
study) is located:

- `references/provenance.md` — tag rendering,
  denominators, the no-currency contract.
- `references/audiences.md` — the tier-3
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

### 2. Locate and verify the firewall

Check for `<run>/reports/case-study-public.md`. If it is missing,
ask via `ask-user-choice` whether to run
the `business-case-study-public` skill now or stop — never draft the release
straight from the interim package. If present, run the firewall
sweep from `audiences.md`; a sweep failure routes back to
the `business-case-study-public` skill, never into hand-patching here.

### 3. Compose one page

Read the deferred references above. From the public case study only:

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

Open with a one-line hero (`✓ PR release: <headline>`,
`✓ Evidence report: <supported claim, unknowns named>`, or
`⚠ Blocked: <reason>`), then exactly these sections:

1. `## Run` — the run chosen.
2. `## Firewall` — the public case study used, and confirmation
   that every figure traces to it.
3. `## Report` — where it was written and the headline.

End with an `ask-user-choice` panel: revise the headline, regenerate
after updating the case study, or stop. Skip the panel in plan mode
or when running non-interactively.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
