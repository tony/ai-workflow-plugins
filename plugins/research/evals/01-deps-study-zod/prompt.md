---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
I want to read the source of the library at the version we actually install. Here's the relevant part of package.json:

```json
{
  "dependencies": {
    "zod": "^3.22.0"
  }
}
```

And here's the matching fragment of package-lock.json:

```json
"node_modules/zod": {
  "version": "3.23.8",
  "resolved": "https://registry.npmjs.org/zod/-/zod-3.23.8.tgz"
}
```
