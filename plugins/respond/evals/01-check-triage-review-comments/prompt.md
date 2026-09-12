---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
screen the review comments on my PR and tell me which are worth fixing. Don't fix anything yet, just give me the verdicts.

1. Alex: "`parse_retry_after` throws a `ValueError` when the header has no numeric value, e.g. `Retry-After: bar`. Needs a fallback."
2. lint-bot: "`session.token` is called without checking `session` for `None` first."
3. Alex: "This will crash if `session` is `None` when `.token` is accessed — looks like the same thing the lint bot flagged above."
4. style-bot: "Consider splitting this 45-line function into smaller pieces for readability."
5. Alex: "Typo: 'recieved' should be 'received' in the log message."
