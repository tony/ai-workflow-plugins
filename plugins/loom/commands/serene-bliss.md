---
description: Loom serene bliss — three-lens DX brainstorm-and-refine with multi-model panel judging
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Task", "AskUserQuestion"]
argument-hint: "<prompt> [--passes=N] [--timeout=N|none] [--mode=fast|balanced|deep]"
---

# Loom Serene Bliss

A first-class three-lens brainstorm-and-refine command for
developer-experience, documentation, and tooling-UX design work. Three
variant slots are fixed to three serene-DX aesthetic lenses — **DX
Bliss**, **DX Serenity**, and **DX Sublimity** — and dispatched across
all available models in parallel. Each refine pass is judged by a
**multi-model panel** (Claude + Gemini + GPT in parallel), with verdicts
merged via **peer-only averaging** to neutralize self-favoritism.

This is the only loom command that uses panel judging. For host or
round-robin judging on user-defined variants, use
`/loom:brainstorm-and-refine` instead.

This is a **project-read-only** command. Session artifacts land under
`$AI_AIP_ROOT`, outside your repository.

The prompt comes from `$ARGUMENTS`. If no prompt is provided, ask the
user what DX artifact, docs page, or tooling surface they want to
brainstorm and refine under the serene lens.

---

## The Three Serene Lenses

| Slot | Lens | Aesthetic | Ask of each model |
|------|------|-----------|-------------------|
| 1 | **DX Bliss** | Frictionless, delightful, zero-friction | "Make this feel effortless. Does every interaction feel weightless?" |
| 2 | **DX Serenity** | Calm, unhurried, information-architectural clarity | "Make this feel like a quiet library. Does the reader's eye rest naturally?" |
| 3 | **DX Sublimity** | Awe-inducing, showcase-grade, novel | "Make this feel like a first. Would this be memorable enough to screenshot?" |

The three slots are exhaustive for serene-DX work. "Reader happiness"
collapses into Serenity; there is no fourth slot.

---

## Compound Preamble (source of truth)

The compound preamble injected into each variant is a single paragraph
(no embedded newlines) for shell-quoting safety. This file is the
canonical location — the `loom:serene-bliss` skill references this
block rather than duplicating it.

```
You are a developer-experience design expert. Apply the Serene DX aesthetic lens matching your variant slot. Variant 1 → DX Bliss: frictionless, delightful, zero-friction; make it feel effortless. Variant 2 → DX Serenity: calm, unhurried, information-architectural; make it feel like a quiet library. Variant 3 → DX Sublimity: awe, novel extensions, showcase-grade; make it feel like a first. Compare the current state to any concrete reference implementation named in the prompt, and name what is ugly or broken. Do NOT modify any files — research only.
```

Loom prepends `"Variant N of M:"` to this string automatically for each
variant, so the compound preamble's slot directives route each model to
the correct lens via its variant number.

---

## Argument Handling

Scan `$ARGUMENTS` for `--name=value` flags anywhere in the text. Flags
are stripped from the prompt text before sending to models, identical
to brainstorm-and-refine's flag handling.

**Reserved flags** — if the user passed any of these, print one warning
line at session start and strip them:

- `--variants=*` — serene-bliss locks `--variants=3`; the three-lens
  contract depends on it.
- `--preamble=*` — serene-bliss locks the compound preamble above.
- `--judge=*` — serene-bliss locks `--judge=panel`; users who want
  host or round-robin should run `/loom:brainstorm-and-refine`.

Warning line format (printed once, at the start of execution if any
reserved flag was seen):

> "Note: `--variants`, `--preamble`, and/or `--judge` were ignored —
> serene-bliss locks all three. Run `/loom:brainstorm-and-refine`
> directly for full control."

**Passthrough flags** — apply unchanged:

- `--passes=N` (default 2)
- `--timeout=N|none`
- `--mode=fast|balanced|deep`

---

## Phase 1: Gather Context

Follow Phase 1 (Gather Context) of
`plugins/loom/commands/brainstorm-and-refine.md` verbatim — read
CLAUDE.md/AGENTS.md for project
conventions, detect the trunk branch, capture the prompt from
`$ARGUMENTS`. No serene-bliss-specific changes.

