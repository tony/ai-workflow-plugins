---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/lean:tighten --stdin

Tighten this draft doc section, please:

```
Certainly! Here's an overview of the caching layer:

[R1] Use write-through caching for consistency, since it is simpler to reason about than write-behind.

The ttl setting controls how long entries live before they get evicted, i.e. their time to live.

As of commit a1b2c3d9, the eviction sweep runs every 500ms on a background thread.

Let me know if you want more detail on any of this!
```
