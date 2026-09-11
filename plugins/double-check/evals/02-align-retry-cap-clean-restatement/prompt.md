---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/double-check:align the retry cap value

Here's what you told me in your last message, and I don't want it repeated in this format:

"Verdict update: Item 1 (MAX_RETRIES) — overstated, corrected to 3. Item 2 (backoff seconds) — still holds at 2. As I mentioned before, the retry loop code confirms this."

Here's the client module again for reference:

```python
# client.py
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2
```

Give me the clean version.
