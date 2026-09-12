---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/spike:bakeoff --strategies="rewrite the cache as an LRU dict; swap in a Redis-backed cache" Compare two ways to fix the unbounded in-memory cache in the session store.
