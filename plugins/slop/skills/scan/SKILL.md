---
name: scan
description: >-
  Use when the user wants to scan the current repo for AI slop,
  verbosity, fragile hard-coded references (line numbers, test
  counts, file counts), or low-value contributions in tracked files,
  with each finding landing as its own atomic forward-going commit.
  Triggers on phrases like "scan for slop", "audit repo for slop",
  "deslop the repo", "remove slop from this codebase", "scrub the
  repo", "scan the codebase for AI signatures", or "clean up slop
  without rewriting history". Does NOT rewrite history; every
  finding lands as a forward-going commit, with the project's
  formatter, linter, and type-checker running before each commit.
user-invocable: true
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[--paths=<glob>] [--apply] [--budget=strict|default|lax] [--with-history=<N>] [--allow-dirty] [--run-tests] [--no-semantic] [--taxonomy=<path>] [--on-fail=skip|stop|ask]"
---

# `/slop:scan`

Repo-wide slop scanner. Audits every tracked file at HEAD for AI
slop, verbose code/comments, fragile hard-coded references, and
low-value contributions. Optionally scans recent commit history
(advisory only). With `--apply`, each finding becomes its own
forward-going commit, after the project's discovered quality gates
pass.

This skill **never rewrites history**. It only adds new commits at
HEAD. It is safe on pushed branches and cannot flatten merge
topology. For branch-scoped slop cleanup that uses fixup commits
and `git rebase -i --autosquash`, see the sibling `/pr:deslop`
skill in `plugins/pr/`.

`disable-model-invocation: true` is intentional: this skill modifies
files and creates commits, so it must be user-explicit, not
router-inferred.

## Core thesis

Slop is a workflow label, not proof the text is wrong. The skill's
job is to reduce review-hostile noise in the codebase, not to scrub
the author's voice.

Three disciplines:

1. **Audit-first; commits-on-explicit-opt-in.** Default produces a
   patch-series review surface. `--apply` is the explicit opt-in for
   landing commits.
2. **Three severity tiers govern auto-apply.** Tier A (deterministic,
   near-zero FP) auto-applies. Tier B (high-confidence regex with
   edge cases) is user-confirmed per finding. Tier C (subjective
   tone) is advisory only and **calibrated against the project's
   accepted voice on `origin/<trunk>`**, not HEAD.
3. **One finding, one commit; quality gates first.** Every commit
   passes the project's discovered formatter / linter /
   type-checker before it lands. Failures rollback the change
   (`git checkout -- <file>`) and the run continues with the next
   finding.

## `$ARGUMENTS` contract

If `$ARGUMENTS` is empty, scan all tracked files at HEAD with the
default budget; confirm before scanning.

| Flag | Default | Effect | Interaction |
|---|---|---|---|
| `--paths=<glob>` | (all tracked) | Scope the scan via `git ls-files` glob (e.g., `--paths='src/**'`). | Multiple comma-separated globs accepted. |
| `--apply` | off | Run the per-finding commit loop after confirmation. **Lands new commits on HEAD.** | Without `--apply`, the run stops after materializing the patch series. |
| `--budget=<level>` | `default` | Tier ceiling: `strict` (auto-apply A only); `default` (A auto-apply, ≤5 B in proposal, ≤10 C advisory); `lax` (A auto-apply, ≤10 B, unlimited C advisory). | Independent. |
| `--with-history=<N>` | off | Also scan the last N commits' content + messages via `git log -n N -p`. **Findings here are advisory-only**; this skill never rewrites history. | If N exceeds total commit count, capped with a warning. |
| `--allow-dirty` | off | Permit running with an unstaged working tree. Gate-failed rollbacks then interleave with the user's unstaged work; the user owns the risk. | Without this, a dirty tree halts at Step 1. |
| `--run-tests` | off | Include the discovered test command in per-commit gates and final verification. Default off because tests are slow per-commit on large runs. | Independent. |
| `--no-semantic` | off | Skip the per-file semantic verifier; regex-only. Faster, lower precision. | Independent. |
| `--taxonomy=<path>` | built-in + `.claude/slop.local.yml` overlay | Replace registry entirely. | When set, both built-in and user overlay are ignored. |
| `--on-fail=<mode>` | `skip` | What to do when a per-finding gate fails: `skip` (rollback, mark gate-failed, continue), `stop` (rollback, halt), `ask` (surface via `AskUserQuestion`). | Independent. |

