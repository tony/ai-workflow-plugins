---
name: GPT CLI
description: >
  Alias for the Codex CLI skill. Use /model-cli:gpt as an alternative entry point
  for running prompts through OpenAI GPT via the codex or agent CLI.
user-invocable: true
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit"]
argument-hint: <prompt> [timeout:<seconds>]
---

# GPT CLI Skill

This is an alias for `/model-cli:codex`. Both entry points use the same backend.

Invoke the Codex CLI skill with `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask the user what they want to run.
