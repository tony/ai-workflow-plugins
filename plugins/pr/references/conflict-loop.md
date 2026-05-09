# Conflict Loop

The rebase-pause handler used by `/pr:deslop --apply-rebase`. Borrows
the structure of `plugins/rebase/commands/rebase.md:46-67` (Phase 4 of
`/rebase`) with three tightenings specific to deslop:

1. **Touched-file gates first, full set at end.** After resolving
   each pause, re-run only the gates relevant to *touched files*. The
   full discovered gate set runs once at Step 12, not after every
   pick. This avoids `N × gate-runtime` cost on a 20-commit rebase.

2. **Tests opt-in via `--run-tests`.** Default off in the conflict
   loop. Per-pick test runs on a long rebase are hostile by default;
   the user opts in deliberately. Tests run at final verification
   only when `--run-tests` was passed.

3. **Track `git diff --cached` alongside unmerged files.**
   `rerere.autoupdate=true` auto-resolves *and stages* previously-seen
   conflicts, removing the conflict markers. A loop that only
   inspects unmerged files (`grep '^UU'` or `--diff-filter=U`) misses
   `rerere`'s resolutions entirely. Quality gates would never run on
   `rerere`-generated code. The loop must validate **both** unmerged
   and staged files.

---

## Setup (Step 10 — before entering the loop)

The autosquash invocation enables `rerere` so repeat invocations of
`/pr:deslop --apply-rebase` replay manual conflict resolutions:

```bash
GIT_SEQUENCE_EDITOR=: git -c rerere.enabled=true -c rerere.autoupdate=true rebase -i --autosquash "${BASELINE_SHA}"
```

`GIT_SEQUENCE_EDITOR=:` accepts the auto-generated todo list
non-interactively. Reword fixups carry their replacement messages
pre-staged in their bodies (`apply-template.sh` writes them with an
`amend! <subject>` prefix line); autosquash strips the prefix and
uses the remainder verbatim — no `GIT_EDITOR` shim required.

---

## The loop (Step 11)

When the rebase pauses with a conflict (or when `rerere` auto-resolves
a known conflict), enter the loop:

### 1. Inspect both unmerged and staged files

```bash
git diff --name-only --diff-filter=U
```

```bash
git diff --name-only --cached
```

The first list is files with unresolved conflict markers. The second
list includes both manually-staged resolutions and `rerere`'s
auto-staged resolutions.

### 2. Resolve any unmerged files

For each file in the first list, read it and resolve the conflict
markers (`<<<<<<<` / `=======` / `>>>>>>>`). Prefer the incoming
(fixup) side for the targeted lines, but preserve any other
structural changes from trunk-side context. When uncertain, surface
the conflict to the user via `AskUserQuestion` rather than guessing.

### 3. Stage explicit paths only

```bash
git add -- <file>
```

Per `plugins/commit/commands/commit.md:181-191` (rule line 187):
**never `git add -A` or `git add .`** — explicit paths only, even in
the conflict loop.

### 4. Run touched-file gates

The "touched files" set is the union of step 1's two lists. For each
discovered gate command (skip empty buckets), run it limited to those
files where the tool supports a path argument; if it does not, run
project-wide and accept the wider work.

```bash
${FORMAT_CMD}
```

```bash
${LINT_CMD}
```

```bash
${TYPECHECK_CMD}
```

If `--run-tests` was passed:

```bash
${TEST_CMD}
```

Treat each gate independently:

- **Formatter** auto-applies. Re-stage anything it changed:
  `git add -- <file>`.
- **Linter** with `--fix` auto-fixes; re-stage. Hard errors that
  don't auto-fix surface to the user via `AskUserQuestion` with three
  options:
  - **Edit and continue** — user fixes manually, the loop re-runs
    gates and continues.
  - **Skip this fixup** — `git rebase --skip` drops the failing
    pick.
  - **Abort** — `git rebase --abort` ends the rebase; the backup
    branch from Step 10 remains.
- **Type checker** never auto-modifies. Errors surface as
  linter-hard.
- **Tests** only run if `--run-tests` was passed. Same triage as
  type-check.

### 5. Continue the rebase

```bash
git rebase --continue
```

### 6. Loop until clean

If the next pick conflicts (or `rerere` auto-resolves another), loop
from step 1. `rerere` replays prior resolutions automatically; the
touched-file gates in step 4 validate `rerere`'s output before the
rebase advances.

### 7. Unrecoverable failure

If at any point recovery is impossible (cascading conflicts, gate
failures the user can't repair):

```bash
git rebase --abort
```

Report the failing pick and remind the user that the backup branch
from Step 10 still exists. They can `git reset --hard <backup>` to
return to the pre-deslop state.

---

## Why these tightenings matter

**Touched-first vs full set per pick.** A naïve loop running
`format` + `lint` + `typecheck` + `test` after every pick on a
20-commit rebase is roughly `20 × N` invocations of each tool.
Touched-first reduces that to per-pick incremental work plus one
final full pass. The trade-off is that a tool whose only failure
mode is project-wide cannot be caught mid-rebase; that's acceptable
because the final pass catches it.

**Tests opt-in.** Most projects' test suites are minutes-long. Running
them after every pick during a long rebase is hostile by default;
the user makes the opt-in decision via `--run-tests`. Final
verification at Step 12 still runs the full gate set including tests
when `--run-tests` was passed.

**`rerere` `--cached` tracking.** Without this, `rerere`'s
auto-staged resolutions never see the formatter or linter, so the
rebase can advance with code that fails project-wide gates. The
practical symptom is "the rebase finished but `lint` reports new
errors" — the conflict loop should catch and fix those errors at
each pause, not punt them to the final pass.