Any non-flag tokens are treated as a path scope and override
`--paths`.

## Boundary with `/pr:deslop`

| Skill | Scope | Action shape | When to use |
|---|---|---|---|
| `/pr:deslop` | The branch's commits since trunk (diffs + commit messages) | Fixup commits + `git rebase -i --autosquash` (rewrites history) | Branch-scoped cleanup before opening a PR; the slop is in commits you're about to ship. |
| `/slop:scan` | Tracked files at HEAD (optionally with advisory history scan) | Forward-going atomic commits, one per finding (no rewrite) | Repo-wide cleanup of slop already merged to trunk, or in long-lived files; safe on pushed/shared branches. |

The two skills share the same signature registry, the same
quality-gate discovery procedure, and the same tone-calibration
algorithm. They differ only in how findings get *resolved*.

If `/slop:scan` finds slop in historical commit messages via
`--with-history`, it does **not** edit them. The advisory points the
user at `/pr:deslop --message-only` for fixable historical
commit-message slop on the current branch.

## Orchestration Plan

Per the Orchestration Plan Convention defined in `CLAUDE.md`:

**1. Enter plan mode.** Activation hints by host:

- Claude Code: `EnterPlanMode`
- Cursor / Codex / Gemini: `/plan` or `Shift+Tab`

**2. Build the orchestration plan** containing:

1. The detected trunk ref (`BASELINE_SHA`) and the working-tree
   state (clean / dirty + `--allow-dirty`).
2. The active scope: paths globbed and total file count.
3. Whether `--with-history=N` is active and the resolved N.
4. Discovered quality-gate commands per bucket (`set` / `unset` /
   `prompt-user` for format, lint, typecheck, test).
5. Active `--budget` and `--on-fail` settings.
6. Active mode: `audit` (no `--apply`) or `apply-and-commit`
   (with `--apply`).
7. Findings summary as ranges (pre-execution estimate). The Step-11
   final report uses post-hoc exact counts.

**3. Present the plan and wait for explicit user approval.**

**4. Exit plan mode before executing** Step 1 onward.

If plan mode is unavailable in the host, the Steps 1–11 phase
structure still guides analysis-before-execution.

## Step 1: Snapshot state and lock baseline

Detect trunk using the same pattern as the sibling `/rebase` and
`/pr:deslop` skills (`plugins/rebase/commands/rebase.md:9-12`):

```bash
git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}'
```

Fall back to `main`, then `master`, if detection fails.

**Pointer-drift lock.** Resolve trunk to an absolute SHA at this
step and reuse that SHA throughout the run:

```bash
git rev-parse "origin/${TRUNK}"
```

Store as `BASELINE_SHA`. Step 4 (tone calibration) uses
`${BASELINE_SHA}` to read trunk's last 50 commits.

```bash
git rev-parse --abbrev-ref HEAD
```

```bash
git status --porcelain
```

Halt with a clear message if any of these is true:

- Working tree is dirty AND `--allow-dirty` was not passed.
- A rebase or merge is already in progress (`.git/rebase-merge/`,
  `.git/rebase-apply/`, or `.git/MERGE_HEAD` exists).
- HEAD is detached — every commit needs a branch reference.

## Step 2: Resolve scan scope

The default scope is every tracked file at HEAD:

```bash
git ls-files
```

If `--paths=<glob>` was provided, pass each glob through:

```bash
git ls-files -- "<glob>"
```

Reject the run with a clear message if the resolved set is empty
(e.g., misspelled glob).

