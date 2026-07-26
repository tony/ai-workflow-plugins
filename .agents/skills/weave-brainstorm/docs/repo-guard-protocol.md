# Repo Guard Protocol

Prevents weave sessions from modifying repository files. All phases — main
agents, sub-agents, judges — must keep mutations within `$SESSION_DIR` (for
read-only commands) or worktrees (for write commands). This protocol applies
to every weave command except `fix-review` (which intentionally modifies the
repository).

The worker backend determines which defenses run. Host-native sub-agents are
the default: every participant receives an isolated worktree, including
read-only participants. The separate model-CLI backend additionally uses the
CLI-specific sandbox and post-CLI checks in Layers 1 and 3. Layers 2, 4, and 5
apply to both backends.

---

## Layer 1: Model-CLI Read-Only Sandboxes

This layer runs only when `worker_backend == model-clis`. Read-only commands
run each external CLI in **its own read-only sandbox** so the model can read
the repository but cannot modify it. Each sandboxed CLI is launched from a
`cd "$SESSION_DIR"` subshell as a backstop (any write that bypassed the
sandbox would land in the session directory, not the repo), and the repository
is exposed read-only through each CLI's own flags. All prompt input and output
paths are absolute, so the working directory does not affect I/O.

The `agy` (Antigravity) CLI is the exception: it has **no native read-only
mode** — its print mode reads *and* writes — so it is isolated in a **disposable
git worktree** rather than a native sandbox (see the `agy` block below).

`$REPO_TOPLEVEL` is captured in Layer 2 and passed to every model-CLI wrapper
sub-agent.

**Read-only commands** (brainstorm, refine, brainstorm-and-refine,
serene-bliss, ask, plan, review).

