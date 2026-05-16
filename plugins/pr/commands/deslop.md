---
description: >-
  Use when the user wants to clean AI slop, verbosity, fragile
  hard-coded references (line numbers, test counts, file counts), or
  low-value contributions out of a branch's commits before review.
  Triggers on phrases like "deslop", "remove AI slop", "clean up
  commits", "tighten the commits", "fix verbose commit messages",
  "drop the fluff", "remove brittle counts", "kill the line-number
  references", "audit the branch for slop", "scrub Claude signatures",
  or "fixup the slop on this branch". Operates per-commit since trunk:
  detects issues, proposes targeted patches and fixup commits (and
  `--fixup=reword:` for commit-message slop), then optionally runs
  `git rebase -i --autosquash`, running the project's formatter,
  linter, and type-checker on every conflict pause.
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "AskUserQuestion", "Task"]
argument-hint: "[<commit-range>] [--apply-patches] [--apply-rebase] [--budget=strict|default|lax] [--targets=diff,messages,both] [--message-only | --diff-only] [--since=<ref>] [--force-rewrite-pushed] [--run-tests] [--no-semantic] [--taxonomy=<path>]"
---

# `/pr:deslop`

Audit-first, autosquash-on-explicit-opt-in slop cleaner. Reviews every
commit on the current branch since trunk for AI slop, verbose
code/comments, fragile hard-coded references, and low-value
contributions. Produces a numbered patch series under
`.git/deslop/<ts>-<pid>/` plus a checkpointed `apply.sh`. With
`--apply-rebase`, applies aggregated fixups (one per target SHA) and
runs `git rebase -i --autosquash`, delegating conflict resolution to
the project's discovered quality gates.

The skill **refuses to operate on already-pushed branches** unless
`--force-rewrite-pushed` is passed, and **refuses `--apply-rebase`
entirely** if the branch contains merge commits since trunk
(`git rebase -i --autosquash` without `--rebase-merges` silently
flattens topology).

Subjective findings are calibrated against the project's accepted
voice on `origin/<trunk>` (not `HEAD`) before being flagged. The
skill auto-applies only Tier A signals; Tier B is user-confirmed per
finding; Tier C is advisory only.

This is a slash command, not a model-invocable skill — history
rewrites must be user-explicit, not router-inferred.

## Core thesis

Slop is a workflow label, not proof the text is wrong. The skill's
job is to reduce review-hostile noise, not to scrub the user's voice.
Three disciplines:

1. **Audit-first, autosquash-on-explicit-opt-in.** Default produces a
   patch series plus a checkpointed `apply.sh`. `--apply-rebase` is
   the explicit opt-in.
2. **Three severity tiers govern auto-apply.** Tier A (deterministic,
   near-zero FP) is auto-applied. Tier B (high-confidence regex with
   edge cases) is user-confirmed per finding. Tier C (subjective
   tone) is advisory only and calibrated against the project's
   accepted voice on `origin/<trunk>`.
3. **Refuse, don't warn, on dangerous topologies.** Pushed branches
   require `--force-rewrite-pushed`. Branches with merge commits
   refuse `--apply-rebase` entirely.

Slop includes **branch-internal narrative bleed** — within-branch
tactical decisions (renames of unshipped symbols, intermediate states,
phantom `### Fixes`) that leak from commits into the artifacts being
committed. Reviewing the diff and the commit message for those
phrasings is part of the audit; the rule and the Published-Release
Test are in `AGENTS.md` § *Shipped vs. Branch-Internal Narrative*.

## `$ARGUMENTS` contract

If `$ARGUMENTS` is empty, default to `<trunk>..HEAD` (trunk
auto-detected; see Step 1) and confirm before scanning.