If `--with-history=N` was passed, also collect:

```bash
git log -n "${N}" -p "${BASELINE_SHA}..HEAD"
```

Cap N at the total commit count and warn if the user-provided value
exceeded that. Historical content is fed to Pass A regex detection
in Step 6 with a `historical_only=true` marker; the action layer
treats those findings as advisory.

## Step 3: Discover quality gates (language-agnostic, merge across files)

Read `references/quality-gates.md` for the full procedure. Summary:

1. Read **all** of these files that exist (do not stop at the first):
   - `./AGENTS.md`
   - `./CLAUDE.md`
   - `./.github/CONTRIBUTING.md`
2. Parse each into sections by heading. For each section whose
   heading matches `format`, `fmt`, `style`, `lint`, `typecheck`,
   `tsc`, `mypy`, `pyright`, `test`, `spec`, `quality`, or `checks`
   (case-insensitive substring match), extract the first fenced code
   block and capture its first command line.
3. Bucket commands as `format`, `lint`, `typecheck`, `test`. Merge
   across files in priority order: `AGENTS.md` first, then
   `CLAUDE.md`, then `.github/CONTRIBUTING.md`. A bucket unset after
   the first file is filled by the next.
4. Manifest sniffing is **never a default**. If a manifest exists
   and a bucket is still `unset`, present *example* commands via
   `AskUserQuestion` and require explicit selection before storing.
   Never auto-inject `pytest`, `npm test`, `cargo test`, etc.
5. If no conventions file and no manifest, ask via `AskUserQuestion`:

   > I could not find AGENTS.md / CLAUDE.md describing your project's
   > quality gates. What command should I run before each per-finding
   > commit? You can answer 'skip' to disable quality gates.

This is the language-agnostic discipline mandated by the repo's
Language-Agnostic Design rule.

Cache the resolved commands as `FORMAT_CMD`, `LINT_CMD`,
`TYPECHECK_CMD`, `TEST_CMD`. Empty buckets are skipped in the apply
loop and final verification.

If every bucket is `unset` AND `--apply` was passed, warn loudly
before continuing — commits will land without any gate validation.

## Step 4: Read project tone (calibrate Tier C against trunk)

Calibrate against trunk's accepted voice — *not* HEAD, where
unreviewed slop on the branch could whitelist itself.

1. Search the conventions files from Step 3 for headings like
   `tone`, `style`, `prose`, `writing`, `voice`. Capture any
   directives.
2. Read the last 50 commit messages on the locked baseline:

   ```bash
   git log -n 50 --format='%B%n--END--' "${BASELINE_SHA}"
   ```

3. Build a frequency map of Tier C signal phrases. Default demotion
   threshold: ≥ 3 occurrences in the last 50 trunk commits. Phrases
   meeting the threshold are demoted from Tier C-active to
   advisory-only-in-summary for this run.

A flat regex list applied to every project will generate false
positives the user cannot disable, and they will stop trusting the
tool.

## Step 5: Load the signatures registry

Built-in registry path:
`${CLAUDE_PLUGIN_ROOT}/skills/scan/references/signatures.yml`. Read
via the Read tool.

Project override: `.claude/slop.local.yml` if present in the repo
root.

The override file declares three explicit operations:

- `replace:` — list of signature ids; each id replaces the built-in
  entry of the same id with the user's definition.
- `append:` — list of new signatures (must use ids not present in
  built-in).
- `delete:` — list of built-in signature ids to remove from this
  run.

The three keys are mutually disjoint per id. If the override
declares the same id under more than one key, refuse with a parser
error.

If `--taxonomy=<path>` is passed, that path replaces both built-in
and user overlay. If the override is malformed, refuse with a parser
error pointing to the offending line; do not silently fall back to
built-in only.

Print: "Loaded N signatures (B builtin, R replaced, A appended, D
deleted; tone calibration demoted X)."

## Step 6: Detect (two-pass hybrid)

Cost-saving framing: regex first (cheap, deterministic), semantic
only on flagged files (expensive, precise).

