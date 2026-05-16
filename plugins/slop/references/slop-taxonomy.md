# Slop Taxonomy

> **Lockstep note**: this catalog is a v1 byte-for-byte duplicate of
> `plugins/pr/skills/deslop/references/slop-taxonomy.md`. Both
> `/pr:deslop` and `/slop:scan` read the matching signature registry,
> and both must describe the tiers identically. When you change one
> file, change the other in the same PR. v1.1 will extract this
> document to a shared location.

This catalog mirrors `signatures.yml` for human reading. Each row maps
to one signature `id` in the registry. The registry is the source of
truth for detection (`pattern`, `kind`, `target`) — this document
explains *why* each signal is in its tier and how the false-positive
guards work.

The framing is intentional: **slop is a workflow label, not proof the
text is wrong**. Tier governs auto-apply; confidence and `fp-guard`
govern *whether* a finding lands in the proposal.

---

## Tier A — auto-apply (deterministic, near-zero FP)

These signatures auto-apply during `--apply-patches` without
per-finding confirmation. They are the only signatures the skill will
modify without explicit user assent on each occurrence.

| Signature | Action | Why Tier A |
|---|---|---|
| `ai-slop.signatures` | remove | Exact-string match on AI-tool footers (`Generated with Claude`, `🤖`, etc.); these phrases are never legitimate in commit bodies. |
| `ai-slop.emoji-in-commit-subject` | remove | Unicode range match; emoji in subjects break terminal rendering and `git log` formatting. Project-overridable for gitmoji users via `.claude/slop.local.yml`. |
| `brittle.commit-message-markdown-leak` | rewrite | Subject opens with markdown syntax (`**bold**`, `# heading`, `- bullet`, `[link](url)`); breaks `git log --oneline` and shell pagers. |
| `low-value.todo-noise` | remove | Net-new `TODO: revisit` / `FIXME: later` etc. with no owner. The pattern requires the literal noise phrasings; deliberately scoped TODOs with tickets pass. |

---

## Tier B — suggest with high confidence (~5% FPR, user-confirmed)

These signatures appear in the proposal with one-by-one confirmation.
The user can accept or decline each finding. The `fp-guard` notes
explain when the rule is suppressed automatically.

| Signature | Action | False-positive guard |
|---|---|---|
| `brittle.line-numbers` | rewrite | Skip inside fenced quoted-output blocks (compiler errors, stack traces are verbatim fixtures). |
| `brittle.counts` | rewrite | Skip inside `CHANGELOG`, `CHANGES`, release-notes contexts where exact counts are first-class. |
| `brittle.sha-in-message` | rewrite | Whitelist trailers (`Fixes:`, `Reverts:`, `Co-Authored-By:`, `See-also:`) — SHAs in trailer position are valid. |
| `verbose.restated-subject-in-body` | rewrite | LCS similarity between subject and `why:` line ≥ 0.85 — only fires when the body genuinely restates the subject. |
| `verbose.what-bullets-mirror-diff` | rewrite | Bullets each name a single file/function in the diff; bullets that describe behavior (verbs, not symbols) pass. |
| `low-value.dead-future-code` | ask | Approximated via `git grep -c <symbol>` returning 1 — only fires when the new symbol has no caller. |
| `low-value.formatting-only-commit` | ask | `git diff --check` confirms whitespace-only; skip when commit subject is `style:` or `chore(format)`. |
| `low-value.log-debris` | ask | Skip in CLI/script paths (`*-cli.*`, `*main.*`, `scripts/`, paths containing `debug`) — those legitimately write to stdout. |
| `ai-slop.co-authored-by-ai` | remove | Demote to advisory if any commit in the last 50 trunk commits used `Co-Authored-By:` legitimately (project pair-programming convention). |
| `hardcoded.test-runner` | rewrite | Suppress when the matching manifest is present (e.g., `package.json` for `npm test`). |
| `hardcoded.os-paths` | rewrite | Skip in test fixtures and example documentation. |
| `branch-internal.rename-narrative` | rewrite | Skip when old symbol appears in trunk before branch point. Skip in `CHANGES` / `CHANGELOG` / `MIGRATION` / `UPGRADING` / `*deprecation*` files. |

---

## Tier C — advisory only (high FPR, never auto-applied)

