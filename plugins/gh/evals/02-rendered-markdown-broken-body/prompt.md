---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
Rewrite this comment body so the code fences actually render on github and the links won't rot:

```
The retry logic drops the timeout after the third attempt because
resolveTarget() resets opts.target before the loop checks it again,
which means every later attempt silently uses the default target
instead of the one the caller passed in.

<details>
<summary>Full stack trace</summary>
TypeError: Cannot read properties of undefined (reading 'target')
    at resolveTarget (src/build.js:42)
</details>

See https://github.com/example/widgets/blob/main/src/build.js#L38-L50 for the code.
```