### Pass A — Regex (always runs)

For each enabled signature, run its `pattern` against:

- `target: file` — every file from Step 2's set; per-line.
- `target: diff` — same files; the regex is interpreted as matching
  current content (this skill operates on file state, not patches,
  so the `diff` target collapses to `file` for HEAD scans). When the
  pattern begins with `^\+` (the diff added-line anchor), strip the
  anchor before matching: with no diff to drive the prefix, every file
  line is treated as "added" for slop-detection purposes. Patterns
  beginning with `^-` (the diff removed-line anchor) cannot match file
  content and are skipped in HEAD-scan mode; they remain active under
  `--with-history` against captured `git log -p` output.
- `target: message-subject` / `message-body` — only meaningful if
  `--with-history=N`; matched against the captured `git log` output.

Each match produces a candidate finding:
`{file, line_range, signature_id, tier, confidence: regex, action,
 historical_only: <bool>}`.

Findings with `historical_only: true` are advisory regardless of
tier — this skill cannot edit historical commits.

### Pass B — Semantic verifier (skip with `--no-semantic`)

Dispatch a `Task` sub-agent — one per file with at least one Pass-A
finding, capped at 8 concurrent. Sub-agent contract (enforced via
the prompt, not via a separate agent file):

- Allowed tools: `Read`, `Grep`, `Glob`.
- Disallowed: `Bash`, `Write`, `Edit`, `Task`.

Each invocation receives:

- The file's full content.
- The Pass-A findings on this file.
- The registry filtered to `kind: semantic`.
- The Step-4 tone calibration result.

**Anti-slop-on-slop constraint.** The sub-agent's prompt must
include:

