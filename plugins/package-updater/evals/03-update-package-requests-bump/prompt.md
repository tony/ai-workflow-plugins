---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/package-updater:update-package requests 2.32.4

Here is the relevant part of pyproject.toml:

```toml
[project]
dependencies = [
    "requests>=2.28.0",
]
```
