---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Let cursor's cli handle the boring refactor on this function:

```python
def get_user(id):
    u = db.query("SELECT * FROM users WHERE id = " + str(id))
    return u
```
