---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/respond:goal --max-rounds=2 Keep running the review-and-CI loop on this branch until nothing new comes back.
