---
name: tighten
description: >-
  Use to tighten specified files (or a pasted draft) in the working tree —
  remove AI slop, verbose prose, brittle references, and low-value noise —
  editing in place and printing a diff, with no commits. Triggers on
  "tighten these files", "trim the slop from", "make this leaner", or
  "deslop this draft in place". For repo-wide commit-per-finding cleanup use
  the `scan` skill; for branch commit cleanup use the `deslop` skill.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "AskUserQuestion"]
metadata:
  argument-hint: "[paths/globs] [--stdin] [--gates] [--diff-only]"
  source: "plugins/lean/commands/tighten.md"
---

# this skill

Tighten specified files in the working tree and print a diff. Never
commits, never pushes, never requires a clean tree, never scans
repo-wide.

This is a slash command, not a model-invocable skill: it edits files,
so it must be user-explicit.

## Difference from the `scan` skill

### Use this skill when

The slop is in files you are actively editing and you want a quick
in-place tidy with a diff to review — no commit ceremony, dirty tree
fine.

### Use the `scan` skill when

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

If `$ARGUMENTS` is empty, ask which files via `ask-user-choice`.

## Steps

1. **Resolve targets.** Expand paths/globs, or read stdin with
   `--stdin`. Reject an empty target set with a clear message.
2. **Load the rubric and voice.** Read
   `references/lean-rubric.md`, then `./AGENTS.md`
   and `./CLAUDE.md` for the host's rubric and accepted voice. For
   `--gates`, take the format/lint/typecheck commands from a checks
   section in those files; if none is defined, skip gates.
3. **Detect.** Flag slop per the rubric — AI signatures, brittle
   references, diff narration, prose inflation, coded labels, and
   tables where prose reads cleaner. Preserve every load-bearing
   reference and "why" comment.
4. **Preview and confirm.** Show the proposed edits and confirm via
   `ask-user-choice` before writing; the preview and the printed diff
   (Step 6) are the review surface. Skip when `--diff-only`.
5. **Apply in place.** Use `Edit`. Replacements must be concrete and
   shorter than the original.
6. **Diff.** Print `git diff -- <targets>`. With `--gates`, run the
   discovered checks once and report; commit on neither pass nor fail.
7. **Report and hand off.** Summarize findings resolved and skipped,
   then offer next steps via `ask-user-choice`: commit with `/commit`,
   run the `scan` skill for repo-wide coverage, or discard the edits —
   review the printed diff first, since `git checkout -- <file>` resets
   the whole file to HEAD and drops any other uncommitted work in it.

## What this does not do

- Commit or push — you decide; use `/commit`.
- Rewrite history — that is the `deslop` skill.
- Scan the whole repo — that is the `scan` skill.
- Delete whole files — too consequential; report them instead.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
