---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Keep this commit message tight, no filler:

```
Fixed the login bug

So I spent a while looking into this and at first I thought it was a
caching problem. Eventually I realized the token expiry check compared
seconds to milliseconds. Let me know if you have any questions!
```
