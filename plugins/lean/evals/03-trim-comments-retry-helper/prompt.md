---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
These comments are too fat, trim them:

```python
def fetch_with_retry(url):
    # This function fetches a URL with retries and returns the response
    MAX_RETRIES = 3  # retries up to 3 times
    for attempt in range(MAX_RETRIES):
        # try to make the request
        try:
            return requests.get(url, timeout=5)
        except requests.ConnectionError:
            # Windows CI runners see a cold DNS cache on the first call; the
            # extra attempt below absorbs it. Do not lower this without
            # testing on the windows-latest runner.
            continue
    raise TimeoutError("exhausted retries")
```
