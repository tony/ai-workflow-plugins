---
description: Fix lint/quality errors in branch history — attribute each to its originating commit, fixup, and autosquash
argument-hint: "[command to pass, e.g. 'ruff check . --fix; ruff format .']"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit"]
---

## Context

- Current branch: !`git branch --show-current`
- Trunk branch: !`git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}' || echo "master"`
- Remote refs available: !`git remote -v 2>/dev/null | head -2`
- Commits on current branch not on trunk: !`TRUNK=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}' || echo "master"); git log --oneline "origin/${TRUNK}..HEAD" 2>/dev/null || echo "(could not determine commits ahead)"`
- Diff from trunk (summary): !`TRUNK=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}' || echo "master"); git diff --stat "origin/${TRUNK}" 2>/dev/null || echo "(could not diff against trunk)"`

## Your Task

Fix lint and quality errors across the branch history by attributing each error to the commit that introduced it, creating `--fixup` commits, and autosquashing. If the user provided a command via `$ARGUMENTS`, use it as the quality gate. Otherwise, discover the project's quality gates.

### Phase 1: Detect trunk and discover quality gates

Determine the trunk branch name from the context above (the "Trunk branch" value). Store it mentally as `TRUNK`. It will typically be `master` or `main`. If detection failed, try both `origin/master` and `origin/main` to see which exists.

**Quality gate discovery:**

If `$ARGUMENTS` provides explicit commands, use those directly as the quality gate.

Otherwise, discover quality gates from the project:

1. Read AGENTS.md / CLAUDE.md at the repo root — this is the primary source for the project's required quality checks.
2. If those files don't specify commands, look for project config files as fallback signals:

   | File | Ecosystem | Likely tools |
   |------|-----------|-------------|
   | `pyproject.toml` | Python | ruff, mypy, pytest |
   | `package.json` | Node.js | eslint, prettier, tsc, jest |
   | `Cargo.toml` | Rust | cargo clippy, cargo fmt, cargo test |
   | `go.mod` | Go | golangci-lint, gofmt, go test |
   | `Makefile` / `justfile` | Any | Look for lint/test/check targets |

   This table is illustrative — actual commands come from the project, never hardcoded.

### Phase 2: Run quality gates and collect errors

1. Run `git fetch origin` to get the latest remote state.
2. Run the discovered quality gate command(s) from Phase 1.
3. Collect all errors with file, line, rule, and message.
4. If no errors are found, report clean and stop.

### Phase 3: User confirmation gate

Present the following to the user and **wait for explicit approval** before proceeding:

- The exact command(s) that must pass
- Number of errors found, grouped by file
- Base branch for rebase (`origin/${TRUNK}`)
- Number of commits on branch
- Ask for special considerations (e.g., "if conflicts arise, ask me")

Do NOT proceed past this phase without user confirmation.

### Phase 4: Attribute errors to originating commits

For each error (by file:line):

1. Check if the line exists in trunk via `git show origin/${TRUNK}:<file>`.
2. **New line** (not in trunk): use `git log -S "<pattern>" --oneline origin/${TRUNK}..HEAD -- <file>` or `git blame` to find the introducing commit.
3. **Unmasked error** (line exists in trunk but error is new): find the branch commit that removed the suppression (e.g., `# noqa`, `// eslint-disable`, `#[allow(...)]`) via `git log -p origin/${TRUNK}..HEAD -- <file>`.
4. **Attribution fails**: flag for user review — ask whether to fix as a standalone commit or attribute manually.

Group errors by target commit SHA. Present an attribution table:

```
| Error | File:Line | Target Commit | Reason |
|-------|-----------|---------------|--------|
```

Wait for user confirmation of the attribution before proceeding.

### Phase 5: Fix errors and create fixup commits

**Single-commit branch shortcut:** if the branch has only one commit, skip fixup/autosquash — just fix the errors, stage, and amend directly (after confirmation).

For each target commit group:

1. Fix all errors attributed to this commit.
2. Run the quality gate to verify the fix is correct.
3. Stage only the specific files that were fixed:

```
git add <specific-files>
```

4. Create a fixup commit targeting the originating commit:

```
git commit --fixup=<target-sha>
```

Never bundle fixes for different target commits into one fixup commit.

### Phase 6: Autosquash

Run the interactive rebase with autosquash:

```
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash origin/${TRUNK}
```

- If clean: run quality gates on HEAD, then proceed to Phase 7.
- If conflicts arise: resolve file-by-file (same pattern as `/rebase` Phase 4), then run `git rebase --continue`.
- If unrecoverable: run `git rebase --abort` and report what went wrong.

Verify no fixup commits remain:

```
git log --oneline origin/${TRUNK}..HEAD
```

Confirm no `fixup!` prefixes appear in the output.

### Phase 7: Per-commit sweep (optional, on user request)

Ask the user: "Run a per-commit sweep to verify every commit passes individually?"

If yes, construct a portable `git rebase -i -x` command. The `-x` script runs under `sh`, not the user's login shell — it must be POSIX compatible:

```
GIT_SEQUENCE_EDITOR=: git rebase -i -x 'git log -1 --oneline HEAD && (<quality-command>) && git add -u && (git diff-index --quiet HEAD -- || git commit --amend --no-edit)' origin/${TRUNK}
```

Key details:
- `GIT_SEQUENCE_EDITOR=:` accepts the auto-generated sequence without opening an editor
- `git add -u` + conditional amend handles auto-fix tools that modify files in-place
- If `git-rebase-each-run` is available (detectable via `command -v git-rebase-each-run`), mention it as the equivalent shorthand

Report the final state after the sweep completes.

## Rules

- Never force-push — report final state, let the user decide
- Never bundle fixes for different target commits into one fixup commit
- Always present the attribution table before creating fixup commits
- Always wait for user confirmation at Phase 3
- If attribution is uncertain, flag for user review rather than guessing
- Use the project's commit message conventions from AGENTS.md / CLAUDE.md for any non-fixup commits
- If the quality gate includes auto-fix flags (e.g., `--fix`), ensure auto-fixes are staged
- The `-x` script must be POSIX `sh` compatible
