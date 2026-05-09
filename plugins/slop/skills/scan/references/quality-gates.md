# Quality-Gate Discovery

> **Lockstep note**: the algorithm in this file is identical to
> `plugins/pr/skills/deslop/references/quality-gates.md`; only the
> ownership/usage notes (which steps in which skill consume the
> result) differ between the two copies. Both `/pr:deslop` and
> `/slop:scan` run the same discovery algorithm and fallback rules.
> When you change algorithm behavior in one file, mirror the change
> in the other in the same PR. v1.1 will extract this document to a
> shared location.

How `/pr:deslop` and `/slop:scan` find the project's formatter,
linter, type-checker, and test command at runtime — language-agnostic,
never hardcoded.

The skill needs four buckets resolved before any apply step (so the
patch driver or per-finding apply loop can record and run them). Any
bucket may legitimately remain `unset`; downstream steps skip empty
buckets.

- `/pr:deslop` resolves them at Step 3 and runs them in the conflict
  loop (Step 11) and final verification (Step 12).
- `/slop:scan` resolves them at Step 3 and runs them before each
  per-finding commit (Step 10) and at final verification (Step 11).

---

## Algorithm

```
function discover_quality_gates():
    files = []
    for path in [./AGENTS.md, ./CLAUDE.md, ./.github/CONTRIBUTING.md]:
        if exists(path):
            files.append((path, read(path)))

    if not files:
        return prompt_user_for_commands()

    gates = {format: None, lint: None, typecheck: None, test: None}

    for (path, content) in files:
        sections = split_by_heading(content)
        for section in sections:
            heading_lower = section.heading.lower()
            for bucket, keywords in [
                ("format",    ["format", "fmt", "style"]),
                ("lint",      ["lint", "ruff check", "eslint", "clippy"]),
                ("typecheck", ["typecheck", "type check", "mypy", "pyright", "tsc"]),
                ("test",      ["test", "spec", "pytest", "vitest", "jest"]),
            ]:
                if any(k in heading_lower for k in keywords):
                    blocks = extract_fenced_blocks(section)
                    if blocks and gates[bucket] is None:
                        gates[bucket] = first_command(blocks[0])

    for bucket, cmd in gates.items():
        if cmd is None and manifest_exists():
            gates[bucket] = ask_user_for_bucket(
                bucket,
                examples=manifest_examples(bucket),
            )

    return gates
```

Files are read in priority order: `AGENTS.md` first, then `CLAUDE.md`,
then `.github/CONTRIBUTING.md`. A bucket unset after the first file
is filled by the next. The first file's command wins on collision.

---

## Heading keywords (per bucket)

| Bucket | Heading patterns matched (case-insensitive) |
|---|---|
| `format` | `format`, `fmt`, `style` |
| `lint` | `lint`, `ruff check`, `eslint`, `clippy` |
| `typecheck` | `typecheck`, `type check`, `mypy`, `pyright`, `tsc` |
| `test` | `test`, `spec`, `pytest`, `vitest`, `jest` |

Match is substring on the lowercased heading. The first fenced code
block under a matching heading is parsed; the first command line of
that block becomes the bucket's command.

---

## Manifest-sniff fallback

Manifest sniffing is **never a default** — only a user-confirmed last
resort when conventions files are silent on a bucket.

When a bucket is still `unset` after parsing all conventions files,
and a recognized manifest exists, the skill presents *example*
commands via `AskUserQuestion` and requires explicit selection
before storing the command. The skill never auto-injects `pytest`,
`npm test`, `cargo test`, etc.

Examples of manifest-derived suggestions (illustrative — do not
hardcode any of these as defaults):

| Manifest | format example | lint example | typecheck example | test example |
|---|---|---|---|---|
| `pyproject.toml` | `ruff format` | `ruff check --fix` | `mypy` or `basedpyright` | `pytest` |
| `package.json` | `prettier --write .` | `eslint --fix` | `tsc --noEmit` | `vitest`, `jest`, or the project's `npm test` script |
| `Cargo.toml` | `cargo fmt` | `cargo clippy --fix` | `cargo check` | `cargo test` |
| `go.mod` | `gofmt -w .` | `golangci-lint run --fix` | `go vet ./...` | `go test ./...` |
| `Gemfile` | (varies) | `rubocop -A` | (none standard) | `rspec` or `rake test` |

---

## Total absence

If no conventions file exists *and* no recognized manifest exists,
the skill prompts the user once via `AskUserQuestion`:

> I could not find AGENTS.md / CLAUDE.md describing your project's
> quality gates. What command should I run after each conflict
> resolution? You can answer 'skip' to disable quality gates.

The user may answer `skip` to disable all gates for the run; the
conflict loop and final verification become no-ops.

---

## Empty buckets

After discovery, any bucket may be `unset`. This is a legitimate
state — not all projects have all four gates. The skill must:

- Skip empty buckets wherever gates run (deslop's conflict loop,
  slop's per-commit apply loop, both skills' final verification).
- Warn at Step 3 if every bucket is `unset` *and* the user requested
  any mode that rewrites or commits — the gates will not validate
  the changes; the user should know before any modification.

---

## Discovered command storage

The four resolved commands are cached as `FORMAT_CMD`, `LINT_CMD`,
`TYPECHECK_CMD`, `TEST_CMD` for the duration of the run. They are
recorded in `0000-PLAN.md` so `apply.sh` re-uses the same commands at
apply time, and so the user can audit what the skill discovered.

The strings are stored verbatim — the skill does not pre-validate
that the commands exist on `$PATH` (the user picked them, the user
owns them). A later command-not-found is surfaced as part of the
conflict-loop error path.
