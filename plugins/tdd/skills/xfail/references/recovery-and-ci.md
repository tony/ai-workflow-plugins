# Recovery, CI, and Cross-Dependency Protocols

Situational protocols for the hermetic xfail workflow. Read the section that
matches the situation you hit; the main SKILL.md phases point here when needed.

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

## Cross-Dependency Workflow

When the bug involves both this project and a dependency:

1. Fix the dependency first using the same hermetic protocol
2. Commit in the dependency using its conventions
3. Verify the dependency's test suite passes
4. Update this project's dependency reference to the fixed local source
5. Then run the protocol in this project
