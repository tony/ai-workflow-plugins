# ai-workflow-plugins

A third-party [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces.md)
providing language-agnostic AI / agentic workflow plugins for DX efficiency.

> **Warning:** Review plugins before installing. Anthropic does not control plugin
> contents and cannot verify they work as intended.

**Repository:** [tony/ai-workflow-plugins](https://github.com/tony/ai-workflow-plugins)

## Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| [commit](plugins/commit/) | Development | Create git commits following project conventions with format enforcement and safety checks |
| [weave](plugins/weave/) | Development | Run independent adversarial participants through host-native sub-agents by default or separate model CLIs by choice — brainstorm, refine, plan, execute, architect, review, and synthesize |
| [rebase](plugins/rebase/) | Development | Automated rebase onto trunk with conflict prediction, resolution, and quality gate verification |
| [changelog](plugins/changelog/) | Productivity | Generate categorized changelog entries from branch commits and PR context; refresh or recut a branch's own entries as it evolves |
| [tdd](plugins/tdd/) | Testing | TDD bug-fix workflow — reproduce bugs as failing tests, find root cause, fix, and verify |
| [model-cli](plugins/model-cli/) | Development | Run prompts through individual AI CLIs — Antigravity/agy (Gemini), codex/GPT, and cursor/agent with fallback support |
| [pr](plugins/pr/) | Development | Generate, refresh, recut, and review gold-standard PR descriptions; detect AI slop, brittle counts, and verbose commit messages on branch commits and resolve via fixup commits and autosquash with quality-gate checks |
| [research](plugins/research/) | Learning | Clone and study your project's dependencies at the exact versions you use — source repos with version-pinned git worktrees |
| [slop](plugins/slop/) | Development | Scan repo tracked files for AI slop, brittle counts, and verbose noise; resolve each finding as an atomic forward-going commit with quality-gate verification |
| [tailwind](plugins/tailwind/) | Design | Detect and fix inconsistent spacing in Tailwind CSS layouts — container fragmentation, margin/gap mixing, padding asymmetry, and more |
| [pytest-optimizer](plugins/pytest-optimizer/) | Testing | Profile a pytest suite, rank safe speedups with a safety-first rubric, and apply each as its own verified commit |
| [spike](plugins/spike/) | Development | Prove a path fast in a no-commit spike — a single probe or a bakeoff of competing strategies in git worktrees — exit through the project's quality gates into stashes, and hand back a commit-by-commit implementation plan |
| [review](plugins/review/) | Development | Address code-review findings on the current branch — provenance-gated to changes the branch introduced, one finding per commit, simplest pragmatic fix, with quality gates before every commit and prompted history rewrites |
| [action](plugins/action/) | Development | Take tickets to branches in isolated git worktrees — resolve Linear/GitHub issues strictly read-only, name branches by the team's own conventions, land gated commits, and fan out multiple tickets in parallel |
| [lean](plugins/lean/) | Development | Write tight, slop-free prose and code, and tighten existing files in place with no commits — a model-invocable writing discipline plus a working-tree cleanup command |
| [double-check](plugins/double-check/) | Productivity | Make verification requests return the re-derived answer instead of a diff against the agent's prior turn — an ambient skill for 'double check' / 'are you sure' moments plus an /align command to repair a chat where the diff already happened |
| [release](plugins/release/) | Development | Cut and bump releases with safe defaults — no push, no tag, no tag push without an explicit flag — and roll new releases out to every downstream consumer repo with CI verification |
| [merge-pr](plugins/merge-pr/) | Development | Merge PRs via gh with merge commits matching the repo's own git history — readiness checks and CI watch before every merge, plus multi-PR runs with stack detection, rebase, and conflict resolution between merges |
| [business](plugins/business/) | Productivity | Measure and report the business value of AI skills and agentic workflows — provenance-tagged data collection and audience-tiered reports in engineer-hours and cycle time, never currency |
| [github-actions](plugins/github-actions/) | Development | Update GitHub Actions pins across one repo or a whole fleet — verify every target tag exists before writing it, research each upgrade against real release notes, land one commit per action on trunk, then close dependabot's PRs by citing the commit that superseded them |
| [situate](plugins/situate/) | Development | Gain situational awareness before touching a repository — sweep the branch against trunk, its diff, its pull request and review threads, its linked tickets, and the project's own conventions, optionally searching prior AI conversations for decisions the repository never recorded; answer a mid-session 'huh' in five lines or less; and re-derive what the work is for to catch both the work nobody asked for and the work nobody did |
| [terraform](plugins/terraform/) | Development | Move Terraform and OpenTofu versions across any repository layout — discover every root module instead of assuming one, move every declaration of a provider together because constraints combine across modules, and refresh each lock file without narrowing its platform coverage |
| [ruff](plugins/ruff/) | Development | Move one repo or a whole fleet onto a new ruff release — work out which rules the release can actually fire against each repo's own select list, gate on the resolver being able to see the version at all, then land one reviewed commit per rule with the upstream rule doc cited |
| [git-branch](plugins/git-branch/) | Development | Redo a branch two ways — keep the code and rebuild only the history into atomic commits, proving the resulting tree is byte-identical to what it replaced; or keep the requirements and replace the implementation from scratch, holding the branch's own tests as the specification and reconciling the result against a ledger of everything the original handled. Both draw their commit messages from the original commits, the pull request, its tickets, and the session that wrote the code, gate every commit through the project's own checks, and never push on their own — plus an editor-free interactive-rebase toolkit for reordering, squashing, and verifying history from an agent shell with no TTY |
| [gh](plugins/gh/) | Development | File GitHub issues a maintainer can still act on in three years — evidence and reproduction before prose, duplicates and the repo's own templates checked first, every symbol backticked and every source link pinned to a tag or a commit, long output folded into details blocks, local paths and PII stripped before anything is opened — plus the rendered-markdown writing discipline those bodies follow, reusable for any pull request, comment, or ticket a renderer will show a human |

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

You can also browse available plugins with `/plugin > Discover`.

Then install any plugin by the name in the table above:

```console
/plugin install commit@ai-workflow-plugins
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

Scripts use [uv](https://docs.astral.sh/uv/) to manage Python dependencies.

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or:

```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

See [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for
other methods.

### Lint and validate

```bash
uv run ./scripts/marketplace.py lint
```

### Sync marketplace manifest with plugin directories

Dry-run:

```bash
uv run ./scripts/marketplace.py sync
```

Write changes to marketplace.json:

```bash
uv run ./scripts/marketplace.py sync --write
```

### Check for outdated entries

```bash
uv run ./scripts/marketplace.py check-outdated
```

### Regenerate the portable skill export

`.agents/skills/` is a generated, committed mirror of every plugin skill and
command in a form that agents outside Claude Code (Codex, Cursor, pi,
Antigravity, Grok) can read: one `SKILL.md` per component, spec-only
frontmatter, no `${CLAUDE_PLUGIN_ROOT}`, and no host-specific inline-bash
expansion. Files a component references are copied into its own directory, so
each exported skill is self-contained and can be moved on its own.

```bash
uv run ./scripts/marketplace.py portable
```

Verify the committed tree matches the plugins it was generated from:

```bash
uv run ./scripts/marketplace.py portable --check
```

Edit `plugins/`, never `.agents/skills/`. `.agents/portable-manifest.json`
records each exported skill's sources, its bundled files, and how many times
each source file is copied across the export.

Hosts that scan `.agents/skills/` read the tree straight from a checkout, with
no install step. The `skills` CLI reads the same tree:

```bash
npx skills add tony/ai-workflow-plugins
```

That installs the export and nothing else. The CLI would otherwise also walk
each plugin's `skills/` directory and offer both renderings of the same skill —
the exported one and the Claude Code original, which has not been through the
transform. `metadata.pluginRoot` in the marketplace manifest is what keeps it to
the export alone; a manifest edit that drops it brings the duplicates back.

### Code quality for scripts

Lint:

```bash
uv run ruff check ./scripts/
```

Format check:

```bash
uv run ruff format --check ./scripts/
```

Type check:

```bash
uv run basedpyright ./scripts/
```

## Documentation

See the [official Claude Code plugin docs](https://code.claude.com/docs/en/plugins) for
authoring guides, component schemas, and marketplace publishing.

## License

MIT
