#!/usr/bin/env bash
# Builds a throwaway repo with an origin whose trunk still has the race, and a
# branch that fixes it across two commits plus a regression test.
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
MD

mkdir -p src tests

cat >src/metrics.py <<'PY'
"""Request metrics, shared across worker threads."""


class Counter:
    def __init__(self) -> None:
        self._hits = 0

    def record(self) -> None:
        current = self._hits
        self._hits = current + 1

    @property
    def hits(self) -> int:
        return self._hits
PY

cat >tests/test_metrics.py <<'PY'
from src.metrics import Counter


def test_single_threaded_count() -> None:
    counter = Counter()
    for _ in range(10):
        counter.record()
    assert counter.hits == 10
PY

git add .gitignore AGENTS.md src/metrics.py tests/test_metrics.py
git commit -q -m 'metrics(feat) Count requests across worker threads'

git init --bare -b main ../origin.git >/dev/null
git remote add origin ../origin.git
git push -q -u origin main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main

git switch -q -c fix/metrics-race

cat >src/metrics.py <<'PY'
"""Request metrics, shared across worker threads."""

import threading


class Counter:
    def __init__(self) -> None:
        self._hits = 0
        self._lock = threading.Lock()

    def record(self) -> None:
        with self._lock:
            self._hits += 1

    @property
    def hits(self) -> int:
        with self._lock:
            return self._hits
PY

git add src/metrics.py
git commit -q -m "$(cat <<'EOF'
metrics(fix[counter]) Guard the hit counter with a lock

why: record() read the counter, then wrote back the value it had read.
Two threads interleaving between those steps both wrote the same number,
so concurrent requests were silently undercounted.

what:
- Hold a threading.Lock across the read-modify-write in record()
- Read hits under the same lock so callers cannot observe a torn value
EOF
)"

cat >>tests/test_metrics.py <<'PY'


def test_concurrent_counts_are_not_lost() -> None:
    import threading

    counter = Counter()
    threads = [
        threading.Thread(target=lambda: [counter.record() for _ in range(1000)])
        for _ in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert counter.hits == 8000
PY

git add tests/test_metrics.py
git commit -q -m "$(cat <<'EOF'
metrics(test[counter]) Cover the concurrent increment path

why: The lock only matters under contention, which the existing
single-threaded test cannot exercise.

what:
- Drive record() from eight threads and assert no increments are lost
EOF
)"
