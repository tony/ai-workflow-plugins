---
name: xfail
description: >-
  Use when fixing a bug that needs strict proof the test fails for the right
  reason — not because a mock is misconfigured. A hermetic xfail TDD workflow
  with diff-gate guards (distinct from a plain TDD fix). Triggers on "xfail",
  "strict xfail", "hermetic TDD", "reproduce with xfail", or "expected
  failure workflow".
user-invocable: true
argument-hint: Paste or describe the bug to reproduce and fix with hermetic xfail guards
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "Task"]
---

# Hermetic xfail TDD Workflow

You are an expert test engineer performing a **hermetic** TDD bug-fix with
strict reproduction guards. Every phase has a gate that must pass before
proceeding. The goal is not just a fix — it is **proof** that the test
fails for the right reason.

Initial bug report: $ARGUMENTS

---

## Orchestration Plan

Before executing any phase, enter plan mode and produce an orchestration
plan. Plan-mode activation varies by host:

- Claude Code: `EnterPlanMode` tool
- Cursor / Codex / Gemini: `/plan` or `Shift+Tab`

The plan must contain:

1. **Bug summary** — symptom, expected behavior, trigger conditions, affected component
2. **Test strategy** — which test file, which fixtures, which xfail mechanism
3. **Mock assessment** — are mocks required? If so, what real behavior do they replace, and how will you verify the failure is genuine (not mock-induced)?
4. **Framework detection** — which xfail mechanism applies (see framework table below)
5. **Diff-gate file sets** — which paths are test files, which are source files
6. **Quality gates** — commands from AGENTS.md/CLAUDE.md (formatter, linter, type checker, test runner)

Present the plan to the user and wait for approval before executing.

If plan mode is unavailable, write the plan as numbered steps in your
response and confirm with the user before proceeding.

---

## Phase 0: Discover Conventions

**Goal**: Understand the project's testing and quality conventions.

**Actions**:
1. Create a todo list tracking all phases
2. Read AGENTS.md / CLAUDE.md to discover:
   - Test framework and conventions (structure, fixtures, assertion style)
   - Quality gate commands (test runner, linter, formatter, type checker)
   - Commit message format
3. Detect the test framework and select the xfail mechanism:

| Framework | xfail mechanism | Strict equivalent | XPASS behavior |
|-----------|----------------|-------------------|----------------|
| pytest | `@pytest.mark.xfail(strict=True, reason="...")` | Built-in | XPASS = test failure |
| Jest | `it.failing('...')` | Built-in (pass = fail) | Passing test fails suite |
| Vitest | `it.fails('...')` | Built-in | Same as Jest |
| Rust | `#[should_panic(expected = "...")]` | `expected` param | Wrong/no panic = failure |
| Go | `t.Skip("known bug: ...")` | No strict equivalent | See skip-cycle protocol below |

### Frameworks without strict xfail (Go, others)

`t.Skip` skips the test entirely — it never executes, so it cannot
XPASS. For these frameworks, use a **skip-remove-run-reskip** cycle at
each verification phase:

- **Phase 1**: Write the test with `t.Skip("known bug: ...")`. Run the
  test to confirm it is skipped.
- **Phase 2**: Temporarily remove `t.Skip`. Run the test — it MUST fail
  for the right reason. Restore `t.Skip`.
- **Phase 3**: Apply the fix. Temporarily remove `t.Skip`. Run the
  test — it MUST pass. Restore `t.Skip`.
- **Phase 4**: Stash the fix. Remove `t.Skip`. Run the test — it MUST
  fail again. Restore `t.Skip`. Pop the stash.
- **Phase 5**: Remove `t.Skip` permanently.

The diff gates and three-commit structure apply identically.

4. Identify the test file glob patterns for this project (used by diff gates):
   - Common patterns: `**/test_*`, `**/*_test.*`, `**/tests/**`, `**/__tests__/**`, `**/*.test.*`, `**/*.spec.*`
5. Use Explore agents to find the relevant source code and existing tests

---

