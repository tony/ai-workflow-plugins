# Weave present-results — unified output rendering and next-step panel

A shared rendering layer for all `/weave:*` commands. Consolidates
output presentation into one place: a hero block, prescribed body
sections per result kind, an attribution footer, and an interactive
next-step panel with active plan-mode handoff.

---

## Caller contract

The caller sets these variables before invoking this reference:

| Variable | Type | Purpose |
|---|---|---|
| RESULT_KIND | one of: review, plan, ask, brainstorm, brainstorm-and-refine, refine, prompt, architecture, execute, fix-review, serene-bliss | Selects template and handoff options |
| ARTIFACT_PATH | absolute path | Desloped final artifact (single file) or directory of per-model outputs |
| SESSION_DIR | absolute path | Session directory for auxiliary writes |
| PASS_COUNT | integer | Toggles Evolution/Confidence sections |
| IN_PLAN_MODE | boolean | True for plan and fix-review; suppresses next-step panel |
| MODELS | JSON array of strings | For Attribution |
| LABEL_MAP_PATH | absolute path or null | For Attribution; null when no label map exists |

---

## Phase A — Render output

### Step 1: Read the artifact

- When RESULT_KIND is `brainstorm` or `prompt`: ARTIFACT_PATH is a
  **directory**. List its contents to find per-model output files.
- All other RESULT_KINDs: ARTIFACT_PATH is a **single markdown file**.
  Read it.

### Step 2: Compose the hero block

Look up RESULT_KIND in this table. Fill placeholders from the artifact
content. Emit 1–4 lines.

| RESULT_KIND | Hero shape |
|---|---|
| review | `⚠ N blockers before merge` + per-blocker one-liner; `✓ No blockers` when zero |
| plan | `Plan: N steps, M files touched` |
| ask | One-sentence answer |
| brainstorm | `N ideas from M models` |
| brainstorm-and-refine | `Refined through N passes` (suffix `(early-stop @ K)` if converged early) |
| refine | `Refined through N passes` (suffix `(early-stop @ K)` if converged early) |
| serene-bliss | `Refined through N passes` (suffix `(early-stop @ K)` if converged early) |
| prompt | `Winner: <model>` |
| architecture | `Architecture: <chosen approach>` |
| execute | `Best of N implementations` |
| fix-review | `N fixes applied, M skipped` |

### Step 3: Render body sections

Look up RESULT_KIND in this table. Render sections **in this exact
order** using the artifact content. Skip a section only when its
condition is false or its data is empty AND the section is marked
optional.

| RESULT_KIND | Body sections (in this exact order) |
|---|---|
| review | Scores · Verified Issues (Critical / Important / Suggestions) · False Positives Rejected · Reviewer Disagreements · Critic Findings · Confidence Evolution (only when PASS_COUNT > 1) · Summary · Attribution |
| plan | Architecture Decision · Implementation Steps · Test Strategy · Risks and Mitigations · Scores · Verification Summary · Adjudication · Critic Findings · Plan Evolution (only when PASS_COUNT > 1) · Attribution. Rendered into the harness plan file, not chat. |
| ask | Verified Answer · Evidence (file:line bullets) · Disagreements (only if any) · Refinement Notes (only when PASS_COUNT > 1) · Attribution |
| brainstorm | Per-model responses (variants flattened) · Attribution |
| brainstorm-and-refine | Final Result · Evolution Summary · Rationale Chain · Attribution |
| refine | Final Result · Evolution Summary · Rationale Chain · Attribution |
| serene-bliss | Final Result · Evolution Summary · Rationale Chain · Attribution |
| prompt | Per-variant outputs · Winner Selection Rationale · Attribution |
| architecture | Chosen Architecture · Component Map · Trade-off Analysis · Risks · Attribution |
| execute | Winning Implementation · Diff Summary · Trade-offs · Attribution |
| fix-review | Applied Fixes · Tests Added · Skipped Findings · Final Verification · Attribution |

### Output contract

> **OUTPUT CONTRACT.** Render exactly:
>
> 1. The hero block. 1–4 lines maximum. No prose paragraphs in the hero.
> 2. The body sections above, in the listed order, with the listed
>    level-2 headings verbatim. Skip a section only when its data is
>    empty *and* the row is marked optional (`only when PASS_COUNT > 1`,
>    `only if any`).
> 3. No invented sections. Do not add `Verified against X`, `Answering
>    your N questions`, `Notes`, `Observations`, `Confidence evolution`
>    outside the prescribed slot, or any other heading not in the section
>    table.
> 4. Prefer tables and tight bullets. Narrative paragraphs are allowed
>    only inside `Adjudication` / `Reviewer Disagreements` and
>    `Critic Findings`.