## Phase 1b: Build Context Packet

Follow Phase 1b (Build Context Packet) of
`plugins/loom/commands/brainstorm-and-refine.md` verbatim — assemble
the structured context bundle that
all models will receive.

For serene-DX work specifically, the host SHOULD ensure the context
packet surfaces a **reference anchor** (a known-good implementation to
compare against) and a **constraint envelope** (what must NOT change:
files, branches, accessibility, dark mode, etc.). The compound
preamble explicitly asks each model to compare against a reference, so
this is load-bearing.

## Phase 2: Configure and Detect Models

Follow Phase 2 (Configuration and Model Detection) of
`plugins/loom/commands/brainstorm-and-refine.md` — flag parsing,
mode/timeout/passes resolution, model
detection (Claude, Gemini, GPT), session directory setup — with these
**serene-bliss overrides** applied after the standard parsing:

- `variant_count = 3` (forced; override any `--variants` from
  `$ARGUMENTS` and emit the reserved-flag warning per the Argument
  Handling section above).
- `user_preamble = <Compound Preamble block above>` (forced; override
  any `--preamble` from `$ARGUMENTS`).
- `judge_mode = panel` (forced; override any `--judge` from
  `$ARGUMENTS`).
- `pass_count` default = 2 (matching brainstorm-and-refine's default).
- Session directory layout adds one path per pass:
  `$SESSION_DIR/refine/pass-NNNN/judges/` for individual panel
  members' assessments, alongside the existing `panel.md` (the merged
  output) and `woven.md` (the weave-step result).

### Panel Feasibility Check

After model detection completes, count the available models:

- **3 models available**: Standard panel mode. Each output will be
  scored by 2 peer judges (its producing model is excluded by the
  peer-only rule). Proceed normally.
- **2 models available**: Degraded panel. Print warning:
  > "Warning: panel has 2 members (<unavailable model> not detected);
  > scoring is single-peer rather than dual-peer."
  Each output will be scored by exactly 1 peer judge. Proceed.
- **1 model available** (only Claude): Panel infeasible. Set
  `judge_mode = host_fallback` and print warning:
  > "Warning: only Claude detected — panel is unavailable. Falling
  > back to host judging for all passes."
  All judging will use the Host Judge Protocol from
  `plugins/loom/commands/brainstorm-and-refine.md` (Phase 5 Step 1,
  Host Judge Protocol).

Record the resolved `judge_mode` and panel member set in
`$SESSION_DIR/metadata.md`.

---

## Phase 3: Brainstorm — Dispatch Three Lens Variants Across All Models

**Goal**: Send the prompt to all available models simultaneously, with
each model producing all three lens variants in parallel.

### Variant Preambles (locked)

The variant preambles are FIXED for serene-bliss — the variant preamble
table from brainstorm.md/brainstorm-and-refine.md does NOT apply.
Instead, every variant receives the **same** compound preamble (above),
prefixed by loom's standard "Variant N of M:" marker. The compound
preamble's slot directives route each variant to its lens by variant
number:

| Variant | Effective preamble |
|---------|--------------------|
| 1 | `Variant 1 of 3: <Compound Preamble>` → routes to DX Bliss slot |
| 2 | `Variant 2 of 3: <Compound Preamble>` → routes to DX Serenity slot |
| 3 | `Variant 3 of 3: <Compound Preamble>` → routes to DX Sublimity slot |

### Prompt Preparation

For each variant N in {1, 2, 3}, write
`$SESSION_DIR/brainstorm/prompts/variant-<N>.md` containing:

- `Variant N of 3: <Compound Preamble>` (shell-safe single paragraph)
- The base user prompt (with reserved flags stripped)
- The context packet content

Create the prompts directory:

```bash
mkdir -p "$SESSION_DIR/brainstorm/prompts"
```

Also write `$SESSION_DIR/brainstorm/prompt.md` as a summary file
listing the base prompt, the compound preamble, the three lens slot
mappings, and a reference to the context packet.

### Claude Variants (Task agents)

For each Claude variant N (1 through 3), launch a separate Task agent
with `subagent_type: "general-purpose"`:

