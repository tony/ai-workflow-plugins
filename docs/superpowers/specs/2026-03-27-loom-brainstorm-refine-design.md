# Loom Brainstorm & Refine — Design Spec

## Context

The existing loom plugin provides multi-model orchestration (Claude, Gemini, GPT)
for tasks like asking questions, planning, executing, and reviewing code. All
existing commands use a **targeted conflict resolution** approach for multi-pass
refinement — subsequent passes only address unresolved conflicts, critic findings,
and low-confidence scores.

This design introduces a fundamentally different multi-pass pattern: **expansive
weaving**. Each refinement pass is a full judge-pick-best-incorporate-strengths-
address-weaknesses cycle. This enables iterative creative refinement where the
output genuinely improves with each pass rather than just resolving disputes.

## Components

Three new loom components, each implemented as a command + skill wrapper pair:

| Component | Command | Skill | Purpose |
|-----------|---------|-------|---------|
| brainstorm | `commands/brainstorm.md` | `skills/brainstorm/SKILL.md` | Independent originals from each model |
| refine | `commands/refine.md` | `skills/refine/SKILL.md` | Iterative improvement of a single artifact |
| brainstorm-and-refine | `commands/brainstorm-and-refine.md` | `skills/brainstorm-and-refine/SKILL.md` | Full pipeline: generate then refine |

All commands follow the existing loom plugin conventions: context packets, model
detection with `agent` CLI fallback, session artifact persistence to `$AI_AIP_ROOT`,
timeout handling, and retry/fallback protocols.

---

## 1. `loom:brainstorm`

### Purpose

Generate independent original responses from each model. No synthesis, no
judging — present all raw responses for the user to inspect.

### Flags

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--variants=N` | 1-3 | 1 | Independent prompts per model |
| `--timeout=N\|none` | seconds or `none` | 450s | External model timeout |
| `--mode=fast\|balanced\|deep` | preset | `balanced` | Timeout multiplier only |
| `--preamble=...` | text | built-in | Override variant preamble |

### Variant Differentiation

Each variant gets a distinct creative-direction preamble to prevent anchoring:

| Variant | Default Preamble |
|---------|-----------------|
| 1 | "Take the most conventional, well-established approach." |
| 2 | "Take an unconventional or creative approach. Challenge the obvious solution." |
| 3 | "Take a contrarian approach. Question the premise itself." |

Users can override with `--preamble='focus on performance'` etc. Overrides
apply to all variants — variant numbering still differentiates.

**No role preambles** (Maintainer/Skeptic/Builder) — brainstorming is about
original thinking, not evaluation lenses. Variant preambles replace them.

### Phases

1. **Gather Context** — Read CLAUDE.md/AGENTS.md, determine trunk, capture
   prompt from `$ARGUMENTS`. Build context packet using `rg`/`ag`/`fd` if
   available for faster file discovery.

2. **Configuration & Model Detection** — Parse flags, detect `gemini`/`codex`/
   `agent` CLIs (with `agent` fallback for each), detect `timeout`/`gtimeout`,
   detect `rg`/`ag`/`fd`. Initialize session directory at
   `$AI_AIP_ROOT/repos/$REPO_DIR/sessions/brainstorm/$SESSION_ID/`.

3. **Generate Originals** — For each model x variant, dispatch independently
   in parallel. Each gets: variant preamble + user prompt + context packet.
   Claude variants via Task agents, external via CLI with `agent` fallback.

4. **Present All Originals** — Display each response labeled by model and
   variant number. No scoring, no ranking. Persist to session artifacts.

### Output Format

```markdown
# Brainstorm Results

**Prompt**: <user's prompt>
**Models**: Claude, Gemini, GPT | **Variants per model**: N

---

## Claude -- Variant 1 (Conventional)
<response>

## Claude -- Variant 2 (Creative)
<response>

## Gemini -- Variant 1 (Conventional)
<response>

## Gemini -- Variant 2 (Creative)
<response>

## GPT -- Variant 1 (Conventional)
<response>

## GPT -- Variant 2 (Creative)
<response>

---

**Session artifacts**: $SESSION_DIR
```

### Session Artifacts

```
$SESSION_DIR/
  session.json
  events.jsonl
  metadata.md
  context-packet.md
  outputs/
    claude-v1.md
    claude-v2.md
    gemini-v1.md
    gemini-v2.md
    gpt-v1.md
    gpt-v2.md
  stderr/
    gemini-v1.txt
    gpt-v1.txt
    ...
  prompt.md
```

---

## 2. `loom:refine`

### Purpose

Take a single artifact (inline text or file path) and iteratively improve it
across models over N passes. Each pass is a full judge-weave-incorporate cycle.

### Input Detection

`$ARGUMENTS` is auto-detected:
- If it resolves to an existing file path: read the file as the artifact
- Otherwise: treat as inline text

### Flags

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--passes=N` | 1-5 | 2 | Number of refinement passes |
| `--timeout=N\|none` | seconds or `none` | 450s | External model timeout |
| `--mode=fast\|balanced\|deep` | preset | `balanced` | fast=1, balanced=2, deep=3 passes |
| `--judge=host\|round-robin` | judge mode | `host` | Who judges each pass |

