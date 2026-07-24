---
description: Merge a set of PRs one at a time — detect stack vs independent set, rebase and resolve conflicts between merges, watch CI, merge each via gh
argument-hint: "[PR numbers/URLs, e.g. '#31 #32'] [--squash | --rebase | any other gh pr merge flag]"
allowed-tools: ["Bash", "Read", "Grep", "Edit", "AskUserQuestion"]
---

# Merge Multiple PRs

Land a set of pull requests one at a time: merge one, refresh trunk,
bring the next PR up to date (rebase, resolve conflicts, force-push,
wait on CI), then merge it — repeating until the set is landed or a
gate halts the run.

Read `${CLAUDE_PLUGIN_ROOT}/references/merge-readiness.md` first; it
defines the readiness gate, the rebase procedure, the merge-message
derivation, flag passthrough, the `--admin` policy, and the rule that
merging is not releasing.

User arguments: $ARGUMENTS

## Context

Trunk:
`!git rev-parse --verify origin/main >/dev/null 2>&1 && echo main || echo master`

Open PRs:
`!gh pr list --json number,title,headRefName,baseRefName,isDraft 2>/dev/null || echo "(gh unavailable)"`

## Procedure

### 1. Assemble the roster

Take the PR set from the arguments, or from the PRs this
conversation has been working on. If the set is ambiguous — the
conversation touched more PRs than the user likely means, or an
argument doesn't match an open PR — present the candidates via
`AskUserQuestion` and let the user pick. Show the final roster
before merging anything.

### 2. Detect the topology

Fetch `baseRefName` and `headRefName` for each PR. If any PR's base
branch is another PR's head branch, the set is a **stack**: order
bottom-up, each PR merging only after its parent. Otherwise the set
is **independent**: honor the order the user gave, falling back to
ascending PR number.

For a stack, plan the retarget: merging a parent with
`--delete-branch` lets GitHub retarget the child to trunk
automatically; when the branch is kept, retarget explicitly with
`gh pr edit <child> --base <trunk>` before rebasing the child.

### 3. Land each PR

For each PR in order:

1. **Readiness gate** — apply the gate from the reference. Failing
   CI, draft state, or `CHANGES_REQUESTED` halts the run with a
   report of what landed and what remains.
2. **Bring up to date** — when the PR is `BEHIND` or `DIRTY`, or an
   earlier merge in this run moved trunk:
   follow the reference's rebase procedure (for a stacked child,
   `git rebase --onto` the new trunk so the parent's merged commits
   drop out), resolve conflicts — asking on any conflict that forces
   a choice between behaviors — verify content did not drift, then
   `git push --force-with-lease`.
3. **Wait on CI** — `gh pr checks <n> --watch` on the rebased head.
4. **Merge** — compose the merge commit message per the reference
   (match `git log --merges`, stay provincial, no release claims)
   and merge via `gh pr merge <n> --merge -t ... -b ...`, passing
   the user's flags through verbatim. `--admin` only within the
   reference's policy, asked-for if the user didn't supply it.
5. **Sync** — checkout trunk, pull, confirm the PR reports merged.

### 4. Halt conditions

Stop and report — never push past — when a rebase produces an
unexpected content diff, CI fails on a rebased head, a PR turned
closed or draft mid-run, or a conflict needs a product decision.
Everything already merged stays merged; the report says exactly
where the run stopped and why.

## Rules

- One PR at a time; never merge two PRs between trunk syncs.
- Merges go through `gh pr merge`, never a local `git merge` pushed
  to trunk.
- Never merge over failing or pending CI, with or without `--admin`.
- Force-pushes use `--force-with-lease` and only ever target PR
  branches.
- When in doubt at any step, ask — do no harm.

## Output

Open with a one-line hero (`✓ Merged N of M PRs` or
`⚠ Halted at #N: <reason>`), then exactly these sections:

1. `## Roster` — the PRs, detected topology (stack or independent),
   and merge order.
2. `## Merges` — per PR: gate result, rebase/conflicts if any, CI
   outcome, merge commit subject.
3. `## Trunk` — the post-run trunk state.

End with an `AskUserQuestion` panel offering next steps (for
example: continue with a halted PR after a fix, merge another set,
stop here) — skip the panel only in plan mode.
