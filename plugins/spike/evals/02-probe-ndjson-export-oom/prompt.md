---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/spike:probe Prove that streaming the export as NDJSON instead of buffering the whole file in memory actually fixes the OOM crash on large exports.