> Variant N of 3: <Compound Preamble>
>
> Respond to the following prompt about this codebase. Read any
> relevant files to give a thorough, original response. Read
> CLAUDE.md/AGENTS.md for project conventions.
>
> Prompt: <user's prompt>
>
> Read the context packet at `$SESSION_DIR/context-packet.md` for
> project context.
>
> Provide a clear, well-structured response. Cite specific files and
> line numbers where relevant. CRITICAL: Do NOT write, edit, create, or
> delete any files in the repository. Do NOT use Write, Edit, or Bash
> commands that modify repository files. All session artifacts are
> written to `$SESSION_DIR`, which is outside the repository. This is a
> READ-ONLY research task.

Each Claude variant agent writes its output to
`$SESSION_DIR/brainstorm/outputs/claude-v<N>.md`.

### Gemini Variants (sub-agents)

For each Gemini variant N (1 through 3), launch a separate Task agent
(`subagent_type: "general-purpose"`, `mode: "default"`) to execute the
Gemini model. Include in the agent prompt: the resolved backend
command and timeout from Phase 2, the `$SESSION_DIR` path, the
`$REPO_TOPLEVEL` path and `$REPO_FINGERPRINT` value, the variant
number, and the prompt with the compound preamble.

The agent must:

1. Read the variant prompt from
   `$SESSION_DIR/brainstorm/prompts/variant-<N>.md`
2. Run the resolved Gemini command with output redirection.
   **Repo Guard**: run inside `(cd "$SESSION_DIR" && ...)` to isolate
   rogue writes from the repository (see `docs/repo-guard-protocol.md`
   Layer 1).

   **Native (`gemini` CLI)**:

   ```bash
   (cd "$SESSION_DIR" && <timeout_cmd> <timeout_seconds> gemini -m gemini-3.1-pro-preview -y -p "$(cat "$SESSION_DIR/brainstorm/prompts/variant-<N>.md")" >"$SESSION_DIR/brainstorm/outputs/gemini-v<N>.md" 2>"$SESSION_DIR/brainstorm/stderr/gemini-v<N>.txt")
   ```

   **Fallback (`agent` CLI)**:

   ```bash
   (cd "$SESSION_DIR" && <timeout_cmd> <timeout_seconds> agent -p -f --model gemini-3.1-pro "$(cat "$SESSION_DIR/brainstorm/prompts/variant-<N>.md")" >"$SESSION_DIR/brainstorm/outputs/gemini-v<N>.md" 2>>"$SESSION_DIR/brainstorm/stderr/gemini-v<N>.txt")
   ```

3. **Repo Guard** post-CLI verification: immediately after the CLI
   returns, check the repository state. If dirty, revert and log the
   violation:

   ```bash
   CURRENT_STATUS="$(git -C "$REPO_TOPLEVEL" status --porcelain)"
   ```

   If `$CURRENT_STATUS` differs from `$REPO_FINGERPRINT`:

   ```bash
   git -C "$REPO_TOPLEVEL" checkout -- . 2>/dev/null || true
   ```

   ```bash
   git -C "$REPO_TOPLEVEL" clean -fd 2>/dev/null || true
   ```

   ```bash
   printf '{"event":"repo_guard_violation","timestamp":"%s","model":"gemini","reverted":true}\n' \
     "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
     >>"$SESSION_DIR/guard-events.jsonl"
   ```

4. On failure: classify (timeout → retry with 1.5x timeout; rate-limit
   → retry after 10s; credit-exhausted → skip retry, escalate to agent
   CLI immediately; crash → not retryable; empty → retry once), retry
   max once with same backend, then fall back to agent CLI if native
   was used; if agent is also credit-exhausted or unavailable, use
   lesser model (gemini-3-flash-preview).
5. Return: exit code, elapsed time, retry count, output file path.

### GPT Variants (sub-agents)

For each GPT variant N (1 through 3), launch a separate Task agent
(`subagent_type: "general-purpose"`, `mode: "default"`) to execute the
GPT model. Same dispatch shape as Gemini, with these command
replacements. Include `$REPO_TOPLEVEL` and `$REPO_FINGERPRINT` in the
agent prompt for post-CLI verification.

**Repo Guard**: run inside `(cd "$SESSION_DIR" && ...)` to isolate
rogue writes from the repository (see `docs/repo-guard-protocol.md`
Layer 1).

