# Weave Brainstorm

Generate independent original responses from adversarial participants in
parallel. Host-native sub-agents are the default; separate model CLIs are
available by explicit choice. Each participant produces its own take — no
synthesis or judging, just raw creative output.

## When to Use

- You need multiple independent perspectives on a problem
- You want to explore creative alternatives before committing
- You want independently prompted participants to approach the same prompt
- You need a pool of originals to feed into the `weave-refine` skill or the `weave-brainstorm-and-refine` skill

## Key Features

- `--workers=subagents|model-clis`: Use host-native sub-agents by default or explicitly select separate model CLIs
- `--variants=N` (1-3): Generate N independent responses per participant for maximum diversity
- Each variant gets a distinct creative-direction preamble (conventional/creative/contrarian)
- Override preambles with `--preamble='...'` for custom creative directions
- All responses presented raw — no scoring or ranking

## How to Invoke

Run this skill with your prompt. The command handles
context gathering, worker selection, parallel dispatch, and artifact
persistence.
