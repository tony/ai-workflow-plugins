# weave

Weave prompts across Claude, Antigravity, and GPT in parallel — plan, execute, review, and synthesize the best of all models.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install weave@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/weave:ask` | Ask all models a question, synthesize the best answer |
| `/weave:plan` | Get implementation plans from all models, synthesize the best plan |
| `/weave:prompt` | Run a prompt in isolated worktrees, pick the best implementation |
| `/weave:execute` | Run a task in isolated worktrees, synthesize the best parts of each |
| `/weave:architecture` | Generate project scaffolding, conventions, skills, and architectural docs, then synthesize the best architecture |
| `/weave:review` | Run code review with all models, produce consensus-weighted report |
| `/weave:fix-review` | Fix review findings as atomic commits with test coverage |
| `/weave:brainstorm` | Generate independent original ideas from each model, with optional multiple variants |
| `/weave:refine` | Iteratively improve an artifact through multi-model critique and weaving |
| `/weave:brainstorm-and-refine` | Full pipeline: brainstorm originals, then iteratively judge, weave, and refine |
| `/weave:serene-bliss` | Three-lens DX brainstorm-and-refine (Bliss, Serenity, Sublimity) with multi-model panel judging |

## Skills

Skills provide auto-discovery — they trigger when the user's intent matches the skill description.

| Skill | Triggers on |
|-------|-------------|
| `weave:brainstorm` | "brainstorm", "give me ideas", "multiple approaches", "explore alternatives" |
| `weave:refine` | "refine this", "improve this", "make this better", "iterate on this" |
| `weave:brainstorm-and-refine` | "brainstorm and refine", "generate ideas then improve", "explore then synthesize" |
| `weave:serene-bliss` | "serene bliss", "DX bliss", "DX serenity", "DX sublimity", "reader happiness" |

## How It Works

The orchestration commands follow consistent multi-phase workflows. The original six (ask, plan, prompt, execute, architecture, review) use **targeted conflict resolution** for multi-pass — subsequent passes only address unresolved conflicts. The new three (brainstorm, refine, brainstorm-and-refine) use **expansive weaving** — each pass is a full judge-pick-best-incorporate-strengths-address-weaknesses cycle. The `fix-review` command is a separate remediation workflow for applying review findings as atomic commits.

1. **Configure** — Parse `--passes`, `--timeout`, `--mode` flags and prompt for any remaining settings.
2. **Detect models** — Check for `agy`, `gemini`, `codex`, and `agent` CLIs. Use native CLIs when available; the Google lane prefers `agy` (Antigravity) and falls back to `gemini`, then the `agent` CLI with `--model` flags.
3. **Run in parallel** — Execute the task across all available models simultaneously.
4. **Synthesize** — Compare outputs, verify claims against the codebase, and combine the best elements.
5. **Refine** (multi-pass) — Optionally re-attack the prior pass's unresolved residuals with all models for deeper results.

### Protocols

All commands share four quality protocols that decorrelate model outputs and improve synthesis:

- **Context packets** — a structured bundle (conventions, repo state, key snippets) included verbatim in every model prompt so all models work from the same information
- **Role differentiation** — each model receives a distinct evaluation lens (Maintainer, Skeptic, Builder) to reduce shared blind spots
- **Blind judging** — model outputs are randomly labeled (A/B/C) during scoring to prevent brand bias (ask/plan/prompt/execute/architecture/review)
- **Structured synthesis** — a five-step protocol (verify claims, score with rubric, adjudicate conflicts, converge, critic) backed by codebase evidence (ask/plan/prompt/execute/architecture/review)
- **Judge-weave-distribute** — pick the best, incorporate strengths from runners-up, redistribute for another round (refine/brainstorm-and-refine)
- **Consensus signal** — findings and disagreements carry per-lane agreement tags (unanimous/majority/split/single); split items are surfaced with both positions, never silently adjudicated away (ask/review; spec in `references/ensemble-techniques.md`)

### Repo Guard Protocol

All weave commands enforce a 5-layer guard that prevents sessions from
modifying repository files. See `docs/repo-guard-protocol.md` for
the full specification.

| Layer | Defense | Scope |
|-------|---------|-------|
| 1 | Native read-only sandbox (`-s read-only` / `--approval-mode plan`), or a disposable HEAD worktree for `agy` (no native read-only mode) | Read-only commands |
| 2 | Pre-session repo fingerprint (HEAD + `git status`) | All commands |
| 3 | Post-CLI repo state verification + auto-revert | All commands |
| 4 | Prompt hardening ("CRITICAL: Do NOT write files") | All commands |
| 5 | Session-end verification against fingerprint | All commands |

**Read-only commands** run external CLIs in their native read-only
sandbox (codex `-s read-only`, gemini `--approval-mode plan`, agent
`--mode plan`) pointed at the repo, so models can read but not write;
the `cd "$SESSION_DIR"` wrapper is a backstop. The `agy` (Antigravity)
CLI has no native read-only mode — its print mode reads *and* writes —
so its read-only lanes run in a disposable git worktree checked out at
`HEAD`, which is discarded afterward; any stray write lands in the
throwaway worktree, never the main repo. **Write commands** run
external CLIs in isolated worktrees
and verify the main tree is unchanged after diff capture. All commands
verify the repo is unchanged at session end.

The guard was introduced because external CLIs have known issues with
unexpectedly modifying project files. The protocol provides
defense-in-depth: the native read-only sandbox (or disposable worktree
for `agy`) blocks writes, post-CLI verification catches writes to
absolute paths, and session-end verification is the final safety net.

### Read-Only Commands

**ask**, **plan**, **brainstorm**, **refine**, **brainstorm-and-refine**,
**serene-bliss**, and **review** do not modify files. They gather multiple
perspectives and synthesize a single best result.

### Write Commands

**prompt**, **execute**, and **architecture** create isolated git worktrees for each external model, so implementations never interfere with each other. After comparison:
- **prompt** picks one winner
- **execute** cherry-picks the best parts from each model
- **architecture** cherry-picks the best conventions, skills, agents, and scaffolding per file

**fix-review** processes findings from a review, applying each as an atomic commit with test coverage. Multi-pass does not apply to fix-review since it is already iterative.

### Brainstorm & Refine Commands

**brainstorm** generates independent originals from each model with no synthesis. Use `--variants=N` (1-3) to get multiple originals per model, each with a distinct creative-direction preamble (conventional, creative, contrarian). Override preambles with `--preamble='...'`.

**refine** takes a single artifact (inline text or file path) and iteratively improves it. Each pass: all models critique and improve → judge picks the best → identifies strengths in runners-up → weaves a revised version → distributes back to all models. Uses `--passes=N` (1-5, default 2).

**brainstorm-and-refine** is the full pipeline: brainstorm originals, present them, let the user choose which enter refinement, then run the refine cycle. A transition gate always asks the user before proceeding.

## Plan Mode

Three commands use plan mode, but in two distinct patterns:

### Temporary plan mode (review, fix-review)

The **review** and **fix-review** commands enter plan mode to create an
orchestration strategy, present it for user approval, then **exit plan mode**
before executing. This is the "plan then execute" pattern.

**review** plans: branch summary, review focus areas, relevant conventions,
known concerns, and model prompt strategy.

**fix-review** plans: findings inventory, validity pre-assessment, fix
ordering, test strategy per finding, risk assessment, and expected commit
sequence.

### Persistent plan mode (plan)

The **plan** command enters plan mode at the start and **stays in plan mode
throughout** — the Claude plan file IS the deliverable. Sub-agents (spawned
with `mode: "default"`) handle all non-readonly operations: git commands,
session directory setup, external CLI execution, and artifact persistence.
The main agent orchestrates from plan mode using Read, Grep, Glob, and the
Task tool (all permitted in plan mode).

### Portable plan mode activation

This works across AI coding tools:

| Tool | Enter plan mode | Exit plan mode |
|------|----------------|----------------|
| Claude Code | `EnterPlanMode` tool | `ExitPlanMode` tool |
| Cursor | `/plan` or `Shift+Tab` | Exit per tool method |
| Codex | `/plan` | Exit per tool method |
| Gemini | `/plan` or `Shift+Tab` | Exit per tool method |

If plan mode is unavailable, the commands still work — the phase structure
guides analysis before execution.

### Output rendering and next-step panel

All weave commands render their final output through the shared reference
`references/present-results.md`. This reference enforces a strict output
contract (hero block + prescribed sections + no invented headings) and
presents a next-step panel that lets the user act on findings — including
an active plan-mode handoff for commands whose results imply implementation
work.

## Sub-Agent Architecture

All weave commands use the Task tool to delegate work to sub-agents. Each model execution runs in its own sub-agent,
enabling true parallel dispatch when the host supports it.

| Role | Agent type | Mode | Purpose |
|------|-----------|------|---------|
| Claude model | `general-purpose` | default | Reads codebase, produces response |
| Antigravity model | `general-purpose` | default | Runs `agy`/`gemini`/`agent` CLI via Bash |
| GPT model | `general-purpose` | default | Runs `codex`/`agent` CLI via Bash |
| Critic | `general-purpose` | default | Challenges synthesized result |
| Context gather | `general-purpose` | default | Runs git commands (plan mode only) |
| Session setup | `general-purpose` | default | Creates session dir, detects models (plan mode only) |

Sub-agents run with `mode: "default"` so they can use Bash, Write, and Edit
even when the parent agent is in plan mode. Each sub-agent receives all
needed context in its prompt since sub-agents don't share the parent's
conversation state.

## Cascade Mode

`--cascade` (ask, review) inverts the cost model: a Claude-only first pass runs, self-verifies against the codebase, and fans out to the external models only when a confidence trigger fires — a contradicted or unverified load-bearing claim, an ambiguous request, a coverage gap, or a judgment call (for review, any Critical finding always escalates). On early exit the result is presented as Claude-lane-only with an "Escalate to full ensemble" option in the next-step panel. Trigger definitions live in `references/ensemble-techniques.md`.

## Multi-Pass Refinement

Multi-pass runs additional rounds after the first synthesis. For ask and review, pass N ≥ 2 is a residual re-attack: models receive only the unresolved items from the prior pass — conflicts evidence could not settle, failed claim verification, leftover critic findings, split-consensus items — and their resolutions merge back into the prior synthesis, which otherwise carries forward verbatim. An empty residual ledger means convergence and stops early. The refine command scopes each redistribution round's critique to the pass's residual focus. This deepens results at the cost of additional model invocations.

### Flags

Control pass count, timeout, and execution mode with explicit flags:

| Flag | Values | Default | Example |
|------|--------|---------|---------|
| `--passes=N` | 1–5 | 1 (refine: 2) | `/weave:plan add auth --passes=2` |
| `--timeout=N\|none` | seconds or `none` | command-specific | `/weave:ask question --timeout=300` |
| `--mode=fast\|balanced\|deep` | mode preset | `balanced` | `/weave:execute task --mode=deep` |
| `--cascade` | flag (ask, review) | off | `/weave:ask question --cascade` |
| `--variants=N` | 1–3 | 1 | `/weave:brainstorm idea --variants=2` |
| `--judge=host\|round-robin` | Who judges each refinement pass | `host` | `/weave:refine draft --judge=round-robin` |
| `--preamble=...` | text | built-in | `/weave:brainstorm idea --preamble='focus on perf'` |

Mode presets vary by command. For the original commands (ask, plan, prompt, execute, architecture, review): `fast` (1 pass, 0.5× timeout), `balanced` (1 pass, 1× timeout), `deep` (2 passes, 1.5× timeout). For brainstorm: presets control variants and timeout (deep = 2 variants). For refine: presets control passes and timeout (balanced = 2 passes, deep = 3 passes). For brainstorm-and-refine: presets control variants, passes, and timeout (deep = 2 variants, 3 passes).

Default timeouts per command: ask (450s), plan (600s), prompt (600s), review (900s), execute (1200s), architecture (1200s).

Legacy trigger words (`multipass`, `x<N>`, `timeout:<seconds>`) are still recognized as aliases for backward compatibility.

### Judge Modes

The `--judge` flag controls who evaluates model outputs during refinement passes (refine
and brainstorm-and-refine commands only).

`--judge=host` (default): The host agent (Claude) judges every pass. This is the most
reliable mode since the host can read session files and parse varied output formats.

`--judge=round-robin`: Judging rotates across available models — Claude, then Antigravity,
then GPT, cycling back. External models receive a structured judge prompt with all
model outputs inline and produce scores, winner selection, and runner-up analysis.
The host agent always weaves regardless of who judged. If an external judge's output
is unparseable, that pass falls back to host judging.

The rotation is built from available models only. If only Claude and Antigravity are
detected, the rotation is Claude → Antigravity → Claude → Antigravity. Pass 1 always starts
with Claude (index 0).

### Interactive Configuration

When flags are provided, the corresponding interactive question is skipped. Otherwise, commands prompt via `AskUserQuestion`:

1. **Pass count** (skipped when `--passes` is provided) — choose single pass (1), multipass (2), or triple pass (3).
2. **Timeout** (skipped when `--timeout` is provided) — choose the default, quick (0.5× default), long (1.5× default), or no timeout.

In headless mode (`claude -p`), pass count uses the flag value if provided, otherwise defaults to 1. Timeout uses the flag value if provided, otherwise the per-command default.

## Deslop Pass

The prose-producing weave commands (`ask`, `refine`, `brainstorm-and-refine`, `serene-bliss`, `plan`, `review`) run a deslop pass on the final synthesised artifact before it reaches the terminal. Slop signatures (flagship phrases, restated subjects, fragile counts/line numbers, AI footers) are detected against the same Tier A/B/C taxonomy used by `/pr:deslop` and `/slop:scan`, with tone calibration against the last 50 trunk commit messages.

The shared procedural reference is `plugins/weave/references/deslop-pass.md`. The slop registry is **not** duplicated into this plugin — it is resolved at runtime from a sibling plugin:

1. `${CLAUDE_PLUGIN_ROOT}/../pr/references/signatures.yml`
2. `${CLAUDE_PLUGIN_ROOT}/../slop/references/signatures.yml`
3. If neither resolves, the deslop pass emits a one-line skip and the synthesis is presented unchanged. Install either the `pr` or `slop` plugin to enable deslop.

### Flags

| Flag | Default | Effect |
|------|---------|--------|
| `--no-deslop` | off | Skip the deslop pass entirely; no sibling, no summary block. |
| `--quiet-deslop` | off | Replace the 8-line summary block with one line. Tier B confirmations still happen. |
| `--verbose-deslop` | off | Add tier letter, signature id, and confidence per finding. Caps at 16 lines; overflow goes to `deslop-report.md`. |

### Skipped commands

`brainstorm` is intentionally never desloped — independent diversity is the product. `execute`, `prompt`, `architecture`, and `fix-review` produce code, not prose, and rely on the project's own quality gates.

### Recovery

The original synthesis is preserved next to the desloped artifact as a `<artifact>.pre-deslop.md` sibling. Stable filename — no timestamp — so the user can `diff` with one tab-complete:

```console
diff $SESSION_DIR/refine/final.pre-deslop.md $SESSION_DIR/refine/final.md
```

A full audit (registry sha256, applied/declined/advisory findings, word delta) is written to `$SESSION_DIR/deslop-report.md`.

A 30% word-delta hard abort restores the original automatically. A 15% suspect-edit threshold demotes a single oversized trim to advisory and writes the held trim to `<artifact>-deslop-held.md` for inspection.

## Session Artifacts

All commands persist model outputs, prompts, and synthesis results to a structured directory under `$AI_AIP_ROOT`. This enables post-session inspection, selective reference to prior pass artifacts during multi-pass refinement, and lightweight resume tracking.

### Storage Root Resolution

The storage root is resolved in this order:

1. `$AI_AIP_ROOT` environment variable (if set)
2. `$XDG_STATE_HOME/ai-aip` (if `$XDG_STATE_HOME` is set)
3. `~/Library/Application Support/ai-aip` (macOS, when `uname -s` = Darwin)
4. `$HOME/.local/state/ai-aip` (Linux/other default)

A `/tmp/ai-aip` symlink is created pointing to the resolved root for backward compatibility.

### Repo Identity

Repos are identified by a combination of a slugified directory name and a 12-character SHA-256 hash of the repo key (origin URL + slug, or absolute path for repos without a remote). This prevents collisions between unrelated repos with the same directory name.

Format: `<slug>--<hash>` (e.g., `my-project--a1b2c3d4e5f6`)

### Session Identity

Session IDs combine a UTC timestamp, PID, and random bytes to prevent collisions:

```
<YYYYMMDD-HHMMSSZ>-<PID>-<4 hex chars>
```

Example: `20260210-143022Z-12345-a1b2`

### Directory Hierarchy

```
$AI_AIP_ROOT/
└── repos/
    └── <slug>--<hash>/
        ├── repo.json
        └── sessions/
            ├── ask/
            │   ├── latest -> <SESSION_ID>
            │   └── <SESSION_ID>/
            │       ├── session.json
            │       ├── events.jsonl
            │       ├── metadata.md
            │       ├── repo-fingerprint.txt
            │       ├── guard-events.jsonl
            │       ├── pass-0001/
            │       │   ├── prompt.md
            │       │   ├── synthesis.md
            │       │   ├── outputs/
            │       │   │   ├── claude.md
            │       │   │   ├── agy.md
            │       │   │   └── gpt.md
            │       │   └── stderr/
            │       │       ├── agy.txt
            │       │       └── gpt.txt
            │       └── pass-0002/
            │           └── ...
            ├── plan/
            │   └── ...
            ├── review/
            │   └── ...
            ├── execute/
            │   └── ...
            ├── prompt/
            │   └── ...
            ├── architecture/
            │   └── ...
            ├── brainstorm/
            │   ├── latest -> <SESSION_ID>
            │   └── <SESSION_ID>/
            │       ├── session.json
            │       ├── events.jsonl
            │       ├── metadata.md
            │       ├── context-packet.md
            │       ├── prompt.md
            │       ├── outputs/
            │       │   ├── claude-v1.md
            │       │   ├── agy-v1.md
            │       │   └── gpt-v1.md
            │       └── stderr/
            ├── refine/
            │   ├── latest -> <SESSION_ID>
            │   └── <SESSION_ID>/
            │       ├── session.json
            │       ├── events.jsonl
            │       ├── original.md
            │       ├── pass-0001/
            │       │   ├── outputs/
            │       │   ├── judge.md
            │       │   ├── judge-prompt.md    # only when external model judges
            │       │   ├── judge-raw.md       # only when external model judges
            │       │   └── woven.md
            │       └── final.md
            └── brainstorm-and-refine/
                ├── latest -> <SESSION_ID>
                └── <SESSION_ID>/
                    ├── brainstorm/
                    │   └── outputs/
                    └── refine/
                        ├── pass-0001/
                        │   ├── outputs/
                        │   ├── judge.md
                        │   ├── judge-prompt.md    # only when external model judges
                        │   ├── judge-raw.md       # only when external model judges
                        │   └── woven.md
                        └── final.md
