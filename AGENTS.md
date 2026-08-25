# AGENTS.md — claude-plugins

Project conventions and standards for AI-assisted development.

## Project Identity

This is a **public, third-party [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)**
providing language-agnostic AI / agentic workflow plugins for DX efficiency. Hosted
on GitHub ([tony/skills](https://github.com/tony/skills)), not affiliated with or
endorsed by Anthropic or OpenAI.

## Official Documentation References

These docs are the canonical references for the two plugin systems this
marketplace targets. Consult them when authoring or reviewing plugin
components.

Codex:

- [Package your plugin](https://developers.openai.com/plugins/build/plugins.md) — `.codex-plugin/plugin.json`, marketplace format, local and repo marketplaces, bundled MCP servers and hooks
- [Build skills](https://developers.openai.com/plugins/build/skills) — SKILL.md authoring for Codex

Claude Code:

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

Keep the subject ≤64 chars (excluding any trailing `(#NN)` PR ref); wrap
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

Never create or push a tag on your own initiative — tags trigger the
CI publish workflow, so cutting one is the user's call. An explicit
instruction in the conversation is that call, including a `--tag` or
`--push-tag` flag; act on it without asking again.

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

## Documentation Standards

### Code Blocks

Code blocks are paste-and-run units: pasting one block runs exactly one
intended action. Doctests and other executed examples are exempt — the test
suite runs them, nobody pastes them.

- **One command per block.** Multiple steps may share a block only when
  explicitly chained with `&&`, `;`, or `\` continuations — the chain is
  then one logical command.
- **Explanations go in prose above the block**, never as `#` comments inside it.
- **Command menus are per-command blocks with prose lead-ins**, not tables.
- **Shell commands use the `console` tag with a `$ ` prefix.** This separates
  interactive commands from scripts and enables prompt-aware copy.
- **Split long commands with `\`** — one flag or flag+value pair per indented
  continuation line, positional arguments last.

Good:

Show the last ten commits as a graph:

```console
$ git log \
    --max-count=10 \
    --graph \
    --oneline
```

Bad:

```console
# Show the last ten commits as a graph
$ git log --max-count=10 --graph --oneline
```

## Comments earn their maintenance cost

A comment ships only if it passes all three gates. Fail any: delete or rewrite.
Borderline: delete — borderline means the information is reconstructible, which
is what makes deletion cheap.

**Loss.** Three years from now, would losing this cost a maintainer real time
rediscovering intent, an invariant, a constraint, or a failure mode the code and
tests do not already make obvious?

**Elite.** Would SQLite, Redis, the Go standard library, or CPython write this
comment, at this length? Those projects state the constraint and stop. They do
not argue with an imagined objector.

**Upkeep.** Will it stay true without maintenance? A comment that hand-syncs a
value the code owns — a count, an offset, a line reference, a duplicated
constant — is false the first time that value moves.

### Ceiling

One or two lines. A comment reaching four is either carrying several facts, in
which case split it, or arguing, in which case cut it to the fact.

Rationale, alternatives weighed, and the story of how the code got here belong
in the commit message: timestamped, attached to the exact diff, and free to
maintain.

A comment often holds both a constraint and the deliberation that found it. Keep
the constraint, cut the deliberation. "Runs at most once per second" survives;
"this is the right trade for now" does not.

### Keep

- Why over how: upstream quirks, protocol and compatibility constraints,
  performance tradeoffs still part of the contract.
- Invariants, preconditions, ordering, lifetime, and concurrency requirements
  that types and tests cannot express.
- Code that looks wrong but is not, so a later cleanup does not reintroduce the
  bug.
- A high-level sketch of an algorithm whose local operations do not reveal the
  whole.

### Delete

- Narration of the next lines; code translated into English.
- Restated names, types, defaults, or control flow.
- Values duplicated from the code and hand-synced.
- Justification, hedging, or apology for a choice.
- Speculation about future requirements.
- History version control already holds, including commented-out code.
- Ticket and issue numbers. They say nothing to a reader without tracker access,
  and they rot when the tracker moves. Unfinished work goes in the tracker, not
  the source.
- Transient observations — "currently", "for now", "the latest release" —
  that go stale with no nearby edit.

### The upkeep gate in practice

It reaches values that track our own code. It does not reach frozen external
facts.

Bad (Delete):

```python
# There are 321 tests to complete for servers.
```

Good (Keep):

```python
# CPython < 3.11 has no ExceptionGroup, so this branch stays.
```

### Documentation exception

Doctests, minimal usage examples, and param, return, and raises lines on public
API are exempt from the loss gate — they serve the caller, not the maintainer.
They are exempt from nothing else. Ceiling: a good man page entry.

NumPy-style `Parameters`, `Returns`, and `Attributes` sections and executable
doctests fall under this exception — autodoc ships every field whether or not
you describe it, and a doctest that runs is also a test.

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
- **Revision-History Leakage:** When asked to double-check, verify,
  or re-examine prior analysis, deliver the re-derived answer —
  standalone, rebuilt from source, in the original request's shape.
  Verdicts about your own prior claims (*overstated*, *still holds*)
  are diff narration against a baseline the reader never adopted; put
  confidence on the claim, not the revision. Exception: if the user
  acted on a prior claim (committed, filed, sent), state that
  correction explicitly, once.
- **Low-Value Scaffolding:** Remove ownerless TODOs (`TODO: revisit`),
  unused future-proofing, debug artifacts, and defensive wrappers that
  do not protect a currently reachable failure mode.
- **Prose Inflation:** Replace generic AI "tells" like *comprehensive,
  robust, seamless, production-ready, leverage, delve, tapestry,* and
  *best practices* with concrete descriptions of behavior,
  constraints, or trade-offs.
- **Coded Labels:** Write rules, options, and findings as plain
  imperatives. Don't tag them with codes like `[R1]`, `A1`, or
  `Option B` in artifacts a human reads — the reader shouldn't have to
  decode an index. Internal agent bookkeeping may use ids; shipped text
  may not.

### Durable Source Links

Link to a pinned revision, never to trunk. A pinned permalink is not a
brittle reference; an unlinked SHA dropped into prose is. `blob/main/…`
links rot silently — the file moves, lines shift, and the anchor lands
on unrelated code while still resolving.

- Prefer a release tag (`blob/v1.4.0/…`). Most durable, and it tells
  the reader which released version the claim held for.
- Otherwise use a 7-char commit ref (`blob/9a29b1a/…`) reachable from
  trunk. Use when there is no tag or the claim is about unreleased
  code. Never a PR-head SHA — it can be rebased or garbage-collected.
- Reserve `blob/main/…` for living documents meant to always show the
  latest state, such as a contributing guide.
- Line anchors (`#L120-L145`) are only safe on a pinned ref.

### Preservation & Context

Subjective cleanup must never remove load-bearing rationale. Adjudicate
comments with the comment policy above; borderline cases are deleted, not
kept.

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

### Change Discipline

- Make the smallest coherent change that solves the verified problem;
  keep unrelated cleanup out of it.
- Reuse an existing file, component, helper, API, or test before adding
  a new one. Modify in place when the change fits the file's
  responsibility.
- Keep new APIs private until a caller outside the module needs them.
- Add a file only for a durable boundary — a distinct responsibility,
  independent reuse, or splitting an oversized high-touch module — not
  for a single-use helper or a one-line re-export.

### Keep Instructions Lean

Treat this file like code and prune it.

- Delete a line whose removal would not cause a mistake.
- Move multi-step procedures into skills, path-specific rules into
  nested AGENTS.md files, and hard limits into hooks or CI.
- Keep only non-obvious, broadly applicable defaults here. Anything a
  reader can infer from the code, a manifest, or a linter does not
  belong.

## Plugin Quality Standards

### Skill Files

- Every `SKILL.md` **must** have YAML frontmatter with at least `name` and `description`
- Skills **must not** hardcode language-specific tool commands (e.g., `uv run pytest`,
  `npm test`, `cargo test`). Instead, reference "the project's test suite / quality checks
  as defined in AGENTS.md/CLAUDE.md"
- Frontmatter `allowed-tools` should use bare tool names (e.g., `Bash`) rather than
  language-specific patterns (e.g., `Bash(uv run:*)`) so skills work across any project

### Plugin Directory Structure

Every plugin directory under `plugins/` must contain `.claude-plugin/plugin.json` and
`README.md`. Beyond that, include any combination of component directories:

```
plugins/<name>/
├── .claude-plugin/
│   └── plugin.json      # name, description (required)
├── .codex-plugin/
│   └── plugin.json      # generated
├── README.md            # usage docs, prerequisites, component reference
├── skills/              # skills (skill-name/SKILL.md)
├── agents/              # sub-agents (*.md with name, description, tools)
├── hooks/               # hooks (hooks.json)
├── .mcp.json            # MCP server configuration
└── .lsp.json            # LSP server configuration
```

At least one component directory (`skills/`, `agents/`, or `hooks/`) or
configuration file (`.mcp.json`, `.lsp.json`) is expected. Claude Code also
accepts `commands/`; this repo does not use it, for the reasons below.

`.codex-plugin/plugin.json` is written by `scripts/marketplace.py portable` and
verified by `portable --check`. Never hand-edit it; change
`.claude-plugin/plugin.json`, which it mirrors, and regenerate.

### Skills Are the Only Workflow Component

Claude Code still supports `commands/`, but this repo does not use it. Every
workflow is a skill, for three reasons:

- Claude Code folds commands into skills already. A command-only plugin reports
  `Skills (1)` in `claude plugin details`, and there is no Commands row at all.
  A plugin shipping both a command and a skill under one name lists that name
  twice.
- Codex reads only `skills/`. It migrates `commands/` on its own, but silently
  drops any command over roughly 3.9KB, which is most of them.
- A skill is invoked the same way from either host: `/pr:deslop` in Claude
  Code, `pr:deslop` in Codex.

A skill carrying a workflow that only makes sense when the user asks for it by
name sets `disable-model-invocation: true`. That keeps a command's semantics —
invocable by name, never routed to on the model's initiative — and keeps it out
of a routing corpus where it would crowd skills meant to be discovered.

Address bundled files by climbing out of the skill directory
(`../../references/x.md`), never through `${CLAUDE_PLUGIN_ROOT}`. Codex performs
no substitution on that variable, and Anthropic's own plugins do not use it in
skills either.

### Component Frontmatter Schemas

Each component type has specific frontmatter requirements:

**Commands** (`commands/*.md`) — supported by Claude Code, unused here:
- `description` (required) — shown in `/` menu
- `allowed-tools` (optional) — tool access list (bare names, e.g. `Bash`)
- `argument-hint` (optional) — placeholder text for command argument
- `model` (optional) — model override for this command
- `disable-model-invocation` (optional) — if true, command runs without model invocation

**Agents** (`agents/*.md`):
- `name` (required) — agent identifier (lowercase letters and hyphens)
- `description` (required) — when to delegate to this agent; include `<example>` blocks
- `tools` (optional) — comma-separated tool access list; inherits every
  tool available to subagents when omitted
- `disallowedTools` (optional) — comma-separated tools to deny
- `model` (optional) — `sonnet`, `opus`, `haiku`, `fable`, a full model
  ID, or `inherit`; defaults to `inherit`
- `effort` (optional) — `low`, `medium`, `high`, `xhigh`, or `max`;
  inherits the session level when unset
- `maxTurns` (optional) — max agentic turns before agent stops
- `skills` (optional) — skill names to preload into agent context
- `memory` (optional) — persistent memory scope: `user`, `project`, `local`
- `background` (optional) — `true` always runs the agent as a background
  task; Claude chooses when unset
- `isolation` (optional) — `worktree`, the only valid value, runs the
  agent in a temporary git worktree off the default branch
- `color` (optional) — visual indicator: `red`, `blue`, `green`,
  `yellow`, `purple`, `orange`, `pink`, or `cyan`

Plugin subagents drop `hooks`, `mcpServers`, and `permissionMode` — the
host ignores all three when an agent loads from a plugin, for security.
An agent shipped from this marketplace is a plugin subagent, so setting
them here does nothing; they only take effect once the file is copied
into a project's `.claude/agents/` or a user's `~/.claude/agents/`.

**Skills** (`skills/*/SKILL.md`):
- `name` (required here) — skill display name; upstream it defaults to
  the directory name, but this repo's gates expect it written out
- `description` (required here) — when and how to invoke the skill
- `argument-hint` (required when the body consumes `$ARGUMENTS`) — placeholder
  Claude shows when the user invokes the skill
- `allowed-tools` (optional) — tools usable without a permission prompt;
  space- or comma-separated string, or a YAML list
- `disallowed-tools` (optional) — tools removed while the skill is active
- `context` (optional) — set to `fork` to run in a subagent
- `disable-model-invocation` (optional) — if true, runs without model invocation
- Content can reference `$ARGUMENTS` to access arguments passed to the skill

Skills hyphenate both tool fields while the Agents schema above uses
camelCase `tools`/`disallowedTools` — a real difference between the two
components, not a typo in one of them. And `allowed-tools` grants
pre-approval rather than sandboxing: every tool stays callable either
way, so listing tools only skips the permission prompt for those. Only
`disallowed-tools` removes a tool from the pool.

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

Two manifests describe the same marketplace. `.claude-plugin/marketplace.json`
is hand-maintained and authoritative; `.agents/plugins/marketplace.json` is
generated from it. Codex prefers the generated one and accepts the Claude
manifest only as a legacy fallback, so both ship and neither host depends on
the other's spelling.

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
or frameworks, present them as illustrative examples (e.g., in lists or short prose), never
as hardcoded instructions.

### Portable Shell Examples

A shell command shipped in a skill or reference runs on whatever
machine the user has. Either use a spelling that works on both GNU
coreutils and BSD/Darwin, or show both forms and label them.

The differences that matter here:

- `sed -i` takes an optional suffix on GNU and a mandatory one on
  BSD/Darwin, and the two spellings are mutually exclusive. Ship
  `sed -i` for GNU and `sed -i ''` for BSD/Darwin.
- In `sed` basic regular expressions, `\+`, `\?`, and `\|` are GNU
  extensions. Write `-E` with a bare `+`, `?`, or `|` — that spelling
  is identical on both.
- `du --files0-from`, `find -printf`, `numfmt`, `tac`, `nproc`,
  `shuf`, `base64 -w`, `readlink -f`, `stat -c`, and `date -d` are
  GNU-only with no BSD/Darwin flag to swap in. Reach for a different
  construct, not a different flag.
- macOS ships bash 3.2, so `mapfile`, `readarray`, `declare -A`, and
  `${var,,}` are unavailable there regardless of which coreutils are
  installed.

Check before splitting a command in two. `xargs -r`, `xargs -0`,
`sort -V`, `du -sch`, `find -print0`, `head -c`, and POSIX `date`
format specifiers all work on BSD/Darwin, so a second variant for
those is noise. `xargs -a` and `xargs -d` are the GNU-only ones.

When a command is genuinely single-platform — WSL virtual disks,
`findmnt`, `systemctl` — say so in the surrounding prose instead of
inventing an equivalent.

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

### Accessible Formatting

- **Prefer prose and nested sections over tables** — reach for a table
  only when the data is genuinely matrix-shaped and stable. Repeated
  semantic headings (e.g., "Use when / Avoid when / Tradeoff") diff,
  wrap, and edit more cleanly than a table.
- **One command per code block** — never combine multiple commands in a single
  fenced block; use separate blocks with explanatory text between them
- **No comments inside code blocks** — explanatory text goes outside as
  regular markdown, not as `#` comments inside the fence
