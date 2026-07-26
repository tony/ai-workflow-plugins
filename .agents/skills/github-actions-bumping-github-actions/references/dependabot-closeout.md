# Dependabot close-out and CI attribution

Shared by the `github-actions-update-action` skill and
the `github-actions-update-actions` skill.

## The one-way rule

Our commit lands on trunk first. The dependabot PR is then closed with
a comment pointing **at** that commit. The reference never runs the
other way.

Do not name, link, or cite a dependabot PR in a commit message. The PR
number may not exist when the commit is written, it carries no meaning
for anyone reading the history later, and it inverts the direction of
the citation. Referencing an *upstream action's* own issue tracker
(`pnpm/action-setup#265`) is fine and often valuable — that is the
vendor's tracker, not dependabot.

Never merge the dependabot PR. Its commit message is the bot's, not
the researched one.

## Closing protocol

Map each open PR to the commit that superseded it by parsing the action
name from the PR title and finding the commit that bumped that action.
Comment, then close:

```console
gh pr comment <n> --repo <slug> --body "Superseded by [\`<sha12>\`](https://github.com/<slug>/commit/<sha>) on \`<trunk>\`, which bumps \`<action>\` with the release notes and migration impact recorded in the commit message."
```

```console
gh pr close <n> --repo <slug>
```

A PR for an action no longer referenced by any workflow closes as
**obsolete**, not superseded — say so plainly rather than inventing a
commit to cite.

Repository renames redirect. `gh` follows them, but a local remote may
still hold the old slug, so a PR can appear to belong to a repo that no
longer answers under that name. Resolve the canonical slug from the API
before mapping.

## Attributing CI failures

Getting this wrong in either direction is expensive: revert good work,
or ship a regression. Establish attribution before acting.

**Compare the same workflow by name.** A fleet often runs a second
workflow — dependency graph, deploy, docs — whose green run sits next
to a red one in the same list. Filtering only by branch mixes them and
reports a failing repo as passing.

**Check the age of the base run.** A green baseline from months ago
proves nothing about a change made today: floating tags moved, runner
images were rebuilt, language runtimes and ABIs shifted underneath. A
base run must be recent enough to isolate the change.

**Compare the failing step, not just the conclusion.** The same step
failing before and after means the failure predates the bump.

**When unsure, revert and observe.** Restore the workflow file
byte-for-byte and re-run. If it still fails, the cause was never the
bump — restore the bumps and correct any commit message that asserted
otherwise.

## Watching CI

For work landed directly on trunk, watch the run:

```console
gh run watch "$(gh run list --branch <trunk> --limit 1 --json databaseId --jq '.[0].databaseId')"
```

When the work goes through a pull request instead, watch its checks:

```console
gh pr checks --watch
```

## Scope discipline

Bump actions. When CI surfaces breakage that predates the change — a
repo's own lint errors, a suite that collects no tests, toolchain rot
in a long-dormant project — report it and move on. Fix it only when the
bump caused it.

Two findings are worth reporting at the end because they explain why a
fleet drifted in the first place: repos with no dependabot
configuration, which file zero PRs and rot silently, and actions pinned
to a moving branch such as `@master`, which no version comparison will
otherwise surface.