| Flag | Default | Effect | Interaction |
|---|---|---|---|
| `--apply-patches` | off | Materialize patches under `.git/deslop/<ts>-<pid>/`; stop after generating `apply.sh`. | Redundant when paired with `--apply-rebase` (no error). |
| `--apply-rebase` | off | Run `apply.sh` then `git rebase -i --autosquash`. **Destructive.** | Strict superset of `--apply-patches`. Requires `--force-rewrite-pushed` on pushed branches. Refused entirely if branch has merge commits. Requires `--since` to be an ancestor of HEAD when set. |
| `--budget=<level>` | `default` | Tier ceiling (see Step 7). | Independent of `--targets`. |
| `--targets=<list>` | `both` | One of `diff`, `messages`, `both`. | `--message-only` and `--diff-only` are shorthands; cannot combine with `--targets`. |
| `--message-only` | off | Shorthand for `--targets=messages`. | Mutually exclusive with `--diff-only` and `--targets`. |
| `--diff-only` | off | Shorthand for `--targets=diff`. | Mutually exclusive with `--message-only` and `--targets`. |
| `--since=<ref>` | auto | Override trunk detection. | Skips Step 1's auto-detection. With `--apply-rebase`, must be an ancestor of HEAD (verified at Step 1). |
| `--force-rewrite-pushed` | off | Required when branch was pushed. Mirrors `git push --force` ergonomics. | No effect on local-only branches. |
| `--run-tests` | off | Include the discovered test command in conflict-loop gates and final verification. | Independent. |
| `--no-semantic` | off | Skip per-commit semantic verifier; regex-only. | Independent. |
| `--taxonomy=<path>` | built-in + `.claude/deslop.local.yml` overlay | Replace registry entirely. | When set, both built-in and user overlay are ignored. |

Any non-flag tokens are treated as a commit range (`<sha>..<sha>` or
single SHA) and override `<trunk>..HEAD`.

## Boundary with `/pr:review-pr`

| Skill | Surface | Posture |
|---|---|---|
| `/pr:review-pr` | The PR description on GitHub | Read-only — only reports findings (`plugins/pr/commands/review-pr.md:78`). |
| `/pr:deslop` | The branch's commits (diffs + messages) | Patch series → optional aggregated fixups → optional autosquash. Never edits the PR description. |

Bidirectional: neither skill modifies the other's surface. `deslop`
may *suggest* running `/pr:review-pr` afterward when it spots
PR-description problems; it never invokes it.

`/pr:review-pr` already includes a "No brittle details" rubric at
`plugins/pr/commands/review-pr.md:55`. `/pr:deslop` reuses that rubric
as Tier A/B core and extends it with the broader signature registry.

## Orchestration Plan

Per the Orchestration Plan Convention defined in this repo's
top-level conventions file, this skill must enter plan mode before
any analysis runs.

**1. Enter plan mode.** Activation hints by host:

- Claude Code: `EnterPlanMode`
- Cursor / Codex / Gemini: `/plan` or `Shift+Tab`

**2. Build the orchestration plan** containing:

1. The detected trunk ref and commit count to scan.
2. The active `--budget` and `--targets` settings.
3. Discovered quality-gate commands per bucket (`set` / `unset` /
   `prompt-user` for format, lint, typecheck, test).
4. Active mode (`audit` / `--apply-patches` / `--apply-rebase`).
5. Branch topology (`local-only` / `pushed` /
   `contains-merge-commits`).
6. Findings summary as ranges (pre-execution estimate). Step 12's
   final report uses post-hoc exact counts.

**3. Present the plan and wait for explicit user approval.**

**4. Exit plan mode before executing** Step 1 onward.

If plan mode is unavailable in the host, the Steps 1–12 phase
structure still guides analysis-before-execution.

## Step 1: Detect trunk, lock baseline, snapshot branch state

Detect trunk using the same pattern as the sibling `/rebase` command
(`plugins/rebase/commands/rebase.md:9-12`):

```bash
git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}'
```

Fall back to `main`, then `master`, if detection fails.

**Pointer-drift lock.** Resolve trunk to an absolute SHA at this
step and reuse that SHA throughout the run — protects against
background `git fetch` shifting the baseline mid-run:

```bash
git rev-parse "origin/${TRUNK}"
```

Store as `BASELINE_SHA`. Subsequent steps reference `${BASELINE_SHA}`,
not `origin/${TRUNK}`.

```bash
git rev-parse --abbrev-ref HEAD
```

```bash
git status --porcelain
```

```bash
git log --oneline "${BASELINE_SHA}..HEAD"
```

```bash
git log --merges --oneline "${BASELINE_SHA}..HEAD"
```

If `--since=<ref>` was passed AND `--apply-rebase` is set, verify it
is an ancestor of HEAD — autosquash on a sibling branch will destroy
topology:

