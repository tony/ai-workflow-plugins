---
max_turns: 15
timeout_seconds: 360
allowed_tools: [Read, Glob, Grep, Skill]
---
Draft a Linear project description for the search rework. We're moving the search backend from Elasticsearch to a custom inverted index, adding typo tolerance, and cutting p95 query latency below 200ms.

Definition of done:
- storage engine changed to a custom inverted index
- typo tolerance shipped
- p95 latency under 200ms
