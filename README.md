# claude-plugins

Language-agnostic workflow plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| [multi-model](plugins/multi-model/) | Development | Run prompts across Claude, Gemini, and GPT in parallel — plan, execute, review, and synthesize |
| [rebase](plugins/rebase/) | Development | Automated rebase onto trunk with conflict prediction, resolution, and quality gate verification |
| [changelog](plugins/changelog/) | Productivity | Generate categorized changelog entries from branch commits and PR context |
| [tdd](plugins/tdd/) | Testing | TDD bug-fix workflow — reproduce bugs as failing tests, find root cause, fix, and verify |

## Installation

Install a plugin from this marketplace repository:

```
/plugin install multi-model@tony/claude-plugins
/plugin install rebase@tony/claude-plugins
/plugin install changelog@tony/claude-plugins
/plugin install tdd@tony/claude-plugins
```

## Design Philosophy

Every plugin in this repository is **language-agnostic**. Commands do not hardcode
language-specific tools like `pytest`, `jest`, `cargo test`, or `ruff`. Instead, they
reference the project's own conventions by reading `AGENTS.md` or `CLAUDE.md` at
runtime to discover:

- How to run the test suite
- How to run linters and formatters
- How to run type checkers
- What commit message format to use
- What test patterns to follow

This means the same plugin works whether your project uses Python, TypeScript, Rust, Go,
or any other language.

## Development

### Lint and validate

```bash
uv run scripts/marketplace.py lint
```

### Sync marketplace manifest with plugin directories

```bash
uv run scripts/marketplace.py sync          # dry-run
uv run scripts/marketplace.py sync --write  # update marketplace.json
```

### Check for outdated entries

```bash
uv run scripts/marketplace.py check-outdated
```

### Code quality for scripts

```bash
ruff check scripts/
ruff format --check scripts/
basedpyright scripts/
```

## License

MIT
