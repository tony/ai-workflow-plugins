---
name: gpt
description: >
  Use when running a prompt through OpenAI GPT directly. An alternative entry
  point for /model-cli:codex — both route to the same backend; use either
  interchangeably.
user-invocable: true
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit"]
argument-hint: <prompt> [timeout:<seconds>]
---

# GPT CLI Skill

This is an alias for `/model-cli:codex`. Both entry points use the same backend.

Invoke the Codex CLI skill with `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask the user what they want to run.

All triggers supported by `/model-cli:codex` are passed through, including `timeout:<seconds>`, `timeout:none`, and `mode:plan`.
