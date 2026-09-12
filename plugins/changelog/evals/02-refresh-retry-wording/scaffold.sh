#!/usr/bin/env bash
# Trunk already has a changelog entry the branch must not touch. The branch
# adds its own vague entry plus the code change it is meant to describe.
set -euo pipefail

git init -b main >/dev/null

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

Format commit messages as `Scope(type[detail]) concise description`.
Changelog entries land under `## Unreleased` in `CHANGES.md`.
MD

cat >CHANGES.md <<'MD'
# Changelog

## Unreleased

### Fixes

- Restore the config loader's search path so project files win over defaults (#12)

## 1.4.0 (2026-07-02)

### Features

- Add the retry queue (#8)
MD

mkdir -p src
cat >src/retry.py <<'PY'
"""Retry backoff."""

MAX_BACKOFF_SECONDS = 60.0


def delay_for(attempt: int) -> float:
    return min(2.0 ** attempt, MAX_BACKOFF_SECONDS)
PY

git add .gitignore AGENTS.md CHANGES.md src/retry.py
git commit -q -m 'retry(feat) Add the backoff calculation'

git init --bare -b main ../origin.git >/dev/null
git remote add origin ../origin.git
git push -q -u origin main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main

git switch -q -c fix/retry-backoff

cat >src/retry.py <<'PY'
"""Retry backoff."""

import random

MAX_BACKOFF_SECONDS = 30.0


def delay_for(attempt: int) -> float:
    capped = min(2.0 ** attempt, MAX_BACKOFF_SECONDS)
    return capped * (0.5 + random.random() / 2)
PY

python3 - <<'PY'
import pathlib
p = pathlib.Path("CHANGES.md")
t = p.read_text().replace(
    "### Fixes\n\n- Restore the config loader's search path so project files win over defaults (#12)\n",
    "### Fixes\n\n- Restore the config loader's search path so project files win over defaults (#12)\n"
    "- Made the retry backoff a bit better (#31)\n",
)
p.write_text(t)
PY

git add CHANGES.md src/retry.py
git commit -q -m 'retry(fix) Cap the backoff and add jitter'
