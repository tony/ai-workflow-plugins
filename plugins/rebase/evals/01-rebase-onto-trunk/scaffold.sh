#!/usr/bin/env bash
# A feature branch behind a trunk that moved on the same file, in a different
# region, so the rebase has overlap to report but replays cleanly.
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

mkdir -p src
cat >src/parser.py <<'PY'
"""Expression parser."""

TOKENS = ("+", "-")


def tokenize(text):
    return [t for t in text.split() if t]
PY

git add .gitignore src/parser.py
git commit -q -m 'parser(feat) Add the tokenizer'

git init --bare -b main ../origin.git >/dev/null
git remote add origin ../origin.git
git push -q -u origin main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main

git switch -q -c feature/evaluate
cat >>src/parser.py <<'PY'


def evaluate(text):
    return sum(int(t) for t in tokenize(text) if t.isdigit())
PY
git add src/parser.py
git commit -q -m 'parser(feat[evaluate]) Sum the numeric tokens'

git switch -q main
python3 - <<'PY'
import pathlib
p = pathlib.Path("src/parser.py")
p.write_text(p.read_text().replace(
    'TOKENS = ("+", "-")\n',
    'import re\n\nTOKENS = ("+", "-", "*", "/")\n\nWHITESPACE = re.compile(r"\\s+")\n'))
PY
git add src/parser.py
git commit -q -m 'parser(feat[tokens]) Recognise multiplicative operators'
git push -q origin main
git switch -q feature/evaluate
