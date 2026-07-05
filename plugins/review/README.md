# review

Address code-review findings on the current branch — provenance-gated
to changes the branch introduced, one finding per commit, simplest
pragmatic fix, with quality gates before every commit and prompted
history rewrites.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install review@ai-workflow-plugins
```

## Command

| Command | Description |
|---------|-------------|
| `/review:address [findings]` | Triage findings by provenance, fix in-branch ones as atomic gated commits, surface the rest for decisions |

Flags: `--pr=<num>` (pull findings from the PR's review comments),
`--base=<ref>` (override the provenance baseline), `--no-fixup`
(forward commits only), `--on-fail=skip|stop|ask` (per-finding gate
failure handling).

## Workflow

1. **Situational awareness** — read AGENTS.md / CLAUDE.md, discover the
   project's format / lint / typecheck / test / build commands and what
   CI covers post-push
2. **Parse findings** — from pasted text or `gh pr view --comments`
3. **Provenance triage** — classify each finding `in-branch`,
   `pre-existing`, `mixed`, or `disputed` against the merge-base with
   trunk; only `in-branch` findings are fixed by default
4. **Plan** — one finding per commit, simplest pragmatic fix,
   forward-vs-`fixup!` shape declared per finding; approval required
5. **Execute** — per finding: minimal fix → fast local gates → commit;
   gate failures revert that fix and follow `--on-fail`
6. **Report** — triage table, commits, deferred/declined findings with
   suggested reviewer replies, and a `gh pr checks --watch` offer

## Scoping rules

- **Pre-existing findings are never silently fixed.** A reviewer may
  flag code the branch didn't touch; those become follow-up
  recommendations unless the user explicitly opts in.
- **Comment and typo findings** are addressed with maximum concision —
  fewer lines, never more.
- **History rewrites are opt-in.** `fixup!` + autosquash is offered
  only for trivial fixes whose causal commit is in-branch and unpushed;
  anything non-trivial always prompts first.

## Verification discovery

The command reads AGENTS.md / CLAUDE.md / CONTRIBUTING.md to discover
which quality checks the project requires, and reads the CI definitions
to learn what a push verifies for free (see
`references/verification-gates.md`). It does **not** hardcode any test
runner, linter, or build tool — and it deliberately runs no more
verification than each fix needs, deferring CI-covered work to
`gh pr checks --watch` after a push.

## Prerequisites

- **git** — provenance triage uses merge-base, diff, log -L, and blame
- **gh** (optional) — enables `--pr` findings ingestion and CI watching