```bash
git merge-base --is-ancestor "<ref>" HEAD
```

Halt with a clear message if any of these is true:

- Working tree is dirty (`git status --porcelain` non-empty; includes
  dirty submodules — single check covers both).
- `git log --oneline "${BASELINE_SHA}..HEAD"` emits no lines.
- Current branch is the trunk itself.
- A rebase is already in progress (`.git/rebase-merge/` or
  `.git/rebase-apply/` exists).
- HEAD is detached.
- Branch contains merge commits AND `--apply-rebase` was requested
  (refuse `--apply-rebase`; `--apply-patches` is permitted).
- `--since=<ref>` was passed AND `--apply-rebase` is set AND the ref
  is not an ancestor of HEAD.

## Step 2: Pushed-branch gate

```bash
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null
```

If no upstream, the branch is local-only; continue.

If an upstream exists:

```bash
git rev-parse --verify '@{u}'
```

```bash
git merge-base --is-ancestor "$(git rev-parse '@{u}')" HEAD
```

If `merge-base --is-ancestor` returns 0, the upstream is reachable
from HEAD — the branch was pushed. Without `--force-rewrite-pushed`,
refuse:

> This branch was already pushed to `<upstream>`. Rewriting its
> history will require force-push and may break any reviewer's local
> checkout. Re-run with `--force-rewrite-pushed` to override, or use
> `--apply-patches` only (no rebase) to produce a patch series the
> user can review.

If `--force-rewrite-pushed` was passed, record the upstream name in
the final report and continue.

## Step 3: Discover quality gates (language-agnostic, merge across files)

Read `${CLAUDE_PLUGIN_ROOT}/references/quality-gates.md` for the full procedure. Summary:

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
   > quality gates. What command should I run after each conflict
   > resolution? You can answer 'skip' to disable quality gates.

This is the language-agnostic discipline mandated by the repo's
Language-Agnostic Design rule.

Cache the resolved commands as `FORMAT_CMD`, `LINT_CMD`,
`TYPECHECK_CMD`, `TEST_CMD`. Empty buckets are skipped in Steps 11
and 12.

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
`${CLAUDE_PLUGIN_ROOT}/references/signatures.yml`. Read
via the Read tool.

Project override: `.claude/deslop.local.yml` if present in the repo
root.

The override file declares three explicit operations (replacing the
ambiguous single `extends:` key):

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

If `.claude/deslop.local.yml` is *tracked by git* AND currently
dirty, warn that `--apply-rebase` may pause if a fixup touches it,
and advise committing or stashing before applying.

Print: "Loaded N signatures (B builtin, R replaced, A appended, D
deleted; tone calibration demoted X)."

## Step 6: Detect (two-pass hybrid)

Cost-saving framing: regex first (cheap, deterministic), semantic
only on flagged hunks (expensive, precise).

### Pass A — Regex (always runs)

For each enabled signature, run its `pattern` against:

- `target: diff` — `git diff "${BASELINE_SHA}..HEAD"` (per-hunk).
- `target: message-subject` — each commit's subject line.
- `target: message-body` — each commit's body.
- `target: file` — staged file content per commit.

Each match produces a candidate finding:
`{commit_sha, signature_id, location, tier, confidence: regex, action}`.

### Pass B — Semantic verifier (skip with `--no-semantic`)

Dispatch a `Task` sub-agent — one per commit, capped at 8 concurrent.
Sub-agent contract (enforced via the prompt, not via separate agent
file):

- Allowed tools: `Read`, `Grep`, `Glob`.
- Disallowed: `Bash`, `Write`, `Edit`, `Task`.

Each invocation receives:

- The commit's full diff (`git show <sha>` content embedded in the
  prompt).
- The commit's full message.
- The registry filtered to `kind: semantic`.
- The Step-4 tone calibration result.

**Anti-slop-on-slop constraint.** The sub-agent's prompt must
include:

