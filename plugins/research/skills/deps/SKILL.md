---
name: study-deps
description: >
  Clone and study your project's dependencies at the exact versions you use.
  Scans manifest files (package.json, pyproject.toml, Cargo.toml, go.mod, etc.),
  resolves official source repositories, clones them to ~/study/<language>/, and
  creates version-pinned git worktrees. Use when the user wants to read upstream
  source code, understand how a dependency works, or study a library at the
  exact version their project depends on.
user-invocable: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "WebSearch", "AskUserQuestion"]
argument-hint: <package-name|"all"|category> [--lang <language>] [--no-worktree]
---

# Study Dependencies

Clone and study your project's dependencies at their exact pinned versions using git worktrees under `~/study/`.

Use `$ARGUMENTS` as the user's filter. If `$ARGUMENTS` is empty, ask the user which dependency to study.

Parse `$ARGUMENTS` for flags and strip them from the filter text:

| Flag | Effect |
|------|--------|
| `--lang <language>` | Override auto-detected language directory |
| `--no-worktree` | Clone only, skip worktree creation |

The remaining text after stripping flags is the **filter** — a package name, `"all"`, or a category like `"dev"` or `"build"`.

## Step 1: Detect Preferred Tools

```bash
for tool in rg ag fd jq; do
  command -v "$tool" >/dev/null 2>&1 && echo "$tool:available" || echo "$tool:missing"
done
```

For content search, prefer `rg` over `ag` over `grep`. For file finding, prefer `fd` over `find`. For JSON parsing, use `jq` when available, otherwise parse manually.

## Step 2: Scan Manifest Files

Search the current project root for manifest files and extract dependencies with their version constraints.

| Manifest | Language dir | Lockfiles | Extraction method |
|----------|-------------|-----------|-------------------|
| `package.json` | `typescript` | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock` | `dependencies`, `devDependencies`, `peerDependencies` fields |
| `pyproject.toml` | `python` | `uv.lock`, `poetry.lock`, `requirements.txt` | `[project]` `dependencies`, `[tool.poetry.dependencies]` |
| `Cargo.toml` | `rust` | `Cargo.lock` | `[dependencies]`, `[dev-dependencies]`, `[build-dependencies]` |
| `go.mod` | `golang` | `go.sum` | `require` entries (block and single-line) |
| `Gemfile` | `ruby` | `Gemfile.lock` | `gem` declarations |
| `mix.exs` | `elixir` | `mix.lock` | `deps` function return |
| `build.gradle` / `build.gradle.kts` | `java` | `gradle.lockfile` | `implementation`, `api`, `testImplementation` |
| `pom.xml` | `java` | — | `<dependency>` elements |

For each manifest found, extract the dependency name, version constraint, and category (runtime, dev, build, peer).

When a lockfile exists alongside the manifest, also extract the **resolved version** (exact pinned version) for each dependency. Prefer the lockfile resolved version over the manifest constraint for tag resolution in Step 7.

## Step 3: Filter Dependencies

Apply the filter from `$ARGUMENTS`:

- **Specific package name** — match exactly (case-insensitive)
- **`"all"`** — include every dependency
- **Category** (`"dev"`, `"build"`, `"peer"`, `"runtime"`) — filter by dependency category

Check `~/study/` for existing clones and worktrees:

```bash
ls -d ~/study/*/*/ 2>/dev/null
```

Mark each dependency as: **new** (needs clone + worktree), **update** (clone exists, needs worktree), or **exists** (worktree at correct version already present). Plain directories (e.g., `vite/`) are main clones; version-suffixed directories (e.g., `vite-6.2.0/`) are worktrees.

If `--lang` was provided, use that as the language directory instead of auto-detecting from the manifest.

## Step 4: Resolve Source Repositories

For each filtered dependency, find the official source repository URL.

**Resolution order** (stop at first success):

1. **Manifest metadata** — `repository` field in `package.json`, `[package]` `repository` in `Cargo.toml`, `project.urls` in `pyproject.toml`
2. **Package registry metadata** — `npm view <pkg> repository.url`, `cargo metadata`, `pip show <pkg>`, `go list -m -json <module>`
3. **WebSearch** — search for `"<package-name>" official source repository` and verify the result

Normalize all URLs to `https://<host>/<owner>/<repo>.git` format where possible. Strip `.git` suffix for display, keep it for clone commands.

