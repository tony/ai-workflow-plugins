---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/terraform:refresh-lock --audit-only

Tell me which root modules have a lock file that can be refreshed.