These signatures appear in the report but are never proposed for
auto-apply. Subject to tone calibration: phrases that the project's
own trunk history uses regularly are demoted to summary-only.

| Signature | Action | Why Tier C |
|---|---|---|
| `ai-slop.flagship-phrases` | ignore | "comprehensive", "robust", "best practices" — legitimate words; flagging them is judgment, not truth. Tone-calibrated against the last 50 trunk commits. |
| `verbose.docstring-exceeds-body` | ask | May be warranted for public API surfaces. |
| `verbose.defensive-wrapping` | ask | May be load-bearing — defensive coding around third-party calls is legitimate. |
| `structure.multi-topic-commit` | ask | Splitting a commit is a creative act; the skill flags but never auto-splits. |
| `brittle.dates` | rewrite | "As of 2026" rots, but dated docs may intentionally pin a moment in time. |

---

## Consolidated false-positive table

When applying any rule, also apply these whole-document suppressions:

| Pattern | Suppress when |
|---|---|
| Counts | In `CHANGELOG` / `CHANGES` / release notes / benchmark reports / measured-performance claims. |
| SHAs | In `Fixes:` / `Reverts:` / `Co-Authored-By:` / `See-also:` trailers, submodule references, lockfiles. |
| Line numbers | In copied stack traces, compiler output, test fixtures inside fenced code blocks. |
| Debug calls | In tests asserting logging/debugging behavior, in CLI tool code paths, in `scripts/`. |
| Tone words | Tier C signals at ≥ 3 occurrences in the last 50 trunk commits — demoted to summary-only. |
| Hardcoded test runner | When the matching manifest exists (`pyproject.toml` → `pytest` may be the actual command). |
| Rename narrative | Symbol existed in a published release (found in `git log` before branch point), OR file is `CHANGES` / `CHANGELOG` / migration / deprecation context. |

---

## Branch-internal narrative bleed

The `branch-internal.*` signature family detects within-branch tactical narrative leaking into shipped artifacts. See `AGENTS.md` § *Shipped vs. Branch-Internal Narrative* for the principle, the Published-Release Test diagnostic, and the cleanup-in-hindsight protocol.

**Worked example** — the discriminator is whether the named symbol or behavior existed in a published release:

| Bleed (flag) | Not bleed (keep) |
|---|---|
| `Renamed from test_foo_old` in an unmerged-branch test docstring | `Deprecated: OldClass was renamed to NewClass in v2.0` (`OldClass` shipped) |
| `### Fixes` entry for a regression the branch itself introduced | `### Fixes` entry for a bug present in the most recent released version |
| `no longer raises spuriously on resize-grow` (the raise never shipped) | `no longer hangs on large datasets` (the hang shipped in v0.4 and earlier) |

---

## How tiers interact with `--budget`

The budget setting (Step 7 of the skill) caps how many findings per
tier enter the *proposal*:

| Budget | Tier A | Tier B | Tier C |
|---|---|---|---|
| `strict` | auto-apply all | none in proposal (all advisory) | none (silently skipped) |
| `default` | auto-apply all | up to 5 in proposal, rest advisory | up to 10 advisory |
| `lax` | auto-apply all | up to 10 in proposal | unlimited advisory |

Findings beyond the budget remain visible in the report's
`0005-advisory.md` artifact.

---

## Project overrides

Projects override the registry via `.claude/slop.local.yml`:

```yaml
version: 1

replace:
  - id: ai-slop.flagship-phrases
    pattern: '(?i)\b(custom phrase 1|custom phrase 2)\b'

append:
  - id: project.no-bullet-headings
    tier: A
    confidence: high
    action: rewrite
    kind: regex
    target: [message-body]
    pattern: '^\s*\*\s+\*\*'
    rationale: This project disallows bold headings inside markdown bullets.

delete:
  - low-value.formatting-only-commit
```

`replace`, `append`, `delete` are mutually disjoint per id. Declaring
the same id under more than one key produces a parser error at load
time (Step 5 of the skill).

---

## What this taxonomy is NOT

It is not a style guide. It does not prescribe voice, brevity, or
formatting *outside* commit messages and code diffs. It does not
attempt to detect "bad code" in any general sense — only specific,
recoverable noise patterns that survive review fatigue.

It is also not a measure of writer skill. A commit may match several
Tier C signatures and still be excellent prose; the calibration step
demotes those signals when the project's voice already accepts them.
