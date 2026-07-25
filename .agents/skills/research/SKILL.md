---
name: research
description: >-
  Collect business-value data for an AI skill or workflow into a
  provenance-tagged run package — instrument discovery, pinned-window
  collection, immutable raw snapshots
allowed-tools: ["Bash", "Read", "Write", "Grep", "AskUserQuestion", "EnterPlanMode"]
metadata:
  argument-hint: "[skill or workflow to measure] [date range, e.g. 2026-04-01..2026-06-30]"
  source: "plugins/business/commands/research.md"
---

# Business Research

Collect the data behind a business-value claim for an AI skill or
agentic workflow — productivity, time saved, quality, capacity,
delivery outcomes — into the interim run package the report commands
render from. Value is stated in engineer-hours, cycle time,
throughput, quality, and capacity. Never money.

Read these first; they bind every step:

- `references/interim-format.md` — the run
  package layout and where runs live.
- `references/provenance.md` — the four tags,
  the anti-inflation rules, and the no-currency contract.
- `references/measurement.md` — what the data
  must feed: the saving formulas, statistics discipline, the
  counterfactual ladder, and the quality guardrails.
- `references/instruments.md` — per-instrument
  probes, collection discipline (timezone and cohort conventions,
  the GraphQL filteredCount trap, absence snapshots), and the
  collection targets in query-ready form.

User arguments: $ARGUMENTS

## Context

Today — run this command and read the output:

```bash
date +%F
```

Kernel (WSL detection) — run this command and read the output:

```bash
grep -qi microsoft /proc/version 2>/dev/null && echo "WSL" || echo "(not WSL)"
```

Instruments on PATH — run this command and read the output:

```bash
for c in git gh jq; do command -v $c >/dev/null && echo "$c: available" || echo "$c: unavailable"; done
```

gh — run this command and read the output:

```bash
gh auth status 2>&1 | head -3
```

## Procedure

### 1. Scope and orchestration plan

Present an orchestration plan before touching disk: what will be
measured, over what pinned date range, with which instruments, to
which output directory. Enter plan mode if the host supports it —
Claude Code `EnterPlanMode`; Cursor, Codex, or Gemini via `/plan` or
Shift+Tab; otherwise present the plan as plain text and pause. Ask
where to write the run, defaulting per the location rules in
`interim-format.md` (Documents root; on WSL prefer the Windows
Documents folder when detected). Wait for confirmation.

### 2. Instrument discovery — never assumption

Probe what is actually available using the per-instrument probes in
`instruments.md`; never assume an instrument exists. Candidates
(illustrative, not a fixed list): `git` history; `gh` (verify auth
and rate limits before relying on it); ticket-tracker MCPs or CLIs
such as Jira or Linear; CI telemetry; session logs; time-tracking
exports. Record every instrument as available or
unavailable in the run README. Data an unavailable instrument would
have provided is recorded as `unknown` — never fabricated, never
silently skipped.

### 3. Collect

For each available instrument, run pinned-window queries per the
collection discipline in `instruments.md` and snapshot raw output
into `raw/` before deriving anything. Targets — collect what the
instruments support and record the rest as unknown:

- Task and PR cycle times, review latency. Prefer GraphQL over the
  Search API for reliability; paginate; compute distributions
  client-side.
- Rework signals: reverts, reopened items, CI failure and retry
  rates, PR-size drift.
- Per-task timing where measurable: manual baseline vs AI-assisted
  duration, including verification/review time and failed-run time.
- Adoption signals: distinct users of the skill vs the eligible
  population — record license-holding and active use as separate
  numbers.
- Skill build and maintenance time: reconstructed from history if
  possible, else ESTIMATED with rationale.

### 4. Write the package

Emit the full interim format from `interim-format.md`: run README,
source manifest with verbatim queries, assumptions register, raw
snapshots, per-topic measurements, and `findings.md`. Every figure
tagged; every unknown listed with what data would resolve it.

## Rules

- Raw snapshots are immutable once written.
- An unavailable instrument yields `unknown`, not an estimate —
  unless the user supplies an assumption, which is registered as
  ESTIMATED with rationale and owner.
- No currency in any output, per `provenance.md`.

## Output

Open with a one-line hero (`✓ Run written: <run path>, window
<start>..<end>` or `⚠ Halted: <reason>`), then exactly these
sections:

1. `## Scope` — what was measured and the pinned window.
2. `## Instruments` — available vs unavailable, and what each
   unavailable one leaves unknown.
3. `## Collected` — per instrument: what landed in `raw/` and
   `measurements/`.
4. `## Package` — the run path, count of registered assumptions, and
   the open unknowns.

End with an `ask-user-choice` panel: generate a report (ask which
tier), collect more, or stop. Skip the panel in plan mode or when
running non-interactively.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