### Phases

1. **Gather Context** — Same as brainstorm. Read the artifact. Build context
   packet with `rg`/`ag`/`fd`.

2. **Configuration & Model Detection** — Same pattern with `agent` fallback.

3. **Pass 1: Independent Critique & Improvement** — All models receive the
   original artifact and produce:
   - Their critique (what's strong, what's weak)
   - Their improved version
   - Their rationale for changes

4. **Pass 2+: Judge-Weave-Refine Cycle** — For each subsequent pass:

   a. **Judge** (host agent by default): Read all responses from prior pass.
      Score each version 0-10. Pick the best.

   b. **Analyze runners-up**: Identify specific strengths in non-winning
      versions that the winner lacks.

   c. **Weave**: Produce a revised version that starts from the winner,
      incorporates identified strengths from runners-up, and addresses
      weaknesses.

   d. **Distribute**: Send the woven version back to ALL models for another
      round of critique & improvement. Each model receives:
      - The woven version
      - The judge's rationale
      - The strengths incorporated and weaknesses addressed
      - Instructions: "Improve this further. Produce your critique and
        improved version."

   e. **Early-stop**: If the judge finds no material improvement between
      passes (woven version receives same or lower score than prior pass
      winner, no new strengths identified), stop early and report convergence.

5. **Present Final Result** — Full rationale chain showing evolution.

### Output Format (Per Pass)

```markdown
## Pass N

### Judge's Assessment
**Winner**: <model> (score: X/10)
**Rationale**: Why this was the best version

### Strengths from Runners-Up
- From <model>: <specific strength to incorporate>
- From <model>: <specific strength to incorporate>

### Weaknesses to Address
- <weakness in winner>

### Woven Result
<the refined version incorporating all improvements>

### Expert Rationales
- **Claude**: <why they made their changes>
- **Gemini**: <why they made their changes>
- **GPT**: <why they made their changes>
```

### Final Output

```markdown
# Refinement Complete

**Original artifact**: <first 100 chars or file path>
**Passes completed**: N (of M requested)
**Convergence**: <early-stop or completed all passes>

## Evolution Summary
- Pass 1: <what changed and why>
- Pass 2: <what changed and why>
- ...

## Final Result
<the refined artifact>

## Full Rationale Chain
<collapsed per-pass details as above>

**Session artifacts**: $SESSION_DIR
```

### Session Artifacts

```
$SESSION_DIR/
  session.json
  events.jsonl
  metadata.md
  context-packet.md
  original.md          # the input artifact
  pass-0001/
    prompt.md
    outputs/
      claude.md        # critique + improved version + rationale
      gemini.md
      gpt.md
    stderr/
    judge.md           # judge's assessment, scores, winner
    woven.md           # woven result after incorporating strengths
  pass-0002/
    prompt.md          # includes woven result + judge rationale
    outputs/
      claude.md
      gemini.md
      gpt.md
    stderr/
    judge.md
    woven.md
  ...
```

---

## 3. `loom:brainstorm-and-refine`

### Purpose

Full pipeline: brainstorm independent originals, then iteratively refine them
through judge-weave-incorporate cycles.

### Flags

Union of brainstorm and refine flags:

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--variants=N` | 1-3 | 1 | Brainstorm variants per model |
| `--passes=N` | 1-5 | 2 | Refinement passes |
| `--timeout=N\|none` | seconds or `none` | 450s | External model timeout |
| `--mode=fast\|balanced\|deep` | preset | `balanced` | Affects both phases |
| `--judge=host\|round-robin` | judge mode | `host` | Who judges refinement |
| `--preamble=...` | text | built-in | Override variant preamble |

### Phases

1. **Brainstorm Phase** — Run the full brainstorm workflow. Present all
   originals to the user.

2. **Transition Gate** — Always ask the user which originals should enter
   refinement. Options:
   - "All of them" (default)
   - Select specific ones by label (e.g., "Claude-v1, GPT-v2")
   - "None -- satisfied with brainstorm results" (exit early)

3. **Refine Phase** — Selected originals become the initial pool for pass 1.
   Instead of all models improving a single artifact, the judge evaluates
   the brainstorm originals as pass-0 candidates. From pass 1 onward,
   follows the standard refine cycle (judge-weave-distribute-improve).

4. **Present Final Result** — Full rationale chain from brainstorm originals
   through each refinement pass.

### Session Artifacts

```
$SESSION_DIR/
  session.json
  events.jsonl
  metadata.md
  context-packet.md
  brainstorm/
    prompt.md
    outputs/
      claude-v1.md, claude-v2.md
      gemini-v1.md, gemini-v2.md
      gpt-v1.md, gpt-v2.md
    stderr/
  refine/
    pass-0001/        # judge picks best from brainstorm originals
      judge.md
      woven.md
      outputs/        # all models improve the woven result
        claude.md
        gemini.md
        gpt.md
      stderr/
    pass-0002/
      ...
