# Provenance and Anti-Inflation Contract

Shared contract for every `/business:*` command. Every figure in
every artifact — interim package, report, chat output — obeys this
file. A figure that cannot satisfy it does not ship.

## The four tags

Every figure carries exactly one tag:

- **MEASURED** — read from instrumented data. Cite the
  source-manifest entry in the run's `sources.md` by its stable name.
- **DERIVED** — computed from measured inputs. Show the formula
  inline next to the figure; each input keeps its own tag.
- **BENCHMARKED** — from an external source. Citation plus retrieval
  date. Vendor sources carry an additional `(vendor)` flag and are
  never used as internal inputs — `evidence.md` holds the vetted
  table and the usage rules.
- **ESTIMATED** — an assumption. Rationale plus confidence
  (high | medium | low); the entry lives in `assumptions.yaml` and
  the figure cites its assumption id.

### Inline rendering

Write the tag with the figure, followed by what the tag requires:

> Median review latency fell from 26 h to 9 h (MEASURED:
> sources.md `gh-review-latency`, 2026-04-01..2026-06-30, n=41 PRs).

> Net per-instance saving 22 min, IQR 9–41 min (DERIVED:
> S_inst = (t_manual − (t_ai + t_verify)) − (p_fail × t_rework),
> inputs MEASURED per measurements/timing.md).

Tier-3 artifacts keep the tag and the method phrase but strip
internal source refs — `audiences.md` defines per-tier rendering.

## No currency, ever

A hard contract, not a preference:

- No currency symbols, currency codes, or currency units. No prices,
  no cost-in-money, no dollar ROI — anywhere, in any artifact or
  command output.
- The only value units: engineer-hours (and engineer-days or
  engineer-weeks), cycle-time deltas, throughput, quality and
  stability rates, and capacity language ("engineer-days per
  quarter").
- If a source artifact contains money figures, do not reproduce
  them: restate the claim in time or capacity units, or omit it. If
  asked to convert savings into money, decline and cite this
  contract.
- Money-adjacent vocabulary counts as currency: "ROI", "dollar",
  "cost savings", "monetize", "payback" in money terms. Do not use
  them even in negations ("no ROI claim is made") — name the time or
  capacity claim instead.

## Anti-inflation rules

- Never output a figure you cannot tag. Unknown → write "unknown"
  and state what data would resolve it. No invented or
  pleasing-round numbers; no interpolation of unmeasured values.
- Every point estimate carries a range or interval.
- Every ratio and percentage states its denominator.
- Every "hours saved" states across how many engineers and over what
  period.
- Pinned date ranges everywhere: explicit start and end dates,
  stated wherever the data appears.
- Deterministic seeds for any resampling (bootstrap, Monte Carlo);
  record the seed next to the result.
- Failed and abandoned AI runs count their time. Verification and
  review time is inside the task boundary — a saving net of neither
  is untaggable.
- Skill build and maintenance cost is amortized into net savings,
  never dropped.
- Adoption and realization multipliers are explicit inputs, strictly
  below 1.0; refuse defaults of 1.0 (`measurement.md` defines both).
