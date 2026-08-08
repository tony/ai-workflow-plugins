# rebase

Automated rebase onto trunk with conflict prediction, resolution, and quality gate verification.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install rebase@ai-workflow-plugins
```

## Command

| Command | Description |
|---------|-------------|
| `/rebase` | Rebase current branch onto trunk, resolve conflicts, verify quality gates |
| `/rebase:fix-history` | Fix lint/quality errors by attributing each to its originating commit, creating fixup commits, and autosquashing |

## 5-Phase Workflow

1. **Detect trunk** — Identify the remote trunk branch (`main` or `master`)
2. **Fetch and analyze** — Fetch latest, identify files changed on both sides, predict conflict zones
3. **Execute rebase** — Run `git pull --rebase origin <trunk> --autostash`
4. **Resolve conflicts** — If any conflicts arise, resolve them file-by-file preserving both sides' intent
5. **Verify** — Confirm clean history, run the project's full quality gate suite

## Arguments

`/rebase:fix-history` accepts an optional argument — the quality gate command to run. If omitted, the command discovers quality gates from the project's AGENTS.md / CLAUDE.md.

```console
/rebase:fix-history ruff check . --fix; ruff format .
```

## 7-Phase Fix-History Workflow

1. **Detect trunk and discover quality gates** — Identify remote trunk branch, resolve quality gate command from `$ARGUMENTS` or project config
2. **Run quality gates and collect errors** — Execute the quality command, collect all errors with file, line, rule, and message
3. **User confirmation gate** — Present error summary and attribution plan, wait for explicit approval
4. **Attribute errors to originating commits** — For each error, use `git log -S`, `git blame`, or diff analysis to find the introducing commit
5. **Fix errors and create fixup commits** — Fix each group, verify, `git commit --fixup=<sha>`
6. **Autosquash** — `git rebase -i --autosquash` to fold fixups into their target commits, resolve any conflicts
7. **Per-commit sweep** (optional) — Run `git rebase -i -x '<quality-command>'` to verify every commit passes individually

## Quality Gate Discovery

The command reads AGENTS.md / CLAUDE.md to discover which quality checks the project requires. It does **not** hardcode any specific test runner or linter — it works with whatever the project uses.

## Prerequisites

- **git** — the rebase command uses standard git operations
- A remote named `origin` with a trunk branch (`main` or `master`)

## Language-Agnostic Design

Quality gate examples are provided for reference, but the command always defers to the project's own AGENTS.md / CLAUDE.md for the actual commands to run.
