---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/weave:fix-review

Here is the weave code review report from our last session:

# Code Review

## Verified Issues

### Critical (consensus 2/3)
- **File**: src/webhook.py:42
- **Description**: The retry counter is never reset after a successful delivery, so a job that succeeds once and fails later starts counting from the old total and can hit the retry ceiling immediately.
- **Recommendation**: Reset `retry_count` to 0 on successful delivery before returning.

### Important (single-reviewer)
- **File**: src/webhook.py:88
- **Description**: `queue.push(job)` is called without checking the queue's max depth, so a burst of failures could grow the queue unboundedly.
- **Recommendation**: Add a max-depth check before pushing.

## Summary
Two issues found in the webhook retry path. Fix the Critical finding first.

Please process these findings.
