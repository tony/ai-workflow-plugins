---
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
Keep this commit message tight, no filler and no story of what I tried:

```
Fixed the login bug

So I spent a while looking into this and at first I thought it was a
caching problem, then I tried clearing the session store, which didn't
help. Eventually I realized the token expiry check was comparing seconds
to milliseconds. This commit fixes that by converting both sides to
milliseconds before comparing. Let me know if you have any questions!
```
