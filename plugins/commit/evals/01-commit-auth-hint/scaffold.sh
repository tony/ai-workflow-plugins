#!/usr/bin/env bash
# Builds a throwaway repo whose history teaches the commit convention, then
# leaves the auth fix unstaged so the case grades a real commit.
set -euo pipefail

git init -b main >/dev/null

cat >AGENTS.md <<'MD'
# Conventions

## Git Commit Standards

Format commit messages as:

```
Scope(type[detail]) concise description

why: Explanation of necessity or impact.

what:
- Specific technical changes made
```

Keep the subject at or under 64 characters; wrap body lines at 72.
Separate the `why:` and `what:` blocks with a blank line.

Common types: feat, fix, refactor, docs, chore, test, style.

## AI Slop Prevention

Commit messages carry no AI signatures: no `Co-Authored-By` trailer, no
"Generated with" footer, no tool attribution, no emoji.
MD

# The harness drops its own dotfiles into the run's working directory. Ignore
# them so the skill sees a working tree holding only the change under test.
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

mkdir -p src tests

cat >src/session.py <<'PY'
"""Session store."""

SESSIONS: dict[str, str] = {}


def put(token: str, user: str) -> None:
    SESSIONS[token] = user


def owner(token: str) -> str | None:
    return SESSIONS.get(token)
PY

git add .gitignore AGENTS.md src/session.py
git commit -q -m 'session(feat[store]) Add the in-memory session store'

cat >src/auth.py <<'PY'
"""Token authentication."""

import time

from .session import owner

GRACE_SECONDS = 0


def is_expired(expires_at: float) -> bool:
    return expires_at < time.time() - GRACE_SECONDS


def authenticate(token: str, expires_at: float) -> str | None:
    if is_expired(expires_at):
        return None
    return owner(token)
PY

cat >tests/test_auth.py <<'PY'
from src.auth import is_expired


def test_expired_token_is_rejected() -> None:
    assert is_expired(0.0)
PY

git add src/auth.py tests/test_auth.py
git commit -q -m 'auth(feat[token]) Reject tokens past their expiry'

cat >README.md <<'MD'
# demo

A small service used to exercise the commit workflow.
MD

git add README.md
git commit -q -m 'docs(chore) Describe the service in the README'

# HEAD treats a token expiring exactly now as still valid. The fix and its
# regression test are left unstaged, so the case has something to commit.
cat >src/auth.py <<'PY'
"""Token authentication."""

import time

from .session import owner

GRACE_SECONDS = 0


def is_expired(expires_at: float) -> bool:
    return expires_at <= time.time() - GRACE_SECONDS


def authenticate(token: str, expires_at: float) -> str | None:
    if is_expired(expires_at):
        return None
    return owner(token)
PY

cat >tests/test_auth.py <<'PY'
import time

from src.auth import is_expired


def test_expired_token_is_rejected() -> None:
    assert is_expired(0.0)


def test_token_expiring_now_is_rejected(monkeypatch) -> None:
    # Freeze the clock: reading it twice lets drift satisfy `<` on its own,
    # so the exact-equality boundary would pass with or without the fix.
    now = 1_700_000_000.0
    monkeypatch.setattr(time, "time", lambda: now)
    assert is_expired(now)
PY
