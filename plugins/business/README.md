# business

Measure and report the business value of AI skills and agentic
workflows — productivity, time saved, quality, capacity, delivery
outcomes.

Never money. No currency symbols or units, no cost-in-money, no
dollar ROI, in any artifact or command output. Value is stated in
engineer-hours, cycle-time deltas, throughput, quality and stability
rates, and capacity language ("engineer-days per quarter"). Every
figure carries a provenance tag (MEASURED, DERIVED, BENCHMARKED,
ESTIMATED), a range or interval, and a denominator; unknowns are
written as unknown, never invented.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install business@ai-workflow-plugins
```

## Workflow

`/business:research` collects data into a run directory (default
`~/Documents/<date>/business/`; on WSL, the Windows Documents
folder) — instrument probing, pinned-window queries, immutable raw
snapshots, a source manifest, and an assumptions register. The five
report commands render from that package at increasing distance from
the raw data, each bound to a disclosure tier: a report may never
contain detail its tier excludes, even though the run directory has
it.

## Components

### `/business:research` (command)

Collect the data. Presents an orchestration plan (plan mode where
the host supports it), probes which instruments actually exist —
git, gh, ticket trackers, CI telemetry, session logs — and records
the unavailable ones as unknown rather than guessing. Collects cycle
times, review latency, rework signals, paired task timings
(verification and failed-run time included), adoption counts, and
skill build/maintenance time, then writes the tagged interim
package.

### `/business:report-leadership` (command, tier 0)

Full-detail leadership report: SCQA opening with the answer first,
exhibits with full-sentence takeaway titles, the value build with
every multiplier explicit, the conservative scenario as the
committed number, assumptions register and data dictionary inline,
limitations with confidence labels, flip thresholds, and pre-answered
objections.

### `/business:report-org-wide` (command, tier 1)

Org-wide projection through `V * F * t * s * a * r` with adoption
and realization as required explicit inputs (refuses 1.0 defaults),
population segmented addressable ⊃ served ⊃ realized, scenario
spread, one-way sensitivity ranking, break-even framing, and a
plain-language close for the whole company. Team aggregates only.

### `/business:case-study-internal` (command, tier 2)

Narrative case study for internal circulation: situation, what was
built, tagged outcomes with denominators, lessons including the
costs, and a replication guide. Team and repo names allowed;
individuals anonymized to roles.

### `/business:case-study-public` (command, tier 3)

External case study under the hard sanitization contract: no
org/repo/person names, ticket IDs, or internal URLs and paths;
aggregates and ranges at honest precision; every headline claim
triangulated against the external evidence table; a candid
limitations section; an explicit final checklist pass before
writing.

### `/business:pr-release` (command, tier 3)

One-page announcement derived only from the public case study — the
sanitization firewall. Headline result, two to three supporting
numbers with denominators, quote placeholder, limitations one-liner.

## Shared references

All commands read from `references/`:

- `provenance.md` — the four tags, anti-inflation rules, and the
  no-currency contract.
- `measurement.md` — saving and projection formulas, statistics
  discipline (medians + IQR, bootstrapped intervals, DIRECTIONAL
  labeling for small n), the counterfactual quality ladder, and the
  quality guardrails that keep "time saved" honest.
- `evidence.md` — the external study table (METR, Cui et al.,
  Google, Peng et al., Bain, DORA, plus vendor telemetry flagged as
  such) and the triangulation procedure.
- `instruments.md` — per-instrument probes and pinned-window
  collection discipline: timezone and cohort conventions, GraphQL
  pagination and the filteredCount trap, absence snapshots.
- `interim-format.md` — the run-directory layout, run location
  rules, and the completeness gate report commands enforce.
- `audiences.md` — the four-tier disclosure ladder and the tier-3
  sanitization checklist.

## Prerequisites

- `git` for history-based collection.
- `gh` CLI, authenticated, for PR and review telemetry (optional —
  its absence is recorded, not worked around).
- Any ticket-tracker MCPs or CLIs the project already uses are
  probed at runtime; none are required.
