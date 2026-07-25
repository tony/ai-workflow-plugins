# Merge Readiness and Merge Conventions

Shared contract for this skill and the `merge-pr-multiple` skill. Both
commands read this file before touching any PR.

## Readiness gate

A PR merges only after every check below is confirmed. When any of
them is ambiguous, do discovery first — read the PR, its checks, and
its branch — and if the answer is still unclear, ask the user rather
than guessing. Do no harm.

- **Open and not draft**: `gh pr view <n> --json state,isDraft`.
  A draft or closed PR halts the run.
- **CI**: `gh pr checks <n>`. Pending checks are waited on with
  `gh pr checks <n> --watch`. Failing checks halt the run — report
  the failing check and stop. `--admin` never overrides failing or
  pending CI.
- **Mergeability**: `gh pr view <n> --json mergeable,mergeStateStatus`.
  `DIRTY` means conflicts with the base; `BEHIND` means the base has
  moved. Either state routes through the rebase procedure below
  before merging.
- **Reviews**: `gh pr view <n> --json reviewDecision`. A
  `CHANGES_REQUESTED` decision halts the run and is surfaced to the
  user; it is their call, not the command's.
- **Situational awareness**: skim the PR title, body, and recent
  commits (`gh pr view <n>`, `gh pr view <n> --json commits`) so the
  merge commit message describes what actually ships and so surprises
  (WIP markers, "do not merge" labels, unresolved review threads the
  user mentioned) surface before the merge, not after.

## Rebase procedure

When a PR is `BEHIND` or `DIRTY`, or an earlier merge in a multi-PR
run has moved trunk. Consent differs by command on purpose:
this skill confirms before rebasing — a rebase expands "merge
this PR" — while the `merge-pr-multiple` skill's between-merge rebases are
its disclosed core loop, covered by the roster shown up front.

1. Check out the PR branch (`gh pr checkout <n>`), fetch, then
   rebase it onto its current base. For a stacked PR whose parent
   just merged, drop the parent's commits with
   `git rebase --onto <base> <old-parent-head> <branch>`.
2. Resolve conflicts. Mechanical resolutions (context drift, adjacent
   hunks, a list both sides appended to) are resolved directly. A
   conflict that forces a choice between two competing behaviors is
   presented to the user via `ask-user-choice` — never silently pick
   a side.
3. Verify the rebase changed history, not content: compare the
   branch's diff against its base before and after (`git range-diff`
   or `git diff` of the two three-dot ranges). Unexpected content
   drift halts the run.
4. If conflicts were resolved, run the project's fast quality gates
   — format, lint, typecheck, scoped tests, discovered from its
   AGENTS.md/CLAUDE.md — and fix failures before pushing.
5. Force-push with `git push --force-with-lease` — never bare
   `--force`.
6. Wait for CI on the rebased head: `gh pr checks <n> --watch`.

## Merge commit message

Study the repository's own merge history before writing the message:

```console
git log --merges -10 --format='%s%n%n%b' <trunk>
```

Match what is observed — subject shape, whether a `(#N)` suffix is
used, body structure, wrapping. If the repo has no merge history,
fall back to the commit conventions in its AGENTS.md/CLAUDE.md, then
to a plain descriptive subject. Keep the body proportional: a small
fix needs a subject only; a feature gets a short narrative paragraph
and labeled bullets. Pass the message via `gh pr merge -t <subject>
-b <body>`.

### Stay provincial

Merging a PR is not cutting a release. Unless the PR itself is
release management (a version bump, a release-notes PR), the merge
commit and any text this command writes must not claim the change
lands "in vX.Y", edit CHANGES/CHANGELOG files, tag, or otherwise
tread into release territory. Describe what the branch ships and
stop there.

## Strategy and flag passthrough

The default strategy is a merge commit (`--merge`). `--squash` and
`--rebase` override it, and every other `gh pr merge` flag the user
supplies passes through verbatim — `--auto`, `--delete-branch`,
`--admin`, `--match-head-commit`, `--author-email`, `--body-file`,
`--repo`, and the rest of `gh pr merge --help`. Do not translate or
second-guess them; `-t`/`-b` are only composed when the strategy
produces a commit whose message this command owns (merge or squash)
and the user has not supplied their own.

### `--admin` policy

`--admin` bypasses branch protection, nothing more. It is acceptable
when CI is otherwise passing and the only blocker is a protection
rule (for example a required-review rule on a solo repo). It is never
used to merge over failing or pending checks, over a critical error
found during discovery, or over anything that violates the repo's
AGENTS.md/CLAUDE.md. If the user did not pass `--admin` and it turns
out to be needed, ask before using it.

## After each merge

1. `git checkout <trunk>` and `git pull` so the local trunk matches
   what was just merged.
2. Confirm the merge landed (`gh pr view <n> --json state,mergedAt`).
3. Report and stand by — never chain into tagging, releasing, or
   deploying.

The merge itself always goes through `gh pr merge`, never a local
`git merge` pushed to trunk.
