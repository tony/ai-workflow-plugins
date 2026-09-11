---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
/ruff:bump --audit-only

Here is the relevant part of pyproject.toml:

```toml
[dependency-groups]
dev = ["ruff==0.13.0"]

[tool.ruff.lint]
select = ["E", "F"]
```
