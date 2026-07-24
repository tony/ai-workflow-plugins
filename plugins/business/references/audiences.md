# Audience Sensitivity Ladder

Four disclosure tiers, from tier 0 (internal leadership, full
detail) to tier 3 (fully external). The binding rule: **an artifact
may never contain detail its tier's contract excludes, even though
the run directory has it.** Sanitization is a property of the
artifact, not of the data.

## When the package holds no committable savings figure

A complete package may still contain no defensible savings number —
early instrumentation, unknowns blocking `S_inst`, no counterfactual
yet. That is not a rendering failure at any tier: render an evidence
report. The answer or headline states plainly what the data does and
does not yet support; where a committed number would go, name the
open unknowns and the data that would resolve them. Refusal is for
gate failures, never for honest absence.

## Tier 0 — leadership

Command: `/business:report-leadership`.

Full detail: names, raw links, registers inline. Provenance tags
render with complete source refs — manifest entry names, file paths,
assumption ids.

## Tier 1 — org-wide

Command: `/business:report-org-wide`.

Team-level aggregates only; no individual names anywhere. Internal
team and system names allowed. Ends with a plain-language summary
readable by the whole company — no methodology jargon, figures still
tagged and true.

## Tier 2 — internal case study

Command: `/business:case-study-internal`.

Internal team and repo names allowed; individuals anonymized to
roles ("a senior engineer", never a name). Tags with internal source
refs allowed.

## Tier 3 — public

Commands: `/business:case-study-public`, `/business:pr-release`.

Hard sanitization contract:

- No organization, repository, or person names; no ticket IDs; no
  internal URLs; no internal or local file paths.
- Aggregates and ranges only. Round to honest precision — a
  number's precision must not exceed what its interval supports.
- Every headline claim triangulated per `evidence.md`.
- A candid limitations section is mandatory — credibility is the PR
  asset.
- Provenance tags remain on every figure, rendered as tag plus
  method phrase ("MEASURED over a 12-week window, n=41 PRs") with
  internal source refs stripped.

## Tier-3 final checklist

`/business:case-study-public` runs this as an explicit final pass
over the finished draft. `/business:pr-release` inherits the result
by sourcing figures only from the public case study.

1. Scan the draft for organization, repository, and person names,
   ticket IDs, internal URLs, and internal or local paths — remove
   every hit.
2. Confirm every figure is an aggregate or a range, rounded to
   honest precision.
3. Confirm every headline claim passed triangulation or carries its
   methodology defense.
4. Confirm the limitations section is present and candid.
5. Confirm no currency appears (`provenance.md` bans it at every
   tier; re-check here because external text travels furthest).

Report the checklist results in the command output — pass per item,
with what was removed or reworded.

## Firewall sweep

`/business:pr-release` treats the public case study as its
sanitization firewall — and verifies it rather than trusting it.
Before deriving the announcement, sweep the located case study:

- No organization, repository, team, person, or ticket identifiers;
  no internal URLs or paths.
- Aggregates and ranges only; figures carry provenance tags and
  denominators.
- A limitations section exists.
- No currency symbols or money-adjacent terms.

Any failure means the case study is regenerated via
`/business:case-study-public`, never patched around in the release.
Report the sweep result in the command output.
