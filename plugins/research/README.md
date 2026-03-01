# research

Clone and study your project's dependencies at the exact versions you use — source repos with version-pinned git worktrees.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install research@ai-workflow-plugins
```

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| Study Dependencies | `/research:deps` | Clone dependencies and create version-pinned worktrees under `~/study/` |

## How It Works

The skill follows a 9-step workflow:

1. **Detect preferred tools** — Check for `rg`, `fd`, `jq` and fall back to standard alternatives
2. **Scan manifest files** — Find `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, and more; extract deps + versions
3. **Filter dependencies** — Apply the user's filter (package name, "all", or category); check `~/study/` for existing repos
4. **Resolve source repositories** — Try manifest metadata first, then registry commands, then web search
5. **Present plan and confirm** — Show a table of what will be cloned/created vs. what exists; wait for approval
6. **Clone repositories** — `git clone` to `~/study/<language>/<repo>/`; `git fetch --tags` for existing clones
7. **Resolve version tag or branch** — Match exact tag, `v`-prefix, scoped, crate-style, or release branch
8. **Create version-pinned worktree** — `git worktree add --detach` for tags, `git worktree add` for branches
9. **Report results** — Summary of created, skipped, and failed items with full paths

## Supported Manifests

| Manifest | Language dir | Lockfiles |
|----------|-------------|-----------|
| `package.json` | `typescript` | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock` |
| `pyproject.toml` | `python` | `uv.lock`, `poetry.lock`, `requirements.txt` |
| `Cargo.toml` | `rust` | `Cargo.lock` |
| `go.mod` | `golang` | `go.sum` |
| `Gemfile` | `ruby` | `Gemfile.lock` |
| `mix.exs` | `elixir` | `mix.lock` |
| `build.gradle` / `build.gradle.kts` | `java` | `gradle.lockfile` |
| `pom.xml` | `java` | — |

## Version Tag Resolution

Tags are resolved in priority order, stopping at the first match:

| Priority | Pattern | Example |
|----------|---------|---------|
| 1 | Exact tag | `5.2.0` |
| 2 | `v`-prefixed tag | `v5.2.0` |
| 3 | Scoped package tag | `@scope/pkg@5.2.0` |
| 4 | Crate-style tag | `pkg-v5.2.0` |
| 5 | Minor branch | `release/5.2`, `stable/5.2.x` |
| 6 | Major branch | `release/5.x`, `v5` |

Lockfile resolved versions are preferred over manifest version constraints.

## Arguments

```console
/research:deps vite
```

```console
/research:deps all
```

```console
/research:deps dev
```

```console
/research:deps react --lang typescript
```

```console
/research:deps tokio --no-worktree
```

## Study Directory Layout

Each language gets its own directory under `~/study/`. The plain directory (e.g., `vite/`) is the
main clone, and the version-suffixed directory (e.g., `vite-6.2.0/`) is the worktree pinned to
that tag.

```
~/study/
├── typescript/
│   ├── vite/
│   ├── vite-6.2.0/
│   ├── react/
│   └── react-19.1.0/
├── python/
│   ├── django/
│   └── django-5.2/
├── rust/
│   ├── tokio/
│   └── tokio-1.44.0/
└── golang/
    ├── chi/
    └── chi-5.2.1/
```

## Prerequisites

- **git** — for cloning and worktree management
- A project with at least one supported manifest file

## Language-Agnostic Design

Manifest detection and language directory assignment are automatic. The skill works with any combination of supported manifests in a single project. Use `--lang` to override the detected language directory when needed.
