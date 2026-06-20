# AGENTS.md — claude-plugins

Project conventions and standards for AI-assisted development.

## Project Identity

This is a **public, third-party [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)**
providing language-agnostic AI / agentic workflow plugins for DX efficiency. Hosted
on GitHub ([tony/ai-workflow-plugins](https://github.com/tony/ai-workflow-plugins)),
not affiliated with or endorsed by Anthropic.

## Official Documentation References

These docs are the canonical references for the Claude Code plugin system.
Consult them when authoring or reviewing plugin components:

- [Plugins overview](https://code.claude.com/docs/en/plugins.md) — plugin lifecycle, installation, discovery
- [Plugin reference](https://code.claude.com/docs/en/plugins-reference.md) — component types, frontmatter schemas, directory structure
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces.md) — marketplace.json schema, source types, publishing
- [Skills](https://code.claude.com/docs/en/skills.md) — skill authoring, SKILL.md format, `$ARGUMENTS`
- [Hooks](https://code.claude.com/docs/en/hooks.md) — hook events, types (command/prompt/agent), hooks.json
- [MCP servers](https://code.claude.com/docs/en/mcp.md) — MCP server configuration, .mcp.json, server types
- [Settings](https://code.claude.com/docs/en/settings.md) — plugin settings, permissions, scopes
- [Sub-agents](https://code.claude.com/docs/en/sub-agents.md) — agent frontmatter, delegation patterns, tool restrictions
- [Agent teams](https://code.claude.com/docs/en/agent-teams.md) — multi-agent coordination (experimental)

## Git Commit Standards

Format commit messages as:
```
Scope(type[detail]) concise description

why: Explanation of necessity or impact.

what:
- Specific technical changes made
- Focused on a single topic
```

Keep the subject ≤50 chars (excluding any trailing `(#NN)` PR ref); wrap
body lines at ≤72 chars. Separate the `why:` and `what:` blocks with a
blank line.

Common commit types:
- **feat**: New features or enhancements
- **fix**: Bug fixes
- **refactor**: Code restructuring without functional change
- **docs**: Documentation updates
- **chore**: Maintenance (dependencies, tooling, config)
- **test**: Test-related updates
- **style**: Code style and formatting
- **ai(rules[AGENTS])**: AI rule updates
- **ai(claude[rules])**: Claude Code rules (CLAUDE.md)
- **ai(claude[command])**: Claude Code command changes

### Project Component Naming

This repo contains Claude Code plugins, commands, skills, hooks, and agents. Use the
`ai(claude[...])` component pattern:

- `ai(claude[plugin])` — plugin manifest, structure, or multi-component changes
- `ai(claude[plugins])` — changes spanning multiple plugins
- `ai(claude[command])` — a single slash command
- `ai(claude[commands])` — changes spanning multiple commands
- `ai(claude[skill])` — a single skill
- `ai(claude[skills])` — changes spanning multiple skills
- `ai(claude[hook])` — a single hook
- `ai(claude[hooks])` — changes spanning multiple hooks
- `ai(claude[agent])` — a single agent definition
- `ai(claude[agents])` — changes spanning multiple agents
- `ai(rules)` — AGENTS.md or other AI convention files

When a change targets a specific named component, include it:
- `ai(claude[skill{commit}])` — the `commit` skill specifically
- `ai(claude[hook{PreToolUse}])` — a PreToolUse hook specifically
- `ai(claude[command{review-pr}])` — the `review-pr` command specifically

Examples:
```
ai(claude[skill/commit]) Add heredoc formatting for multi-line messages

why: Commit messages with body text need preserved newlines

what:
- Add heredoc template to commit skill prompt
- Include why/what body format in instructions
```

```
ai(claude[hooks]) Add PreToolUse validation for Bash commands

why: Prevent accidental destructive shell commands

what:
- Add PreToolUse hook to intercept Bash tool calls
- Block rm -rf and git push --force without confirmation
```

```
ai(rules) Add project-specific commit component conventions

why: Claude Code plugins need distinct component prefixes

what:
- Add ai(claude[...]) naming scheme for plugins, commands, skills, hooks
- Include examples for single and multi-component changes
```

#### Release commits

Never create tags. Never push tags. The user handles tagging and tag
pushes (tags trigger the CI publish workflow).

Release commit subjects are plain and short: `Tag v<version>`. Put
the detailed why/what in the commit body. Don't use the
`Scope(type[detail]):` format for releases — don't bury the lede.

For multi-line commits, use heredoc to preserve formatting:
```bash
git commit -m "$(cat <<'EOF'
feat(Component[method]) add feature description

why: Explanation of the change.

what:
- First change
- Second change
EOF
)"
```

## AI Slop Prevention

Treat AI slop as **review-hostile noise**, not as proof that text or
code is wrong. The goal is to maximize information density by removing
artifacts that make the repository harder to trust or navigate.

### The Anti-Slop Rubric

Before committing, audit all AI-assisted changes for these noise
patterns:

- **AI Signatures:** Remove "Generated by", footers, conversational
  filler ("Certainly!", "Here is..."), unexplained emojis (🤖, ✨), and
  AI-tool metadata.
- **Brittle References:** Avoid hard-coded line numbers, fragile
  file/test counts, dated "as of" claims, bare SHAs, and local
  absolute paths unless they are strict evidentiary artifacts (e.g.,
  benchmark logs).
- **Diff Narration:** Do not restate what moved, was renamed, or was
  removed in artifacts the downstream reader holds: code, docstrings,
  README, CHANGES, PR descriptions, or release notes. The diff and
  commit message already carry this history.
- **Branch-Internal Narrative:** Do not mention intermediate branch
  states, abandoned approaches, or "no longer" behavior unless users
  of a published release actually experienced the old state (**The
  Published-Release Test**).
- **Low-Value Scaffolding:** Remove ownerless TODOs (`TODO: revisit`),
  unused future-proofing, debug artifacts, and defensive wrappers that
  do not protect a currently reachable failure mode.
- **Prose Inflation:** Replace generic AI "tells" like *comprehensive,
  robust, seamless, production-ready, leverage, delve, tapestry,* and
  *best practices* with concrete descriptions of behavior,
  constraints, or trade-offs.

### Preservation & Context

**When unsure, leave the text in place and ask.** Subjective cleanup
must never be a reason to remove load-bearing rationale.

- **Preserve the "Why":** You MUST NOT delete comments that document
  invariants, protocol constraints, platform quirks, security
  boundaries, and upstream workarounds.
- **Evidence is Immune:** Preserve exact counts, dates, and SHAs when
  they serve as evidence in benchmark results, release notes, stack
  traces, or lockfiles.
- **Behavior Over Inventory:** A useful description explains what
  changed for the *system or user*; it does not provide an inventory
  of files or functions the diff already shows.

### The Published-Release Test

Long-running branches accumulate tactical decisions — renames,
refactors, attempts-then-reverts. When deciding what counts as
branch-internal, use trunk or the parent branch as the baseline — not
intermediate states inside the current branch. Ask:

> Did users of the most recently published release ever experience
> this old name, old behavior, or bug?

If the answer is **no**, it is branch-internal narrative. Move it to
the commit message and describe only the final state in the artifact.

**Keep in shipped artifacts:**
- Deprecations and migration guides for symbols that actually shipped.
- `### Fixes` entries for bugs that affected users of a published
  release.
- Comments explaining *why the current code looks this way*
  (invariants, platform quirks) that make sense to a reader who never
  saw the previous version.

### Cleanup in Hindsight

When applying these rules retroactively from inside a feature branch,
first establish scope by diffing against the parent branch (or trunk)
to identify which commits this branch actually introduced. Then:

- **In-branch commits:** Prompt the user with two options: `fixup!`
  commits with `git rebase --autosquash` to address each causal commit
  at its source, or a single cleanup commit at branch tip.
- **Trunk/Parent commits:** Default to leaving them alone. Act only on
  explicit user instruction. If the user opts in, fold the cleanup
  into a single commit at branch tip; do not rewrite shared history.
- **Scope guard:** If cleaning prior slop would touch a colleague's
  work or expand the branch beyond its stated goal, stay in lane:
  protect the current goal and leave prior slop alone.

## Plugin Quality Standards

### Command Files

- Every command `.md` file **must** have YAML frontmatter with at least a `description` field
- Commands **must not** hardcode language-specific tool commands (e.g., `uv run pytest`,
  `npm test`, `cargo test`). Instead, reference "the project's test suite / quality checks
  as defined in AGENTS.md/CLAUDE.md"
- Frontmatter `allowed-tools` should use bare tool names (e.g., `Bash`) rather than
  language-specific patterns (e.g., `Bash(uv run:*)`) so commands work across any project

### Plugin Directory Structure

Every plugin directory under `plugins/` must contain `.claude-plugin/plugin.json` and
`README.md`. Beyond that, include any combination of component directories:

```
plugins/<name>/
├── .claude-plugin/
│   └── plugin.json      # name, description (required)
├── README.md            # usage docs, prerequisites, component reference
├── commands/            # slash commands (*.md with YAML frontmatter)
├── agents/              # sub-agents (*.md with name, description, tools)
├── skills/              # skills (skill-name/SKILL.md)
├── hooks/               # hooks (hooks.json)
├── .mcp.json            # MCP server configuration
└── .lsp.json            # LSP server configuration
```

At least one component directory (`commands/`, `agents/`, `skills/`, or `hooks/`) or
configuration file (`.mcp.json`, `.lsp.json`) is expected.

### Component Frontmatter Schemas

Each component type has specific frontmatter requirements:

**Commands** (`commands/*.md`):
- `description` (required) — shown in `/` menu
- `allowed-tools` (optional) — tool access list (bare names, e.g. `Bash`)
- `argument-hint` (optional) — placeholder text for command argument
- `model` (optional) — model override for this command
- `disable-model-invocation` (optional) — if true, command runs without model invocation

**Agents** (`agents/*.md`):
- `name` (required) — agent identifier (lowercase letters and hyphens)
- `description` (required) — when to delegate to this agent; include `<example>` blocks
- `tools` (optional) — comma-separated tool access list
- `disallowedTools` (optional) — comma-separated tools to deny
- `model` (optional) — `sonnet`, `opus`, `haiku`, or `inherit`
- `permissionMode` (optional) — `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, `plan`
- `maxTurns` (optional) — max agentic turns before agent stops
- `skills` (optional) — skill names to preload into agent context
- `mcpServers` (optional) — MCP servers available to this agent
- `hooks` (optional) — lifecycle hooks scoped to this agent
- `memory` (optional) — persistent memory scope: `user`, `project`, `local`
- `color` (optional) — visual indicator: `yellow`, `green`, `red`, `cyan`, `pink`

**Skills** (`skills/*/SKILL.md`):
- `name` (required) — skill display name
- `description` (required) — describes when and how to invoke the skill
- `version` (optional) — skill version
- `tools` (optional) — comma-separated tool access list
- `disallowedTools` (optional) — comma-separated tools to deny
- `context` (optional) — agent context mode
- `disable-model-invocation` (optional) — if true, runs without model invocation
- Content can reference `$ARGUMENTS` to access arguments passed to the skill

**Hooks** (`hooks/hooks.json`):
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "..." }] }
    ]
  }
}
```
- Events: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`,
  `SubagentStart`, `SubagentStop`, `UserPromptSubmit`, `PermissionRequest`,
  `SessionStart`, `SessionEnd`, `PreCompact`, `Notification`,
  `TeammateIdle`, `TaskCompleted`
- Hook types: `command` (shell script), `prompt` (LLM evaluation), `agent` (agentic verifier)
- Use `${CLAUDE_PLUGIN_ROOT}` for portable paths in command hooks

**MCP Servers** (`.mcp.json`):
```json
{
  "server-name": {
    "type": "http",
    "url": "https://api.example.com/mcp",
    "headers": { "Authorization": "Bearer ${API_KEY}" }
  }
}
```
- Server types: `http` (remote REST), `stdio` (local subprocess), `sse` (server-sent events)
- `stdio` servers use `command` and `args` instead of `url`
- Environment variables expanded with `${VAR_NAME}` syntax
- Use `${CLAUDE_PLUGIN_ROOT}` for portable paths to local server binaries

**LSP Servers** (`.lsp.json`):
```json
{
  "server-name": {
    "command": "pyright-langserver",
    "args": ["--stdio"],
    "extensionToLanguage": { ".py": "python", ".pyi": "python" }
  }
}
```
- Required: `command`, `extensionToLanguage`
- Optional: `args`, `transport` (`stdio`/`socket`), `env`, `initializationOptions`,
  `settings`, `startupTimeout`, `shutdownTimeout`, `restartOnCrash`, `maxRestarts`
- Users must install the language server binary separately

### Marketplace Manifest

- Located at `.claude-plugin/marketplace.json`
- Must reference every plugin under `plugins/` with a valid `source` path
- Official spec requires only `name` and `source` per entry; this marketplace also
  requires `description`, `version`, `author`, and `category` for quality
- Valid categories: `development`, `productivity`, `testing`, `security`, `design`,
  `database`, `deployment`, `monitoring`, `learning`
- Source types for plugin entries:
  - Relative path: `"./plugins/my-plugin"` (for git-based marketplaces)
  - GitHub: `{ "source": "github", "repo": "owner/repo" }` (optional `ref`, `sha`)
  - Git URL: `{ "source": "url", "url": "https://.../.git" }` (optional `ref`, `sha`)
- Reserved marketplace names: `claude-code-marketplace`, `claude-code-plugins`,
  `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`,
  `agent-skills`, `life-sciences`. Names impersonating official Anthropic
  marketplaces are also blocked.

### Language-Agnostic Design

Plugins in this repository are designed to work with **any** programming language or
framework. Commands discover project-specific tooling by reading AGENTS.md / CLAUDE.md
at runtime rather than assuming a particular ecosystem. When listing examples of tools
or frameworks, present them as illustrative examples (e.g., in tables or lists), never
as hardcoded instructions.

### Orchestration Plan Convention

Skills with analysis-then-execute phases should include a portable
"Orchestration Plan" section before execution begins. This section:

1. Instructs the host to enter plan mode with tool-specific activation hints:
   Claude Code (`EnterPlanMode`), Cursor/Codex/Gemini (`/plan` or `Shift+Tab`)
2. Defines what the orchestration plan should contain (skill-specific checklist)
3. Requires presenting the plan and waiting for user approval
4. Instructs exiting plan mode before execution

The orchestration plan is the host's STRATEGY for the task — not just
write-prevention. It demonstrates understanding of the task and lets the
user course-correct before work begins.

Include graceful degradation: if plan mode is unavailable, the skill's
phase structure still guides analysis before execution.

### Output Contract Convention

Commands that produce structured output for users should declare their
sections in a fixed order. When multiple commands share the same output
pattern, extract the template into a portable reference file.

1. A hero block is allowed at the top (1–4 lines, `⚠`/`✓` prefix or
   short summary; no prose paragraphs).
2. Body sections appear in a declared fixed order with verbatim level-2
   headings. No invented sections.
3. After the prescribed sections, end with an interactive next-step panel
   (via `AskUserQuestion`) where the user can act on the result without
   composing a follow-up command. Skip the panel only when the command
   is already running inside plan mode.

### Accessible Code Blocks

- **One command per code block** — never combine multiple commands in a single
  fenced block; use separate blocks with explanatory text between them
- **No comments inside code blocks** — explanatory text goes outside as
  regular markdown, not as `#` comments inside the fence