**Native (`codex` CLI)**:

```bash
(cd "$SESSION_DIR" && <timeout_cmd> <timeout_seconds> codex exec -c model_reasoning_effort=medium "$(cat "$SESSION_DIR/brainstorm/prompts/variant-<N>.md")" >"$SESSION_DIR/brainstorm/outputs/gpt-v<N>.md" 2>"$SESSION_DIR/brainstorm/stderr/gpt-v<N>.txt")
```

**Fallback (`agent` CLI)**:

```bash
(cd "$SESSION_DIR" && <timeout_cmd> <timeout_seconds> agent -p -f --model gpt-5.4-high "$(cat "$SESSION_DIR/brainstorm/prompts/variant-<N>.md")" >"$SESSION_DIR/brainstorm/outputs/gpt-v<N>.md" 2>>"$SESSION_DIR/brainstorm/stderr/gpt-v<N>.txt")
```

**Repo Guard** post-CLI verification: immediately after the CLI
returns, check the repository state. If dirty, revert and log:

```bash
CURRENT_STATUS="$(git -C "$REPO_TOPLEVEL" status --porcelain)"
```

If `$CURRENT_STATUS` differs from `$REPO_FINGERPRINT`:

```bash
git -C "$REPO_TOPLEVEL" checkout -- . 2>/dev/null || true
```

```bash
git -C "$REPO_TOPLEVEL" clean -fd 2>/dev/null || true
```

```bash
printf '{"event":"repo_guard_violation","timestamp":"%s","model":"gpt","reverted":true}\n' \
  "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  >>"$SESSION_DIR/guard-events.jsonl"
```

Same retry/fallback classification as Gemini. Lesser model fallback:
gpt-5.4-mini via agent.

### Execution Strategy

- **Launch ALL `model × variant` agents in the same turn** to execute
  simultaneously. With 3 models × 3 variants = up to 9 parallel
  dispatches per session. If parallel dispatch is unavailable, launch
  sequentially — Phase 4 tolerates partial results.
- Each variant MUST be a separate, independent prompt invocation.
  Never send multiple variants to the same model in a single prompt —
  this prevents anchoring across lens slots.
- Each sub-agent handles its own retry and fallback protocol
  internally.
- After all agents return, verify output files exist in
  `$SESSION_DIR/brainstorm/outputs/`.
- If a sub-agent reports failure after exhausting retries, mark that
  model variant as unavailable in `session.json` and continue. The
  presentation phase will display partial results.

---

## Phase 4: Present Originals and Transition Gate

Follow Phase 4 (Present Brainstorm Results and Transition Gate) of
`plugins/loom/commands/brainstorm-and-refine.md` verbatim. Present all
successful brainstorm originals
to the user, ask which ones enter refinement via `AskUserQuestion`,
update `session.json` to `phase: "refine"`, and proceed.

If the user selects "None", end the session and report the brainstorm
artifacts only.

---

## Phase 5: Panel Judge — First Refine Pass

This phase introduces the **Panel Judge Protocol** — net-new to
serene-bliss. All available models judge in parallel and their
verdicts are merged via peer-only averaging.

### Step 1: Build the shared judge prompt

The panel judges share a single prompt. Build it identically to the
External Judge Protocol from `plugins/loom/commands/refine.md` (lines
522-616) — scoring rubric (4 dimensions × 0-10), expected output format
(scores table, winner, rationale, runner-up analysis), and ALL
selected originals included inline (external models cannot read
session files).

Prepend this additional instruction to the standard External Judge
Protocol prompt:

> "You are one of three judges on a panel. Score every output honestly
> including outputs from your own model. Do not self-favor — the merge
> step will exclude your self-scores automatically via peer-only
> averaging. Rate each output on the four dimensions (Quality,
> Originality, Completeness, Coherence) on a 0-10 scale."

Write the shared prompt to
`$SESSION_DIR/refine/pass-0001/panel-prompt.md`.

### Step 2: Dispatch panel judges in parallel

Launch one judge per available model **in the same turn**:

- **Claude judge**: Task agent with `subagent_type: "general-purpose"`
  receiving the panel-prompt content directly. Writes assessment to
  `$SESSION_DIR/refine/pass-0001/judges/claude.md`.
