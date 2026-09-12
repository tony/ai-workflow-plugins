---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/github-actions:update-actions --audit-only

Audit every workflow action pin in this repository and tell me what's outdated. Don't make any changes yet.
