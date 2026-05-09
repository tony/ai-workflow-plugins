# Per-Finding Commit Templates

When `/slop:scan` lands a finding's fix, it must produce a commit
message that follows this repo's `Scope(type[detail])` convention
(see `CLAUDE.md` Git Commit Standards). Each commit covers exactly
one finding — one signature match in one file. The commit `type` and
`scope` are derived from the signature category.

## Subject templates by signature prefix

| Signature prefix | Commit subject template | Example |
|---|---|---|
| `ai-slop.*` | `chore(slop[<id>]) Remove <description> from <file>` | `chore(slop[ai-slop.signatures]) Remove AI footer from README.md` |
| `brittle.line-numbers` | `docs(slop[<id>]) Replace line-number reference in <file>` | `docs(slop[brittle.line-numbers]) Replace line-number reference in CONTRIBUTING.md` |
| `brittle.counts` | `docs(slop[<id>]) Replace brittle count in <file>` | `docs(slop[brittle.counts]) Replace brittle count in PR-template.md` |
| `brittle.sha-in-message` | `docs(slop[<id>]) Replace bare SHA reference in <file>` | (commit-message slop is advisory only in this skill) |
| `brittle.dates` | `docs(slop[<id>]) Generalize dated marker in <file>` | `docs(slop[brittle.dates]) Generalize dated marker in docs/install.md` |
| `brittle.commit-message-markdown-leak` | (commit-message-only — advisory in this skill) | — |
| `verbose.*` | `refactor(slop[<id>]) Drop <description> in <file>` | `refactor(slop[verbose.docstring-exceeds-body]) Drop oversized docstring in src/foo.py` |
| `low-value.log-debris` | `chore(slop[<id>]) Remove debug log statement from <file>` | `chore(slop[low-value.log-debris]) Remove debug log statement from src/auth.py` |
| `low-value.todo-noise` | `chore(slop[<id>]) Remove vague TODO from <file>` | `chore(slop[low-value.todo-noise]) Remove vague TODO from src/utils.py` |
| `low-value.dead-future-code` | `chore(slop[<id>]) Remove unused symbol from <file>` | `chore(slop[low-value.dead-future-code]) Remove unused symbol from src/helpers.py` |
| `low-value.formatting-only-commit` | (whole-commit signal — advisory in this skill) | — |
| `hardcoded.test-runner` | `docs(slop[<id>]) Generalize test-runner reference in <file>` | `docs(slop[hardcoded.test-runner]) Generalize test-runner reference in README.md` |
| `hardcoded.os-paths` | `refactor(slop[<id>]) Replace absolute user path in <file>` | `refactor(slop[hardcoded.os-paths]) Replace absolute user path in scripts/setup.sh` |
| `structure.*` | (advisory only — never auto-commits) | — |

## Body shape

Every commit body uses the standard heredoc format with `why:` and
`what:` sections, wrapping body lines at 72 characters per
`CLAUDE.md`. The `<description>` placeholder above is a short noun
phrase derived from the signature's `rationale` field.

```
why: <signature rationale, paraphrased to one line>
what:
- <one-line description of the specific edit, naming the
  file and the textual change>
```

Example for `ai-slop.signatures` finding in `README.md`:

```
chore(slop[ai-slop.signatures]) Remove AI footer from README.md

why: Trailing AI-tool footers leaked into committed source.
what:
- Removed `🤖 Generated with Claude Code` block from the
  bottom of README.md.
```

Example for `brittle.line-numbers` finding in `docs/architecture.md`:

```
docs(slop[brittle.line-numbers]) Replace line-number reference in docs/architecture.md

why: Line-number references rot on every refactor; symbolic
anchors stay accurate.
what:
- Replaced "see line 42" with "see the `parse_config`
  function" in docs/architecture.md.
```

## Construction rules

1. The signature `id` from `signatures.yml` goes verbatim into the
   `[<id>]` slot of the commit subject.
2. `<file>` is the repo-relative path of the modified file.
3. `<description>` is a short human-readable phrase derived from the
   signature's `rationale` (the registry's source of truth for what
   the signal means).
4. Subject line stays under 72 characters when possible. If the file
   path is unusually long, wrap by truncating `<description>` first,
   never the file path.
5. Body wraps at 72 characters. Use the project's standard prose
   shape: complete sentences, no markdown bullet symbols other than
   the `-` opening each `what:` line.
6. **Never** include exact counts of files, lines, or tests in the
   body — the skill itself flags those as `brittle.counts`.
7. **Never** include emoji, AI signatures, or `Co-Authored-By:`
   lines. The skill's whole purpose is removing those.

## When the template does not apply

Some signatures cannot be auto-committed by `/slop:scan` because the
slop only exists in commit messages or whole-commit structure:

- `ai-slop.signatures` (in commit message body, not file content)
- `ai-slop.co-authored-by-ai`
- `ai-slop.emoji-in-commit-subject`
- `brittle.commit-message-markdown-leak`
- `brittle.sha-in-message`
- `verbose.restated-subject-in-body`
- `verbose.what-bullets-mirror-diff`
- `low-value.formatting-only-commit`
- `structure.multi-topic-commit`

When these signatures match historical commits via `--with-history`,
the report flags them advisory-only and points the user at
`/pr:deslop --message-only` (or `/pr:deslop` for diff slop) to clean
them via fixup commits and autosquash.

When these same signatures match the *current commit* the user is
about to make, the right tool is the future `commit/hooks/`
preventative hook, not this skill.

## Cited repo conventions

- `CLAUDE.md` Git Commit Standards — `Scope(type[detail]) subject`,
  72-character body wrap, `why:` / `what:` body shape.
- `CLAUDE.md` Project Component Naming — `slop[<id>]` follows the
  same nesting pattern as `claude[skill{deslop}]` from existing
  commit examples.
- `plugins/commit/commands/commit.md:181-191` — never `git add -A`,
  never `--amend`, never `--no-verify`, never empty commits. The
  per-finding commit loop honors all of these.
