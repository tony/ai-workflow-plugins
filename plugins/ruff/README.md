# ruff

Move one repository or a whole fleet onto a new [ruff](https://docs.astral.sh/ruff/) release — work out which rules the release can actually fire against each repository's own `select` list, gate on the resolver being able to see the version at all, then land one reviewed commit per rule with the upstream rule documentation cited.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install ruff@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/ruff:bump [version]` | Raise the ruff floor across the repositories in scope and absorb what the release surfaces, one commit per rule |

With no version, it targets the latest stable release. It defaults to the current repository, working on a branch in a throwaway worktree and opening a pull request.

`--root <dir>` sweeps every repository beneath a directory, `--repo` names individual ones, and `--owner <name>` keeps only those belonging to given accounts. `--audit-only` reports the predicted work and writes nothing. `--adopt-defaults` carries through the default-rule-set change described below rather than only measuring it. `--no-pr` commits and pushes without opening a pull request; `--no-changelog` skips the changelog entry.

## Why this isn't just `ruff check --fix`

Running the autofixer is the easy five percent. The parts that go wrong are the ones around it.

**The headline change is usually not the change that affects you.** Ruff is pre-1.0 and ships breaking changes in minor releases, but an explicit `[tool.ruff.lint] select` *replaces* the default rule set rather than extending it — so a release that dramatically expands the defaults produces no new diagnostics for most repositories, while a quietly stabilized preview rule inside a prefix you already select is what actually fires. The command predicts the diagnostics per repository by intersecting the release with that repository's own configuration, and treats a diagnostic it did not predict as a signal that it misread something rather than as a cue to apply the fix.

**Producing no diagnostics is not the same as having no consequence.** That same `select` means the repository is now silently opted out of the baseline the vendor curated and recommends — invisibly, permanently, and a little further at every future release. The command measures what adopting the default set would actually cost, per repository and per rule, and surfaces it as a decision. It also refuses the tempting shortcut: a curated default set takes a *subset* of each linter, so widening `select` to whole linter prefixes enables far more than the vendor recommends. Measured on real repositories, the prefix shortcut produced 50-100x more findings than the exact default set.

**Formatter scope changes dwarf lint fixes.** When a release brings a new *file type* into the formatter's scope, it rewrites files no formatter in that repository has ever touched. That churn needs to be isolated in its own commit and labelled as mechanical, or review stalls on a diff nobody can read.

**The version is often invisible to the resolver.** A supply-chain cooldown that hides releases younger than a threshold, a lagging mirror, a transitive cap — the package index shows the version plainly while the resolver insists there is no such release. The command diagnoses which layer is blocking before working around it, and when a temporary exemption is genuinely warranted it lands as its own revertible commit, annotated where it lives, and surfaced as a pre-merge blocker on the pull request. A cooldown exemption that gets merged is a permanent hole in a supply-chain guard traded for a few hours of convenience.

**Pins drift across files.** The same tool is routinely pinned in project metadata, a requirements file, and a pre-commit configuration, and they disagree. Pre-commit is the most commonly missed: the project metadata says the new version, pre-commit keeps running the old one, and the two disagree about what "clean" means until it surfaces as a mystery failure on somebody else's pull request.

**Not every fix is cosmetic.** Rules that touch exception handling, logging, the iterator protocol, or return types exist because the current code is subtly wrong, and satisfying them changes what the program does. Those need the behavior delta stated and the tests re-run, not batched in with a hundred import reorderings.

## Components

| Path | Purpose |
|------|---------|
| `commands/bump.md` | The command |
| `references/release-triage.md` | Sorting a release into the five buckets that matter, intersecting it with a repository's configuration, and grading each fix by how much care it needs |
| `references/pin-sites-and-gating.md` | Every file a version can be pinned in, and diagnosing and gating a resolver that cannot see the release |
| `references/default-rule-set.md` | Measuring what a newly curated default rule set would cost, the three config shapes and why two are wrong, and curating what adoption surfaces |

## Prerequisites

- `git`, and a git remote you can push to
- The GitHub CLI, authenticated, for opening pull requests and watching CI
- The project's own resolver and quality-check commands, as its `AGENTS.md`/`CLAUDE.md` or CI workflow defines them — the command reads them rather than assuming a toolchain
