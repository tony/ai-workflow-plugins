---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/scholar:extract --out=notes/ontology/sample-lib/

Harvest the terms this library uses for its own concepts, starting from whatever sources.jsonl already has on file.
