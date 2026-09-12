---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
/github-actions:update-action actions/checkout

Current pin in .github/workflows/ci.yml:

```yaml
      - uses: actions/checkout@v3
```
