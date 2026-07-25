# Weave Brainstorm & Refine

The full pipeline: generate independent originals from each model, then iteratively refine them through judge-weave-incorporate cycles.

## When to Use

- You want the best of both worlds: creative divergence then convergent refinement
- You want to explore a problem space broadly, then hone in on the best solution
- You need a high-quality result and are willing to spend tokens on multiple passes

## Key Features

- Phase 1 (Brainstorm): Independent originals from each model, optional `--variants=N`
- Transition gate: You choose which originals enter refinement
- Phase 2 (Refine): Iterative judge-weave-distribute cycle over `--passes=N`
- Full rationale chain from brainstorm through every refinement pass
- `--judge=host|round-robin`: Host judges every pass, or rotate judging across models

## The Pipeline

1. **Brainstorm**: Each model generates independent original responses
2. **Review**: All originals presented — you pick which ones to refine
3. **Refine**: Judge picks the best, weaves in strengths from runners-up, redistributes to all models
4. **Repeat**: Each pass improves the woven result until convergence or passes exhausted

## How to Invoke

Run this skill with your prompt. The command handles both phases, the transition gate, and artifact persistence.
