---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/pytest-optimizer:00-scan tests/

Profile the suite under tests/ and tell me what's slow.
