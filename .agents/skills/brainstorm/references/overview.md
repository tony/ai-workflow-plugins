# Weave Brainstorm

Generate independent original responses from Claude, Antigravity, and GPT in parallel. Each model produces its own unique take — no synthesis, no judging, just raw creative output.

## When to Use

- You need multiple independent perspectives on a problem
- You want to explore creative alternatives before committing
- You want to see how different AI models approach the same prompt
- You need a pool of originals to feed into the `refine` skill or the `brainstorm-and-refine` skill

## Key Features

- `--variants=N` (1-3): Generate N independent responses per model for maximum diversity
- Each variant gets a distinct creative-direction preamble (conventional/creative/contrarian)
- Override preambles with `--preamble='...'` for custom creative directions
- All responses presented raw — no scoring or ranking

## How to Invoke

Run this skill with your prompt. The command handles context gathering, model detection, parallel dispatch, and artifact persistence.