### Step 4: Render Attribution

Shared across all RESULT_KINDs. Render as the final body section:

- If LABEL_MAP_PATH is set and file exists: read the label map and show
  the blind-label → model-name mapping.
- List models from MODELS.
- End with: `**Session artifacts**: $SESSION_DIR`

---

## Phase B — Next-step panel

When IN_PLAN_MODE is true, skip Phase B entirely.

### Step 1: Present options

Call `AskUserQuestion` with options from this table:

| RESULT_KIND | Options (in display order) |
|---|---|
| review | **Draft plan from findings** · **Fix now** (suggest `/weave:fix-review`) · **Done** |
| ask | **Turn this into a plan** · **Refine the answer** (suggest `/weave:refine`) · **Done** |
| brainstorm | **Pick one and plan it** (sub-prompt for which idea, then plan) · **Refine further** (suggest `/weave:refine`) · **Done** |
| brainstorm-and-refine | **Plan the refined result** · **Refine again** (suggest `/weave:refine`) · **Done** |
| serene-bliss | **Plan the refined result** · **Refine again** (suggest `/weave:refine`) · **Done** |
| refine | **Plan the refined result** · **Refine again** (suggest `/weave:refine`) · **Done** |
| architecture | **Plan the chosen architecture** · **Brainstorm alternatives** (suggest `/weave:brainstorm`) · **Done** |
| execute | **Apply the winning implementation** · **Compare with another model** (suggest `/weave:prompt`) · **Done** |
| prompt | **Use the winner — plan it** · **Re-run with different variants** · **Done** |

### Step 2: Route user choice

- **Done** → return. Session finalization is the caller's
  responsibility.
- Text-suggestion options (Fix now, Refine, Brainstorm alternatives,
  Compare, Re-run) → emit a one-line suggestion with the command name
  and return.
- **Plan-entry options** (Draft plan, Turn into plan, Plan the refined
  result, Plan the chosen architecture, Pick one and plan it, Use the
  winner — plan it, Apply the winning implementation) → proceed to
  Phase C.

---

## Phase C — Active plan-mode entry

Triggered only when the user picks a plan-entry option in Phase B.

### Step 1: Synthesize plan brief

Launch one Task sub-agent (`subagent_type: "general-purpose"`,
`mode: "default"`). Input: ARTIFACT_PATH content + the extractor
instruction from this table. Output written to
`$SESSION_DIR/handoff/plan-brief.md`.

| RESULT_KIND | Extractor instruction |
|---|---|
| review | List each verified finding as a fix step: file, change, test, commit message. Order by consensus then severity. |
| ask | Treat the answer as a task. List the implementation steps required to act on it. |
| brainstorm | Treat the user-selected idea as a task. List the implementation steps. |
| brainstorm-and-refine / refine / serene-bliss | Treat the refined artifact as a task. List the implementation steps. |
| architecture | Decompose the chosen architecture into ordered build steps: file, change, dependencies, tests. |
| execute / prompt | Convert the winning implementation / output into apply-as-PR steps: file, diff, test, commit. |

### Step 2: Enter plan mode

Call `EnterPlanMode`. If unavailable, go to headless fallback.

### Step 3: Write plan file

In plan mode: read `$SESSION_DIR/handoff/plan-brief.md`, read the
codebase files referenced in the brief, write the plan file at the path
supplied by Claude Code's plan-mode system message. Format as an
Implementation Plan (same shape as `/weave:plan` Phase 4 output). Call
`ExitPlanMode`.

### Headless fallback

If `EnterPlanMode` is unavailable (e.g. `claude -p`), emit one line
and stop:

```
Plan mode unavailable — plan brief written to $SESSION_DIR/handoff/plan-brief.md.
Run /weave:plan with this context to enter plan mode.
```

---

## Failure modes

| Mode | Behaviour |
|---|---|
| ARTIFACT_PATH missing or empty | Emit error line; skip rendering, skip panel. |
| LABEL_MAP_PATH set but file missing | Omit label mapping from Attribution; note "label map unavailable". |
| AskUserQuestion unavailable | Skip Phase B; emit "Session complete" line. |
| EnterPlanMode unavailable | Headless fallback (Phase C). |
| Task unavailable (Phase C Step 1) | Emit plan-brief stub with ARTIFACT_PATH pointer; proceed to headless fallback. |
| Plan-brief generation fails | Emit error; do not enter plan mode. |
