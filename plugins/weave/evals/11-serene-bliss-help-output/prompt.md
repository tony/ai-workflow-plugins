---
max_turns: 60
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill]
---
Our CLI's --help output is a wall of text with no grouping, unlike Stripe's CLI which groups commands by category with short one-line descriptions and colored section headers. Improve our --help formatting to feel calmer and more scannable. Do not change any command behavior, only the help text rendering. We use Python's argparse. Make the developer experience more serene here.
