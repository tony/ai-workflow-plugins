# Weave clean outputs + plan handoff

**Date**: 2026-05-17
**Status**: Approved (brainstorming complete; ready for implementation plan)
**Scope**: `plugins/weave/` (+ small updates to repo-level `CLAUDE.md`)

## Problem

The final outputs emitted by the eleven `/weave:*` commands are hard
to read and offer no actionable next step. Three observed failure
modes from a recent `/weave:review` run:

1. **Structural drift** — the chat output ad-libbed sections that
   are not in the command's prescribed output template (e.g.
   `Two blockers before merge`, `Verified against tmux source`,
   `False positives surfaced and rejected`, `Confidence evolution`,
   `Answering your four questions (a)/(b)/(c)/(d)`), while *omitting*
   sections the template requires (Scores table, Attribution).
2. **No handoff** — the report ends at `Session artifacts: …` with no
   prompt to act on the findings.
3. **Inconsistent plan-mode posture** — `/weave:plan` already enters
   plan mode in Phase 0, but the transition is silent. Other weave
   commands cannot hand their result off into plan mode at all,
   forcing the user to manually compose a follow-up `/weave:plan`
   invocation.

## Goals

- Tight, predictable final output across all weave commands.
- One unified next-step panel that lets the user act on a result
  without composing a follow-up command by hand.
- For commands whose result implies implementation work, the panel
  can take the user directly into Claude Code plan mode with a
  pre-drafted plan derived from the result.
- `/weave:plan`'s plan-mode entry becomes user-visible.

## Non-goals

- No changes to the deslop pass, repo guard, session directory
  layout, label map, scoring rubrics, model dispatch, retry logic,
  or convergence-mode definitions.
- No new weave commands.
- No marketplace-level changes outside `plugins/weave/`.

## Design

### Architecture: a shared reference, like deslop

Create `plugins/weave/references/present-results.md`. Every
command's "Present …" phase shrinks to a 5–10 line block that calls
this reference with a `RESULT_KIND` and an artifact path. The bulk
of the output template plus the next-step panel live in the
reference. Pattern mirrors `references/deslop-pass.md`.

### Reference caller contract

The caller sets these variables before invoking the reference:

| Variable | Type | Purpose |
|---|---|---|
| `RESULT_KIND` | one of: `review`, `plan`, `ask`, `brainstorm`, `brainstorm-and-refine`, `refine`, `prompt`, `architecture`, `execute`, `fix-review`, `serene-bliss` | Selects template and handoff options |
| `ARTIFACT_PATH` | absolute path (file or directory) | The desloped final artifact (single-file render) *or* the directory holding per-model outputs (multi-file render). The reference branches on `RESULT_KIND` to know which. |
| `SESSION_DIR` | absolute path | Where to write the optional plan-brief on handoff |
| `PASS_COUNT` | integer | Toggles the Confidence Evolution / Plan Evolution section |
| `IN_PLAN_MODE` | bool | True for `plan` and `fix-review`; suppresses the next-step panel |
| `MODELS` | JSON array of strings | For Attribution |
| `LABEL_MAP_PATH` | absolute path (or null) | For Attribution; null when no blind-judging label map exists (`brainstorm`, `ask` single-pass) |

### Phase A — Render output

Every template:

```markdown
# Weave <Result Kind> — <task summary>

<hero block — 1-4 lines, ⚠/✓ prefix, · bullets>

---

<RESULT_KIND-specific sections in fixed order>

---

**Session artifacts**: $SESSION_DIR
```

#### Section table per RESULT_KIND

| RESULT_KIND | Hero shape | Body sections (in this exact order) |
|---|---|---|
| `review` | `⚠ N blockers before merge` + per-blocker one-liner; `✓ No blockers` when zero | Scores · Verified Issues (Critical / Important / Suggestions, nested headings) · False Positives Rejected · Reviewer Disagreements · Critic Findings · Confidence Evolution (only when `PASS_COUNT>1`) · Summary · Attribution |
| `plan` | `Plan: N steps, M files touched` | Architecture Decision · Implementation Steps · Test Strategy · Risks and Mitigations · Scores · Verification Summary · Adjudication · Critic Findings · Plan Evolution (only when `PASS_COUNT>1`) · Attribution. Rendered into the harness plan file, not chat. |
| `ask` | One-sentence answer | Verified Answer · Evidence (`file:line` bullets) · Disagreements (only if any) · Refinement Notes (only when `PASS_COUNT>1`) · Attribution |
| `brainstorm` | `N ideas from M models` | Per-model responses (variants flattened) · Attribution |
| `brainstorm-and-refine` / `refine` / `serene-bliss` | `Refined through N passes` (suffix `(early-stop @ K)` if converged early) | Final Result · Evolution Summary · Rationale Chain · Attribution |
| `prompt` | `Winner: <model>` | Per-variant outputs · Winner Selection Rationale · Attribution |
| `architecture` | `Architecture: <chosen approach>` | Chosen Architecture · Component Map · Trade-off Analysis · Risks · Attribution |
| `execute` | `Best of N implementations` | Winning Implementation · Diff Summary · Trade-offs · Attribution |
| `fix-review` | `N fixes applied, M skipped` | Applied Fixes · Tests Added · Skipped Findings · Final Verification · Attribution |

