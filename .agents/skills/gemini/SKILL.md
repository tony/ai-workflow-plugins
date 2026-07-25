---
name: gemini
description: >-
  Use when running a prompt through Google's Gemini directly. A manual
  invocation point for the `agy` skill — the Antigravity (agy) CLI
  supersedes the standalone gemini CLI (Google retires it on 2026-06-18), so
  both entry points resolve through the same backend chain: agy, then the
  gemini CLI, then agent --model gemini-3.1-pro.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Edit"]
metadata:
  argument-hint: "<prompt> [timeout:<seconds>]"
  source: "plugins/model-cli/skills/gemini/SKILL.md"
---

# Gemini CLI Skill

This is an alias for the `agy` skill. Google's Antigravity (`agy`) CLI is the
successor to the standalone `gemini` CLI, so this entry point resolves through the
same backend chain (`agy` → `gemini` → `agent --model gemini-3.1-pro`). When `agy`
is unavailable it still falls back to the `gemini` CLI, so this skill
keeps working before and after the gemini CLI is retired.

Invoke the Antigravity (agy) CLI skill with `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask the user what they want to run.

All triggers supported by the `agy` skill are passed through, including `timeout:<seconds>`, `timeout:none`, and `mode:plan`.


## Portability notes

- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
