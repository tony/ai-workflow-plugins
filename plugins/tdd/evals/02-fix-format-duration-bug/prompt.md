---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/tdd:fix `format_duration(0)` returns an empty string instead of '0s', so a zero-second duration shows blank in the UI.

```python
def format_duration(total_seconds: int) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    parts = []
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    return " ".join(parts)
```
