---
name: changelog-recut
description: >-
  Rebase out the branch's earlier changelog commits and regenerate its
  entries fresh; commits only with --commit
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "AskUserQuestion"]
metadata:
  argument-hint: "[--commit] [optional additional context about the changes]"
  source: "plugins/changelog/commands/recut.md"
---

# Recut Changelog Entries

Remove the changelog commits this branch accumulated, then regenerate
its entries from the branch's **current net change**. With `--commit`,
the regenerated entries land as one fresh commit at the tip; otherwise
they are left as an uncommitted edit for the user to commit. Where
the `changelog-refresh` skill stacks a correcting commit on top, recut rewrites
the branch so its changelog history collapses to a single clean
commit.

Hard scope rule: only the branch's own changelog content is rewritten.
Changelog content from the base branch — earlier releases, or
unreleased entries from other work — is never modified. The branch's
**code** history is never modified either; only changelog commits are
touched.

Additional context from user: $ARGUMENTS

---

## Phase 1: Safety checks and scope

1. **Preconditions** — refuse to proceed (report why) if any fail:
   - Working tree dirty (`git status --porcelain` non-empty)
   - Detached HEAD, or an in-progress rebase/merge/cherry-pick
   - Currently on the base/trunk branch

2. **Detect the base.** If the branch has a PR
   (`gh pr view --json baseRefName`), the base is its `baseRefName` —
   stack-aware. Otherwise detect trunk via
   `git symbolic-ref refs/remotes/origin/HEAD` (fall back to `master`).

3. **Find the changelog file** the same way `/changelog` does (scan for
   `CHANGES`, `CHANGES.md`, `CHANGELOG.md`, `HISTORY.md`, `NEWS.md`, …).

4. **Partition the branch's commits** touching the changelog file
   (`git log origin/<base>..HEAD --format='%h %s' -- <changelog-file>`):
   - **Pure changelog commits** — the commit's diff touches only the
     changelog file. These will be dropped in Phase 2.
   - **Mixed commits** — changelog hunks entangled with code changes.
     These cannot be dropped wholesale. Ask via `ask-user-choice` how
     to handle each: leave the commit intact and let the new tip
     commit supersede its entries (recommended — no code history
     rewrite), or abort so the user can split the commit first.
   - No changelog commits at all → nothing to recut; suggest
     `/changelog` (or the `changelog-refresh` skill) and stop.

5. **Pushed-branch gate.** If the branch exists on the remote and the
   commits to drop are pushed, warn that completing the recut will
   require the **user** to `git push --force-with-lease` afterwards,
   and get explicit confirmation before rewriting. This command never
   pushes.

6. **Back up.** Record the current tip and create a backup branch:
   ```
   git branch changelog-recut-backup-$(date -u +%Y%m%d-%H%M%SZ)
   ```
   Report the backup branch name and SHA to the user.

## Phase 2: Rebase out the old changelog commits

1. Drop the pure changelog commits non-interactively with a scripted
   sequence editor — for example, turning their `pick` lines into
   `drop` by SHA:
   ```
   GIT_SEQUENCE_EDITOR='sed -i -E "s/^pick (<sha1>|<sha2>)/drop \1/"' git rebase -i origin/<base>
   ```
   Use each dropped commit's abbreviated SHA exactly as it appears in
   the todo list. On conflict, stop and show the state — never resolve
   by discarding user code.

2. **Verify the invariant** before going further:
   - Code unchanged:
     `git diff <backup> HEAD -- . ':(exclude)<changelog-file>'` must be
     empty (mixed commits kept intact keep this true by construction).
   - If only pure commits were dropped and no mixed commits exist,
     `git diff origin/<base> HEAD -- <changelog-file>` must now be
     empty.

   If either check fails, restore (`git reset --hard <backup>`), report,
   and stop.

## Phase 3: Regenerate entries fresh

Read the sibling command file
the `changelog` skill and apply its rules
verbatim — the *Core Constraint* (a branch is not a release), Phase 1
convention detection, Phase 2 commit categorization, Phase 3 entry
generation and voice, and its Phase 4 presentation gate. Generate
entries from the branch's current net change against `origin/<base>`.

Entries superseding a mixed commit's surviving changelog hunks may
update those hunks — they are branch-owned content — but nothing from
the base branch.

## Phase 4: Present, edit, commit

**Mandatory gate — never edit or commit without explicit approval.**

1. Present: the summary line
   (`Branch: <name> | Base: <base> | Dropped: <shas> | Backup: <branch>`),
   the proposed entries as exact markdown, the insertion point, and the
   `Target: unreleased section` line. Recut never touches version
   headings or version files.
2. On approval, apply with the Edit tool. **With `--commit`** in
   `$ARGUMENTS`, commit **once** at the tip, following the commit
   message rules in the sibling command's *Commit message conventions
   for CHANGES edits* — project convention first, fallback
   `docs(CHANGES) <what the update covers>`, never a version, never a
   `#N` in the message. Stage the changelog file explicitly by path —
   never `git add -A`. **Without `--commit`** (the default), leave the
   edit uncommitted and show a ready-to-use commit message built from
   the same rules — committing is the user's decision, as with
   `/changelog`.
3. Close by reporting: the backup branch to delete once satisfied
   (`git branch -D <backup>`), that an uncommitted changelog edit is
   awaiting the user's commit (when `--commit` was not passed), and —
   if the branch was pushed — that the user needs
   `git push --force-with-lease` to publish the rewrite.

---

## Rules

- **Backup before rewrite**: the backup branch is created before any
  rebase and its name reported; restoration is one `git reset --hard`.
- **Code history is sacred**: only pure changelog commits are dropped;
  mixed commits are never rewritten without an explicit user choice,
  and the post-rebase code-diff check must come back empty.
- **Branch-scoped, always**: base-branch changelog content is never
  modified.
- **Commits only with `--commit`**: by default the regenerated entries
  are left uncommitted with a suggested message; the rebase that drops
  old changelog commits still runs (that is the point of recut), behind
  its own confirmation gates.
- **Never pushes**: force-pushing the rewritten branch is the user's
  explicit act, flagged in the closing report.
- **A branch is not a release**: all Core Constraint rules from
  `/changelog` apply — no version headings, no version predictions, no
  version-file edits.
- **Ask on ambiguity**: mixed commits, unclear entry ownership, or a
  pushed branch all get a question, not a guess.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
