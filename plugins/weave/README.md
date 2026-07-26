# weave

Weave prompts across independent adversarial participants in parallel — plan,
execute, review, and synthesize their strongest work. Host-native sub-agents
are the default; separate model CLIs are available by explicit choice.

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
| `/weave:ask` | Ask adversarial participants a question, synthesize the best answer |
| `/weave:plan` | Get independent implementation plans, synthesize the best plan |
| `/weave:prompt` | Run a prompt in isolated worktrees, pick the best implementation |
| `/weave:execute` | Run a task in isolated worktrees, synthesize the best parts of each |
| `/weave:architecture` | Generate project scaffolding, conventions, skills, and architectural docs, then synthesize the best architecture |
| `/weave:review` | Run independent code reviews, produce a consensus-weighted report |
| `/weave:fix-review` | Fix review findings as atomic commits with test coverage |
| `/weave:brainstorm` | Generate independent original ideas from each participant, with optional multiple variants |
| `/weave:refine` | Iteratively improve an artifact through adversarial critique and weaving |
| `/weave:brainstorm-and-refine` | Full pipeline: brainstorm originals, then iteratively judge, weave, and refine |
| `/weave:serene-bliss` | Three-lens DX brainstorm-and-refine (Bliss, Serenity, Sublimity) with panel judging |

## Skills

Skills provide auto-discovery — they trigger when the user's intent matches the skill description.

| Skill | Triggers on |
|-------|-------------|
| `weave:brainstorm` | "brainstorm", "give me ideas", "multiple approaches", "explore alternatives" |
| `weave:refine` | "refine this", "improve this", "make this better", "iterate on this" |
| `weave:brainstorm-and-refine` | "brainstorm and refine", "generate ideas then improve", "explore then synthesize" |
| `weave:serene-bliss` | "serene bliss", "DX bliss", "DX serenity", "DX sublimity", "reader happiness" |

## How It Works

