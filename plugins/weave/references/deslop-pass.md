# Weave deslop pass — single-artifact prose polish

A reusable polish step for `/weave:*` commands that produce a synthesised
prose artifact. Scrubs AI-slop signatures (flagship phrases, hedging,
restated subjects, fragile counts/line numbers, AI footers) from one
markdown file in `$SESSION_DIR` before the user sees the synthesis.

Distinct from `/pr:deslop` (mutates git history via patch series + autosquash)
and `/slop:scan` (mutates working-tree files via forward-going atomic
commits). Weave deslop edits **one** file, **once**, in `$SESSION_DIR`.
The repo guard never triggers — no project-tree changes occur.

---

## Caller contract

The caller (one of the 6 prose weave commands) sets these inputs:

- `ARTIFACT_PATH` — absolute path to the markdown file to clean.
  Always inside `$SESSION_DIR`.
- `SESSION_DIR` — the run's session directory (already exists).
- `BASELINE_SHA` — trunk SHA the caller's repo guard locked, used for
  tone calibration.
- `DESLOP_MODE` — one of `default`, `quiet`, `verbose`. Defaults to
  `default`. Set from `--quiet-deslop` / `--verbose-deslop` flags.
- `NO_SEMANTIC` — boolean. Set when `--no-semantic` was passed.

The caller is responsible for honouring `--no-deslop`: if set, do **not**
invoke this reference at all. Skip cleanly with no banner, no sibling
file, no summary block.

---

## Step 1 — Resolve the registry

The slop taxonomy is owned by the `pr` plugin. Weave never ships a copy.
Resolve at runtime in this order:

1. `${CLAUDE_PLUGIN_ROOT}/../pr/references/signatures.yml`
2. `${CLAUDE_PLUGIN_ROOT}/../slop/references/signatures.yml`
3. If neither exists, emit one line and return:

   ```
   Skipping deslop (registry not found — install pr or slop plugin)
   ```

   The weave run continues; the synthesis is presented unchanged. Deslop
   is non-blocking by design.

Apply the project overlay `.claude/deslop.local.yml` if present (same
`replace:` / `append:` / `delete:` semantics as `/pr:deslop`, see
`plugins/pr/commands/deslop.md:285-310`). Hash the resolved registry
(sha256) for the audit record.

---

## Step 2 — Tone calibration

Mirror `plugins/pr/commands/deslop.md:254-275`. Read the last 50 commit
messages on the locked baseline:

```bash
git log -n 50 --format='%B%n--END--' "${BASELINE_SHA}"
```

Build a frequency map of Tier C signal phrases. Demote any phrase with
≥3 occurrences from Tier C-active to advisory-only. Trunk's accepted
voice is the authority — never HEAD.

If `BASELINE_SHA` is unset (caller did not lock one), skip calibration
silently. All Tier C signatures stay active.

---

## Step 3 — Detect (two-pass hybrid, single-file scope)

### Pass A — Regex (always runs)

Apply registry signatures whose `target` contains `file` or
`message-body`. The artifact is a single long body for this purpose.
Skip signatures with `target: diff` or `target: message-subject` —
those concern commits, not prose.

Tier A and Tier B candidates are produced. Tier C is never auto-applied;
Tier C matches are recorded for the summary only.

### Pass B — Semantic verifier (skip if `NO_SEMANTIC`)

Dispatch **one** `Task` sub-agent (not per-finding, not per-paragraph —
the artifact is one file). Sub-agent contract:

- Allowed tools: `Read`, `Grep`, `Glob`.
- Disallowed: `Bash`, `Write`, `Edit`, `Task`.

The prompt receives the artifact text, the registry filtered to
`kind: semantic`, and the Step 2 tone calibration. The
**anti-slop-on-slop constraint** from `plugins/pr/commands/deslop.md:346-353`
applies verbatim:

