---
name: refine
description: >-
  Use when the user has an existing draft, text, code, or artifact and wants
  it iteratively improved through multi-model critique and weaving across
  multiple passes. Triggers on phrases like "refine this", "improve this",
  "make this better", "iterate on this", or "polish this"
user-invocable: true
argument-hint: "<text or file path> [--passes=N] [--timeout=N|none] [--mode=fast|balanced|deep] [--judge=host|round-robin]"
---

# Weave Refine

Iteratively improve an artifact through multi-model critique and weaving. Each pass is a full judge-pick-best-incorporate-strengths-address-weaknesses cycle.

## When to Use

- You have a draft that needs improvement
- You want multiple AI models to critique and enhance an artifact
- You want iterative refinement where each pass genuinely improves the output
- You have output from `/weave:brainstorm` that you want to refine further

## Key Features

- Accepts inline text or file paths (auto-detected)
- `--passes=N` (1-5, default 2): Number of refinement cycles
- Each pass: all models critique and improve, judge picks best, weaves in strengths from runners-up
- Full rationale chain showing evolution across passes
- Early-stop when no material improvement detected
- `--judge=host|round-robin`: Host judges every pass, or rotate judging across models

## The Refinement Cycle

1. All models independently critique and improve the artifact
2. Judge scores versions, picks the best, identifies strengths in runners-up
3. Judge weaves a revised version incorporating all improvements
4. Woven version goes back to all models for another round
5. Repeat until passes exhausted or convergence

## How to Invoke

Run the `/weave:refine` command with your text or file path. The command handles context gathering, model detection, the judge-weave-distribute cycle, and artifact persistence.