- **Gemini judge**: sub-agent dispatching the gemini CLI (or agent
  fallback) with the shared prompt as input. Same retry/fallback
  protocol as Phase 3 Gemini variants. Writes to
  `$SESSION_DIR/refine/pass-0001/judges/gemini.md`.
- **GPT judge**: sub-agent dispatching the codex CLI (or agent
  fallback) with the shared prompt as input. Same retry/fallback
  protocol as Phase 3 GPT variants. Writes to
  `$SESSION_DIR/refine/pass-0001/judges/gpt.md`.

**Repo Guard**: Gemini and GPT judge CLIs must use the same
`(cd "$SESSION_DIR" && ...)` wrapping as Phase 3 variant dispatches
(see `docs/repo-guard-protocol.md` Layer 1). After each judge CLI
returns, run the post-CLI repo state verification — capture
`CURRENT_STATUS="$(git -C "$REPO_TOPLEVEL" status --porcelain)"`,
and if `$CURRENT_STATUS` differs from `$REPO_FINGERPRINT`, revert
and log the violation to `$SESSION_DIR/guard-events.jsonl` with the
judge's model name.

Each judge file uses the standard judge assessment format (scores
table, winner, rationale, runner-up analysis) with this header:

```markdown
# Judge's Assessment — Pass 1
**Judged by**: <model> (panel member, peer-only averaging)
```

If only 2 models are available (degraded panel), launch 2 judges and
proceed. If only Claude is available (panel infeasible), skip Phase 5
Steps 1-4 entirely and use the **Host Judge Protocol** from
`plugins/loom/commands/brainstorm-and-refine.md` (Phase 5 Step 1,
Host Judge Protocol).

### Step 3: Parse judge responses

For each judge that completed dispatch:

1. Read the judge file from `$SESSION_DIR/refine/pass-0001/judges/<model>.md`.
2. Attempt to parse the scores table (originals × 4 dimensions),
   declared winner, rationale, and runner-up analysis.
3. On parse failure: log a warning to
   `$SESSION_DIR/refine/pass-0001/parse-errors.txt` and exclude this
   judge from the merge step.
