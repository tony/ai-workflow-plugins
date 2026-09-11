---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/respond:action --on-fail=stop Fix the review findings below on this branch:

1. `parse_retry_after` throws a `ValueError` when the header has no numeric value; add a fallback to 5 seconds.
2. Typo in the log message: 'recieved' should be 'received'.