The orchestration commands follow consistent multi-phase workflows. Of the original six, plan, prompt, execute, and architecture use **targeted conflict resolution** for multi-pass (passes only address unresolved conflicts), while ask and review use **residual re-attack** (passes address only the prior pass's unresolved residuals). The new three (brainstorm, refine, brainstorm-and-refine) use **expansive weaving** — each pass is a full judge-pick-best-incorporate-strengths-address-weaknesses cycle. The `fix-review` command is a separate remediation workflow for applying review findings as atomic commits.

1. **Choose workers** — Use `--workers=subagents|model-clis` or answer the first configuration prompt. Host-native sub-agents are recommended and selected automatically in headless mode.
2. **Configure** — Parse `--passes`, `--timeout`, `--mode` flags and prompt for any remaining settings. CLI timeouts apply only to `model-clis`.
3. **Run in parallel** — Dispatch the Maintainer, Skeptic, and Builder as independent participants.
4. **Synthesize** — Compare outputs, verify claims against the codebase, and combine the best elements.
5. **Refine** (multi-pass) — Optionally re-attack the prior pass's unresolved residuals with all participants for deeper results.

When `model-clis` is selected, Weave detects `agy`, `gemini`, `codex`,
and `agent` only after that explicit choice. Retry and fallback stay
within the selected worker backend; Weave never switches between
sub-agents and model CLIs without asking.

### Protocols

All commands share quality protocols that decorrelate participant outputs and improve synthesis:

- **Context packets** — a structured bundle (conventions, repo state, key snippets) included verbatim in every participant prompt so all lanes work from the same information
- **Role differentiation** — each lane receives a distinct evaluation lens (Maintainer, Skeptic, Builder) to reduce shared blind spots
- **Blind judging** — participant outputs are randomly labeled (A/B/C) during scoring to prevent identity bias (ask/plan/prompt/execute/architecture/review)
- **Structured synthesis** — a five-step protocol (verify claims, score with rubric, adjudicate conflicts, converge, critic) backed by codebase evidence (ask/plan/prompt/execute/architecture/review)
- **Judge-weave-distribute** — pick the best, incorporate strengths from runners-up, redistribute for another round (refine/brainstorm-and-refine)
- **Consensus signal** — findings and disagreements carry per-lane agreement tags (unanimous/majority/split/single); split items are surfaced with both positions, never silently adjudicated away (ask/review; spec in `references/ensemble-techniques.md`)

### Repo Guard Protocol

All weave commands enforce a 5-layer guard that prevents sessions from
modifying repository files. See `docs/repo-guard-protocol.md` for
the full specification.

| Layer | Defense | Scope |
|-------|---------|-------|
| 1 | Isolated worktree per host-native participant; native CLI read-only sandbox or disposable worktree for model-CLI lanes | Read-only commands |
| 2 | Pre-session repo fingerprint (HEAD + `git status`) | All commands |
| 3 | Post-CLI repo state verification + auto-revert | `model-clis` lanes |
| 4 | Prompt hardening ("CRITICAL: Do NOT write files") | All commands |
| 5 | Session-end verification against fingerprint | All commands |

Default host-native sub-agents run in session-scoped isolated worktrees under
the host's permissions and prompt hardening. Read-only worktrees are
disposable; write participants retain separate branch worktrees through
comparison and refinement. Native workers never receive the writable user
checkout.

With `--workers=model-clis`, **read-only commands** run external CLIs in their native read-only
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

With the default native backend, **prompt**, **execute**, and
**architecture** create an isolated git worktree for every participant. The
opt-in model-CLI backend preserves its existing host lane and isolates its
external lanes in separate worktrees. After comparison:
- **prompt** picks one winner
- **execute** cherry-picks the best parts from each participant
- **architecture** cherry-picks the best conventions, skills, agents, and scaffolding per file

**fix-review** processes findings from a review, applying each as an atomic commit with test coverage. Multi-pass does not apply to fix-review since it is already iterative.

### Brainstorm & Refine Commands

**brainstorm** generates independent originals from each participant with no synthesis. Use `--variants=N` (1-3) to get multiple originals per participant, each with a distinct creative-direction preamble (conventional, creative, contrarian). Override preambles with `--preamble='...'`.

**refine** takes a single artifact (inline text or file path) and iteratively improves it. Each pass: all participants critique and improve → judge picks the best → identifies strengths in runners-up → weaves a revised version → distributes back to all participants. Uses `--passes=N` (1-5, default 2).

**brainstorm-and-refine** is the full pipeline: brainstorm originals, present them, let the user choose which enter refinement, then run the refine cycle. A transition gate always asks the user before proceeding.

## Plan Mode

Three commands use plan mode, but in two distinct patterns:

### Temporary plan mode (review, fix-review)

The **review** and **fix-review** commands enter plan mode to create an
orchestration strategy, present it for user approval, then **exit plan mode**
before executing. This is the "plan then execute" pattern.

**review** plans: branch summary, review focus areas, relevant conventions,
known concerns, and worker prompt strategy.

**fix-review** plans: findings inventory, validity pre-assessment, fix
ordering, test strategy per finding, risk assessment, and expected commit
sequence.

### Persistent plan mode (plan)

The **plan** command enters plan mode at the start and **stays in plan mode
throughout** — the host's plan file is the deliverable. Host-native
sub-agents handle non-readonly operations such as git commands, session
directory setup, optional model-CLI execution, and artifact persistence.

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

## Worker Architecture

The default backend launches three independent host-native sub-agents:
Maintainer, Skeptic, and Builder. They receive the same task and context
packet but do not see one another's answers before producing their own.
Native artifacts use the IDs `maintainer`, `skeptic`, and `builder`; this
mode does not claim that the participants use different models. Each WorkItem
runs in an isolated worktree; the orchestrator persists the returned artifact
and removes only that exact worktree after use.

The opt-in `model-clis` backend preserves the host, Antigravity, and GPT
lanes and their artifact IDs: `claude`, `agy`, and `gpt`. The GPT lane
normally runs through the `codex` CLI. Wrapper sub-agents run the selected
executors and keep their existing fallback chains.

## Cascade Mode

`--cascade` (ask, review) starts with the Maintainer lane through the selected
worker backend. It self-verifies against the codebase and launches the Skeptic
and Builder only when a confidence trigger fires or the user escalates. The
worker backend never changes during escalation. Trigger definitions live in
`references/ensemble-techniques.md`.

## Multi-Pass Refinement

Multi-pass runs additional rounds after the first synthesis. For ask and review, pass N ≥ 2 is a residual re-attack: participants receive only the unresolved items from the prior pass — conflicts evidence could not settle, failed claim verification, leftover critic findings, split-consensus items — and their resolutions merge back into the prior synthesis, which otherwise carries forward verbatim. An empty residual ledger means convergence and stops early. The refine command scopes each redistribution round's critique to the pass's residual focus.

### Flags

Control pass count, timeout, and execution mode with explicit flags:

| Flag | Values | Default | Example |
|------|--------|---------|---------|
| `--workers=...` | `subagents` or `model-clis` | `subagents` | `/weave:ask question --workers=model-clis` |
| `--passes=N` | 1–5 | 1 (refine: 2) | `/weave:plan add auth --passes=2` |
| `--timeout=N\|none` | seconds or `none` | command-specific (`model-clis` only) | `/weave:ask question --timeout=300` |
| `--mode=fast\|balanced\|deep` | mode preset | `balanced` | `/weave:execute task --mode=deep` |
| `--cascade` | flag (ask, review) | off | `/weave:ask question --cascade` |
| `--variants=N` | 1–3 | 1 | `/weave:brainstorm idea --variants=2` |
| `--judge=host\|round-robin` | Who judges each refinement pass | `host` | `/weave:refine draft --judge=round-robin` |
| `--preamble=...` | text | built-in | `/weave:brainstorm idea --preamble='focus on perf'` |

Mode presets vary by command. For the original commands (ask, plan, prompt, execute, architecture, review): `fast` (1 pass, 0.5× timeout), `balanced` (1 pass, 1× timeout), `deep` (2 passes, 1.5× timeout). For brainstorm: presets control variants and timeout (deep = 2 variants). For refine: presets control passes and timeout (balanced = 2 passes, deep = 3 passes). For brainstorm-and-refine: presets control variants, passes, and timeout (deep = 2 variants, 3 passes).

Default timeouts per command: ask (450s), plan (600s), prompt (600s), review (900s), execute (1200s), architecture (1200s).

Legacy trigger words (`multipass`, `x<N>`, `timeout:<seconds>`) are still recognized as aliases for backward compatibility.

### Judge Modes

The `--judge` flag controls who evaluates participant outputs during refinement passes (refine
and brainstorm-and-refine commands only).

`--judge=host` (default): The host agent judges every pass.

`--judge=round-robin`: Judging rotates across successful participants. Native
mode launches a fresh role-matched sub-agent; model-CLI mode uses the resolved
provider backend for that lane. The host always weaves and falls back to host
judging when a judge response cannot be parsed.

### Interactive Configuration

When flags are provided, the corresponding interactive question is skipped. Otherwise, commands prompt via `AskUserQuestion`:

1. **Workers** (skipped when `--workers` is provided) — choose recommended host-native sub-agents or separate model CLIs.
2. **Pass count** (skipped when `--passes` is provided) — choose single pass (1), multipass (2), or triple pass (3).
3. **Timeout** (`model-clis` only; skipped when `--timeout` is provided) — choose the default, quick (0.5× default), long (1.5× default), or no timeout.

Headless mode defaults to `subagents`. If the host cannot create native
sub-agents, Weave stops and explains how to rerun with
`--workers=model-clis`; it never launches separate CLIs implicitly.

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

All commands persist participant outputs, prompts, and synthesis results to a structured directory under `$AI_AIP_ROOT`. This enables post-session inspection, selective reference to prior pass artifacts during multi-pass refinement, and lightweight resume tracking.

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

The tree below shows `model-clis` lane IDs. With the default `subagents`
backend, replace `claude`, `agy`, and `gpt` with `maintainer`, `skeptic`, and
`builder`; CLI stderr files are absent.

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

Only files that differ from HEAD are snapshotted into
`files/<participant>/`. The directory structure mirrors the repository
layout. Deleted files appear in the diff only, not as snapshots. This enables
post-session inspection and multi-pass file-level cross-referencing without
depending on worktree persistence.

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
  "worker_backend": "subagents",
  "participants": ["maintainer", "skeptic", "builder"],
  "executors": {
    "maintainer": "host-native",
    "skeptic": "host-native",
    "builder": "host-native"
  },
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
| `worker_backend` | `"subagents"` or `"model-clis"` |
| `participants` | Successful role IDs (`subagents`) or lane artifact IDs (`model-clis`) |
| `executors` | Participant ID to actual executor mapping |
| `models` | Resolved providers or models; present only for `model-clis` |
| `judge_mode` | `"host"` or `"round-robin"` (refine/brainstorm-and-refine only) |
| `completed_passes` | How many passes finished |
| `prompt_summary` | First 120 chars of the user's prompt |
| `created_at` | ISO 8601 UTC timestamp of session start |
| `updated_at` | ISO 8601 UTC timestamp of last update |

The session is updated after each pass (`completed_passes` incremented, `updated_at` refreshed) and at session end (`status` set to `completed`). A `latest` symlink is updated at session end to point to the most recent completed session.

### Event Log (`events.jsonl`)

Each session directory contains an `events.jsonl` file with one JSON object per line:

```json
{"event":"session_start","timestamp":"2026-02-10T14:30:22Z","command":"ask","worker_backend":"subagents","participants":["maintainer","skeptic","builder"]}
```

```json
{"event":"pass_complete","timestamp":"2026-02-10T14:32:45Z","pass":1,"participants_completed":["maintainer","skeptic","builder"]}
```

Refine and brainstorm-and-refine commands include additional fields in `pass_complete`:

```json
{"event":"pass_complete","timestamp":"2026-02-10T14:32:45Z","pass":1,"winner":"maintainer","winner_score":35,"woven":true,"judged_by":"host"}
```

```json
{"event":"session_complete","timestamp":"2026-02-10T14:32:50Z","completed_passes":1}
```

To list sessions, scan `session.json` files under `$AI_AIP_ROOT/repos/<slug>--<hash>/sessions/<command>/`. The `latest` symlink points to the most recently completed session for quick access.

## Prerequisites

The default backend requires a host that can launch sub-agents. No separate
provider CLI or account is required.

To use `--workers=model-clis`, install one or more supported CLIs:

| CLI | Model | Install |
|-----|-------|---------|
| `agy` | Gemini (via Antigravity) | [Antigravity CLI](https://antigravity.google/product/antigravity-cli) |
| `gemini` | Gemini (fallback; gemini CLI retired 2026-06-18) | [Gemini CLI](https://github.com/google-gemini/gemini-cli) |
| `codex` | GPT | [Codex CLI](https://github.com/openai/codex) |
| `agent` | Any (fallback) | [Agent CLI](https://cursor.com/cli) |

### macOS timeout support

Model-CLI commands are wrapped with `timeout` (GNU coreutils) to enforce time
limits. On macOS, install GNU coreutils to get `gtimeout`:

```console
brew install coreutils
```

If neither `timeout` nor `gtimeout` is found, commands run without a time limit.

If no model CLI resolves, Weave reports the unavailable lanes. It does not
cross-fallback to host-native sub-agents.

### Model-CLI selection and reasoning depth

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

The `model-clis` backend uses `command -v` (POSIX-portable) instead of
`which` for CLI detection. Prompts are written to the session directory
(`$SESSION_DIR/pass-NNNN/prompt.md`) to avoid shell metacharacter injection
while also persisting artifacts. stderr is captured per pass for failure
diagnostics. A structured retry protocol classifies failures and retries
within the selected lane before marking that participant unavailable.

## Language-Agnostic Design

All commands discover project-specific tooling by reading AGENTS.md / CLAUDE.md at runtime. Quality gates, test commands, and conventions are never hardcoded — they work with any language or framework.