4. On dispatch failure (reported by Step 2's sub-agent): also exclude.

**Full-panel failure fallback**: if 0 judges succeed (all parse or
dispatch failed), fall back to the **Host Judge Protocol** from
`plugins/loom/commands/brainstorm-and-refine.md` (Phase 5 Step 1,
Host Judge Protocol). Run
that protocol now and produce a single `judge.md` file. Mark the
resulting `panel.md` (Step 4) as
`**Judged by**: Claude (fallback — all panel judges failed)` and
include the full host judgment inline.

### Step 4: Merge via peer-only averaging

For each successfully-parsed judge, the input is a scores table where
each row is one original (e.g., `claude-v1`, `gemini-v2`, `gpt-v3`)
and each column is a dimension score (0-10).

**Peer-only averaging algorithm** (described in prose; the host
implements this directly):

For each original `O` in the pass's review set:

1. Identify the **producer model** for `O` from its label
   (e.g., `claude-v2` → producer = Claude; `gemini-v1` → producer =
   Gemini).
2. For each successfully-parsed judge `J`:
   - If `J` is the same as the producer: **exclude** this judge's
     score for `O` (peer-only rule).
   - Otherwise: include `J`'s 4 dimension scores in the per-dimension
     accumulators for `O`.
3. Compute the **merged per-dimension scores** for `O` as the
   arithmetic mean of the included judges' scores.
4. Compute the **merged total** for `O` as the sum of merged
   per-dimension scores (0-40).

After all originals have merged scores:

5. **Winner** = the original with the highest merged total.
6. **Tie resolution**: if 2+ originals share the highest merged total,
   the host (Claude) picks among them and writes a 1-paragraph
   tie-break rationale into `panel.md`.

**Merged runner-up analysis**: read the runner-up sections from each
parsed judge file, deduplicate strengths that multiple judges noted
(collapse to one bullet with `(N/3 judges)` annotation), and preserve
unique observations from each judge.

Write the merged assessment to
`$SESSION_DIR/refine/pass-0001/panel.md` using this template:

```markdown
# Panel Assessment — Pass 1
**Judged by**: Panel (Claude + Gemini + GPT, peer-only averaging)
**Judges succeeded**: 3/3   <!-- or "2/3 (gemini parse failed)" etc. -->

## Individual Scores
| Original   | Claude | Gemini | GPT  | Merged (peer-only) |
|------------|--------|--------|------|---------------------|
| claude-v1  |   —    |  33    |  31  |  32 / 40            |
| claude-v2  |   —    |  28    |  35  |  31 / 40            |
| gemini-v1  |  34    |   —    |  30  |  32 / 40            |
| gemini-v2  |  31    |   —    |  29  |  30 / 40            |
| gpt-v1     |  32    |  30    |   —  |  31 / 40            |
| ...        |  ...   |  ...   | ...  |  ...                |

(em-dashes mark self-scores excluded by the peer-only rule)

## Winner
**<label>** — merged score XX / 40
<!-- if tie: "tied with <other>, broken by host: <rationale>" -->

## Merged Runner-Up Analysis

### <label> (N/3 judges agree)
- <strength noted by multiple judges>

### <label> (1/3 judge — Claude only)
- <unique observation>

## Individual Judge Summaries
- **Claude**: picked <label>; emphasized <one-line rationale>
- **Gemini**: picked <label>; emphasized <one-line rationale>
- **GPT**: picked <label>; emphasized <one-line rationale>

## Merge Notes
- Peer-only averaging: each original's score excludes the producing
  model's self-assessment.
- Tie resolution: <"none" | "host arbitrated between A and B">.
```

### Step 5: Weave

Follow Phase 5 Steps 2-3 (Analyze Runners-Up and Weave) of
`plugins/loom/commands/brainstorm-and-refine.md` verbatim, with one
substitution: read `panel.md` (this command's
merged assessment) instead of `judge.md`. The host (Claude) constructs
the woven version incorporating the winner plus runner-up strengths
and writes it to `$SESSION_DIR/refine/pass-0001/woven.md`.

### Step 6: Distribute (if pass_count > 1)

Follow Phase 5 Step 4 (Distribute for Pass 2) of
`brainstorm-and-refine.md` verbatim. Send the woven version back to
all 3 models for the next
pass's critique.

---

## Phase 6: Panel Judge — Subsequent Passes

Repeat Phase 5 Steps 1-6 for each pass from 2 through `pass_count`.
The panel composition is **stable across passes** — no rotation, no
membership changes (this is the key difference from
brainstorm-and-refine's round-robin mode, where the judge rotates).

For each subsequent pass `N`:

- Input under review = output of pass `N-1` (each model's critique of
  the previous woven version).
- Judges = the same panel members detected in Phase 2.
- Merge step = peer-only averaging as in Phase 5 Step 4.
- Output paths use `pass-NNNN` (zero-padded) consistently.

**Early-stop detection** mirrors Phase 6 Step 5 (Early-Stop
Detection) of `plugins/loom/commands/brainstorm-and-refine.md`: if
the woven version of pass `N` is substantially identical to the woven
version of pass `N-1`, stop early and skip to Phase 7.

The final pass skips Step 6 (distribute) — there is no next pass to
prepare for.

---

## Phase 7: Present Final Result

Follow Phase 7 (Present Final Result) of
`plugins/loom/commands/brainstorm-and-refine.md` verbatim. Present the
final woven version, the full
rationale chain across all passes, and the session directory path for
post-session inspection.

**Repo Guard**: The session-end verification from brainstorm-and-refine
Phase 7 applies here — repo state is checked against the pre-session
fingerprint before marking the session as completed.

In the presentation summary, include one additional line specific to
serene-bliss:

> "Judged by: Panel (Claude + Gemini + GPT, peer-only averaging) across
> N pass(es)."

---

## Relationship to the skill

The `loom:serene-bliss` skill at
`plugins/loom/skills/serene-bliss/SKILL.md` auto-discovers on serene-DX
vocabulary ("serene bliss", "DX bliss", "DX serenity", "DX sublimity",
"reader happiness", etc.) and routes to this command. The skill owns
the trigger surface; this command owns the execution contract, the
canonical preamble text, and the panel judging protocol.
