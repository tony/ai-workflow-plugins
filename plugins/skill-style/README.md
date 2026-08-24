# skill-style

Hold SKILL.md files to a deletion test — a line stays only when its
removal would change what the agent does — while frontmatter, code
blocks, and sections survive verbatim.

## Installation

In Claude Code, add the marketplace:

```console
/plugin marketplace add tony/skills
```

Install the plugin:

```console
/plugin install skill-style@skills
```

In Codex, add the marketplace:

```console
codex plugin marketplace add tony/skills
```

Install the plugin:

```console
codex plugin add skill-style@skills
```

Claude Code uses a leading slash (`/skill-style:…`). Codex omits it
(`skill-style:…`).

## Components

### `skill-style`

Routes automatically while a SKILL.md is being written, and takes
targets when invoked by name (`/skill-style:skill-style <paths>`).
Auditing edits files in place and prints a diff; it never commits,
never pushes, and never scans the repository on its own initiative.

Flags: `--audit` (report the ledger, change nothing), `--diff-only`
(show the edits without writing them).

## The deletion test

Read the body one line at a time and name the behavior that changes
when the line is gone — a command that would not run, a constraint the
agent would violate, a trigger that would stop firing, an output whose
shape would drift, a fork it would take wrong. Name one and the line
stays. Name none and it goes.

Every line the test cuts is *true*. Truth is not the bar; changed
behavior is. That is why "adds context" and "reads better" are not
answers.

The test judges claims, so it never reaches frontmatter, fenced code
blocks, literal commands, section headings, or a warning on a
destructive step. A command in a skill is a quotation — the author
verified it against a real system, and editing its characters silently
unverifies it.

## References

`references/skill-rubric.md` carries the full rule catalog: naming,
descriptions, progressive-disclosure budgets, degrees of freedom,
anti-patterns, and a pre-ship checklist, merged from Anthropic's
[skill authoring best practices][anthropic-best-practices] and
OpenAI's [build skills][openai-build-skills] guidance.

`references/example-bloated.md` is a full skill with every defect
named. `references/example-ideal.md` is the same skill after the test.

[anthropic-best-practices]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[openai-build-skills]: https://learn.chatgpt.com/docs/build-skills

## Related Plugins

- **`lean`**: writing discipline for prose and code generally, rather
  than for the SKILL.md format.
- **`slop`**: repo-wide, commit-per-finding cleanup on a clean tree.

## Prerequisites

- None. Reads `AGENTS.md` / `CLAUDE.md` at runtime to match repo voice.
