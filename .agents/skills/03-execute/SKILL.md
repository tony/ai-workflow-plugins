---
name: 03-execute
description: >-
  Phase 4 of the pytest-optimizer pipeline. Apply each approved speedup from
  plan.json as its own commit and verify green. Iterates the plan in order:
  apply one change, run the project quality checks and test suite, and on
  success commit it alone with the drafted why/what message; on failure,
  revert that change and mark it skipped, then continue. Checkpoints after
  every item to execution-log.json and resumes from the last applied index,
  so it is crash-safe and idempotent. Refuses to run on a dirty tree. Use
  after 02-plan to land the speedups as separate, verified commits.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit", "AskUserQuestion"]
metadata:
  argument-hint: "[--from=<index>] [--dry-run] [--memory-dir=<path>]"
  source: "plugins/pytest-optimizer/commands/03-execute.md"
---

# 03-execute

Land the plan as separate, verified commits. This is the **only** phase that edits
the suite and writes history.

`$ARGUMENTS` may pass `--from=<index>` to start at a specific plan item,
`--dry-run` to apply and verify without committing (reverting after each), and
`--memory-dir` to override the memory location.

## Step 1: Preconditions

Read `plan.json`, `baseline.json`, and the project quality-check + test commands.
Refuse to run unless:

- the working tree is **clean** (one commit per speedup needs a clean base), and
- `plan.json` exists and was approved in the `02-plan` skill.

Read `execution-log.json` if present and resume from `last_applied_index + 1`
(or `--from`). Never re-apply an item that already has a `commit_sha`.

## Step 2: Apply each item in order

For each plan item not yet applied:

1. **Apply** the single change (the heuristic's action). Touch only the files the
   plan lists for this item.
2. **Verify green.** Run the project quality checks (formatter, linter, type
   checker) and the test suite, as declared in the project's `AGENTS.md`/
   `CLAUDE.md` — substitute that command wherever this file writes `pytest`:

   ```bash
   pytest -p no:cacheprovider -q
   ```

   For a typing/parametrize item (goals 9, 10), the type checker must cover
   `tests/` and pass.
3. **On success** — commit this change **alone** with the drafted why/what
   message (`templates/commit-message.tmpl`, adapted to
   the target project's convention). Record the `commit_sha`.
4. **On failure** — revert the change (`git checkout -- <files>` / discard), mark
   the item `skipped` with the reason. Do not let one failure block the rest.
5. **Checkpoint** — append the item's outcome to `execution-log.json` immediately
   and update `state.json` (`phase=execute`, `last_applied_index`). This makes the
   loop crash-safe: a re-run continues from the last durable checkpoint.

Under `--dry-run`, perform 1–2 then revert and log the verify result without
committing.

## Step 3: Re-measure and report

After the plan is exhausted, re-run the baseline measurement (serial, cache
disabled, N runs) and compare total wall-time to `baseline.json`. Emit the
`03-execute` sections from `references/output-contract.md`:
hero block, then `## Applied` (commit SHAs + measured verify), `## Skipped`
(revert reasons), `## Result` (post-suite wall-time vs baseline, total recovered).

## Step 4: Offer another pass

Close with an `ask-user-choice` panel: re-scan for a second pass (the suite is now
leaner, so new candidates may surface), scaffold the opt-in cache/timing plugin,
or stop. Re-scanning restarts the loop at the `00-scan` skill with a fresh
baseline.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
