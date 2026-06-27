---
description: Validate the most recent (or specified) weave session against schema and file-path invariants.
allowed-tools: ["Bash"]
argument-hint: "[session_path]"
---

# Validate weave session

Run the validator at `${CLAUDE_PLUGIN_ROOT}/scripts/validate_session.py`. The validator checks artifact *shape* (required fields, event ordering, pass-tracking exactness, fingerprint integrity) — it does **not** evaluate output quality, judging quality, or reasoning quality.

The slash command always passes `--strict` so humans see clear pass/fail.

## When `$ARGUMENTS` is empty

Validate the latest in-progress brainstorm-and-refine session for the current repository. If no in-progress session exists, the validator no-ops cleanly.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_session.py" --latest-in-progress brainstorm-and-refine --strict
```

## When `$ARGUMENTS` is set

Validate the specified session directory.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_session.py" "$ARGUMENTS" --strict
```

## Optional: also verify repository state

Add `--check-repo` to compare the current `git rev-parse HEAD` and `git status --porcelain` against the captured `repo-fingerprint.txt`. This requires the session to live under `$AI_AIP_ROOT`. Failures emit warnings (not errors) so worktrees and missing-git environments do not break validation.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_session.py" "$ARGUMENTS" --strict --check-repo
```

## Exit codes

- `0` — validation passed (or best-effort fallback when `--strict` is omitted).
- `2` — validation errors, only when `--strict` is set.
- `1` — internal failure (e.g. no session selected without `--latest-in-progress`).

Diagnostics print to stderr in the form `error: <message>` or `warning: <message>`, followed by a summary count and the disclaimer `note: validates artifact shape only - not output quality.`
