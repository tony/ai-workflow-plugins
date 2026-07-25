---
name: gpt
description: >-
  Use when running a prompt through OpenAI GPT directly. An alternative
  invocation point for the `codex` skill — both use the same backend (codex
  binary or agent --model gpt-5.4-high fallback). Use this or the `codex`
  skill interchangeably.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit"]
metadata:
  argument-hint: "<prompt> [timeout:<seconds>]"
  source: "plugins/model-cli/skills/gpt/SKILL.md"
---

# GPT CLI Skill

This is an alias for the `codex` skill. Both entry points use the same backend.

Invoke the Codex CLI skill with `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask the user what they want to run.

All triggers supported by the `codex` skill are passed through, including `timeout:<seconds>`, `timeout:none`, and `mode:plan`.


## Portability notes

- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
