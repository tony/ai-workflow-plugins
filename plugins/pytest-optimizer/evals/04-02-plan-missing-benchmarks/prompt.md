---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/pytest-optimizer:02-plan --max-commits=3

Turn the validated speedups into an ordered commit plan.
