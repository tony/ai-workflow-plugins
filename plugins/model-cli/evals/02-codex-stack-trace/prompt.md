---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Have codex read this stack trace and find the bug:

```
Traceback (most recent call last):
  File "app/worker.py", line 42, in process_job
    result = queue.pop_next()
AttributeError: 'JobQueue' object has no attribute 'pop_next'
```
