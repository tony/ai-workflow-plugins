---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/pr:review-pr #42

Here's the PR body, in case you can't fetch it from GitHub in this session:

## Summary
- Add retry logic to the sync client so transient network errors don't fail the whole run
- Bump the HTTP timeout from 5s to 15s

## Test plan
- All 340 tests pass

### Fixes
- The sync client no longer throws on an empty response body

First I tried wrapping the whole sync loop in a blanket try/except, but that swallowed real errors too, so I narrowed it down to just the retryable exception types.