## Phase 1: Reproduce — Write xfail Test

**Goal**: Create a test that reproduces the bug, marked as expected-to-fail.

### Mock contamination rule

The reproduction test MUST exercise real code paths. If mocking is
unavoidable (network, filesystem, external services), the test must
verify the failure matches the bug's actual symptom — same exception
type, same error message, same wrong-value pattern. If the mock is what
causes the failure (not the bug), discard the test and start over.

**Actions**:
1. Study existing test patterns in the target test file
2. Write a test function that:
   - Has a descriptive name reflecting the bug scenario
   - Uses existing fixtures wherever possible
   - Is marked as expected-to-fail with the framework's strict mechanism
   - Asserts the **correct** (expected) behavior, not the buggy behavior
   - For pytest: include `reason=`, `strict=True`, and `raises=` when the expected exception type is known
3. Run the test — it must report as an expected failure (e.g., `xfail` in pytest, not `FAILED`)
4. Run the full test file to confirm no other tests broke
5. Run all quality gates from AGENTS.md/CLAUDE.md

### Gate 1: xfail confirmation

The test must produce an expected-failure result. If it passes outright,
the test does not reproduce the bug — rewrite it. If it fails with an
unexpected exception (not matching `raises`), the reproduction is
targeting the wrong symptom.

6. **Commit** using the project's commit format. The commit must contain only test file changes.

---

## Phase 2: Verify Reproduction Is Genuine

**Goal**: Prove the test fails because of the bug, not because of test setup.

**Actions**:
1. Temporarily remove the xfail marker from the test
2. Run the test — it MUST fail
3. Inspect the failure output:
   - Does the error match the bug's actual symptom?
   - Is the exception type what you expect?
   - Could a misconfigured mock produce this same failure?
4. Restore the xfail marker

### Gate 2: genuine-failure confirmation

If the failure does not match the bug's symptom, the reproduction is
contaminated. **Restart, don't patch** — delete the test entirely and
return to Phase 1. Do not tweak mock setup to make it "look right."

This phase produces no commit. It is a verification-only checkpoint.

---

## Phase 3: Apply Fix

**Goal**: Fix the source code. Zero test file changes in this commit.

**Principles**:
- Minimal change — only fix what's broken
- Don't refactor surrounding code
- Don't add features beyond the fix
- Follow existing code patterns from AGENTS.md/CLAUDE.md

**Actions**:
1. Apply the fix to the source code
2. Remove any debug instrumentation from Phase 2
3. Run the xfail test — it should now XPASS (unexpected pass):
   - pytest with `strict=True`: test reports as FAILED with `[XPASS(strict)]`
   - Jest `it.failing`: test reports as failed (because it passed)
   - Vitest `it.fails`: same as Jest
   - Rust `#[should_panic]`: test reports as failed (no panic)
4. Run non-test quality gates (formatter, linter, type checker). The full
   test suite is not run at this phase — the XPASS(strict) failure is
   expected and confirms the fix works.

### Gate 3: zero-diff on test files

Using the test file patterns identified in Phase 0, verify no test files
were modified. Example using common patterns:

```
git diff --stat HEAD -- <test-file-patterns>
```

This must produce empty output. If test files were modified, unstage them
and move those changes to Phase 5.

Do **not** commit yet — Phase 4 must verify fix isolation first.

---

## Phase 4: Verify Fix Isolation

**Goal**: Prove the fix is what resolved the test, not an unrelated change.

**Actions**:
1. Stash the fix: `git stash -u`
2. Run the xfail test — it must xfail again (the bug is back)
3. Restore the fix: `git stash pop`
4. Run the xfail test — it must XPASS again (the fix works)

### Gate 4: stash round-trip confirmation

If the test does not return to xfail when the fix is stashed, the fix is
not what resolved the test. Investigate what else changed.

5. **Commit** the fix using the project's commit format. Include the root
   cause explanation.

---

## Phase 5: Remove xfail Marker

**Goal**: Convert the xfail test to a permanent regression test. Zero source
code changes in this commit.

