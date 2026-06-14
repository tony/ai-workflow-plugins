# Design: `agy` (Antigravity) as the preferred Google backend

**Date:** 2026-06-13
**Status:** Approved (design phase)
**Scope:** `plugins/model-cli`, `plugins/weave`

## Why

Google is shutting off the standalone `gemini` CLI on **2026-06-18** (it now
prints a migration banner pointing at the Antigravity CLI). `agy` (Antigravity)
is the multi-model successor and defaults to Gemini. Rather than add a
disconnected fourth model, **`agy` becomes the preferred backend for the existing
"Gemini/Google" lane** wherever that lane appears, with `gemini` and then the
Cursor `agent` CLI as fallbacks so the lane keeps working before and after the
shutdown.

## Verified `agy` behavior

Confirmed empirically on this machine (signed in, current auth):

| Fact | Detail |
|------|--------|
| Non-interactive run | `agy -p --model "Gemini 3.1 Pro (High)" --dangerously-skip-permissions "<prompt>" </dev/null` returns text, exit 0 |
| Stdin | `</dev/null` required to avoid a stdin-wait hang (same as `codex`) |
| Model string | `--model "Gemini 3.1 Pro (High)"` (a display name from `agy models`) is accepted |
| Read-only guarantee | Print mode **without** `--dangerously-skip-permissions` does not write files — no approval path exists non-interactively |
| Plan mode | No `--approval-mode plan` equivalent to `gemini`'s |
| `--sandbox` | Requires a **separate** Google OAuth login (different scopes); intentionally avoided |
| Workspace | `--add-dir <path>` (repeatable) sets the workspace; `agy` also prints a harmless `Shell cwd was reset to <repo>` line to stderr and has its own cwd notion |
| Models | `agy models`: Gemini 3.5 Flash (Low/Medium/High), Gemini 3.1 Pro (Low/High), Claude Sonnet 4.6 (Thinking), Claude Opus 4.6 (Thinking), GPT-OSS 120B (Medium) |

Resolution chain (decided): **`agy` → `gemini` → `agent --model gemini-3.1-pro`.**
Model pin: **Gemini 3.1 Pro (High)**. Lesser fallback: **Gemini 3.5 Flash (High)**.

## Part 1 — `plugins/model-cli`

### 1a. New skill `skills/agy/SKILL.md`

Mirror the existing `gemini` skill's 6-step structure verbatim (timeout parsing,
temp-file prompt, `mode:plan` preamble, failure classification, cleanup). Only the
backend resolution differs.

- **Frontmatter:** `name: agy`, `user-invocable: true`, **auto-invocable** (no
  `disable-model-invocation`), `allowed-tools` and `argument-hint` identical to the
  gemini skill. Description: delegate to Google's Gemini via the Antigravity (`agy`)
  CLI; detects `agy`, falls back to `gemini`, then `agent --model gemini-3.1-pro`.
- **Step 1 — Detect CLI:** check `agy`, then `gemini`, then `agent`.
- **Resolution (priority order):**
  1. `agy` → `agy -p --model "Gemini 3.1 Pro (High)" --dangerously-skip-permissions "$(cat "$TMPFILE")" </dev/null`
  2. else `gemini` → `gemini -m gemini-3-pro-preview -y --skip-trust -p`
  3. else `agent` → `agent -p -f --model gemini-3.1-pro`
  4. else → report all unavailable and stop
- **stderr file:** `/tmp/mc-stderr-agy.txt`.
- **Step 5 — Failure handling:** same classification as the gemini skill. On `agy`
  failure (or credit-exhaustion) escalate to `gemini`, then to `agent`. Lesser
  fallback: `agy -p --model "Gemini 3.5 Flash (High)"`, then `gemini -m
  gemini-3-flash-preview`. Reuse the gemini skill's credit-exhaustion stderr
  patterns (`RESOURCE_EXHAUSTED`, `quota exceeded`, `insufficient_quota`,
  `billing`, HTTP 429, …).

### 1b. Update `skills/gemini/SKILL.md`

`agy` supersedes the `gemini` CLI, so:

- Add `disable-model-invocation: true` (manual alias only — mirrors the
  `codex`-auto / `gpt`-manual pattern, preventing duplicate auto-triggering with
  the new auto-invocable `agy` skill).
- Reorder resolution to **`agy` → `gemini` → `agent`** so `/model-cli:gemini`
  keeps working after 2026-06-18.
- Description notes `agy` is now preferred; this entry remains as a manual
  invocation point.

### 1c. Docs / manifests

- `README.md`: add the `agy` row to the skills table and fallback-resolution
  table; note the new auto/manual split (agy auto, gemini manual); add the
  Antigravity CLI to prerequisites with the install command
  (`curl -fsSL https://antigravity.google/cli/install.sh | bash`) and link
  `https://antigravity.google/product/antigravity-cli`.
