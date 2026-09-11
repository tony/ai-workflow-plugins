---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
write a failing test that proves this bug before we touch the code.

Bug report: `is_business_day(5)` returns `True` for Saturday, but Saturday should not count as a business day. Here's the function:

```python
def is_business_day(weekday: int) -> bool:
    """Return True for Monday (0) through Friday (4)."""
    return weekday >= 0 and weekday <= 5
```
