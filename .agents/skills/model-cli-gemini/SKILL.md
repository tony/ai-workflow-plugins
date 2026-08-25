---
name: model-cli-gemini
description: >-
  Use when invoking Google's Gemini directly through the shared Antigravity,
  Gemini CLI, or agent fallback chain.
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit"]
metadata:
  argument-hint: "<prompt> [timeout:<seconds>]"
  source: "plugins/model-cli/skills/gemini/SKILL.md"
---

# Gemini CLI Skill

This is an alias for the `model-cli-agy` skill. Google's Antigravity (`agy`) CLI is the
successor to the standalone `gemini` CLI, so this entry point resolves through the
same backend chain (`agy` → `gemini` → `agent --model gemini-3.1-pro`). When `agy`
is unavailable it still falls back to the `gemini` CLI, so this skill
keeps working before and after the gemini CLI is retired.

Invoke the Antigravity (agy) CLI skill with `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask the user what they want to run.

All triggers supported by the `model-cli-agy` skill are passed through, including `timeout:<seconds>`, `timeout:none`, and `mode:plan`.


## Portability notes

- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