> Do not introduce slop in your suggested replacements. Do not use
> phrases listed in the registry. Do not narrate your changes ("I
> tightened…"). Replacement text should be concrete and shorter than
> the original where possible.

The sub-agent returns a JSON list of findings. Parse resiliently:

1. Strip markdown fences (` ```json … ``` ` or plain ` ``` … ``` `).
2. Extract the first balanced `[ … ]` from the response.
3. Parse. On failure, mark `verifier=skipped-for-<sha>` for that
   commit and fall back to that commit's Pass A findings only. Do
   not crash the run.

Findings are joined to Pass A by `(commit_sha, location)`:

- semantic confirms — confidence upgraded.
- semantic denies — finding dropped.
- semantic-only — added fresh.

If `Task` is unavailable, mark `verifier=skipped` globally and
continue with Pass A only.

## Step 7: Apply tiers, budget, and grouping

| Budget | Tier A | Tier B | Tier C |
|---|---|---|---|
| `strict` | auto-apply all | none in proposal (advisory) | none (silently skipped) |
| `default` | auto-apply all | up to 5 in proposal, rest advisory | up to 10 advisory |
| `lax` | auto-apply all | up to 10 in proposal | unlimited advisory |

Within each tier, rank findings by `(commits_affected DESC,
confidence DESC, signature_id ASC)` and take the top N per the
budget. Remaining findings become advisories in the report.

Group findings by target commit:

| Finding scope | Patch shape | Tool (git ≥ 2.32) | git < 2.32 fallback |
|---|---|---|---|
| Diff slop in commit X | One fixup commit per X (aggregated from N patches) | `git commit --fixup=<X>` | Same. |
| Subject-only or body slop in commit X | One reword fixup per X | `git commit --fixup=reword:<X>` | Empty fixup + manual reword note in `apply.sh` |
| Diff AND message slop in commit X | One amend fixup carrying tree + message | `git commit --fixup=amend:<X>` | Two fixups: `--fixup=<X>` for diff + manual reword note for message |
| Whole-commit low-value | `drop` line in `git-rebase-todo` | sequence-editor honors it | Same. |

`--fixup=amend:` and `--fixup=reword:` are documented in `git commit
--help`, available since git 2.32. The pre-2.32 fallback **preserves
diff fixups** rather than refusing across the board — only message
rewrites become manual notes.

`git interpret-trailers` is *not* a general message-rewrite tool —
only narrow trailer cleanup. `--fixup=reword:` is the canonical
mechanism for message rewrites.

## Step 8: Materialize the patch series

Always materialize first — this is the user's review surface.

The directory uses `<ts>-<pid>` to prevent collisions on fast
double-invocation (second-precision timestamps race):

```bash
mkdir -p ".git/deslop/$(date -u +%Y%m%d-%H%M%SZ)-$$"
```

Layout:

```
.git/deslop/<ts>-<pid>/
├── 0000-PLAN.md                 (plan + registry source path + SHA-256)
├── 0001-fixup-<sha>-<id>.patch  (per-finding diff patches)
├── 0002-reword-<sha>.txt
├── 0003-amend-<sha>.patch
├── 0004-drop-<sha>.note
├── 0005-advisory.md
├── reword/
│   └── <sha>.txt                (one file per target SHA needing reword)
├── reword-map.tsv               (autosquash-subject → target-sha → reword-file)
├── .checkpoint/                 (per-step durable markers for apply.sh idempotency)
└── apply.sh                     (rendered from ${CLAUDE_PLUGIN_ROOT}/references/apply-template.sh)
```

`0000-PLAN.md` records: registry version, registry source path
(built-in or `--taxonomy=<path>`), registry SHA-256, resolved
`FORMAT_CMD` / `LINT_CMD` / `TYPECHECK_CMD` / `TEST_CMD`,
`BASELINE_SHA`, commit range, budget, tone-calibration result.

**Patch aggregation per target SHA**: one fixup commit per target,
not one fixup per finding. Multiple `.patch` files for the same
target are visible artifacts (one per finding for reviewability),
but `apply.sh` applies them all to the working tree before creating
the single fixup. See `${CLAUDE_PLUGIN_ROOT}/references/apply-template.sh`
for the patch driver template.

`apply.sh` is the single artifact the user runs. Idempotent via
durable per-step checkpoints; re-running skips completed steps.
Re-reads the registry source path recorded in `0000-PLAN.md`,
recomputes its SHA-256, and aborts if changed since materialization.

If `--apply-patches` was passed without `--apply-rebase`, stop here.
The user runs `bash .git/deslop/<ts>-<pid>/apply.sh` themselves.

`.git/deslop/` is run-scoped, not a permanent record. Git ignores
subdirectories of `.git/` that aren't its known data directories;
the patch files are POSIX files, not git objects.

## Step 9: Confirmation gate

Use `AskUserQuestion`:

| Choice | Effect |
|---|---|
| **Patches only** (default) | Files written; nothing applied. |
| **Apply patches now** | Run `apply.sh`; create fixup commits on `HEAD`; **do not rebase**. |
| **Apply and autosquash** | Full rewrite. Only offered if `--apply-rebase` was passed AND no merge commits were detected in Step 1. |
| **Cancel** | Delete `.git/deslop/<ts>-<pid>/` and exit. |

For "Apply patches now" the skill must show this warning before
proceeding:

> Fixup commits will be on `HEAD`. Run `git rebase -i --autosquash
> <trunk>` yourself before pushing, or reviewers will see the raw
> `fixup!` / `amend!` commits. The Step-10 backup branch is created
> for this option too.

If the skill was invoked without `--apply-rebase`, the third option
is hidden.

## Step 10: Backup and apply

Before any history-affecting action — including the middle option —
create the backup branch:

```bash
git branch "$(git branch --show-current)-pre-deslop-$(date -u +%Y%m%d-%H%M%S)"
```

Record the backup branch name in the final report. Tell the user:
the original branch state is preserved at this branch; if anything
goes wrong they can `git reset --hard <backup>`.

Apply patches:

```bash
bash ".git/deslop/${TS_PID}/apply.sh"
```

`apply.sh` aggregates per target. For each target SHA, it applies
all relevant `.patch` files to the working tree, stages explicit
paths, and creates one fixup commit per target. See
`${CLAUDE_PLUGIN_ROOT}/references/apply-template.sh` for the full contract.

**Never `git add -A` or `git add .`** — explicit paths only, per
`plugins/commit/commands/commit.md:181-191` (rule line 187). This
rule applies to the patch driver too.

If the user chose "Apply patches now" (middle option), stop here.
Steps 11–12 only run for "Apply and autosquash".

For autosquash, run with `rerere` enabled. The reword fixup commits
already carry their replacement messages in their bodies (Step 8's
`apply-template.sh` pre-stages the message with an `amend! <subject>`
prefix line), so autosquash uses the body verbatim — no editor needs
to be invoked, and no shim is required:

```bash
GIT_SEQUENCE_EDITOR=: git -c rerere.enabled=true -c rerere.autoupdate=true rebase -i --autosquash "${BASELINE_SHA}"
```

`GIT_SEQUENCE_EDITOR=:` accepts the auto-generated todo list
non-interactively; autosquash strips the `amend! <subject>` prefix
from each fixup body and uses the remainder as the target's new
commit message.

If autosquash exits 0, jump to Step 12.

## Step 11: Conflict loop (rerere-safe, gates touched-first)

This loop is borrowed from `plugins/rebase/commands/rebase.md:46-67`
(Phase 4 of `/rebase`) with three tightenings. See
`${CLAUDE_PLUGIN_ROOT}/references/conflict-loop.md` for the full discussion.

**Tightening 1 — gates touched-first then full set.** After
resolving each pause, re-run only the gates relevant to *touched
files*. The full discovered gate set runs once at Step 12.

**Tightening 2 — tests are opt-in.** Default off (`TEST_CMD`
skipped). Pass `--run-tests` to include per-pick.

**Tightening 3 — track `git diff --cached` alongside unmerged
files.** `rerere.autoupdate=true` auto-resolves *and stages*
previously-seen conflicts, removing the conflict markers. Validate
both unmerged and staged paths to ensure the formatter and linter
see `rerere`'s output.

The loop:

1. Inspect both unmerged and staged files:

   ```bash
   git diff --name-only --diff-filter=U
   ```

   ```bash
   git diff --name-only --cached
   ```

2. For each file with conflict markers (`<<<<<<<`), read it and
   resolve. Prefer the incoming (fixup) side for targeted lines;
   preserve other structural changes from trunk-side context. When
   uncertain, surface the conflict via `AskUserQuestion` rather than
   guessing.

3. Stage explicit paths only:

   ```bash
   git add -- <file>
   ```

4. Run touched-file gates (skip empty buckets):

   ```bash
   ${FORMAT_CMD}
   ```

   ```bash
   ${LINT_CMD}
   ```

   ```bash
   ${TYPECHECK_CMD}
   ```

   - **Formatter** auto-applies. Re-stage modified files explicitly.
   - **Linter** with `--fix` auto-fixes; re-stage. Hard errors
     surface via `AskUserQuestion` with three options: **Edit and
     continue**, **Skip this fixup** (`git rebase --skip`), **Abort**
     (`git rebase --abort`).
   - **Type checker** never auto-modifies. Errors surface as
     linter-hard.
   - **Tests** only if `--run-tests` was passed; same triage as
     type-check.

5. Continue:

   ```bash
   git rebase --continue
   ```

6. If the next pick conflicts, loop from step 1. `rerere` replays
   prior resolutions automatically; the touched-file gates in step 4
   validate `rerere`'s output before the rebase advances.

7. Unrecoverable:

   ```bash
   git rebase --abort
   ```

   Report what failed. Remind the user the backup branch from Step
   10 exists.

## Step 12: Final verification and report

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

The final report uses post-execution counts — these are post-hoc
fact, distinct from the Orchestration Plan's pre-execution range
estimates.

Report sections:

```
Slop summary
============
Budget: <level>
Findings: <total> (<a> Tier A, <b> Tier B, <c> Tier C)
Auto-applied: <a> Tier A
Proposed and accepted: <accepted> Tier B (<declined> declined)
Advisories: <c> Tier C — see <advisory file>

Tone calibration: demoted <phrases>
Verifier: <enabled|skipped> (<scanned> commits scanned; <skipped-per-sha> skipped)

Commits: <m> → <n>
  - <k> fixups squashed (aggregated)
  - <d> commits dropped
Backup branch: <branch>-pre-deslop-<ts>

Quality gates (final)
=====================
format=<status> | lint=<status> | typecheck=<status> | tests=<status>

Patch series: .git/deslop/<ts>-<pid>/
```

**Do NOT push.** The user decides. If `--force-rewrite-pushed` was
passed, recommend `git push --force-with-lease` over `git push
--force`.

## Edge cases

| Case | Behavior |
|---|---|
| Merge commits in range + `--apply-rebase` | Refused at Step 1 (autosquash without `--rebase-merges` flattens topology). `--apply-patches` is permitted. |
| Merge commits in range + `--apply-patches` only | Permitted; patches written for review. User can rebase manually with `--rebase-merges`. |
| `--since=<ref>` not an ancestor of HEAD with `--apply-rebase` | Refused at Step 1. |
| Root commit | Warn and require `git rebase --root`. |
| Empty diff after edit | Skip the fixup; record as "no-op". |
| Already-pushed branch | See Step 2. |
| Branch is the trunk | See Step 1 halt list. |
| Detached HEAD | See Step 1 halt list. |
| Concurrent rebase in progress | See Step 1 halt list. |
| Single-commit branch + no body | Reword fixup is right; autosquash collapses cleanly. |
| `--message-only` on diff slop | Run, report skipped diff findings, only build reword fixups. |
| No conventions file and no manifest | Step 3.5 prompts user; empty buckets are skipped in Steps 11/12. |
| Worktrees | Permitted — `<trunk>..HEAD` model unaffected. |
| `.git/deslop/` collision (race or restart) | `<ts>-<pid>` directory naming guarantees uniqueness. |
| Pre-existing `--fixup!` / `--amend!` commits on branch | Detect via `git log -E --grep='^(fixup\|amend)!'`; offer to autosquash them as a precondition. |
| Non-UTF-8 commit message | Skip slop checks on the message; report warning. |
| Pre-commit hook modifies staged content during fixup | `apply.sh` aborts the affected step with the hook's stderr; user resolves and re-runs. The skill never uses `--no-verify`. |
| `.gitignore` intersection (patch ignores file the patch modifies) | `git add` errors out; `apply.sh` aborts that step with an actionable error pointing to both files. |
| Sub-agent fails / times out / parses non-JSON | Mark `verifier=skipped-for-<sha>`; fall back to Pass A. Do not crash. |
| User override `.claude/deslop.local.yml` malformed | Refuse with parser error. Do not silently fall back. |
| User override is git-tracked AND dirty | Warn at Step 5. |
| `--taxonomy=<path>` points at missing file | Refuse with path-resolution error. |
| User-overridden registry disables every signature | "No active signatures — nothing to detect." Exit 0. |
| Git < 2.32 (no `--fixup=reword:` / `--fixup=amend:`) | Detect via `git --version`. Diff fixups still work. Message rewrites become per-fixup notes requiring manual `git rebase -i`. Warn the user. |
| Live registry diverged between materialize and apply | `0000-PLAN.md` records source path + SHA-256. `apply.sh` recomputes, aborts on divergence. |
| Terminal codepage prevents emoji unicode read | Read `signatures.yml` as UTF-8 bytes; never rely on locale-default decoding. |

## What this skill does NOT cover

- The PR description on GitHub — `/pr:review-pr`'s job. Never edit
  it from this skill.
- Full rebase onto trunk — `/rebase`'s job.
- New commit creation — `/commit`'s job.
- Pushing the rewritten branch — explicit user action, never
  automatic.
- Auto-splitting multi-topic commits — flagged advisory; manual via
  `git rebase -i`.
- Auto-applying Tier C suggestions — never. Prose voice belongs to
  the author.
- Pre-commit prevention — that's a future `PostToolUse` hook (see
  below).

