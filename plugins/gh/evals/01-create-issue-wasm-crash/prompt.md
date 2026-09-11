---
max_turns: 15
timeout_seconds: 360
allowed_tools: [Read, Glob, Grep, Skill]
---
Report this bug to the maintainers with a reproduction. It's in the open-source project example/widgets. Here's what I found:

Running `widgets build --target=wasm` on version 2.4.1 with Node 20 throws:

```
TypeError: Cannot read properties of undefined (reading 'target')
```

I confirmed it happens every time by running the same command on a clean checkout of v2.4.1. It works fine on v2.3.0. Looking at the source, `resolveTarget()` in `src/build.js` assumes `opts.target` is always set, but the wasm preset never populates it.