- `.claude-plugin/plugin.json` + root `.claude-plugin/marketplace.json`: update the
  model-cli `description` to mention Antigravity/agy.

## Part 2 — `plugins/weave` (rename the lane to Antigravity)

Swap the Gemini lane's backend to `agy` and **rename the lane**. Slug `agy`
(matching the binary and the short-slug convention of `gpt`/`claude`); display
label **"Antigravity"** in tables/prose.

### Rename map

| Old | New |
|-----|-----|
| `outputs/gemini.md`, `gemini-vN.md` | `outputs/agy.md`, `agy-vN.md` |
| `stderr/gemini.txt`, `stderr/judge-gemini.txt` | `stderr/agy.txt`, `stderr/judge-agy.txt` |
| worktree `*-weave-gemini` | `*-weave-agy` |
| branch `weave/gemini/<ts>` | `weave/agy/<ts>` |
| `gemini.diff` | `agy.diff` |
| `"models": [… "gemini" …]` | `"models": [… "agy" …]` |
| label `**Gemini**` / "Gemini" | `**Antigravity**` / "Antigravity" |

### Per-command edits (10 files)

`ask, plan, review, brainstorm, brainstorm-and-refine, refine, execute, prompt,
architecture, serene-bliss` — apply uniformly:

1. **Detection:** add `command -v agy …` ahead of `command -v gemini …`.
2. **Resolution table row:** primary `agy` (`agy` binary, `Gemini 3.1 Pro (High)`)
   → fallback `gemini` (`gemini-3-pro-preview`) → `agent --model gemini-3.1-pro`.
3. **Invocation snippets:**
   - **Read-only commands** (`ask, plan, review, brainstorm,
     brainstorm-and-refine, refine`, incl. judge invocations) — primary:
     `(cd "$SESSION_DIR" && <timeout> agy -p --model "Gemini 3.1 Pro (High)" --add-dir "$REPO_TOPLEVEL" "$(cat …)" </dev/null >…/agy.md 2>…/agy.txt)`.
     No `--dangerously-skip-permissions` → read-only. Keep the `(cd "$SESSION_DIR")`
     backstop. gemini and agent fallbacks retain their existing read-only flags
     (`--approval-mode plan` / `--mode plan`).
   - **Write command** (`execute`) — primary:
     `(cd "$WORKTREE" && <timeout> agy -p --model "Gemini 3.1 Pro (High)" --dangerously-skip-permissions --add-dir "$WORKTREE" "$(cat …)" </dev/null >…/agy.md 2>…/agy.txt)`,
     where `$WORKTREE = $REPO_TOPLEVEL/../$REPO_SLUG-weave-agy`.
4. **Lesser-model note:** `gemini-3-flash-preview for Gemini` → `Gemini 3.5 Flash
   (High) via agy, then gemini-3-flash-preview`.

### Supporting files

- `README.md`: tagline, model-detection step, plan-mode table row, round-robin
  judge prose (Claude → Antigravity → …), directory-tree examples
  (`agy.md`/`agy-vN.md`/`agy.diff`/`agy/`), `"models"` example array, prerequisites
  row (Antigravity CLI), and the **"Gemini reasoning depth"** section — rewrite to
  describe `agy`'s `--model "Gemini 3.1 Pro (High)"` selection, keeping a short note
  about the `gemini` fallback alias.
- `docs/repo-guard-protocol.md`: replace the gemini read-only example with the
  `agy` read-only invocation (`--add-dir` + no skip-permissions + `(cd
  "$SESSION_DIR")` backstop); update the "Gemini/GPT sub-agent" wording.
- `commands/fix-review.md`, `skills/brainstorm/SKILL.md`,
  `skills/serene-bliss/SKILL.md`, `.claude-plugin/plugin.json` + root
  `marketplace.json` weave entry: replace "Gemini" with "Antigravity" in
  model-list prose.
- `commands/fix-review.md` plan-mode hints mention "Gemini `/plan`" — update the
  label to Antigravity (agy has no plan mode; it is a host plan-mode hint, so keep
  the generic Cursor/Codex guidance).

### Open verification item (implementation-time)

`agy`'s cwd-reset vs. worktree isolation in `execute` is **unconfirmed** — in
probes `agy -p` chatted instead of writing, so where it writes under `--add-dir` +
a worktree `cd` is not yet observed. Before finalizing `execute.md`, verify against
a throwaway worktree that `agy` writes inside the worktree (not the main repo). If
`agy` proves unreliable for the write lane, `agent` remains the write fallback.

## Out of scope / intentionally untouched

- `docs/specs/2026-05-17-clean-output-and-plan-handoff.md` — a dated point-in-time
  record; left as historical (one `gemini-vN.md` reference).
- No rename of the Claude or GPT lanes.
- `agy`'s multi-model capability (it can also run Claude/GPT-OSS) is not exposed;
  the lane stays pinned to Gemini models.

## Deliverable flow

Spec (this file, committed) → writing-plans → implementation → verification.