```

---

## 4. Skill Wrappers

Each command gets a thin SKILL.md for auto-discovery. Skills describe
triggering conditions only — execution delegates to the command.

### `skills/brainstorm/SKILL.md`

```yaml
---
name: brainstorm
description: >-
  Use when the user wants multiple independent ideas, alternatives, or
  approaches from different AI models for a creative prompt, design question,
  or open-ended problem
user-invocable: true
argument-hint: "<prompt> [--variants=N]"
---
```

### `skills/refine/SKILL.md`

```yaml
---
name: refine
description: >-
  Use when the user has an existing draft, text, code, or artifact and wants
  it iteratively improved through multi-model critique and weaving across
  multiple passes
user-invocable: true
argument-hint: "<text or file path> [--passes=N]"
---
```

### `skills/brainstorm-and-refine/SKILL.md`

```yaml
---
name: brainstorm-and-refine
description: >-
  Use when the user wants to generate multiple original ideas then iteratively
  judge, weave, and refine them into the best possible result across multiple
  passes
user-invocable: true
argument-hint: "<prompt> [--variants=N] [--passes=N]"
---
```

---

## 5. Tool Detection

### Search Tools

Detect and use faster search tools when available for context-packet building:

| Tool | Purpose | Fallback |
|------|---------|----------|
| `rg` (ripgrep) | Content search | `ag` then `grep` |
| `ag` (silver searcher) | Content search | `grep` |
| `fd` | File discovery | `find` |

Detection runs in parallel alongside model detection:

```bash
command -v rg >/dev/null 2>&1 && echo "rg:available" || echo "rg:missing"
command -v ag >/dev/null 2>&1 && echo "ag:available" || echo "ag:missing"
command -v fd >/dev/null 2>&1 && echo "fd:available" || echo "fd:missing"
```

### Model Detection

Same as existing loom commands:

| Slot | Native CLI | Agent fallback |
|------|-----------|----------------|
| Claude | Always available (host) | -- |
| Gemini | `gemini` binary | `agent --model gemini-3.1-pro` |
| GPT | `codex` binary | `agent --model gpt-5.4-high` |

---

## 6. Key Design Decisions

1. **No role preambles in brainstorm** — Maintainer/Skeptic/Builder lenses are
   evaluation-oriented. Brainstorming needs creative-direction preambles
   (conventional/creative/contrarian) instead.

2. **Expansive weaving vs targeted conflict resolution** — Each refine pass is
   a FULL re-evaluation cycle, not a narrow conflict-only pass. This is the
   core differentiator from existing loom multi-pass.

3. **All models re-improve each pass** — The woven result goes back to all
   models, not just the judge. This preserves multi-perspective diversity
   through every refinement pass.

4. **Host agent judges by default** — The agent running the skill (typically
   Claude) judges. `--judge=round-robin` rotates judging across available models
   (Claude → Gemini → GPT). External model judges produce scores and pick
   winners; the host agent always weaves.

5. **Always-ask transition gate** — In brainstorm-and-refine, the user always
   chooses which originals enter refinement. No auto-proceed.

6. **Full rationale chain** — Every pass preserves each expert's reasoning,
   the judge's assessment, strengths incorporated, and weaknesses addressed.
   Fully traceable evolution.

---

## 7. Files to Create

```
plugins/loom/
  commands/
    brainstorm.md              # new
    refine.md                  # new
    brainstorm-and-refine.md   # new
  skills/
    brainstorm/
      SKILL.md                 # new
    refine/
      SKILL.md                 # new
    brainstorm-and-refine/
      SKILL.md                 # new
```

Update:
- `plugins/loom/.claude-plugin/plugin.json` — update description if needed
- `plugins/loom/README.md` — add documentation for new commands/skills
- `.claude-plugin/marketplace.json` — verify loom plugin entry still accurate

---

## 8. Verification

1. **Skill discovery**: Install the plugin, verify `/loom:brainstorm`,
   `/loom:refine`, `/loom:brainstorm-and-refine` appear in command list
   and skills are auto-triggered by matching descriptions.

2. **Brainstorm**: Run `/loom:brainstorm "design a CLI flag parser"
   --variants=2`. Verify 6 independent responses (3 models x 2 variants),
   each with distinct creative direction, all persisted to session dir.

3. **Refine**: Run `/loom:refine "My draft paragraph about X" --passes=2`.
   Verify pass 1 produces independent critiques, pass 2 shows judge
   assessment with winner/strengths/weaknesses, woven result improves.

4. **Brainstorm-and-refine**: Run the full pipeline. Verify transition gate
   appears after brainstorm, refinement passes show full rationale chain.

5. **Fallback**: Test with only `agent` CLI available (no `gemini`/`codex`).
   Verify fallback works.

6. **Session artifacts**: Verify all files written to `$AI_AIP_ROOT` match
   the documented directory structures.
