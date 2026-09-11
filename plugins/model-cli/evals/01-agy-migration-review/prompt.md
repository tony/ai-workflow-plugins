---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Have gemini look at this migration and tell me what breaks:

```sql
ALTER TABLE orders DROP COLUMN legacy_status;
ALTER TABLE orders ADD COLUMN status_id INTEGER NOT NULL DEFAULT 1;
```
