---
name: bumping-github-actions
description: Use when GitHub Actions pins are out of date, when dependabot has opened action-bump pull requests, when asked which workflow actions need updating, or when auditing `uses:` versions across one or many repositories.
---

# Bumping GitHub Actions

Audit `uses:` pins, research each upgrade against real release notes,
land one commit per action, and close dependabot's pull requests by
citing the commit that superseded them.

Two reference files carry the parts that must not drift between this
skill and the plugin's commands:

- `${CLAUDE_PLUGIN_ROOT}/references/action-pinning.md` — inventory,
  tag verification, annotated-tag dereferencing, pin granularity, and
  the per-repo gates to check before claiming an upgrade is safe.
- `${CLAUDE_PLUGIN_ROOT}/references/dependabot-closeout.md` — the
  one-way citation rule, the closing protocol, CI attribution, and
  scope discipline.

## Core principle

Verify the target tag exists before writing it. Everything else in this
procedure is recoverable; a pin naming a tag that does not resolve
breaks every workflow that references it, in every repo, at once.

## Scope

Own repositories only. Ownership by account name is not enough — a fork
you own is still someone else's project, and its workflows belong
upstream. Check whether the repository is a fork and skip it unless the
user says otherwise.

## Phase 1 — Inventory

Discover repositories with workflows, resolve each one's default
branch, and read every `uses:` line from that branch. Follow the
inventory section of the pinning reference, including its
word-splitting warning: a naive loop silently drops repos with more
than one workflow file and reports the fleet as clean.

Record, per pin: repository, default branch, file, action, and current
version. That table is the unit of work for the rest of the procedure.

## Phase 2 — Resolve and verify

For each distinct action, resolve the latest version, choose a target
that preserves the repository's existing pin shape, and confirm the
target tag exists. Dereference annotated tags before comparing two of
them. All four steps are in the pinning reference.

Nothing proceeds past this phase on an unverified tag.

## Phase 3 — Research each upgrade

For every distinct upgrade chain, gather the exact latest version,
every major release between the current pin and the target with a real
release URL, the breaking changes, and what the consuming workflows
must actually change. Use web search and the vendor's own release
notes; fan out one researcher per chain when there are many.

Validate every URL before it reaches a commit message:

```console
gh api repos/<owner>/<action>/releases/tags/<tag> --jq .tag_name
```

Then check the research's claims against the actual workflows, per the
gates section of the pinning reference. Research describes the action;
only the repository can confirm what applies to it.

## Orchestration Plan

Before any file is written, enter plan mode — `EnterPlanMode` in Claude
Code, `/plan` or `Shift+Tab` in Cursor, Codex, and Gemini — and present
a plan covering:

- Which repositories and actions are in scope, and which were excluded
  as forks, upstream projects, or already current.
- The target version for each action, and the evidence each target tag
  exists.
- Which upgrades carry breaking changes, and which repositories those
  changes actually reach.
- The commit granularity and where commits land: the default branch
  directly, or a branch and pull request per repository.
- How many commits this produces, and whether they will be pushed.

Present it and wait for approval. Exit plan mode before Phase 4.

If plan mode is unavailable, the phase structure still applies: finish
inventory, verification, and research, and confirm scope with the user
before writing anything.

## Phase 4 — Commit

One commit per repository and action pair. Never bundle several actions
into one commit: each bump carries its own rationale and needs its own
revert.

The body justifies the bump — what changed upstream, and what it means
for this repository — and links every major release between the old pin
and the new one. Follow the project's own commit conventions from
AGENTS.md or CLAUDE.md for the subject format.

A repository whose checkout sits on a feature branch gets a throwaway
worktree based on the remote default branch, not the local one, which
may be stale and will be rejected as a non-fast-forward after the work
is done.

Make the run resumable. Push whenever the local branch is ahead of the
remote, rather than only when the current invocation created the
commits, so a run interrupted by a network failure can be re-invoked
without hand-repair.

## Phase 5 — Verify and close out

Watch CI, attribute any failure before blaming the bump, and close the
dependabot pull requests by citing the commits. All three are in the
close-out reference.

Report what was excluded and why, along with the two findings that
explain fleet-wide drift: repositories with no dependabot
configuration, and actions pinned to a moving branch.

## Common mistakes

**Assuming every action publishes a floating major.** It does not
follow from the action being popular or well maintained.

**Comparing annotated tags by `.object.sha`.** That compares tag
objects, not commits, and makes identical tags look different.

**Auditing the working tree.** Feature-branch content gets audited
instead of the branch that actually runs.

**One commit for all of a repository's bumps.** No independent revert,
and no per-action rationale.

**A generic commit body containing a repository-specific claim.** The
claim is false for the repositories the generalization does not fit,
permanently, in their history.

**Trusting a stale baseline CI run.** Leads to reverting changes that
were never the cause.

**Citing a dependabot pull request from a commit message.** The
citation runs one way: the pull request points at the commit.
