---
name: create-issue
description: >-
  Use when filing a GitHub issue — reporting a bug, proposing a
  feature or a piece of work, or turning an audit, review finding, or
  investigation into something tracked. Reproduces and gathers
  evidence before writing prose, checks the repository's own templates
  and existing issues for a duplicate, pins every source link to a tag
  or commit, strips local paths and PII, previews the body through
  GitHub's renderer, and opens it with `gh` only after you approve the
  full title and body.
user-invocable: true
allowed-tools: ["Bash", "Read", "Write", "Grep", "Glob", "WebSearch", "WebFetch", "AskUserQuestion"]
---

# Create issue

File an issue a maintainer three years from now can act on without
asking you anything.

Argument: $ARGUMENTS — a description, a repository, a pasted finding,
or nothing.

The body follows `${CLAUDE_PLUGIN_ROOT}/references/rendered-markdown.md`
and every link in it follows
`${CLAUDE_PLUGIN_ROOT}/references/source-links.md`. Read both before
drafting.

## Core principle

Evidence before prose.

An issue is worth filing when it carries something the maintainer
cannot reconstruct: the exact command, the exact version, the line
that does it, the output that proves it. Everything else is a
paragraph asking them to do the investigation again.

## Phase 1 — Resolve the target repository

It is often not the one you are standing in. Take it from the argument
when given; otherwise resolve it from the checkout's remote:

```
gh repo view "$(git remote get-url origin)" --json nameWithOwner --jq .nameWithOwner
```

