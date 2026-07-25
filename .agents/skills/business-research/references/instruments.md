# Instrument discovery and collection queries

How this skill probes what exists and queries it without
sampling, truncating, or mislabeling. Discovery is always probe-based:
never infer availability from convention or from the project's
ecosystem.

## Discovery: probe, record, classify

For each instrument class, run a cheap probe, record the command and
its result in the run README, and classify the instrument available
or unavailable.

### git

Probe each candidate repository:

```console
git -C <repo> log -1 --format=%H
```

Record the git version for the manifest:

```console
git --version
```

### gh

Probe authentication:

```console
gh auth status
```

Probe rate-limit headroom before any bulk collection:

```console
gh api rate_limit
```

If the remaining GraphQL budget cannot cover the planned pagination,
say so in the plan and shrink the window — never sample silently.

### Ticket trackers

Look for MCP servers or CLIs for Jira, Linear, or whatever the team
uses — check the host's MCP listing and the project's
AGENTS.md/CLAUDE.md for tracker mentions. Nothing found →
unavailable.

### CI telemetry, session logs, time tracking

CI: the forge's checks API (`gh api` on GitHub) or the CI system's
own CLI. Session/usage logs and time-tracking data: only from
exports the user provides. Each absent source is recorded
unavailable, not worked around.

## Collection discipline

- Pin every query to the run's date range; put the range inside the
  query itself wherever the API allows.
- State the timezone convention once in the run README and hold it:
  forge timestamps are UTC; git author/committer dates are local —
  convert to UTC before windowing, and note the offset. State the
  cohort rule per metric in `sources.md` (for example: PR cycle time
  by mergedAt-in-window; review latency by createdAt-in-window).
- Snapshot each response to `raw/` and add its `sources.md` entry
  before computing anything from it.
- Prefer GraphQL over the Search API for PR and issue queries —
  search results truncate and drift; GraphQL with cursor pagination
  is reliable. Paginate to exhaustion or record the cutoff
  explicitly.
- GraphQL event-count trap: `timelineItems(...).totalCount` ignores
  the `itemTypes` filter and returns the count of all timeline
  items. Use `filteredCount` for reopened/closed event counts, and
  sanity-check any surprising count against one item fetched raw.
- Prove absences with snapshots, not assertions: a "0 reverts" or
  "no AI-attribution markers" claim gets a `raw/` snapshot of the
  full query output that shows the zero, so the absence is MEASURED.
- Compute distributions client-side from the raw snapshots: the API
  returns events; medians, IQRs, and intervals are computed locally
  per `measurement.md`.
- A snapshot found defective is never edited: add a superseding
  snapshot and record the supersession in the run README and
  `sources.md`.

## Collection targets

### Cycle times and review latency

Per PR or task in the window: open-to-merge time, first-review
latency, review rounds. Segment AI-assisted vs not only when an
honest marker exists (skill telemetry, labels, commit trailers). No
marker → the segmentation is unknown; do not guess from prose style.

### Rework signals

Reverts (revert markers in `git log` plus forge revert links),
reopened issues and PRs — across all items, not only merged ones —
CI failure and retry rates, PR-size drift across the window.

### Per-task timing

Manual baseline vs AI-assisted duration. The task boundary includes
verification and review time and the time of failed or abandoned AI
runs. Timing counts as MEASURED only when both sides come from
recorded timestamps; recalled durations are ESTIMATED with low
confidence and say so.

### Adoption

Distinct users who actually invoked the skill in the window, vs the
eligible population. License-holding and active use are different
numbers; report both or mark the missing one unknown.

### Build and maintenance time

Reconstruct from history — commits, PRs, and doc edits on the skill
itself — when possible. Reconstruction yields MEASURED counts and
calendar spans only; engineer-hours inferred from spans are DERIVED
with the inference method stated, or ESTIMATED with rationale and a
named owner in the assumptions register. Commit timestamps alone
never yield MEASURED engineer-hours.
