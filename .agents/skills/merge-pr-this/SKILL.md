---
name: merge-pr-this
description: >-
  Merge one PR via gh with a merge commit matching the repo's git history —
  readiness-gated, CI-watched, trunk synced after
allowed-tools: ["Bash", "Read", "Grep", "Edit", "AskUserQuestion"]
metadata:
  argument-hint: "[PR number or URL] [--squash | --rebase | any other gh pr merge flag]"
  source: "plugins/merge-pr/commands/this.md"
---

# Merge This PR

Merge a single pull request — the one this conversation is about, or
the one the current branch belongs to — via `gh pr merge`, with a
merge commit whose message matches the repository's own
`git log --merges` history. Nothing merges until the readiness gate
passes.

Read `references/merge-readiness.md` first; it
defines the readiness gate, the rebase procedure, the merge-message
derivation, flag passthrough, the `--admin` policy, and the rule that
merging is not releasing.

User arguments: $ARGUMENTS

## Context

Current branch — run this command and read the output:

```bash
git branch --show-current
```

PR for the current branch — run this command and read the output:

```bash
gh pr view --json number,title,url,state,isDraft,baseRefName,mergeable,mergeStateStatus,reviewDecision 2>/dev/null || echo "(no PR for current branch)"
```

Checks — run this command and read the output:

```bash
gh pr checks 2>/dev/null || echo "(no PR or no checks)"
```

## Procedure

### 1. Identify the PR

Precedence: an explicit argument (number or URL) > the PR this
conversation has been working on > the current branch's PR. If the
candidates disagree — the argument names one PR while the
conversation is about another — ask via `ask-user-choice` before
proceeding.

### 2. Run the readiness gate

Apply the readiness gate from the reference. Pending checks are
waited on with `gh pr checks <n> --watch`; failing checks, a draft
state, or `CHANGES_REQUESTED` halt with a report. If the PR is
`BEHIND` or `DIRTY`, confirm with the user, then follow the rebase
procedure: rebase, resolve conflicts, verify content did not drift,
`git push --force-with-lease`, and watch CI again.

### 3. Compose the merge commit message

Follow the merge-message section of the reference: study
`git log --merges` on trunk, match the observed format, keep the body
proportional to the change, and stay provincial — no release or
version claims unless the PR itself is release work. Skip this step
when the user's flags make the message theirs to control (their own
`-t`/`-b`, or `--rebase`, which produces no merge commit).

### 4. Merge

Default to a merge commit; pass the user's `gh pr merge` flags
through verbatim:

```console
gh pr merge <n> --merge -t "<subject>" -b "<body>"
```

Use `--admin` only within the reference's policy — CI green, blocked
purely by branch protection, nothing violating AGENTS.md — and ask
first if the user did not pass it.

### 5. Sync trunk and stand by

Checkout trunk, pull, and confirm the PR reports merged. Then stop:
no tagging, no releasing, no follow-on work.

## Rules

- The merge goes through `gh pr merge`, never a local `git merge`
  pushed to trunk.
- Never merge over failing or pending CI, with or without `--admin`.
- Force-pushes use `--force-with-lease` and only ever target the PR
  branch.
- When in doubt at any step, ask — an unnecessary question costs a
  moment; a wrong merge costs an afternoon.

## Output

Open with a one-line hero (`✓ Merged #N: <title>` or
`⚠ Blocked: <reason>`), then exactly these sections:

1. `## Merge readiness` — the gate results, including anything that
   required a rebase or a wait on CI.
2. `## Merge` — strategy used, flags passed through, and the merge
   commit subject (or why no merge happened).
3. `## Trunk` — the post-merge trunk state after checkout and pull.

End with an `ask-user-choice` panel offering next steps (for example:
merge another PR, delete the local branch, stop here) — skip the
panel only in plan mode.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