#### Output contract (emitted into every command's render block, verbatim)

> **OUTPUT CONTRACT.** Render exactly:
>
> 1. The hero block. 1-4 lines maximum. No prose paragraphs in the hero.
> 2. The body sections above, in the listed order, with the listed level-2 headings verbatim. Skip a section only when its data is empty *and* the row is marked optional (`only when PASS_COUNT>1`, `only if any`).
> 3. No invented sections. Do not add `Verified against X`, `Answering your N questions`, `Notes`, `Observations`, `Confidence evolution` outside the prescribed slot, or any other heading not in the section table.
> 4. Prefer tables and tight bullets. Narrative paragraphs are allowed only inside `Adjudication` / `Reviewer Disagreements` and `Critic Findings`.

### Phase B — Next-step panel

Skipped when `IN_PLAN_MODE` is true.

Implemented as a single `AskUserQuestion` call. Options per
RESULT_KIND:

| RESULT_KIND | Options (in display order) |
|---|---|
| `review` | **Draft plan from findings** (active entry) · **Fix now (/weave:fix-review)** (text suggestion to spawn fix-review) · **Done** |
| `ask` | **Turn this into a plan** (active entry, answer-as-task) · **Refine the answer (/weave:refine)** · **Done** |
| `brainstorm` | **Pick one and plan it** (AskUserQuestion sub-prompt for which idea, then active entry) · **Refine further (/weave:refine)** · **Done** |
| `brainstorm-and-refine` / `serene-bliss` | **Plan the refined result** (active entry) · **Refine again (/weave:refine)** · **Done** |
| `refine` | **Plan the refined result** (active entry) · **Refine again (/weave:refine)** · **Done** |
| `architecture` | **Plan the chosen architecture** (active entry) · **Brainstorm alternatives (/weave:brainstorm)** · **Done** |
| `execute` | **Apply the winning implementation** (active entry into apply mode) · **Compare with another model (/weave:prompt)** · **Done** |
| `prompt` | **Use the winner — plan it** (active entry on winner output) · **Re-run with different variants** · **Done** |
| `fix-review` | (panel skipped — `IN_PLAN_MODE` was true for the fix-review session) |
| `plan` | (panel skipped — `IN_PLAN_MODE` was true) |

`Done` is always last and always present.

### Phase C — Active plan-mode entry

Triggered only when the user picks a `… — plan it` / `Draft plan from
findings` option in Phase B.

1. **Synthesize a plan brief.** Launch one Task sub-agent
   (`subagent_type: "general-purpose"`, `mode: "default"`). Input:
   `ARTIFACT_PATH` content + RESULT_KIND-specific extractor
   instructions. Output written to `$SESSION_DIR/handoff/plan-brief.md`.
   Extractor templates per RESULT_KIND:
   - `review` → "List each verified finding as a fix step: file,
     change, test, commit message. Order by consensus then severity."
   - `ask` → "Treat the answer as a task. List the implementation
     steps required to act on it."
   - `architecture` → "Decompose the chosen architecture into
     ordered build steps: file, change, dependencies, tests."
   - `execute` / `prompt` → "Convert the winning implementation /
     output into apply-as-PR steps: file, diff, test, commit."
   - `refine` / `brainstorm-and-refine` / `serene-bliss` → "Treat the
     refined artifact as a task. List the implementation steps."
   - `brainstorm` → "Treat the user-selected idea as a task. List
     the implementation steps."
2. **Call `EnterPlanMode`.** The user-facing approval is implicit in
   the AskUserQuestion answer, but the harness still surfaces its
   own confirmation per the tool spec.
3. **In plan mode:** the agent (a) reads
   `$SESSION_DIR/handoff/plan-brief.md`, (b) reads the codebase
   files referenced in the brief, (c) writes the plan file at the
   path supplied by Claude Code's plan-mode system message
   (`ExitPlanMode` reads the plan from that path; it takes no
   plan-content parameter), formatted as an Implementation Plan
   identical in shape to `/weave:plan` Phase 4's output template,
   (d) calls `ExitPlanMode`, which surfaces the plan for user
   approval.
4. **Headless fallback** (`EnterPlanMode` unavailable, e.g. `claude
   -p`): emit one line and stop:
   ```
   Plan mode unavailable — plan brief written to $SESSION_DIR/handoff/plan-brief.md.
   Run /weave:plan with this context to enter plan mode.
   ```

### Per-command modification template

Every command's existing "Present the *" section (currently 30–150
lines per command) is replaced with this block. `<placeholders>` are
filled per command.

```markdown
### Phase N: Present results

Read `${CLAUDE_PLUGIN_ROOT}/references/present-results.md` and apply
it with:

- `RESULT_KIND` = `<review|ask|brainstorm|...>`
- `ARTIFACT_PATH` = `$SESSION_DIR/<pass-NNNN/synthesis.md or equivalent>`
- `SESSION_DIR` = `$SESSION_DIR`
- `PASS_COUNT` = <resolved pass count>
- `IN_PLAN_MODE` = <false | true for plan/fix-review>
- `MODELS` = <models list>
- `LABEL_MAP_PATH` = `$SESSION_DIR/<pass-NNNN/label-map.json or null>`

After the reference returns, finalize the session per the existing
"Finalize Session" block (repo guard, session.json status update,
events.jsonl session_complete event, latest symlink).
```

