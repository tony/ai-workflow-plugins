---
name: verify
description: "Re-check a finished study against the corpus it cites — refs that moved, files that vanished, quotations that no longer match, numbers that changed"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "WebFetch"]
argument-hint: "[<study-dir>] [--refresh-metrics]"
user-invocable: true
disable-model-invocation: true
---


# /scholar:verify

A study is a set of claims about a corpus that keeps moving. Without this, it
rots into confident falsehood: every link still resolves, every number still
reads as measured, and none of it is true any more.

Read `../../references/citation.md` for what a citation was required to carry.

User arguments: $ARGUMENTS

## Procedure

### 1. Walk every citation

For each `cites` entry in `terms.jsonl`, confirm three things separately,
because they fail differently:

The ref still exists. A tag can be moved or deleted, and a deleted tag makes
every URL built on it a 404 rather than a wrong answer.

The file still exists at that path on that ref.

```console
$ curl -s -o /dev/null -w '%{http_code}\n' -L '<url>'
```

The quoted text still appears at the recorded locator. This is the one that
fails silently: a file that grew by ten lines leaves a line-anchor citation
resolving to unrelated code while still returning 200.

### 2. Re-run the measurements

With `--refresh-metrics`, run every command recorded in `evidence/metrics.md`
and diff the output against what was recorded. A number that changed is not
automatically wrong — the corpus moved — but it is no longer evidence for the
claim it was cited under.

### 3. Report by failure mode

Four categories, because the remedy differs:

- **Moved** — the ref advanced or the tag was retargeted. Re-pin.
- **Vanished** — the file or ref is gone. The claim needs a new source or it
  needs retracting.
- **Misquoted** — the locator resolves but the text there is not what was
  quoted. This is the dangerous one, and it is why quotations are recorded
  rather than just links.
- **Changed** — a measurement produced a different number.

## Rules

- Do not edit a claim in place. Anything that overturns a standing claim goes
  to `/scholar:revise`, which records what was believed and why it failed.
- Report a broken citation; do not repair it by finding a new source that
  happens to support the same claim. That is fitting evidence to a conclusion.
- A citation that cannot be checked — a source now behind a paywall, a deleted
  repository — is reported as uncheckable, not as passing.

## Output

Open with a one-line hero (`✓ <n> citations checked, <n> stale` or
`⚠ <n> misquoted`), then exactly these sections:

1. `## Moved` — each citation whose ref advanced, with the new ref.
2. `## Vanished` — each source that is gone.
3. `## Misquoted` — each locator whose text no longer matches, with both texts.
4. `## Changed` — each measurement that produced a different number, with both.

End with an `AskUserQuestion` panel offering next steps (for example: revise
the overturned claims, re-pin the moved ones, stop here) — skip the panel only
in plan mode.
