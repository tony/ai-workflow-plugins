---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/model-cli:gpt "double check this regex handles unicode edge cases" timeout:90

```
^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$
```
