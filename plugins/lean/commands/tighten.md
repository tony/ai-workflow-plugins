---
description: >-
  Use to tighten specified files (or a pasted draft) in the working
  tree — remove AI slop, verbose prose, brittle references, and
  low-value noise — editing in place and printing a diff, with no
  commits. Triggers on "tighten these files", "trim the slop from",
  "make this leaner", or "deslop this draft in place". For repo-wide
  commit-per-finding cleanup use /slop:scan; for branch commit cleanup
  use /pr:deslop.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "AskUserQuestion"]
argument-hint: "[paths/globs] [--stdin] [--gates] [--diff-only]"
---

# `/lean:tighten`

Tighten specified files in the working tree and print a diff. Never
commits, never pushes, never requires a clean tree, never scans
repo-wide.

This is a slash command, not a model-invocable skill: it edits files,
so it must be user-explicit.

## Difference from `/slop:scan`

### Use `/lean:tighten` when

The slop is in files you are actively editing and you want a quick
in-place tidy with a diff to review — no commit ceremony, dirty tree
fine.

### Use `/slop:scan` when

You want repo-wide coverage with one reviewable, revertable commit per
finding, on a clean tree.

## `$ARGUMENTS`

- `paths/globs` — files to tighten (via `git ls-files -- <glob>` when
  tracked, else literal paths).
- `--stdin` — tighten a pasted draft read from stdin instead of files;
  print the tightened text and edit nothing.
- `--gates` — after editing, run the project's discovered
  format/lint/typecheck once and report. Never commits.
- `--diff-only` — show what would change without editing.

If `$ARGUMENTS` is empty, ask which files via `AskUserQuestion`.

## Steps

1. **Resolve targets.** Expand paths/globs, or read stdin with
   `--stdin`. Reject an empty target set with a clear message.
2. **Load the rubric and voice.** Read
   `${CLAUDE_PLUGIN_ROOT}/references/lean-rubric.md`, then `./AGENTS.md`
   and `./CLAUDE.md` for the host's rubric and accepted voice. For
   `--gates`, take the format/lint/typecheck commands from a checks
   section in those files; if none is defined, skip gates.
3. **Detect.** Flag slop per the rubric — AI signatures, brittle
   references, diff narration, prose inflation, coded labels, and
   tables where prose reads cleaner. Preserve every load-bearing
   reference and "why" comment.
4. **Preview and confirm.** Show the proposed edits and confirm via
   `AskUserQuestion` before writing; the preview and the printed diff
   (Step 6) are the review surface. Skip when `--diff-only`.
5. **Apply in place.** Use `Edit`. Replacements must be concrete and
   shorter than the original.
6. **Diff.** Print `git diff -- <targets>`. With `--gates`, run the
   discovered checks once and report; commit on neither pass nor fail.
7. **Report and hand off.** Summarize findings resolved and skipped,
   then offer next steps via `AskUserQuestion`: commit with `/commit`,
   run `/slop:scan` for repo-wide coverage, or discard the edits —
   review the printed diff first, since `git checkout -- <file>` resets
   the whole file to HEAD and drops any other uncommitted work in it.

## What this does not do

- Commit or push — you decide; use `/commit`.
- Rewrite history — that is `/pr:deslop`.
- Scan the whole repo — that is `/slop:scan`.
- Delete whole files — too consequential; report them instead.
