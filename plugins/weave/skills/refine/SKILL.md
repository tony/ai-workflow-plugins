---
name: refine
description: >-
  Use when the user has an existing draft, text, code, or artifact and wants
  it iteratively improved through independent adversarial critique and weaving
  across multiple passes. Triggers on phrases like "refine this", "improve
  this", "make this better", "iterate on this", or "polish this"
user-invocable: true
argument-hint: "<text or file path> [--passes=N] [--timeout=N|none] [--mode=fast|balanced|deep] [--judge=host|round-robin] [--workers=subagents|model-clis]"
---

# Weave Refine

Iteratively improve an artifact through independent adversarial critique and
weaving. Host-native sub-agents are the default; separate model CLIs are
available by explicit choice. Each pass judges the alternatives, picks the
best, incorporates runner-up strengths, and addresses weaknesses.

## When to Use

- You have a draft that needs improvement
- You want independent adversarial participants to critique and enhance an artifact
- You want iterative refinement where each pass genuinely improves the output
- You have output from `/weave:brainstorm` that you want to refine further

## Key Features

- Accepts inline text or file paths (auto-detected)
- `--workers=subagents|model-clis`: Use host-native sub-agents by default or explicitly select separate model CLIs
- `--passes=N` (1-5, default 2): Number of refinement cycles
- Each pass: all participants critique and improve, judge picks best, weaves in strengths from runners-up
- Full rationale chain showing evolution across passes
- Early-stop when no material improvement detected
- `--judge=host|round-robin`: Host judges every pass, or rotate judging across participants

## The Refinement Cycle

1. All participants independently critique and improve the artifact
2. Judge scores versions, picks the best, identifies strengths in runners-up
3. Judge weaves a revised version incorporating all improvements
4. Woven version goes back to all participants for another round
5. Repeat until passes exhausted or convergence

## How to Invoke

Run the `/weave:refine` command with your text or file path. The command
handles context gathering, worker selection, the judge-weave-distribute
cycle, and artifact persistence.