With more than one GitHub remote, list them with `git remote -v` and
ask which one the issue belongs to. Do not use a bare `gh repo view`
or `gh issue` to decide: they sort remotes upstream before origin, so
on a fork clone they answer with the upstream project. (`gh repo
set-default --view` prints to stderr and exits 0 when no default is
configured, so empty output there means "no default", not "no
repository".)

Pass `--repo OWNER/REPO` on every command from here.

## Phase 2 — Decide it belongs in a public issue

A vulnerability does not. Check the resolved repository's policy
before anything else:

```
gh repo view OWNER/REPO --json isSecurityPolicyEnabled,securityPolicyUrl
```

That covers `SECURITY.md` wherever the project keeps it — root,
`.github/`, or `docs/` — including in a repository you have not
cloned. When a policy exists and the finding is a security defect,
read it, follow its private reporting path, and stop.

Also stop and ask when the evidence cannot be sanitized — an internal
log that carries customer data does not become fileable by trimming
it.

Then classify: **defect**, **proposal**, or **task**. The kind decides
which sections the body carries.

## Phase 3 — Preflight the repository

```
gh repo view OWNER/REPO --json hasIssuesEnabled,isBlankIssuesEnabled,issueTemplates,contactLinks
```

Issues disabled means the project takes reports somewhere else — read
`contactLinks` and `CONTRIBUTING.md` and report where, rather than
filing.

That call returns templates only when they are legacy markdown. A
repository using YAML issue forms returns an empty list, so list the
directory itself:

```
gh api repos/OWNER/REPO/contents/.github/ISSUE_TEMPLATE --jq '.[].name'
```

```
gh api repos/OWNER/REPO/contents/.github/ISSUE_TEMPLATE/bug_report.yml -H 'Accept: application/vnd.github.raw'
```

Templates live on the default branch only. When several fit, ask —
their file order is a filename artifact, not the maintainer's ranking,
so never take the first one as the intended default.

A template's structure wins over the section order below. Fill it in;
do not restructure it.

Read `CONTRIBUTING.md` for anything the project asks reporters to
include.

## Phase 4 — Look for the issue that already exists

```
gh issue list --repo OWNER/REPO --state all --search "KEYWORDS in:title" --limit 50 --json number,title,state,url
```

```
gh search issues "KEYWORDS" --repo OWNER/REPO --match body --json number,title,url,state
```

Search closed issues too — a closed one is often the answer, and a
duplicate of a closed issue is a regression report, which is a
different and more useful issue.

Read the candidate before dismissing it:

```
gh issue view 123 --repo OWNER/REPO --comments
```

When one matches, say so and stop. Offer to comment on it with the new
evidence instead.

## Phase 5 — Gather the evidence

For a defect: the smallest command sequence that reproduces it, run to
confirm it actually does; the exact versions of the project, runtime,
and OS; the verbatim error; and the code that produces it, located and
pinned per the source-links reference.

For a proposal or task: what is impossible or awkward today, shown
concretely; what the project already does that is adjacent; and what
the change would touch.

For every open-source project the issue names, research its link set —
repository, homepage, docs, the changelog at the release in question,
registry page — rather than reconstructing URLs from memory.

Reproduce before you write. An unreproduced defect is filed as an
observation, and says so.

## Phase 6 — Draft

### Title

Under about 70 characters. Name the symptom, not your guess at the
cause. Backtick the symbols. No issue number, no type prefix unless
the project uses one.

### Body sections, in this order

Include only the ones you have content for; never invent another.

1. `### Summary` — what happens and who it affects, in two or three
   sentences. Always present.
2. `### Motivation` — proposals and tasks: what is impossible or
   awkward today.
3. `### Reproduction` — defects: numbered steps, one command per
   fence.
4. `### Expected` and `### Actual` — defects: two short sections, not
   a table.
5. `### Environment` — defects: versions, inside `<details>`.
6. `### Evidence` — logs, traces, and full output, inside
   `<details>`.
7. `### Proposal` — the change being suggested, when there is one.
   Nested sections for competing options; no table.
8. `### Alternatives` — only when one was genuinely weighed and
   rejected, with the reason.
9. `### References` — pinned links to code, related issues, upstream
   releases, and specs.

Start at `###`. The title is a separate field, and `##` draws a
full-width rule across the body.

Match the detail to the finding. A one-line typo report does not get
nine sections.

## Phase 7 — Sanitize, then preview

Reread the whole body for local absolute paths, hostnames, emails,
tokens, and internal URLs — including inside every pasted log. This is
a gate, not a pass.

Write the body to a scratch file outside the working tree, so nothing
lands in the user's checkout:

```
BODY=$(mktemp "${TMPDIR:-/tmp}"/gh-issue-XXXXXX.md)
```

Then render it the way GitHub will:

```
gh api --method POST /markdown -f mode=gfm -f context=OWNER/REPO -f text="$(cat "$BODY")"
```

Literal `**` or backticks in that output mean a `<details>` block lost
its blank line after `</summary>`. A `<br>` inside a prose paragraph
means the body is hard-wrapped. Fix and re-render.

## Phase 8 — Present, then file

Show the full title and body. Then offer, via `AskUserQuestion`:
file it, print the body only, revise a named section, or drop it.

Labels are optional and validated first — an unknown label aborts the
create and files nothing:

```
gh label list --repo OWNER/REPO --limit 200 --json name,description
```

File from a file, never from an inline `--body`, so fences, HTML, and
`$` survive shell quoting:

```
gh issue create --repo OWNER/REPO --title "TITLE" --body-file "$BODY" --label bug
```

Remove the scratch file on the way out, whichever branch the user
picked — filed, printed, or dropped:

```
rm -f "$BODY"
```

Return the issue URL. Then offer the next step: open it, add a
comment, or start a branch for it.

## Rules

- Read-only until the filing gate. No commits, no pushes, no edits to
  existing issues.
- Never file without showing the full title and body first.
- Never invent a version, an error string, a line number, or a link.
  Unverified goes in as unverified, or comes out.
- Never `@mention` anyone in a generated body. Mentions send mail.
- Language-agnostic: discover how to build, run, and test from
  `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md`.

## Common mistakes

**Filing the investigation instead of the finding.** The maintainer
needs what reproduces it, not the sequence of hypotheses that led
there.

**A bare `gh issue create` in a non-interactive shell.** It cannot
prompt, so it exits with `must provide --title and --body when not
running interactively` and files nothing. Always pass `--title` plus
`--body-file`.

**Combining `--template` with a body.** `gh` rejects it outright. To
honor a template non-interactively, read it, fill it in, and pass the
result as the body.

**Trusting `issueTemplates` to mean "no templates".** It returns empty
for every repository that uses YAML issue forms.

**Filing a duplicate because only open issues were searched.** The
default is `--state open`, capped at 30.

**Pasting a full log because it was easier.** Fold it into
`<details>`, and read it for secrets first.

**Reporting a symptom with no version.** It ages into an issue nobody
can close, because nobody can tell whether it still happens.
