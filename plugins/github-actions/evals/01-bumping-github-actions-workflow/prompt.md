---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
Dependabot opened a stack of PRs to bump the actions in my workflows. Instead of merging those one at a time, go through this workflow and get everything current:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@main
      - uses: astral-sh/setup-uv@v4
      - run: npm test
```