```

Write commands (execute, prompt, architecture) add per-pass diff, quality gate, and file snapshot artifacts:

```
pass-0001/
├── ...
├── quality-gates.md
├── diffs/
│   ├── claude.diff
│   ├── agy.diff
│   └── gpt.diff
└── files/
    ├── claude/
    │   └── <repo-relative paths of changed files>
    ├── agy/
    │   └── ...
    └── gpt/
        └── ...
```

Only files that differ from HEAD are snapshotted into `files/<model>/`. The directory structure mirrors the repository layout. Deleted files appear in the diff only, not as snapshots. This enables post-session inspection and multi-pass file-level cross-referencing without depending on worktree persistence.

Pass directories use zero-padded 4-digit numbering (`pass-0001`, `pass-0002`, ...) for correct lexicographic sorting. Directories are created with `mkdir -p -m 700` and are preserved after the session for user inspection.

### Repo Manifest (`repo.json`)

Each `repos/<slug>--<hash>/` directory contains a `repo.json` written on the first session for that repo:

```json
{
  "schema_version": 1,
  "slug": "my-project",
  "id": "a1b2c3d4e5f6",
  "toplevel": "/home/user/projects/my-project",
  "origin": "git@github.com:user/my-project.git"
}
```

### Session Manifest (`session.json`)

Each session directory contains a `session.json` that tracks session state. Updated via atomic replace (write to `.tmp`, then `mv`):

```json
{
  "schema_version": 1,
  "session_id": "20260210-143022Z-12345-a1b2",
  "command": "ask",
  "status": "in_progress",
  "branch": "feature/add-auth",
  "ref": "abc1234",
  "models": ["claude", "agy", "gpt"],
  "completed_passes": 0,
  "prompt_summary": "How does the authentication middleware work?",
  "created_at": "2026-02-10T14:30:22Z",
  "updated_at": "2026-02-10T14:30:22Z"
}
```

| Field | Description |
|-------|-------------|
| `schema_version` | Always `1` |
| `session_id` | Session directory name |
| `command` | Which command created this session |
| `status` | `in_progress` or `completed` |
| `branch` | Git branch at session start |
| `ref` | Git commit ref (short SHA) at session start |
| `models` | Which models participated |
| `judge_mode` | `"host"` or `"round-robin"` (refine/brainstorm-and-refine only) |
| `completed_passes` | How many passes finished |
| `prompt_summary` | First 120 chars of the user's prompt |
| `created_at` | ISO 8601 UTC timestamp of session start |
| `updated_at` | ISO 8601 UTC timestamp of last update |

The session is updated after each pass (`completed_passes` incremented, `updated_at` refreshed) and at session end (`status` set to `completed`). A `latest` symlink is updated at session end to point to the most recent completed session.

### Event Log (`events.jsonl`)

Each session directory contains an `events.jsonl` file with one JSON object per line:

```json
{"event":"session_start","timestamp":"2026-02-10T14:30:22Z","command":"ask","models":["claude","agy","gpt"]}
```

```json
{"event":"pass_complete","timestamp":"2026-02-10T14:32:45Z","pass":1,"models_completed":["claude","agy","gpt"]}
```

Refine and brainstorm-and-refine commands include additional fields in `pass_complete`:

```json
{"event":"pass_complete","timestamp":"2026-02-10T14:32:45Z","pass":1,"winner":"claude","winner_score":35,"woven":true,"judged_by":"claude"}
```

```json
{"event":"session_complete","timestamp":"2026-02-10T14:32:50Z","completed_passes":1}
```

To list sessions, scan `session.json` files under `$AI_AIP_ROOT/repos/<slug>--<hash>/sessions/<command>/`. The `latest` symlink points to the most recently completed session for quick access.

## Prerequisites

At minimum, Claude (this agent) is always available. For weave functionality, install one or more external CLIs:

| CLI | Model | Install |
|-----|-------|---------|
| `agy` | Gemini (via Antigravity) | [Antigravity CLI](https://antigravity.google/product/antigravity-cli) |
| `gemini` | Gemini (fallback; gemini CLI retired 2026-06-18) | [Gemini CLI](https://github.com/google-gemini/gemini-cli) |
| `codex` | GPT | [Codex CLI](https://github.com/openai/codex) |
| `agent` | Any (fallback) | [Agent CLI](https://cursor.com/cli) |

### macOS timeout support

External CLI commands are wrapped with `timeout` (GNU coreutils) to enforce time
limits. On macOS, install GNU coreutils to get `gtimeout`:

```console
brew install coreutils
```

If neither `timeout` nor `gtimeout` is found, commands run without a time limit.

If no external CLIs are available, commands fall back to Claude-only mode with a note about the limitation.

### Model selection and reasoning depth

The Antigravity lane invokes `agy --model "Gemini 3.1 Pro (High)"` — the
strongest Gemini Pro option reported by `agy models`. The `(High)` suffix
selects HIGH reasoning depth directly, so no alias configuration is needed.

When `agy` is unavailable, the lane falls back to the `gemini` CLI with
`gemini -m gemini-3-pro-preview` rather than `gemini-3.1-pro-preview`. This is
deliberate: in the installed `gemini-cli` bundle, only `gemini-3-pro-preview`
extends the built-in `chat-base-3` alias that sets `thinkingLevel: HIGH`. The
`3.1` variant has no alias linking it to HIGH thinking, so one-shot `-p`
invocations produce noticeably shallower output.

**Diagnostic**: to confirm the active backend and model:

```console
agy --model "Gemini 3.1 Pro (High)" --dangerously-skip-permissions -p "Report your exact model ID and reasoning level." </dev/null
```

## Shell Resilience

All commands use `command -v` (POSIX-portable) instead of `which` for CLI detection. Prompts are written to the session directory (`$SESSION_DIR/pass-NNNN/prompt.md`) to avoid shell metacharacter injection while also persisting artifacts. stderr is captured per-pass (`$SESSION_DIR/pass-NNNN/stderr/<model>.txt`) for failure diagnostics. A structured retry protocol classifies failures (timeout, rate-limit, crash, empty output) and retries retryable failures once before marking a model unavailable.

## Language-Agnostic Design

All commands discover project-specific tooling by reading AGENTS.md / CLAUDE.md at runtime. Quality gates, test commands, and conventions are never hardcoded — they work with any language or framework.
