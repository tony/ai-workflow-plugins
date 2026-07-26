# github-actions

Update GitHub Actions pins across one repository or a whole fleet —
verify every target tag exists before writing it, research each upgrade
against the vendor's own release notes, land one commit per action, and
close dependabot's pull requests by citing the commit that superseded
them.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install github-actions@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/github-actions:update-action <owner/action>` | Take one named action to its current version wherever it is pinned — verify the tag, research the span, commit per repository |
| `/github-actions:update-actions` | Audit every action in scope and update the out-of-date ones, then close the dependabot PRs those commits superseded |

One action you already know is stale → `update-action`. "What's out of
date?" across a repo or a fleet → `update-actions`, which also accepts
`--audit-only` to report without writing.

Both default to the current repository and to committing on the default
branch. `--pr` branches and opens a pull request instead; `--no-push`
commits locally and stops. `update-actions` additionally takes
`--root <dir>` to sweep every repository beneath a directory and
`--owner <name>` to keep only those belonging to given accounts.

## Why not just merge dependabot's PRs

Dependabot opens one pull request per action with a generated message
and no read on what the upgrade means for your workflows. This plugin
inverts that: it researches the span between your pin and the target,
writes the rationale into a commit on the default branch, and then
closes the bot's pull request with a comment pointing at that commit.

The citation runs one way. A commit never references a dependabot pull
request — the number may not exist when the commit is written, and it
means nothing to a reader a year later. The pull request references the
commit.

## Workflow

1. **Inventory** — read `uses:` lines from each repository's default
   branch, covering `.github/workflows/` and `.github/actions/`
2. **Verify** — resolve the latest version and confirm the target tag
   actually exists before it is written anywhere
3. **Research** — collect every major release between pin and target
   with verified links, plus the breaking changes
4. **Plan gate** — scope, targets, evidence, and commit count,
   confirmed before anything is written
5. **Commit** — one per repository and action, body carrying the
   upgrade rationale and release links
6. **Close out** — watch CI, attribute failures before blaming a bump,
   close the superseded dependabot pull requests

## Pinning

Major-level floats (`@v7`) are the default: they collect patches
without a commit per patch release. Each repository's existing shape is
preserved — an exact patch pin is repinned to the float when one
exists, and a commit SHA pin keeps its shape with the trailing version
comment moved alongside the SHA.

Not every action publishes a floating major. When none exists the pin
is an exact release, and the commit body says why, so a later reader
does not "fix" it to a tag that does not resolve.

## Shared references

Both commands and the skill read the same files at runtime, so the
single-action path and the fleet audit cannot drift:

- `references/action-pinning.md` — inventory from the default branch,
  tag verification, annotated-tag dereferencing, pin granularity, and
  the per-repository gates to check before claiming an upgrade is safe
- `references/dependabot-closeout.md` — the one-way citation rule, the
  closing protocol, CI attribution, and scope discipline

## Skill

`bumping-github-actions` carries the full phase structure and triggers
on its own when a conversation turns to out-of-date actions or
dependabot's action pull requests. The commands are the explicit entry
points to the same procedure.

## Scope

Own repositories only. A fork you own is still someone else's project,
so forks are detected and skipped rather than filtered by account name.

The plugin bumps actions. Breakage that predates a bump — a repo's own
lint failures, a suite collecting no tests, toolchain rot in a dormant
project — is reported, not fixed.

## Prerequisites

- **git** — inventory reads workflow content from the default branch
- **gh** — tag verification, release lookup, CI watching, and closing
  dependabot pull requests