**Actions**:
1. Remove the expected-failure marker from the test
2. Update any test comments to describe it as a regression test (not a bug report)
3. Run the test — it MUST pass
4. Run the full test suite for the affected file/module
5. Run all quality gates

### Gate 5: zero-diff on source files

Using the test file patterns identified in Phase 0, verify no source
files (non-test) were modified. Example using common patterns:

```
git diff --stat HEAD -- . ':!<test-file-patterns>'
```

This must produce empty output. If source files were modified, unstage
them — they belong in a separate commit.

6. **Commit** using the project's commit format.

---

## Phase 6: Final Verification

**Goal**: Full suite passes cleanly.

**Actions**:
1. Run the complete test suite
2. Run all quality gates
3. Verify three commits were produced with the correct separation:
   - Commit 1: test files only (xfail reproduction)
   - Commit 2: source files only (fix)
   - Commit 3: test files only (xfail removal)

### Gate 6: full suite green

If any test fails, diagnose whether the fix introduced a regression.
Apply a minimal fix and re-run from Phase 3.

---

## Recovery Protocol

### A. Reproduction is not genuine (Phase 2 fails)

The test fails, but not because of the bug.

**Action**: Delete the test entirely. Return to Phase 1. Do not adjust
mocks to produce the "right" failure — that is the mock contamination
the protocol is designed to prevent.

### B. Fix does not resolve the test (Phase 3 fails)

The xfail test still xfails after applying the fix.

**Action**: Revert the fix. Return to root cause analysis. Re-examine
whether the test exercises the code path you fixed.

### C. Fix is not isolated (Phase 4 fails)

The test does not return to xfail when the fix is stashed.

**Action**: Something else resolved the test. Investigate: stale build
cache, unrelated change in the working tree, dependency update. Identify
the true cause before proceeding.

### D. Loop limit

After 3 failed attempts at any phase, stop and present findings:
- What was tried
- What the test output shows
- What the suspected issue is
- Ask for guidance

---

## CI Integration (Optional)

When the project has CI, the three-commit sequence provides additional
verification. Push after each commit phase:

| After | Expected CI result | Why |
|-------|-------------------|-----|
| Phase 1 commit | Green | xfail = expected failure, suite passes |
| Phase 4 commit | Red | `strict=True` makes XPASS a failure (expected) |
| Phase 5 commit | Green | xfail removed, test passes normally |

If CI is not available or the user prefers local-only verification, the
diff gates and stash round-trip provide equivalent confidence.

---

## Cross-Dependency Workflow

When the bug involves both this project and a dependency:

1. Fix the dependency first using the same hermetic protocol
2. Commit in the dependency using its conventions
3. Verify the dependency's test suite passes
4. Update this project's dependency reference to the fixed local source
5. Then run the protocol in this project

---

## Quality Gates (every commit must pass)

Before EVERY commit, run the project's quality gates as defined in
AGENTS.md/CLAUDE.md. Common gates include:

| Gate | Example commands |
|------|-----------------|
| Formatter | `ruff format`, `prettier --write`, `rustfmt`, `gofmt` |
| Linter | `ruff check`, `eslint`, `clippy`, `golangci-lint` |
| Type checker | `mypy`, `tsc --noEmit`, `basedpyright` |
| Tests | `pytest`, `jest`, `cargo test`, `go test` |

ALL gates must pass. A commit with failing tests or lint errors is not
acceptable.

**Exception**: Phase 3 runs non-test gates only. The XPASS(strict)
result is the expected proof that the fix works; the full test suite
passes after Phase 5 removes the xfail marker.

---

## Commit Message Format

Use the project's commit message format from AGENTS.md/CLAUDE.md. If no
format is specified, use a conventional format that clearly describes:
- The component affected
- Whether this is a test addition (xfail), a fix, or xfail removal
- Why the change was needed
- What specifically changed

Wrap body lines at **72 characters**. Let URLs, file paths, hashes, and
long identifiers overflow rather than breaking mid-token.
