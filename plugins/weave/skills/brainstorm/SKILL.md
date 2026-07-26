---
name: brainstorm
description: >-
  Use when the user wants multiple independent ideas, alternatives, or
  approaches from adversarial participants for a creative prompt, design
  question, or open-ended problem. Triggers on phrases like "brainstorm",
  "give me ideas", "multiple approaches", "what are my options", or
  "explore alternatives"
user-invocable: true
argument-hint: "<prompt> [--variants=N] [--timeout=N|none] [--mode=fast|balanced|deep] [--preamble=...] [--workers=subagents|model-clis]"
---

# Weave Brainstorm

Generate independent original responses from adversarial participants in
parallel. Host-native sub-agents are the default; separate model CLIs are
available by explicit choice. Each participant produces its own take — no
synthesis or judging, just raw creative output.

## When to Use

- You need multiple independent perspectives on a problem
- You want to explore creative alternatives before committing
- You want independently prompted participants to approach the same prompt
- You need a pool of originals to feed into `/weave:refine` or `/weave:brainstorm-and-refine`

## Key Features

- `--workers=subagents|model-clis`: Use host-native sub-agents by default or explicitly select separate model CLIs
- `--variants=N` (1-3): Generate N independent responses per participant for maximum diversity
- Each variant gets a distinct creative-direction preamble (conventional/creative/contrarian)
- Override preambles with `--preamble='...'` for custom creative directions
- All responses presented raw — no scoring or ranking

## How to Invoke

Run the `/weave:brainstorm` command with your prompt. The command handles
context gathering, worker selection, parallel dispatch, and artifact
persistence.
