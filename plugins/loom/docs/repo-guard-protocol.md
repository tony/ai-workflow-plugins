# Repo Guard Protocol

Prevents loom sessions from modifying repository files. All phases — main
agents, sub-agents, judges — must keep mutations within `$SESSION_DIR` (for
read-only commands) or worktrees (for write commands). This protocol applies
to every loom command except `fix-review` (which intentionally modifies the
repository).

---

## Layer 1: CLI Working Directory Isolation

Wrap ALL external CLI invocations in a `cd "$SESSION_DIR"` subshell so that
rogue file writes land in the session directory, not the repository. All
prompt input and output paths use absolute paths, so this is transparent.

**Read-only commands** (brainstorm, refine, brainstorm-and-refine,
serene-bliss, ask, plan, review):

```bash
(cd "$SESSION_DIR" && <timeout_cmd> <timeout_seconds> gemini -m gemini-3.1-pro-preview -y -p "$(cat "$SESSION_DIR/...")" >"$SESSION_DIR/.../gemini.md" 2>"$SESSION_DIR/.../stderr.txt")
```

**Write commands** (execute, prompt, architecture) already wrap external CLIs
in `(cd "$WORKTREE_PATH" && ...)` — no change needed for external model
invocations.

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

For **plan.md**: this runs inside the setup Task agent alongside other session
initialization work.

---

## Layer 3: Post-CLI Repo State Verification

After each external CLI command (gemini, codex, agent) returns, the sub-agent
that invoked the CLI must immediately verify the repository is unchanged.

Add these steps to each Gemini/GPT sub-agent's instructions, after the CLI
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

**Concurrency note**: Multiple sub-agents run external CLIs in parallel.
If two rogue writes happen concurrently, one sub-agent's verification may
partially observe the other's changes. Layer 1 (working directory isolation)
is the primary defense — it prevents writes from reaching the repo at all.
Layer 3 is a safety net for writes to absolute paths; the race window is
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

Strengthen Claude Task agent prompts with:

> CRITICAL: Do NOT write, edit, create, or delete any files in the repository.
> Do NOT use Write, Edit, or Bash commands that modify repository files. All
> session artifacts are written to `$SESSION_DIR`, which is outside the
> repository. This is a READ-ONLY research task.

---

## Layer 5: Session-End Verification

Before marking the session as completed (before updating `session.json` to
`"status": "completed"`), run a final verification:

```bash
FINAL_STATUS="$(git -C "$REPO_TOPLEVEL" status --porcelain)"
FINAL_HEAD="$(git -C "$REPO_TOPLEVEL" rev-parse HEAD)"
if [ "$FINAL_HEAD" != "$REPO_HEAD" ] || [ "$FINAL_STATUS" != "$REPO_FINGERPRINT" ]; then
  git -C "$REPO_TOPLEVEL" checkout -- . 2>/dev/null || true
  git -C "$REPO_TOPLEVEL" clean -fd 2>/dev/null || true
  printf '{"event":"repo_guard_final","timestamp":"%s","repo_clean":false,"reverted":true}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >>"$SESSION_DIR/guard-events.jsonl"
else
  printf '{"event":"repo_guard_final","timestamp":"%s","repo_clean":true,"reverted":false}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >>"$SESSION_DIR/guard-events.jsonl"
fi
```

Append to `events.jsonl`:

```json
{"event":"repo_guard_final","timestamp":"<ISO 8601 UTC>","repo_clean":true,"reverted":false}
```

For **plan.md**: this runs inside the sub-agent that persists session
artifacts at session end.
