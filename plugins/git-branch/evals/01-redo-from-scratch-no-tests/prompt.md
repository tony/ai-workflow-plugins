---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
The proof of concept grew into the real thing, redo it properly. The current implementation hand-rolls a small recursive descent parser for config files and works, but nobody ever wrote a test suite for it. I want the parsing logic reimplemented from scratch, now that we understand the real requirements: read `.ini`-style files, support nested sections via dotted keys, and merge in environment variable overrides. Please start the rewrite.
