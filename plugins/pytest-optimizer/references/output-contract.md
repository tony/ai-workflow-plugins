# Output contract

Every phase command prints its result in this fixed shape. Verbatim level-2
headings, declared order, no invented sections. This keeps four separate commands
feeling like one pipeline and makes the JSON memory legible at a glance.

## Shape

1. **Hero block** (1–4 lines, optional). A `⚠`/`✓` prefix or a one-line summary.
   No prose paragraphs. Examples:
   - `✓ scan complete — baseline 12.5s ± 0.15s (MAD), 7 hypotheses, 0 suite edits`
   - `⚠ 1 hypothesis dropped at the safety gate (xdist over shared SQLite)`
2. **Body sections** in the order each command declares (below). Skip a section
   only when it is genuinely empty, and say so in one line rather than inventing
   filler.
3. **Next-step panel** — an `AskUserQuestion` so the user can act without composing
   a follow-up command. Skip the panel only when the command is already running
   inside plan mode (where the plan itself is the decision point).

## Per-command body sections

**`00-scan`**

- `## Environment` — pytest + plugin versions, gated-off capabilities, resolved
  test command, memory dir.
- `## Baseline` — median wall-time, noise band (MAD), trust floor.
- `## Slowest tests` — top `call` rows with root-cause notes.
- `## Slowest fixtures` — top `setup`/`teardown` rows; note shared-scope
  attribution.
- `## Hypotheses` — candidate table: id, heuristic, goal(s), evidence, prior
  risk/effort.

**`01-benchmark`**

- `## Validated` — candidates whose measured delta cleared the noise band and
  passed the gates (id, median delta, confidence).
- `## Rejected` — within-noise or gate-failing candidates, each with the reason.
- `## Safety-gate results` — order-independence and collection-determinism
  outcomes.

**`02-plan`**

- `## Ranked plan` — ordered commits with score breakdown, target files, draft
  subject, verify command.
- `## Dropped at the gate` — candidates below `safety 0.4` or `impact 0`, with the
  prerequisite refactor surfaced separately.
- `## Ordering rationale` — why safety-gate fixes and typings precede scope and
  parallelism.

**`03-execute`**

- `## Applied` — per item: commit SHA, measured verify result.
- `## Skipped` — per item: revert reason (failed green-verify, conflict).
- `## Result` — post-suite wall-time vs `baseline.json`, total recovered.

## Next-step panel

After the body (outside plan mode), offer the natural continuations, e.g.:

- `00-scan` → "Benchmark the hypotheses now", "Narrow scope", "Stop".
- `01-benchmark` → "Build the plan", "Re-benchmark a subset", "Stop".
- `02-plan` → "Execute the plan", "Cap the number of commits", "Edit the plan".
- `03-execute` → "Re-scan for a second pass", "Scaffold the cache/timing plugin",
  "Stop".
