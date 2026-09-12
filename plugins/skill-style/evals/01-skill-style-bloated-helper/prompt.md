---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---
This SKILL.md is bloated, cut the lines that don't change what the agent does:

```
---
name: helper
description: "This skill helps you with various tasks related to formatting code."
allowed-tools: ["Read", "Edit"]
---

# Code Formatter Helper

This skill helps format code nicely. It is designed to help make your code cleaner and more readable.

## Notes

Formatting is important because it makes code easier to read. Well-formatted code is generally considered a best practice in software engineering.

## Steps

1. Read the file.
2. Look at the code.
3. Apply formatting fixes as needed.
4. Show the diff.

## Table of options

| Option | Description |
|---|---|
| --check | Only check, do not modify |
| --fix | Apply fixes |
```