> Do not introduce slop in your suggested replacements. Do not use
> phrases listed in the registry. Do not narrate your changes ("I
> tightened…"). Replacement text should be concrete and shorter than
> the original where possible.

Parse resiliently: strip markdown fences, extract the first balanced
`[ … ]`, parse JSON. On failure, mark `verifier=skipped` and use Pass A
findings only. Never crash the run.

If `Task` is unavailable, set `verifier=skipped` and continue.

---

## Step 4 — Decide

For each finding produced by Step 3:

- **Tier A** — auto-apply silently. The summary block discloses the
  category and phrase pair.
- **Tier B** — count the candidates.
  - Exactly 1: auto-apply with phrase-pair disclosure in the summary.
  - 2 or more: present **one** batched `AskUserQuestion` with up to 4
    options ("apply both", "apply [a] only", "apply [b] only", "skip
    both"). Per-finding interrogation is wrong here — the artifact is
    one prose blob, not a series of commits.
- **Tier C** — advisory only. List in the summary; never edit.

---

## Step 5 — Rewrite (single-file edit)

1. Copy the original to a sibling rollback file with a stable name:

   ```
   cp "$ARTIFACT_PATH" "${ARTIFACT_PATH%.md}.pre-deslop.md"
   ```

   Stable filename — no timestamp suffix — so the user can `diff` with
   one tab-complete.

2. Apply each accepted edit via the `Edit` tool against `ARTIFACT_PATH`.

3. **Sanity guard.** Compute word-count delta:

   - Hard abort: if the desloped artifact removed ≥30% of the original
     word count, restore from the sibling and surface:

     ```
     Held back: deslop would have removed N% of the artifact (>30% threshold).
     Original preserved at <sibling path>.
     ```

     The synthesis is presented unchanged.

   - Suspect-edit: if any **single** finding's edit would have removed
     ≥15% of the original, demote that finding to advisory. The other
     findings still apply. The summary block opens with `(!)` and lists
     the held-back finding under a `!` glyph. The held trim is written
     to `${SESSION_DIR}/$(basename "${ARTIFACT_PATH%.md}")-deslop-held.md`
     for the user to inspect.

---

## Step 6 — Report

Write `${SESSION_DIR}/deslop-report.md` with:

- Resolved registry path + sha256
- Tier A applied (count + signature ids)
- Tier B accepted, declined (counts; phrase pairs)
- Tier C advisories (list)
- Word-count delta (before → after)
- Path to `<artifact>.pre-deslop.md` sibling
- Verifier status (`enabled` | `skipped` | `skipped-for-cause`)

Emit the terminal summary block per `DESLOP_MODE`:

### `default` (≤ 8 lines, no banner, no tier letters)

```
Desloped synthesis  ·  -84 words  ·  3 trims, 1 kept-as-is
  • flagship-phrases   "comprehensive solution" → (removed, 2x)
  • restated-subject   trimmed 1 paragraph that paraphrased the question
  • line-numbers       "see line 142" → "see the resolve_trunk helper"
  ~ hedging            kept "may", "likely" (load-bearing, advisory)
Original preserved at <sibling path>
```

`•` = applied, `~` = held as advisory. Word delta is the trust anchor.
Phrase pairs are the diff at the only granularity that matters for slop
edits.

### `quiet` (1 line)

```
Desloped synthesis (-84 words, 3 trims). Original: <sibling path>
```

Tier B confirms still happen — quiet does not mean non-consenting.

### `verbose` (≤ 16 lines)

Adds `tier=A|B|C`, `signature_id`, and `confidence` per finding. Adds
Tier C phrases that were demoted by tone calibration with their trunk
counts. Caps at 16 lines; overflow goes to `deslop-report.md` with a
`+N more — see deslop-report.md` line.

### Suspect-edit banner

When the suspect-edit sentinel fires:

```
Desloped synthesis  ·  -84 words  ·  2 trims, 1 held back  (!)
  • flagship-phrases   "comprehensive solution" → (removed, 2x)
  ! restated-subject   would have removed 312 words — held as advisory
Review held trim:  <held-trim path>
Original preserved at <sibling path>
```

### No-op

If Steps 3–5 produced zero applied edits, replace the in-progress line
with one line and emit no block:

```
Synthesis already clean (no deslop edits applied)
```

---

## Inline transition

Before Step 1 starts, the caller prints:

```
Polishing synthesis (deslop pass)…
```

This single line is replaced in place by the summary block (or the
no-op line) when Step 6 finishes.

---

## Failure modes

| Mode | Behaviour |
|---|---|
| Registry missing | One-line skip; run continues unchanged. |
| Verifier fails to parse | Mark `verifier=skipped`; fall back to Pass A. |
| `Task` unavailable | Mark `verifier=skipped`; Pass A only. |
| Hard abort triggered | Restore from sibling; surface the held-back banner. |
| Sibling write fails | Refuse to edit `ARTIFACT_PATH`; surface a one-line error and continue with the original synthesis. |
| `Edit` tool denied | Skip that finding; record as `declined` in `deslop-report.md`. |
