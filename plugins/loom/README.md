# loom

Weave prompts across Claude, Gemini, and GPT in parallel — plan, execute, review, and synthesize the best of all models.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install loom@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/loom:ask` | Ask all models a question, synthesize the best answer |
| `/loom:plan` | Get implementation plans from all models, synthesize the best plan |
| `/loom:prompt` | Run a prompt in isolated worktrees, pick the best implementation |
| `/loom:execute` | Run a task in isolated worktrees, synthesize the best parts of each |
| `/loom:architecture` | Generate project scaffolding, conventions, skills, and architectural docs, then synthesize the best architecture |
| `/loom:review` | Run code review with all models, produce consensus-weighted report |
| `/loom:fix-review` | Fix review findings as atomic commits with test coverage |
| `/loom:brainstorm` | Generate independent original ideas from each model, with optional multiple variants |
| `/loom:refine` | Iteratively improve an artifact through multi-model critique and weaving |
| `/loom:brainstorm-and-refine` | Full pipeline: brainstorm originals, then iteratively judge, weave, and refine |

## Skills

Skills provide auto-discovery — they trigger when the user's intent matches the skill description.

| Skill | Triggers on |
|-------|-------------|
| `loom:brainstorm` | "brainstorm", "give me ideas", "multiple approaches", "explore alternatives" |
| `loom:refine` | "refine this", "improve this", "make this better", "iterate on this" |
| `loom:brainstorm-and-refine` | "brainstorm and refine", "generate ideas then improve", "explore then synthesize" |

## How It Works

The orchestration commands follow consistent multi-phase workflows. The original six (ask, plan, prompt, execute, architecture, review) use **targeted conflict resolution** for multi-pass — subsequent passes only address unresolved conflicts. The new three (brainstorm, refine, brainstorm-and-refine) use **expansive weaving** — each pass is a full judge-pick-best-incorporate-strengths-address-weaknesses cycle. The `fix-review` command is a separate remediation workflow for applying review findings as atomic commits.

1. **Configure** — Parse `--passes`, `--timeout`, `--mode` flags and prompt for any remaining settings.
2. **Detect models** — Check for `gemini`, `codex`, and `agent` CLIs. Use native CLIs when available, fall back to the `agent` CLI with `--model` flags.
3. **Run in parallel** — Execute the task across all available models simultaneously.
4. **Synthesize** — Compare outputs, verify claims against the codebase, and combine the best elements.
5. **Refine** (multi-pass) — Optionally re-run all models with the prior synthesis as context for deeper results.

### Protocols

All commands share four quality protocols that decorrelate model outputs and improve synthesis:

- **Context packets** — a structured bundle (conventions, repo state, key snippets) included verbatim in every model prompt so all models work from the same information
- **Role differentiation** — each model receives a distinct evaluation lens (Maintainer, Skeptic, Builder) to reduce shared blind spots
- **Blind judging** — model outputs are randomly labeled (A/B/C) during scoring to prevent brand bias (ask/plan/prompt/execute/architecture/review)
- **Structured synthesis** — a five-step protocol (verify claims, score with rubric, adjudicate conflicts, converge, critic) backed by codebase evidence (ask/plan/prompt/execute/architecture/review)
- **Judge-weave-distribute** — pick the best, incorporate strengths from runners-up, redistribute for another round (refine/brainstorm-and-refine)

### Read-Only Commands

**ask**, **plan**, and **review** do not modify files. They gather multiple perspectives and synthesize a single best result.

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

## Sub-Agent Architecture

All loom commands use the Task tool to delegate work to sub-agents. Each model execution runs in its own sub-agent,
enabling true parallel dispatch when the host supports it.

| Role | Agent type | Mode | Purpose |
|------|-----------|------|---------|
| Claude model | `general-purpose` | default | Reads codebase, produces response |
| Gemini model | `general-purpose` | default | Runs `gemini`/`agent` CLI via Bash |
| GPT model | `general-purpose` | default | Runs `codex`/`agent` CLI via Bash |
| Critic | `general-purpose` | default | Challenges synthesized result |
| Context gather | `general-purpose` | default | Runs git commands (plan mode only) |
| Session setup | `general-purpose` | default | Creates session dir, detects models (plan mode only) |

Sub-agents run with `mode: "default"` so they can use Bash, Write, and Edit
even when the parent agent is in plan mode. Each sub-agent receives all
needed context in its prompt since sub-agents don't share the parent's
conversation state.

## Multi-Pass Refinement

Multi-pass re-runs all models with the prior synthesis prepended as context, allowing each model to challenge, deepen, or confirm the previous round's results. This produces higher-quality outputs at the cost of additional model invocations.

### Flags

Control pass count, timeout, and execution mode with explicit flags:

| Flag | Values | Default | Example |
|------|--------|---------|---------|
| `--passes=N` | 1–5 | 1 (refine: 2) | `/loom:plan add auth --passes=2` |
| `--timeout=N\|none` | seconds or `none` | command-specific | `/loom:ask question --timeout=300` |
| `--mode=fast\|balanced\|deep` | mode preset | `balanced` | `/loom:execute task --mode=deep` |
| `--variants=N` | 1–3 | 1 | `/loom:brainstorm idea --variants=2` |
| `--judge=host\|round-robin` | Who judges each refinement pass | `host` | `/loom:refine draft --judge=round-robin` |
| `--preamble=...` | text | built-in | `/loom:brainstorm idea --preamble='focus on perf'` |

Mode presets vary by command. For the original commands (ask, plan, prompt, execute, architecture, review): `fast` (1 pass, 0.5× timeout), `balanced` (1 pass, 1× timeout), `deep` (2 passes, 1.5× timeout). For brainstorm: presets control variants and timeout (deep = 2 variants). For refine: presets control passes and timeout (balanced = 2 passes, deep = 3 passes). For brainstorm-and-refine: presets control variants, passes, and timeout (deep = 2 variants, 3 passes).

Default timeouts per command: ask (450s), plan (600s), prompt (600s), review (900s), execute (1200s), architecture (1200s).

Legacy trigger words (`multipass`, `x<N>`, `timeout:<seconds>`) are still recognized as aliases for backward compatibility.

### Judge Modes

The `--judge` flag controls who evaluates model outputs during refinement passes (refine
and brainstorm-and-refine commands only).

`--judge=host` (default): The host agent (Claude) judges every pass. This is the most
reliable mode since the host can read session files and parse varied output formats.

`--judge=round-robin`: Judging rotates across available models — Claude, then Gemini,
then GPT, cycling back. External models receive a structured judge prompt with all
model outputs inline and produce scores, winner selection, and runner-up analysis.
The host agent always weaves regardless of who judged. If an external judge's output
is unparseable, that pass falls back to host judging.

The rotation is built from available models only. If only Claude and Gemini are
detected, the rotation is Claude → Gemini → Claude → Gemini. Pass 1 always starts
with Claude (index 0).

### Interactive Configuration

When flags are provided, the corresponding interactive question is skipped. Otherwise, commands prompt via `AskUserQuestion`:

1. **Pass count** (skipped when `--passes` is provided) — choose single pass (1), multipass (2), or triple pass (3).
2. **Timeout** (skipped when `--timeout` is provided) — choose the default, quick (0.5× default), long (1.5× default), or no timeout.

In headless mode (`claude -p`), pass count uses the flag value if provided, otherwise defaults to 1. Timeout uses the flag value if provided, otherwise the per-command default.

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
            │       ├── pass-0001/
            │       │   ├── prompt.md
            │       │   ├── synthesis.md
            │       │   ├── outputs/
            │       │   │   ├── claude.md
            │       │   │   ├── gemini.md
            │       │   │   └── gpt.md
            │       │   └── stderr/
            │       │       ├── gemini.txt
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
            │       │   ├── gemini-v1.md
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
│   ├── gemini.diff
│   └── gpt.diff
└── files/
    ├── claude/
    │   └── <repo-relative paths of changed files>
    ├── gemini/
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
  "models": ["claude", "gemini", "gpt"],
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
{"event":"session_start","timestamp":"2026-02-10T14:30:22Z","command":"ask","models":["claude","gemini","gpt"]}
```

```json
{"event":"pass_complete","timestamp":"2026-02-10T14:32:45Z","pass":1,"models_completed":["claude","gemini","gpt"]}
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

At minimum, Claude (this agent) is always available. For loom functionality, install one or more external CLIs:

| CLI | Model | Install |
|-----|-------|---------|
| `gemini` | Gemini | [Gemini CLI](https://github.com/google-gemini/gemini-cli) |
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

## Shell Resilience

All commands use `command -v` (POSIX-portable) instead of `which` for CLI detection. Prompts are written to the session directory (`$SESSION_DIR/pass-NNNN/prompt.md`) to avoid shell metacharacter injection while also persisting artifacts. stderr is captured per-pass (`$SESSION_DIR/pass-NNNN/stderr/<model>.txt`) for failure diagnostics. A structured retry protocol classifies failures (timeout, rate-limit, crash, empty output) and retries retryable failures once before marking a model unavailable.

## Language-Agnostic Design

All commands discover project-specific tooling by reading AGENTS.md / CLAUDE.md at runtime. Quality gates, test commands, and conventions are never hardcoded — they work with any language or framework.
