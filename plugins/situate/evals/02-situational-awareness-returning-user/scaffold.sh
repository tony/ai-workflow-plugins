#!/usr/bin/env bash
# A branch left mid-rewrite two weeks ago: commits landed, the backoff change
# is still unstaged, and trunk has moved underneath it.
set -euo pipefail

# The prompt and history.jsonl both say this work stopped two weeks ago. Date
# the commits to match, so a skill reading `git log --format=%cr` is not told
# one thing by the transcript and another by the repository.
export GIT_AUTHOR_DATE="2026-08-28T09:00:00+00:00"
export GIT_COMMITTER_DATE="2026-08-28T09:00:00+00:00"

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

mkdir -p src

cat >src/backoff.py <<'PY'
"""Retry backoff."""


def delay_for(attempt: int) -> float:
    return float(attempt) * 2.0
PY

git add .gitignore src/backoff.py
git commit -q -m 'backoff(feat) Add the linear retry delay'

git init --bare -b main ../origin.git >/dev/null
git remote add origin ../origin.git
git push -q -u origin main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main

git switch -q -c fix/exponential-backoff

cat >src/backoff.py <<'PY'
"""Retry backoff."""

import random


def delay_for(attempt: int) -> float:
    capped = min(2.0 ** attempt, 30.0)
    return capped * (0.5 + random.random() / 2)
PY

git add src/backoff.py
git commit -q -m 'backoff(feat[jitter]) Move to exponential delay with jitter'

git switch -q main
cat >>src/backoff.py <<'PY'


MAX_DELAY_SECONDS = 30.0
PY
git add src/backoff.py
git commit -q -m 'backoff(chore) Name the delay ceiling'
git push -q origin main

git switch -q fix/exponential-backoff

# Left unstaged when the work stopped two weeks ago. Switching branches has to
# happen before this, or git refuses to carry it across.
cat >>src/backoff.py <<'PY'


def retry_budget(attempt: int) -> float:
    raise NotImplementedError("decide whether the budget is per-call or total")
PY