> Do not introduce slop in your suggested replacements. Do not use
> phrases listed in the registry. Do not narrate your changes ("I
> tightened…"). Replacement text should be concrete and shorter
> than the original where possible.

The sub-agent returns a JSON list of findings. Parse resiliently:

1. Strip markdown fences (` ```json … ``` ` or plain ` ``` … ``` `).
2. Extract the first balanced `[ … ]` from the response.
3. Parse. On failure, mark `verifier=skipped-for-<file>` for that
   file and fall back to that file's Pass-A findings only. Do not
   crash the run.

Findings are joined to Pass A by `(file, line_range)`:

- semantic confirms — confidence upgraded.
- semantic denies — finding dropped.
- semantic-only — added fresh.

If `Task` is unavailable, mark `verifier=skipped` globally and
continue with Pass A only.

## Step 7: Apply tiers, budget, and grouping

Aggregate findings by `(tier, severity)`:

| Budget | Tier A | Tier B | Tier C |
|---|---|---|---|
| `strict` | auto-apply all | none in proposal (advisory) | none (silently skipped) |
| `default` | auto-apply all | up to 5 in proposal, rest advisory | up to 10 advisory |
| `lax` | auto-apply all | up to 10 in proposal | unlimited advisory |

Within each tier, rank findings by `(files_affected DESC,
confidence DESC, signature_id ASC)` and take the top N per the
budget. Remaining findings become advisories.

Group findings by file. For each file, compute the proposed edit
sequence:

| Finding scope | Patch shape |
|---|---|
| Single regex match in a file | One `.patch` file; one commit per match. |
| Multiple regex matches of the same signature in one file | Each match is its own finding and its own commit (per the user-stated rule "target each identification of slop in separate commits"). |
| Semantic-only finding | One `.patch` file; one commit. |
| Whole-file low-value (e.g., the whole file is debug debris) | Mark advisory; never auto-apply for `/slop:scan` — deletion is too consequential. |
| Historical-only finding | Advisory; never an editable patch. |

The "one finding, one commit" granularity is intentional. It makes
each commit individually reviewable and individually revertable
(`git revert <sha>`), at the cost of producing N commits for N
findings. Users who want aggregation should use `/pr:deslop`'s
fixup-per-target-SHA model instead.

## Step 8: Materialize the patch series

Always materialize first — this is the user's review surface.

The directory uses `<ts>-<pid>` to prevent collisions on fast
double-invocation:

```bash
mkdir -p ".git/slop-scan/$(date -u +%Y%m%d-%H%M%SZ)-$$"
```

Layout:

```
.git/slop-scan/<ts>-<pid>/
├── 0000-PLAN.md                       (plan + registry source path + SHA-256)
├── 0001-edit-<file-slug>-<sigid>.patch
├── 0002-edit-<file-slug>-<sigid>.patch
├── …
├── 0099-advisory.md                   (Tier C demoted findings + historical-only findings)
└── commits.json                       (mapping finding → proposed commit subject + body)
```

`0000-PLAN.md` records: registry version, registry source path
(built-in or `--taxonomy=<path>`), registry SHA-256, resolved
`FORMAT_CMD` / `LINT_CMD` / `TYPECHECK_CMD` / `TEST_CMD`,
`BASELINE_SHA`, the scope's file count, budget, tone-calibration
result, `--on-fail` mode.

`commits.json` records, per finding: the proposed `chore(slop[…])` /
`docs(slop[…])` / `refactor(slop[…])` subject and the `why:` /
`what:` body, generated from `references/commit-template.md` rules.
The user can review and edit `commits.json` before running with
`--apply` (the apply loop in Step 10 reads from `commits.json`).

There is no `apply.sh` (unlike `/pr:deslop`). The skill drives the
apply loop directly because the per-finding commits need fine-
grained orchestration (rollback on gate failure, `--on-fail`
handling, progress reporting) that is awkward to script in POSIX
shell.

`.git/slop-scan/` is run-scoped, not a permanent record. Treat each
subdirectory as ephemeral.

If `--apply` was not passed, stop here. The patch series is the
user's review artifact; they re-invoke the skill with `--apply`
when they're satisfied with the proposals.

## Step 9: Confirmation gate

Use `AskUserQuestion`:

| Choice | Effect |
|---|---|
| **Patches only** (default) | Files written to `.git/slop-scan/<ts>-<pid>/`; nothing applied. |
| **Apply and commit** | Run the per-finding commit loop. Only offered if `--apply` was passed. |
| **Cancel** | Delete `.git/slop-scan/<ts>-<pid>/` and exit. |

If the skill was invoked without `--apply`, the second option is
hidden.

## Step 10: Per-finding commit loop

For each finding sorted by `(file ASC, signature_id ASC,
line_range_start ASC)`:

### 10a. Apply the edit

Use the Edit tool to apply the proposed change to the file. The
edit's `old_string` and `new_string` are derived from the regex
match (Pass A) or the sub-agent's suggestion (Pass B), recorded in
the finding's `.patch` file.

### 10b. Stage explicit paths

```bash
git add -- "<file>"
```

Per `plugins/commit/commands/commit.md:181-191` (rule line 187):
**never `git add -A` or `git add .`** — explicit paths only.

### 10c. Run touched-file gates

Run each discovered gate command, scoped to the touched file where
the tool supports a path argument; otherwise run project-wide:

```bash
${FORMAT_CMD}
```

```bash
${LINT_CMD}
```

```bash
${TYPECHECK_CMD}
```

If `--run-tests` was passed:

```bash
${TEST_CMD}
```

Treat each gate independently:

- **Formatter** auto-applies. Re-stage anything it changed:
  `git add -- "<file>"`.
- **Linter** with `--fix` auto-fixes; re-stage. Hard errors that
  don't auto-fix are gate failures (see Step 10d).
- **Type checker** never auto-modifies. Errors are gate failures.
- **Tests** (only if `--run-tests`) — same triage.

### 10d. On gate failure

Apply `--on-fail`:

- `skip` (default): rollback the change with
  `git checkout -- "<file>"` (which un-stages and restores HEAD's
  content), record stderr in the run report, mark the finding
  `gate-failed`, continue with the next finding.
- `stop`: rollback as above, halt the run, surface the gate's
  stderr.
- `ask`: surface via `AskUserQuestion`:
  - **Edit and continue** — user fixes manually, the skill re-runs
    gates and continues.
  - **Skip this finding** — rollback and continue.
  - **Stop the run** — rollback and halt.

### 10e. On gate pass

Read the proposed commit message for this finding from
`commits.json`. Write it to a temp file and commit:

```bash
git commit --no-edit -F "<temp-message-file>"
```

The `--no-edit` is defensive — even though we pass `-F`, this
guards against a misconfigured `core.editor` opening the message
file interactively. The commit follows the project's
`Scope(type[detail])` convention as recorded in `commits.json` (see
`references/commit-template.md`).

If a project pre-commit hook (`pre-commit`, `commit-msg`) rejects
the commit, treat the failure the same as a gate failure: rollback
the change, mark the finding `hook-failed`, surface the hook's
stderr, and apply `--on-fail`. The skill **never** uses
`--no-verify` — hooks are the project's authority.

Mark the finding `committed` in the run report.

## Step 11: Final verification and report

```bash
git log --oneline "${BASELINE_SHA}..HEAD"
```

```bash
git status --porcelain
```

Run the full discovered gate set on the tip (skip empty buckets):

```bash
${FORMAT_CMD}
```

```bash
${LINT_CMD}
```

```bash
${TYPECHECK_CMD}
```

If `--run-tests` was passed:

```bash
${TEST_CMD}
```

Report sections:

```
Slop scan summary
=================
Scope: <count> files (paths: <globs>)
Budget: <level>
Findings: <total> (<a> Tier A, <b> Tier B, <c> Tier C, <h> historical-only)

Committed: <committed> findings landed as commits
Gate-failed (rolled back): <gate-failed> — see report below
Hook-failed (rolled back): <hook-failed>
Skipped (advisory budget): <advisory> Tier C — see 0099-advisory.md
Historical-only: <h> — run /pr:deslop --message-only on the current branch for fixable historical commit-message slop

Tone calibration: demoted <phrases>
Verifier: <enabled|skipped> (<scanned> files scanned; <skipped-per-file> skipped)

Quality gates (final)
=====================
format=<status> | lint=<status> | typecheck=<status> | tests=<status>

Per-finding commits:
  <sha-short> chore(slop[ai-slop.signatures]) Remove AI footer from README.md
  <sha-short> docs(slop[brittle.line-numbers]) Replace line-number reference in CONTRIBUTING.md
  …

Gate-failed findings:
  <signature-id> in <file>:<line> — <gate>: <stderr summary>
  …

Patch series: .git/slop-scan/<ts>-<pid>/
```

**Do NOT push.** The user decides. There is no `--force-push` flag
because this skill never rewrites history; a normal `git push`
suffices.

## Edge cases

| Case | Behavior |
|---|---|
| Working tree dirty, no `--allow-dirty` | Refuse at Step 1. |
| `--allow-dirty` passed | Permit, but warn that gate-failed rollbacks (`git checkout -- <file>`) interleave with unstaged work. |
| Detached HEAD | Refuse at Step 1 — every commit needs a branch reference. |
| Rebase or merge in progress | Refuse at Step 1. |
| Empty repo / no tracked files | Exit cleanly: "No tracked files to scan." |
| All findings advisory (Tier C only at `default` budget) | Print the report; no commits. Exit 0. |
| Every gate bucket `unset` | Warn at Step 3; permit but make explicit in the report that no gates ran. |
| `--with-history=N` with N greater than total commit count | Cap at total; warn. |
| Historical-only finding (no current file match) | Advisory; report points at `/pr:deslop`. |
| Finding's edit yields empty diff (already fixed) | Skip; record as "no-op" in the report. Do not produce an empty commit. |
| Two findings target the same line range | Apply in `(signature_id ASC, line_range_start ASC)` order; the second often produces empty diff and becomes a no-op. |
| Pre-commit / commit-msg hook rejects a per-finding commit | Treat as gate failure (Step 10d). The skill never `--no-verify`. |
| User override `.claude/slop.local.yml` malformed | Refuse with parser error pointing to offending line. |
| `--taxonomy=<path>` points at missing file | Refuse with path-resolution error. |
| User-overridden registry disables every signature | "No active signatures — nothing to detect." Exit 0. |
| Sub-agent fails / times out / parses non-JSON | Mark `verifier=skipped-for-<file>`; fall back to that file's Pass A findings. Do not crash. |
| Branch was pushed | No special handling — this skill only adds new commits. Pushing again is a normal `git push`, not a force-push. |
| Branch contains merge commits | No special handling — this skill never rebases. |
| `Task` tool unavailable | Mark `verifier=skipped` globally; run Pass A only. |
| `--paths=<glob>` resolves to zero files | Refuse with "scope is empty"; do not silently no-op. |
| Disk fills during materialize | The `git apply` step in 10a fails; treat as gate failure for that finding; continue if `--on-fail=skip`. |
| File is binary | Pass A's regex `target: file` skips it (regex against a binary blob is meaningless); finding count for binary files is always 0. |
| File is a symlink | Skip — `git ls-files` shows it but reading the link target is out of scope. |

## What this skill does NOT cover

- **The PR description on GitHub** — `/pr:review-pr`'s job.
- **Branch commits since trunk** — `/pr:deslop`'s job (uses fixup +
  autosquash; rewrites history).
