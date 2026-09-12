---
max_turns: 15
timeout_seconds: 360
allowed_tools: [Read, Glob, Grep, Skill]
---
This jira ticket is full of insertion counts and line numbers, rewrite it. It's WIDGET-482 in the tracker (no API access here, so I'm pasting exactly what's on the ticket right now):

Title: Rework the retry queue

Body:
Changed retryQueue.js (+142/-38 lines) to add a circuit breaker. Added new file breaker.js (89 lines). The fix replaces the linear backoff (lines 12-40 in the old retryQueue.js) with exponential backoff capped at 30s.

We first tried a token-bucket limiter but abandoned it because it caused thundering-herd retries under load; exponential backoff with jitter avoided that.

Definition of done:
- Circuit breaker implemented using the half-open state pattern
- Backoff capped at exactly 30 seconds
- retryQueue.js test coverage above 90%