agy (Antigravity, the Google lane's primary) — no native read-only mode, so it
runs in a disposable worktree checked out at `HEAD`. agy reads the snapshot; any
stray write lands in the throwaway worktree, which is removed afterward, never
touching the main repo. `--add-dir` scopes its workspace to that worktree:

```bash
(AGY_RO_WT="${REPO_TOPLEVEL}-weave-agy-ro"; git -C "$REPO_TOPLEVEL" worktree remove --force "$AGY_RO_WT" 2>/dev/null; git -C "$REPO_TOPLEVEL" worktree add -q --detach "$AGY_RO_WT" HEAD && (cd "$AGY_RO_WT" && <timeout_cmd> <timeout_seconds> agy --model "Gemini 3.1 Pro (High)" --add-dir "$AGY_RO_WT" --dangerously-skip-permissions -p "$(cat "$SESSION_DIR/...")" </dev/null >"$SESSION_DIR/.../agy.md" 2>"$SESSION_DIR/.../agy.txt"); rc=$?; git -C "$REPO_TOPLEVEL" worktree remove --force "$AGY_RO_WT" 2>/dev/null; exit "$rc")
```

gemini (the Google lane's fallback) — `--approval-mode plan` is read-only mode,
`--include-directories` grants repo reads, `--skip-trust` clears the
untrusted-folder gate (plain `-y` does not):

```bash
(cd "$SESSION_DIR" && <timeout_cmd> <timeout_seconds> gemini -m gemini-3-pro-preview --approval-mode plan --include-directories "$REPO_TOPLEVEL" --skip-trust -p "$(cat "$SESSION_DIR/...")" >"$SESSION_DIR/.../agy.md" 2>"$SESSION_DIR/.../stderr.txt")
```

When multiple `agy` read-only lanes run concurrently (e.g. brainstorm variants),
each gets a uniquely-suffixed worktree (`...-weave-agy-ro-v<N>`, `...-weave-agy-ro-judge`)
so parallel runs never share a worktree path.

codex — `-s read-only` blocks writes, `-C` roots it in the repo,
`--skip-git-repo-check` lets it start outside a checked-out repo, `</dev/null`
prevents the stdin-wait hang:

```bash
(cd "$SESSION_DIR" && <timeout_cmd> <timeout_seconds> codex exec -s read-only -C "$REPO_TOPLEVEL" --skip-git-repo-check </dev/null -c model_reasoning_effort=medium "$(cat "$SESSION_DIR/...")" >"$SESSION_DIR/.../gpt.md" 2>"$SESSION_DIR/.../stderr.txt")
```

agent fallback — `--mode plan` is read-only mode, `--workspace` grants repo reads
(never `-f`/`--force`, which enables writes and shell):

```bash
(cd "$SESSION_DIR" && <timeout_cmd> <timeout_seconds> agent -p --mode plan --trust --workspace "$REPO_TOPLEVEL" --model <model> "$(cat "$SESSION_DIR/...")" >"$SESSION_DIR/.../gpt.md" 2>"$SESSION_DIR/.../stderr.txt")
```

The model CLI's read-only sandbox — or, for `agy`, the disposable worktree — is the
primary write defense; the `cd "$SESSION_DIR"` working directory and the
fingerprint/revert checks (Layers 2–5) are backstops.

Host-native participants use a unique session-scoped worktree for every
read-only WorkItem. The orchestrator points the participant at that exact path
and removes only that worktree after capturing its response. Pre-existing
working-tree changes stay in the context packet; the writable user checkout is
never exposed to a native worker.

**Write commands** (execute, prompt, architecture) wrap external CLIs in
`(cd "$WORKTREE_PATH" && ...)`. In the default sub-agent backend, the
Maintainer, Skeptic, and Builder also receive separate branch worktrees; they
do not share or modify the main checkout.

---

## Layer 2: Pre-Session Repo Fingerprint

Capture the repository state immediately after creating the session directory.
This establishes a baseline for all subsequent verification checks.

Add as **Step 8b** in Session Directory Initialization (after writing
`metadata.md`, before writing the context packet):

```bash
REPO_TOPLEVEL="$(git rev-parse --show-toplevel)"
```

```bash
REPO_HEAD="$(git -C "$REPO_TOPLEVEL" rev-parse HEAD)"
```

```bash
REPO_FINGERPRINT="$(git -C "$REPO_TOPLEVEL" status --porcelain)"
```

Write `$SESSION_DIR/repo-fingerprint.txt` containing:

```
head: <REPO_HEAD>
status:
<REPO_FINGERPRINT or "(clean)">
```

For **write commands**: this step runs after stashing user changes (Step 4b),
so the fingerprint reflects the clean stashed state.

For **plan.md**: this runs inside the setup host-native sub-agent alongside
other session initialization work.

---

## Layer 3: Post-model-CLI Repo State Verification

This layer runs only when `worker_backend == model-clis`. After each external
CLI command (agy, gemini, codex, agent) returns, the wrapper sub-agent that
invoked it must immediately verify the repository is unchanged.

Add these steps to each Antigravity/GPT sub-agent's instructions, after the CLI
invocation and before returning. The sub-agent must receive `$REPO_TOPLEVEL`
and `$REPO_FINGERPRINT` (captured in Layer 2) as part of its prompt.

```bash
CURRENT_STATUS="$(git -C "$REPO_TOPLEVEL" status --porcelain)"
```

Compare against the pre-session fingerprint — not just emptiness, since the
repo may have had pre-existing uncommitted changes:

```bash
if [ "$CURRENT_STATUS" != "$REPO_FINGERPRINT" ]; then
  git -C "$REPO_TOPLEVEL" checkout -- . 2>/dev/null || true
  git -C "$REPO_TOPLEVEL" clean -fd 2>/dev/null || true
  printf '{"event":"repo_guard_violation","timestamp":"%s","model":"%s","reverted":true}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "<model>" \
    >>"$SESSION_DIR/guard-events.jsonl"
fi
```

The model output was already captured via stdout redirect, so the session
continues normally after reverting.

**Concurrency note**: Multiple wrapper sub-agents run external CLIs in parallel.
If two rogue writes happen concurrently, one sub-agent's verification may
partially observe the other's changes. Layer 1 (model-CLI sandbox or disposable
worktree) is the primary defense — the CLIs cannot write the repo at all. Layer 3 is a
safety net for any write that bypasses the sandbox; the race window is
acceptable because the worst case is a redundant revert.

For **write commands**: this verification runs on the main tree only (not
worktrees, where writes are intentional). Use it after diff capture and
analysis phases to verify the main tree is unchanged.

---

## Layer 4: Prompt Hardening

Append this block to every external model prompt file (the file passed via
`$(cat ...)` to gemini/codex/agent CLIs):

```
---
CRITICAL: Do NOT write, edit, create, or delete any files. Do NOT use any
file-writing or file-modification tools. This is a READ-ONLY research task.
All output must go to stdout. Any file modifications will be automatically
detected and reverted.
```

Apply the same contract to every host-native read-only participant prompt,
even though its isolated worktree contains accidental writes:

> CRITICAL: Do NOT write, edit, create, or delete any files in the repository.
> Do NOT use Write, Edit, or Bash commands that modify repository files. All
> session artifacts are written to `$SESSION_DIR`, which is outside the
> repository. This is a READ-ONLY research task.

---

## Layer 5: Session-End Verification

Before marking the session as completed (before updating `session.json` to
`"status": "completed"`), run a final verification. This check is
non-destructive: worker isolation should make drift impossible, and the guard
must never erase user data while trying to repair an unexpected change.

```bash
FINAL_STATUS="$(git -C "$REPO_TOPLEVEL" status --porcelain)"
FINAL_HEAD="$(git -C "$REPO_TOPLEVEL" rev-parse HEAD)"
if [ "$FINAL_HEAD" != "$REPO_HEAD" ] || [ "$FINAL_STATUS" != "$REPO_FINGERPRINT" ]; then
  printf '{"event":"repo_guard_final","timestamp":"%s","repo_clean":false,"reverted":false}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >>"$SESSION_DIR/guard-events.jsonl"
  printf '%s\n' "Repository drift detected; session stopped without modifying the checkout." >&2
  exit 1
else
  printf '{"event":"repo_guard_final","timestamp":"%s","repo_clean":true,"reverted":false}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >>"$SESSION_DIR/guard-events.jsonl"
fi
```

Append to `events.jsonl`:

```json
{"event":"repo_guard_final","timestamp":"<ISO 8601 UTC>","repo_clean":true,"reverted":false}
```

For **plan.md**: this runs inside the host-native sub-agent that persists
session artifacts at session end.
