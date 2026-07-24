---
description: Update the branch's own changelog entries to match its current net change; commits only with --commit
argument-hint: "[--commit] [optional additional context about the changes]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "AskUserQuestion"]
---

# Refresh Changelog Entries

Bring the changelog entries **this branch introduced** back in sync
with what the branch currently does. With `--commit`, the correction
lands as a **new commit stacked on top**; otherwise the edit is left
uncommitted for the user to commit, like `/changelog`. History is
never rewritten — for that, use `/changelog:recut`.

Hard scope rule: this command only ever edits changelog content the
branch itself added. Entries that came from the base branch — earlier
releases, or unreleased entries from other work — are read-only. If a
correction would require touching a line the branch didn't add, stop
and ask.

Additional context from user: $ARGUMENTS

---

## Phase 1: Establish scope

1. **Detect the base.** If the branch has a PR
   (`gh pr view --json baseRefName`), the base is its `baseRefName` —
   stack-aware. Otherwise detect trunk via
   `git symbolic-ref refs/remotes/origin/HEAD` (fall back to `master`).
   If currently on the base/trunk itself, report and stop.

2. **Find the changelog file** the same way `/changelog` does (scan for
   `CHANGES`, `CHANGES.md`, `CHANGELOG.md`, `HISTORY.md`, `NEWS.md`,
   …). No changelog changes on this branch and no changelog file →
   suggest `/changelog` instead and stop.

3. **Extract the branch's changelog footprint**:
   ```
   git diff origin/<base>...HEAD -- <changelog-file>
   ```
   The added lines are the branch-owned entries — the only region this
   command may edit. Also list the branch commits touching the file:
   ```
   git log origin/<base>..HEAD --oneline -- <changelog-file>
   ```
   If the branch has no changelog commits yet, say so and offer to
   generate entries via the `/changelog` procedure instead.

## Phase 2: Recompute what the entries should say

Read the sibling command file
`${CLAUDE_PLUGIN_ROOT}/commands/changelog.md` and apply its rules
verbatim — the *Core Constraint* (a branch is not a release), Phase 1
convention detection, Phase 2 commit categorization, and Phase 3 entry
generation and voice. Generate, from the branch's **current net
change** (`git log` / `git diff` against `origin/<base>`), the entries
the branch *should* have.

## Phase 3: Diff documented vs. actual

Compare the branch-owned entries (Phase 1) against the recomputed
entries (Phase 2):

- **Accurate** — leave byte-for-byte untouched, including phrasing
  you'd have written differently. Refresh fixes drift, not style.
- **Stale** — the entry describes something the branch no longer does,
  or misstates scope. Rewrite it in place, matching the file's style.
- **Missing** — a user-visible change with no entry. Insert it in the
  correct section of the unreleased block, following the sibling
  command's section-order and homogeneity rules.
- **Orphaned** — an entry whose change was removed from the branch
  entirely. Remove the entry.
- **Out of reach** — the fix would touch content the branch didn't add
  (e.g., the branch's entry was merged into a pre-existing bullet, or
  a section heading shared with base-branch entries must change). Ask
  via `AskUserQuestion` before touching anything outside the branch's
  footprint; if declined, leave it and note the limitation.

## Phase 4: Present, edit, commit

**Mandatory gate — never edit or commit without explicit approval.**

1. Present a summary line
   (`Branch: <name> | Base: <base> | Changelog commits: <shas>`),
   then the proposed edit as old → new markdown for each touched
   entry, and the statement that everything else in the file is
   untouched. Include the `Target: unreleased section` line from the
   sibling command's Phase 4 — refresh never touches version headings
   or version files.
2. On approval, apply with the Edit tool, confined to the branch's
   footprint plus approved insertions in the unreleased block.
3. Show the modified region for verification, then verify the scope
   guard mechanically: `git diff -- <changelog-file>` combined with the
   branch footprint must show no modifications to base-branch lines.
4. **Commit only with `--commit`.** When `$ARGUMENTS` contains
   `--commit`, commit the edit as a new commit on top of the branch,
   following the commit message rules in the sibling command's *Commit
   message conventions for CHANGES edits* — project convention first,
   fallback `docs(CHANGES) <what the update covers>`, never a version,
   never a `#N` in the message. Stage the changelog file explicitly by
   path — never `git add -A`. Without `--commit` (the default), leave
   the edit uncommitted and show a ready-to-use commit message built
   from the same rules — committing is the user's decision, as with
   `/changelog`.

---

## Rules

- **Branch-scoped, always**: never modify changelog content the branch
  didn't introduce; when a fix requires it, ask first.
- **Never rewrites**: no rebase, no amend, no force-push. With
  `--commit` it stacks a single new commit; otherwise it commits
  nothing. Rewriting the branch's changelog history is
  `/changelog:recut`.
- **A branch is not a release**: all Core Constraint rules from
  `/changelog` apply — no version headings, no version predictions, no
  version-file edits.
- **Whole-branch perspective**: entries document the net result
  against the base, not the branch's internal history.
- **Ask on ambiguity**; the cost of a question is smaller than a
  changelog that lies.
