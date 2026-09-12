#!/usr/bin/env bash
# A branch whose commits carry the slop the audit is meant to find: an
# attribution footer, inflated adjectives, diff narration, a line-number
# reference, and a bare ticket id. Not pushed, so the skill does not refuse.
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

## AI Slop Prevention

No attribution footers, no inflated adjectives, no narration of what the
diff already shows, no hard-coded line numbers, no bare ticket ids.
MD

mkdir -p src
cat >src/queue.py <<'PY'
"""Work queue."""


class Queue:
    def __init__(self) -> None:
        self._items: list[str] = []

    def push(self, item: str) -> None:
        self._items.append(item)
PY

git add .gitignore AGENTS.md src/queue.py
git commit -q -m 'queue(feat) Add the work queue'

git init --bare -b main ../origin.git >/dev/null
git remote add origin ../origin.git
git push -q -u origin main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main

git switch -q -c feature/queue-drain

cat >>src/queue.py <<'PY'

    def drain(self) -> list[str]:
        # Renamed this from flush() to drain() because flush was confusing.
        # Previously this returned None; now it returns the items.
        drained = list(self._items)
        self._items.clear()
        return drained
PY
git add src/queue.py
git commit -q -m "$(cat <<'MSG'
queue(feat) Add a comprehensive and robust drain method 🚀

This commit adds a new method called drain() to the Queue class in
src/queue.py at lines 12-18. It was previously named flush() but has
been renamed. This is a production-ready, best-practices implementation
that leverages a seamless approach.

Closes PROJ-4471

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
MSG
)"

cat >>src/queue.py <<'PY'


    def size(self) -> int:
        return len(self._items)
PY
git add src/queue.py
git commit -q -m "$(cat <<'MSG'
queue(feat) Add size

Added a size() method. Changed src/queue.py (+4/-0 lines). 3 tests pass.
MSG
)"
