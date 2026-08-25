---
name: gather
description: "Resolve and pin a corpus, inventory it, and record what was read and what was deliberately skipped, into sources.jsonl"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "AskUserQuestion", "WebFetch"]
argument-hint: "<target>... [--kind=code|prose|fleet] [--out=<dir>]"
user-invocable: true
disable-model-invocation: true
---


# /scholar:gather

Stage 1. Turn a loose target — a repository, a set of them, a book — into a
pinned, inventoried source list a later stage can cite against.

Read `../../references/citation.md` for how to pin, and
`../../references/stage-gates.md` for this stage's exit condition.

User arguments: $ARGUMENTS

## The invariant

```
GATHER NEVER WRITES INTO THE CORPUS IT READS
```

Studying a project must not dirty its checkout. Output lands under `--out`,
defaulting to `notes/ontology/<subject>/` in the current repository. The corpus
is recorded by URL and ref, not by local path.

## Context

Current repository:
`!git remote get-url origin 2>/dev/null || echo "(not a git repository)"`

Existing studies:
`!ls notes/ontology/ 2>/dev/null || echo "(none)"`

## Procedure

### 1. Resolve each target to a ref

For a git repository, prefer a release tag; fall back to a 7-character commit
reachable from trunk. Never a branch name — it moves, and every citation built
on it rots silently.

Newest tag of a repository you have not cloned:

```console
$ gh release list --repo OWNER/REPO --limit 1 --exclude-drafts --exclude-pre-releases --json tagName --jq '.[0].tagName'
```

A repository can have thousands of tags and no releases, in which case that
prints nothing. Fall back to the tags:

```console
$ git ls-remote --tags --refs --sort=-v:refname https://github.com/OWNER/REPO
```

For a local checkout, record both the remote and the exact ref:

```console
$ git rev-parse --short HEAD
```

For prose, the ref is the edition — publisher, year, and printing where the
locator scheme depends on it. A page number without an edition is not a
locator.

### 2. Inventory without reading everything

Establish the shape of the corpus cheaply. For code, the module or package
list and the size of each. For prose, the table of contents. For a fleet, the
repository list and what each one is for.

The inventory is what makes the coverage decision in step 3 an informed one
rather than a guess.

### 3. Decide scope with the user

Present the inventory via `AskUserQuestion` and settle what will be read. Most
studies should not read everything; the point is to decide deliberately rather
than to run out of attention silently.

### 4. Write sources.jsonl

One row per source, including every source deliberately not read:

```
{"source": "https://github.com/OWNER/REPO", "ref": "v2.40.0", "scope": "src/parser/", "read": true, "why": ""}
{"source": "https://github.com/OWNER/REPO", "ref": "v2.40.0", "scope": "test/", "read": false, "why": "tests name fixtures, not domain concepts"}
```

A study that does not state its coverage boundary is not honest about what it
does not know. `contest`'s completeness pass reads exactly this file.

## Rules

- Never write into the corpus. Never `git checkout`, `git clean`, or edit
  inside a target.
- Every source has a resolved ref before this stage hands off.
- Every skipped source has a reason in `why`. "Out of scope" is not a reason;
  say what it contains and why that does not bear on the vocabulary.
- Where a corpus has no stable anchors, record that the locator is a search
  string rather than a position, so `annotate` and `extract` know.

## Output

Open with a one-line hero (`✓ <subject>: <n> sources pinned, <n> skipped` or
`⚠ Blocked: <reason>`), then exactly these sections:

1. `## Pinned` — each source read, its ref, and how the ref was resolved.
2. `## Skipped` — each source not read, and why.
3. `## Shape` — the inventory that informed the scope decision.

End with an `AskUserQuestion` panel offering next steps (for example: run
extract, widen scope, stop here) — skip the panel only in plan mode.