## Step 5: Present Plan and Confirm

Show a summary table of planned actions:

| Package | Version | Repository | Action | Target Path |
|---------|---------|------------|--------|-------------|
| vite | 6.2.0 | vitejs/vite | clone + worktree | `~/study/typescript/vite-6.2.0/` |
| react | 19.1.0 | facebook/react | worktree only | `~/study/typescript/react-19.1.0/` |
| zod | 3.25.0 | colinhacks/zod | exists | `~/study/typescript/zod-3.25.0/` |

**Confirmation gate** — ask the user to approve before proceeding. Use `AskUserQuestion` with options:

- **Proceed** — clone and create worktrees as shown
- **Select specific** — let the user pick individual packages from the list
- **Cancel** — abort

Do not proceed past this step without user approval.

## Step 6: Clone Repositories

Always quote variables and use `--` to separate options from arguments to prevent shell injection from manifest-derived values.

For each approved dependency that needs cloning:

```bash
git clone -- "$repo_url" "$HOME/study/<language>/<repo-name>/"
```

If the clone directory already exists, fetch latest tags instead:

```bash
git -C "$HOME/study/<language>/<repo-name>/" fetch --tags --force
```

Clone one repository at a time. Report progress after each clone.

## Step 7: Resolve Version Tag or Branch

For each dependency, find the matching git ref. Try these patterns in order (stop at first match):

| Priority | Pattern | Example |
|----------|---------|---------|
| 1 | Exact tag | `5.2.0` |
| 2 | `v`-prefixed tag | `v5.2.0` |
| 3 | Scoped package tag | `@scope/pkg@5.2.0`, `pkg@5.2.0` |
| 4 | Crate-style tag | `pkg-v5.2.0`, `pkg-5.2.0` |
| 5 | Minor branch | `release/5.2`, `stable/5.2.x`, `5.2.x` |
| 6 | Major branch | `release/5.x`, `v5` |

Use the lockfile resolved version (from Step 2) when available, otherwise use the manifest version constraint stripped of range operators (`^`, `~`, `>=`, etc.).

```bash
git -C "$HOME/study/<language>/<repo-name>/" tag -l
```

```bash
git -C "$HOME/study/<language>/<repo-name>/" branch -r -l
```

If no matching ref is found, warn the user and offer to use the default branch instead.

## Step 8: Create Version-Pinned Worktree

Skip this step if `--no-worktree` was passed.

For tag refs (detached HEAD):

```bash
git -C "$HOME/study/<language>/<repo-name>/" worktree add --detach "$HOME/study/<language>/<repo-name>-<version>/" <tag>
```

For branch refs:

```bash
git -C "$HOME/study/<language>/<repo-name>/" worktree add "$HOME/study/<language>/<repo-name>-<version>/" <branch>
```

The worktree path follows the convention: `~/study/<language>/<repo-name>-<version>/`.

If the worktree path already exists, skip creation and report it as already present.

For monorepo-hosted packages (e.g., `@tanstack/react-query` and `@tanstack/react-table` both in `tanstack/query`), the entire repo is cloned once. The worktree contains all packages — the user can navigate to the specific package subdirectory.

## Step 9: Report Results

Present a summary of what was done:

| Status | Package | Path |
|--------|---------|------|
| created | vite@6.2.0 | `~/study/typescript/vite-6.2.0/` |
| skipped | zod@3.25.0 | `~/study/typescript/zod-3.25.0/` (already exists) |
| failed | some-pkg@1.0.0 | no matching tag found |

Include the full path for each created worktree so the user can navigate directly.

If any dependencies failed, suggest manual steps to resolve (e.g., checking available tags, using a different version).