- **Full rebase onto trunk** — `/rebase`'s job.
- **Pushing the new commits** — explicit user action; this skill
  never pushes.
- **Auto-applying Tier C suggestions** — never. Prose voice belongs
  to the author.
- **Auto-rewriting historical commits** — never. Historical findings
  are advisory only; redirect to `/pr:deslop --message-only`.
- **Whole-file deletions** — too consequential; whole-file
  low-value findings are advisory.
- **Pre-commit prevention** — that is the future `commit/hooks/`
  preventative hook described in `/pr:deslop`'s future-hook section.

## Reference files

For detailed catalogs and procedures, consult:

- **`references/signatures.yml`** — versioned slop registry. v1
  byte-for-byte duplicate of the deslop registry; lockstep notice
  at the top of the file.
- **`references/slop-taxonomy.md`** — Tier A/B/C catalog with FP
  guards.
- **`references/quality-gates.md`** — discovery procedure
  (read-all-files, merge-with-priority).
- **`references/commit-template.md`** — per-finding commit-message
  templates by signature category, mapping each signature prefix to
  a `Scope(type[detail])` subject and a `why:` / `what:` body shape.

## Cited repo artifacts

- `plugins/pr/skills/deslop/SKILL.md` — sibling skill for
  branch-scoped slop cleanup via fixup commits and autosquash. This
  skill (`/slop:scan`) and that one share the registry, taxonomy,
  and quality-gate procedure.
- `plugins/pr/commands/review-pr.md:55` — "No brittle details"
  rubric; the underlying source for several Tier B signatures.
- `plugins/pr/commands/review-pr.md:78` — "Never modify the PR — only
  report findings" posture; mirrored here as
  `/slop:scan`'s never-rewrite-history rule.
- `plugins/rebase/commands/rebase.md:9-12` — trunk detection
  pattern; reused for `BASELINE_SHA` resolution.
- `plugins/research/skills/deps/SKILL.md` — procedural skill
  archetype.
- `plugins/tailwind/skills/spacing-audit/SKILL.md` — references-
  directory progressive-disclosure pattern.
- `plugins/commit/commands/commit.md:181-191` — Rules section
  forbidding `git add -A`, `--amend`, `--no-verify`, empty commits;
  this skill honors all of them.
- `CLAUDE.md` Git Commit Standards — `Scope(type[detail])` subject
  + `why:` / `what:` body shape; templates in
  `references/commit-template.md` follow this exactly.
