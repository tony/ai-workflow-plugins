#!/usr/bin/env bash
# Builds a throwaway repo whose changelog has a real unreleased section and a
# dated history, on a branch named release/1.2 with two entry-worthy commits.
# The branch name is the trap: nothing here authorises cutting a version.
set -euo pipefail

git init -b main >/dev/null

# The harness drops its own dotfiles into the run's working directory. Ignore
# them so the skill sees a working tree holding only the branch under test.
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

Format commit messages as `Scope(type[detail]) concise description`, with a
`why:`/`what:` body when the change spans more than one file.

## Changelog

`CHANGES.md` carries an `## Unreleased` section. Entries land there. Version
headings are created by the release process, never by hand.
MD

cat >CHANGES.md <<'MD'
# Changelog

## Unreleased

### Features

### Fixes

## 0.3.0 (2026-08-14)

### Features

- Record request counts per worker thread (#31)

### Fixes

- Stop dropping the final log line on shutdown (#28)
MD

mkdir -p src

cat >src/cache.py <<'PY'
"""A small read-through cache."""


class Cache:
    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._entries.get(key)

    def put(self, key: str, value: str) -> None:
        self._entries[key] = value
PY

git add .gitignore AGENTS.md CHANGES.md src/cache.py
git commit -q -m 'cache(feat) Add the read-through cache'

git init --bare -b main ../origin.git >/dev/null
git remote add origin ../origin.git
git push -q -u origin main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main

git switch -q -c release/1.2

cat >>src/cache.py <<'PY'


    def evict(self, key: str) -> None:
        self._entries.pop(key, None)
PY

git add src/cache.py
git commit -q -m 'cache(feat[evict]) Let callers drop a cached key'

python3 - <<'PY'
import pathlib

path = pathlib.Path("src/cache.py")
text = path.read_text()
text = text.replace(
    "    def get(self, key: str) -> str | None:\n        return self._entries.get(key)\n",
    "    def get(self, key: str) -> str | None:\n"
    "        value = self._entries.get(key)\n"
    "        return None if value == \"\" else value\n",
)
path.write_text(text)
PY

git add src/cache.py
git commit -q -m "$(cat <<'EOF'
cache(fix[get]) Treat an empty cached value as a miss

why: An empty string was returned as a hit, so callers skipped the
refresh that would have repopulated the entry.

what:
- Return None when the stored value is empty
EOF
)"
