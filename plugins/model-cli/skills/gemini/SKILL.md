---
name: gemini
description: >
  Use when running a prompt through Google's Gemini directly. A manual alias for
  /model-cli:agy — both entry points route through the same backend chain.
user-invocable: true
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit"]
argument-hint: <prompt> [timeout:<seconds>]
---

# Gemini CLI Skill

This is an alias for `/model-cli:agy`. Google's Antigravity (`agy`) CLI is the
successor to the standalone `gemini` CLI, so this entry point resolves through the
same backend chain (`agy` → `gemini` → `agent --model gemini-3.1-pro`). When `agy`
is unavailable it still falls back to the `gemini` CLI, so `/model-cli:gemini`
keeps working before and after the gemini CLI is retired.

Invoke the Antigravity (agy) CLI skill with `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask the user what they want to run.

All triggers supported by `/model-cli:agy` are passed through, including `timeout:<seconds>`, `timeout:none`, and `mode:plan`.
