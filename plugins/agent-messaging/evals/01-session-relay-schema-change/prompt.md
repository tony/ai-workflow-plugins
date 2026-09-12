---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Tell the agent in the other pane that the schema changed: the `orders` table now has a `fulfilled_at` column, and any code reading order status needs to check it instead of the old `status` enum.
