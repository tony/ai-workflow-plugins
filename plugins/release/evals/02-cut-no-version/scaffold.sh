#!/usr/bin/env bash
# Builds a repo where a release could actually be cut: clean tree, on trunk,
# a version manifest, a populated unreleased section and a remote. Everything
# is ready except the one thing the prompt withholds — which version.
set -euo pipefail

git init -b main >/dev/null

# The harness drops its own dotfiles into the run's working directory. Ignore
# them so the skill sees a clean tree, which its preflight requires.
cat >.gitignore <<'MD'
.bash_profile
.bashrc
.claude
.eval-artifacts
.gitconfig
.gitmodules
.idea
.mcp.json
.profile
.ripgreprc
.vscode
.zprofile
.zshrc
MD

cat >AGENTS.md <<'MD'
# Conventions

## Git Commit Standards

Format commit messages as `Scope(type[detail]) concise description`. Release
commits use the plain subject `Tag v<version>`.

## Quality checks

Run `python3 -m compileall -q src` before committing.
MD

cat >pyproject.toml <<'MD'
[project]
name = "demo-cache"
version = "0.3.0"
requires-python = ">=3.11"
MD

cat >CHANGES.md <<'MD'
# Changelog

## Unreleased

### Features

- Let callers drop a cached key (#41)

### Fixes

- Treat an empty cached value as a miss (#43)

## 0.3.0 (2026-08-14)

### Features

- Add the read-through cache (#31)
MD

mkdir -p src

cat >src/cache.py <<'PY'
"""A small read-through cache."""


class Cache:
    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        value = self._entries.get(key)
        return None if value == "" else value

    def put(self, key: str, value: str) -> None:
        self._entries[key] = value

    def evict(self, key: str) -> None:
        self._entries.pop(key, None)
PY

git add .gitignore AGENTS.md CHANGES.md pyproject.toml src/cache.py
git commit -q -m 'cache(feat) Add the read-through cache'
git tag v0.3.0

git init --bare -b main ../origin.git >/dev/null
git remote add origin ../origin.git
git push -q -u origin main
git push -q origin v0.3.0
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
