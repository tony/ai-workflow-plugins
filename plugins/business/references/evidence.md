# External Evidence Table

The BENCHMARKED sources for triangulating internal claims. An
internal savings claim must land inside a defensible external range
or explicitly explain its divergence. Defensible range: **−19% to
+56%**. Realistic field cluster: **~10–26%**.

## Studies

- **METR RCT** (Jul 2025, arXiv 2507.09089) — 16 experienced OSS
  devs, 246 real tasks on mature repos: **19% slower** with
  early-2025 AI, while believing +20%. Highest rigor, narrow
  setting; METR's Feb 2026 update labels the result historical.
- **Cui et al. three-firm RCT** (SSRN 4945566; Management Science) —
  4,867 devs: **+26.08%** completed tasks (SE 10.3%),
  treatment-on-the-treated; gains concentrated in junior and
  short-tenure devs; pooled estimate including an abandoned
  experiment 21.34%.
- **Google internal RCT** (2024, arXiv 2410.12944) — ~96 engineers,
  enterprise task: **~21% faster**, wide CI.
- **Peng et al.** (2023, arXiv 2302.06590) — 95 devs, synthetic
  greenfield HTTP server: **+55.8%** (CI [21%, 89%]). Lab upper
  bound; do not use as a field expectation.
- **Bain Technology Report 2025** — **10–15%** with basic
  assistants, 25–30% only with end-to-end process change; coding is
  only 25–35% of idea-to-launch. Consultancy/survey — flag as such.
- **DORA 2024** (~3,000 respondents) — 25% more AI adoption ↔ −1.5%
  delivery throughput, −7.2% stability. **DORA 2025** (~5,000): "AI
  doesn't fix a team; it amplifies what's already there"; adds
  rework rate as a key metric; 30% trust AI output little or not at
  all.
- **Faros telemetry 2025/2026** (vendor) — individuals +21% tasks /
  +98% merged PRs, but review time +91%, PR size +154%, bugs per dev
  +9%; 2026: review time 5×, 31% of PRs merged unreviewed; org-level
  delivery flat. Direction informative; magnitudes vendor-sourced.
- **CodeRabbit 2025–2026** (vendor) — 470 PRs, AI-coauthored code
  1.7× issues per PR. Directional only.

## Usage rules

- Cite a BENCHMARKED figure with its study label above and a
  retrieval date.
- Never import a vendor headline as an internal savings-rate input.
  Cite it alongside your own MEASURED number, flagged `(vendor)`.
- Vendor magnitudes are directional context only; internal inputs
  come from your own instruments or from the non-vendor studies,
  clearly cited.

## Triangulation procedure

For each headline claim:

1. State the internal figure with its tag and denominator.
2. Place it against the defensible range. Inside the range: note the
   nearest comparable study and how the settings differ.
3. Outside the range: either remove the claim, or keep it with an
   explicit methodology defense — what makes this setting different,
   and which rung of the counterfactual ladder
   (`measurement.md`) the comparison sits on.
4. Record the triangulation outcome next to the claim so a reviewer
   can retrace it.
