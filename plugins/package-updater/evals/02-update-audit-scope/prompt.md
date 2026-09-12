---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/package-updater:update --audit-only

Audit this repository for outdated packages and toolchain pins and tell me what is out of date. Do not make any changes yet.