## Future: `PostToolUse` preventative hook (not shipped here)

The right preventative layer is a `PostToolUse` hook on `Bash`
matching `^\s*git\s+commit\b`, in the `commit` plugin
(`plugins/commit/hooks/`). It would inspect the just-created commit
message and **warn** (not block) on Tier A signals. The user can
then run `/pr:deslop --message-only`.

`PostToolUse` is correct over `PreToolUse`: blocking the agent's
tool call mid-flight is invasive UX, while warning on an
already-created commit (recoverable via `git commit --amend` or
`git reset --soft HEAD~1`) is a softer touch.

The hook is not shipped in this skill — it is reserved as a
follow-up. No plugin in this repo currently has a `hooks/`
directory; introducing the first one warrants its own change.

## Reference files

For detailed catalogs and discovery procedures, consult:

- **`${CLAUDE_PLUGIN_ROOT}/references/signatures.yml`** — versioned slop registry with
  ≥ 20 entries across Tier A/B/C; project-overridable via
  `.claude/deslop.local.yml`.
- **`${CLAUDE_PLUGIN_ROOT}/references/slop-taxonomy.md`** — Tier A/B/C catalog with FP
  guards and the consolidated false-positive table.
- **`${CLAUDE_PLUGIN_ROOT}/references/quality-gates.md`** — discovery procedure
  (read-all-files, merge-with-priority, manifest-confirmation).
