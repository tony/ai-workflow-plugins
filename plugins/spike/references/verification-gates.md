# Verification-Gate & CI Discovery

> **Lockstep note**: this file is identical to
> `plugins/review/references/verification-gates.md`. When you change
> discovery behavior in one copy, mirror the change in the other in the
> same PR. It extends the four-bucket algorithm shared by `/pr:deslop`
> and `/slop:scan` (`plugins/pr/references/quality-gates.md`) with a
> `build` bucket and a CI-coverage pass.

How `/spike:probe`, `/spike:bakeoff`, and `/review:address` learn, at
runtime, which
verification the project expects — and how much of it to run locally
versus observe in CI after pushing. Language-agnostic, never hardcoded.

## Local gate buckets

Five buckets, resolved by reading the project's conventions files in
priority order: `AGENTS.md`, then `CLAUDE.md`, then
`.github/CONTRIBUTING.md`. Split each file by heading; a heading whose
lowercased text contains a bucket keyword claims the first fenced code
block beneath it. The first file's command wins on collision.

| Bucket | Heading keywords (case-insensitive) |
|---|---|
| `format` | `format`, `fmt`, `style` |
| `lint` | `lint`, `ruff check`, `eslint`, `clippy` |
| `typecheck` | `typecheck`, `type check`, `mypy`, `pyright`, `tsc` |
| `test` | `test`, `spec`, `pytest`, `vitest`, `jest` |
| `build` | `build`, `compile`, `bundle`, `dist` |

When a bucket is unset **and the manifest shows evidence the project
has that gate** — a typecheck config (`mypy`/`pyright` section,
`tsconfig.json`), a `build` script, a test-runner dependency — present
*example* commands via `AskUserQuestion` and require explicit
selection. Never auto-inject `pytest`, `npm test`, `cargo build`, etc.
Without such evidence, the bucket is legitimately `unset`: skip it
downstream, do not prompt. In a non-interactive run, treat
evidence-backed unset buckets as `unset` too, and name them in the
report.

If no conventions file and no manifest exist, prompt once; the user
may answer `skip` to disable gates for the run.

## CI-coverage pass

After resolving local buckets, discover what CI verifies after a push
so local runs are not duplicated effort:

1. List CI definitions: `.github/workflows/*.yml`, `.gitlab-ci.yml`,
   `.circleci/config.yml`, `Jenkinsfile`, or equivalents.
2. For each job, note which buckets it covers and anything it runs
   that has **no local bucket** (matrix builds, slow/property-based
   suites, integration/e2e jobs, artifact builds).
3. Detect observability: if the `gh` CLI is present and the repo has a
   GitHub remote, post-push results can be watched with
   `gh pr checks --watch` (or `gh run watch` when no PR exists yet).

Record the result as a two-column split the calling skill embeds in
its plan output:

| Runs locally (per commit) | Deferred to CI (post-push) |
|---|---|
| fast buckets: `format`, `lint`, `typecheck`, scoped `test` | full-matrix tests, slow/marked suites, e2e, release builds |

## Right-sizing: no more verification than the change needs

The gates exist to keep every commit green — not to re-run the world.

- **Per-commit**: run `format`, `lint`, `typecheck` on the tree, and
  the `test` bucket **scoped to the affected area** when the runner
  supports path/keyword selection; otherwise — including when no test
  maps to the change (docs-only edits) — the project's default fast
  test command as written (its defaults often already exclude slow
  suites).
- **`build`**: run per commit only when the change plausibly affects
  build output (build config, entry points, packaging, codegen).
  Otherwise run it once at the end of the run, or defer to CI when a
  CI job covers it.
- **Deferred-to-CI** work is never silently dropped: the skill's final
  report must name what was deferred and, when observable, end by
  offering `gh pr checks --watch` after the push.
- Buckets discovered as `unset` are skipped, not reinvented.

## Storage

Resolved commands are cached for the run as `FORMAT_CMD`, `LINT_CMD`,
`TYPECHECK_CMD`, `TEST_CMD`, `BUILD_CMD`, plus `CI_COVERAGE` (the
two-column split) and `CI_WATCH_CMD` (empty when unobservable). They
are recorded verbatim in the skill's plan output so the user can audit
what was discovered — the skill does not pre-validate they exist on
`$PATH`.
