# Design: `agy` (Antigravity) as the preferred Google backend

**Date:** 2026-06-13
**Status:** Implemented
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

Confirmed empirically during implementation (signed in, current auth):

| Fact | Detail |
|------|--------|
| Non-interactive run | `agy --model "Gemini 3.1 Pro (High)" --dangerously-skip-permissions -p "<prompt>" </dev/null` returns text, exit 0 |
| Flag order | `-p`/`--print` is a Go-style value-flag: it must come **last**, after every other flag, or it swallows the next flag as the prompt |
| Stdin | `</dev/null` required to avoid a stdin-wait hang (same as `codex`) |
| Model string | `--model "Gemini 3.1 Pro (High)"` (a display name from `agy models`) is accepted |
| Write behavior | Print mode reads **and** writes even without `--dangerously-skip-permissions`; read-only isolation comes from a disposable `HEAD` worktree (Repo Guard Layer 1), not from withholding the flag |
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
  1. `agy` → `agy --model "Gemini 3.1 Pro (High)" --dangerously-skip-permissions -p "$(cat "$TMPFILE")" </dev/null`
  2. else `gemini` → `gemini -m gemini-3-pro-preview -y --skip-trust -p`
  3. else `agent` → `agent -p -f --model gemini-3.1-pro`
  4. else → report all unavailable and stop
- **stderr file:** `/tmp/mc-stderr-agy.txt`.
- **Step 5 — Failure handling:** same classification as the gemini skill. On `agy`
  failure (or credit-exhaustion) escalate to `gemini`, then to `agent`. Lesser
  fallback: `agy --model "Gemini 3.5 Flash (High)" --dangerously-skip-permissions -p`, then `gemini -m
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
     brainstorm-and-refine, refine`, incl. judge invocations) — agy has no
     read-only mode, so the primary runs in a disposable `HEAD` worktree (any write
     lands in the throwaway worktree, removed after); gemini/agent fallbacks keep
     their native read-only flags (`--approval-mode plan` / `--mode plan`):
     `(AGY_RO_WT="${REPO_TOPLEVEL}-weave-agy-ro"; git -C "$REPO_TOPLEVEL" worktree add -q --detach "$AGY_RO_WT" HEAD && (cd "$AGY_RO_WT" && <timeout> agy --model "Gemini 3.1 Pro (High)" --add-dir "$AGY_RO_WT" --dangerously-skip-permissions -p "$(cat …)" </dev/null >…/agy.md 2>…/agy.txt); git -C "$REPO_TOPLEVEL" worktree remove --force "$AGY_RO_WT")`.
   - **Write command** (`execute`) — primary:
     `(cd "$WORKTREE" && <timeout> agy --model "Gemini 3.1 Pro (High)" --dangerously-skip-permissions --add-dir "$WORKTREE" -p "$(cat …)" </dev/null >…/agy.md 2>…/agy.txt)`,
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
- `docs/repo-guard-protocol.md`: document the `agy` read-only invocation as a
  disposable `HEAD` worktree (Layer 1) with `--add-dir` scoped to the worktree,
  removed after; update the "Gemini/GPT sub-agent" wording to "Antigravity/GPT".
- `commands/fix-review.md`, `skills/brainstorm/SKILL.md`,
  `skills/serene-bliss/SKILL.md`, `.claude-plugin/plugin.json` + root
  `marketplace.json` weave entry: replace "Gemini" with "Antigravity" in
  model-list prose.
- `commands/fix-review.md` plan-mode hints mention "Gemini `/plan`" — update the
  label to Antigravity (agy has no plan mode; it is a host plan-mode hint, so keep
  the generic Cursor/Codex guidance).

### Verification (resolved)

`agy`'s worktree isolation was confirmed against the live repo: launched with
`(cd "$WORKTREE" … --add-dir "$WORKTREE")`, `agy` writes inside that worktree and
the main tree's `git status` is byte-identical before and after; the read-only
disposable-worktree pattern was verified the same way. `agent` remains the write
fallback if `agy` is unavailable.

## Out of scope / intentionally untouched

- `docs/specs/2026-05-17-clean-output-and-plan-handoff.md` — a dated point-in-time
  record; left as historical (one `gemini-vN.md` reference).
- No rename of the Claude or GPT lanes.
- `agy`'s multi-model capability (it can also run Claude/GPT-OSS) is not exposed;
  the lane stays pinned to Gemini models.