- **`${CLAUDE_PLUGIN_ROOT}/references/conflict-loop.md`** — rebase pause handling with
  rerere safety and the three tightenings.
- **`${CLAUDE_PLUGIN_ROOT}/references/apply-template.sh`** — patch driver template that
  becomes per-run `apply.sh`. Idempotent via durable
  `.checkpoint/<NNNN>.done` markers; aggregates patches per target
  SHA. Reword fixups are pre-staged with an `amend! <subject>`
  prefix line in the body so autosquash uses the body verbatim
  without invoking `GIT_EDITOR`.

## Cited repo artifacts

- `plugins/pr/commands/review-pr.md:55` — "No brittle details"
  rubric; this skill extends it for commit-level rules.
- `plugins/pr/commands/review-pr.md:78` — "Never modify the PR — only
  report findings" posture; mirrored as
  `/pr:deslop`'s never-edit-PR-description rule.
- `plugins/rebase/commands/rebase.md:46-67` — Phase 4 conflict loop
  with quality gates; the model this skill borrows.
- `plugins/rebase/commands/rebase.md:9-12` — trunk detection pattern.
- `plugins/research/skills/deps/SKILL.md` — procedural skill
  archetype with frontmatter, numbered steps, decision tables, and
  `AskUserQuestion` confirmation gate.
- `plugins/tailwind/skills/spacing-audit/SKILL.md` — references-
  directory progressive-disclosure pattern.
- `plugins/commit/commands/commit.md:181-191` — Rules section
  forbidding `git add -A`, `--amend`, `--no-verify`, empty commits;
  this skill honors all of them.