#### Per-command parameter table

| Command | RESULT_KIND | ARTIFACT_PATH (relative to `$SESSION_DIR`) | IN_PLAN_MODE | LABEL_MAP_PATH |
|---|---|---|---|---|
| `review.md` | `review` | `pass-NNNN/synthesis.md` | false | `pass-NNNN/label-map.json` |
| `plan.md` | `plan` | `pass-NNNN/synthesis.md` (then written to harness plan file) | true | `pass-NNNN/label-map.json` |
| `ask.md` | `ask` | `pass-NNNN/synthesis.md` | false | `pass-NNNN/label-map.json` (when multi-pass) or null |
| `brainstorm.md` | `brainstorm` | `outputs/` directory containing `claude-vN.md` / `gemini-vN.md` / `gpt-vN.md` per variant | false | null |
| `brainstorm-and-refine.md` | `brainstorm-and-refine` | `pass-<final>/woven.md` | false | `pass-NNNN/label-map.json` |
| `refine.md` | `refine` | `pass-<final>/woven.md` | false | `pass-NNNN/label-map.json` |
| `serene-bliss.md` | `serene-bliss` | `pass-<final>/woven.md` | false | `pass-NNNN/label-map.json` |
| `prompt.md` | `prompt` | `outputs/` directory containing per-variant files; the reference also reads `winner.md` from the same dir | false | `pass-NNNN/label-map.json` |
| `architecture.md` | `architecture` | `pass-NNNN/synthesis.md` | false | `pass-NNNN/label-map.json` |
| `execute.md` | `execute` | `pass-NNNN/synthesis.md`; the reference also reads worktree refs from `worktrees.json` in the same dir for the "Apply the winning implementation" handoff | false | `pass-NNNN/label-map.json` |
| `fix-review.md` | `fix-review` | `phase-4-summary.md` | true | null |

### `/weave:plan` user-visible transition

Two new emitted lines, no logic changes:

- After Phase 0's `EnterPlanMode` call:
  `Plan mode active — drafting implementation plan…`
- After Phase 4's plan-file write:
  `Plan ready for review.`

The harness surfaces the plan-approval UI on its own after the
second line.

## Convention update (CLAUDE.md)

Add a sibling "Output Contract Convention" subsection beside the
existing "Orchestration Plan Convention". Three rules, codifying
the design for future weave-like plugins:

- Final user-facing output of a command must declare its sections
  in a fixed order, in a portable reference if shared across commands.
- A hero block is allowed at the top (1-4 lines, no prose
  paragraphs).
- After the prescribed sections, end with an interactive next-step
  panel where the user can act on the result without composing a
  follow-up command. Skip the panel only when the command is
  already running inside plan mode.

## Files touched

**Created** (2):
- `plugins/weave/references/present-results.md`
- `plugins/weave/docs/specs/2026-05-17-clean-output-and-plan-handoff.md` (this file)

**Modified** (13):
- `plugins/weave/commands/architecture.md`
- `plugins/weave/commands/ask.md`
- `plugins/weave/commands/brainstorm-and-refine.md`
- `plugins/weave/commands/brainstorm.md`
- `plugins/weave/commands/execute.md`
- `plugins/weave/commands/fix-review.md` (set `IN_PLAN_MODE=true`)
- `plugins/weave/commands/plan.md` (set `IN_PLAN_MODE=true`; add the two transition lines)
- `plugins/weave/commands/prompt.md`
- `plugins/weave/commands/refine.md`
- `plugins/weave/commands/review.md`
- `plugins/weave/commands/serene-bliss.md`
- `plugins/weave/README.md` (point at the new reference)
- `CLAUDE.md` (add Output Contract Convention subsection)

## Validation plan

The implementation plan should produce one atomic commit per
phase boundary:

1. New reference file + CLAUDE.md convention update + README pointer.
2. `plan.md` and `fix-review.md` retrofitted with `IN_PLAN_MODE=true`
   (no behavior change; just the new call pattern).
3. Each non-plan-mode command retrofitted (one commit per file, or
   one commit per logical group — implementation plan decides).
4. End-to-end manual validation: run `/weave:review` against a
   small change, verify hero + strict sections + next-step panel
   appear; pick "Draft plan from findings"; verify plan mode
   activates with a populated plan file.

No automated tests in this repo; validation is manual per the
existing plugin testing posture.

## Resolved questions

All three architectural axes were decided during the brainstorming
session that produced this spec:

- Where the cleanup lives → **shared reference file**
  (`references/present-results.md`).
- How plan-mode entry works from non-plan commands → **active
  in-session entry** (write brief, call `EnterPlanMode`).
- Output strictness → **hero block + strict prescribed sections,
  no invented additions**.

## Open questions

None. The implementation plan can proceed.
