# package-updater

Update dependencies and toolchain pins across one repository or a whole
fleet. Check the supply-chain cooldown before calling anything current,
research each move against the vendor's own release notes, and land the
toolchain, the named bumps, the bulk lockfile refresh and their fallout
as separate commits.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install package-updater@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/package-updater:update` | Find everything outdated in scope and bring it current, in commit order |
| `/package-updater:update-package <name>` | Take one named package to a target version everywhere it is pinned |
| `/package-updater:update-toolchain [tool]` | Move `.tool-versions`, `.nvmrc`, `packageManager` and `engines`, one tool per commit |

"What's out of date?" → `update`, which also takes `--audit-only` to
report without writing. One package you already know is stale →
`update-package`. A runtime or CLI tool → `update-toolchain`.

All three default to the current repository and to committing on the
default branch. `--branch <name>` works on a branch, `--pr` opens a pull
request from it, `--no-push` commits locally and stops. `update` and
`update-toolchain` additionally take `--root <dir>` to sweep every
repository beneath a directory and `--owner <name>` to keep only those
belonging to given accounts.

`update --issue github|linear` files the audit before the work starts:
create the issue or card listing what is outstanding, derive the branch
name from it, then work on that branch.

## The four commit tracks

The plugin's central claim is that a dependency commit's value is its
reasoning, and reasoning does not survive bundling. So the work splits:

1. **Toolchain and runtime** — one tool per commit, even when one edit
   to `.tool-versions` moves three. Every release in the span is linked,
   because the intermediate ones are where regressions hide.
2. **Package manager and engines** — `packageManager` and `engines` pin
   the toolchain despite living in a manifest, so they never ride along
   with a dependency bump.
3. **Named package bumps** — one per package, or per release train when
   the body can say why they are coupled. `why:` then `what:`, with
   verified links.
4. **Bulk lockfile refresh** — everything routine, in one commit, with
   an **empty body**. The lockfile diff already says what moved, and a
   generated list of package names buries the commits that carry real
   reasoning.

Fallout lands after, as its own commit: a `biome.jsonc` schema bump, a
snapshot regeneration, a framework migration.

## Supply-chain cooldown

A cooldown makes the resolver ignore releases younger than a threshold.
The plugin checks for one before reporting anything as current, because
a gated release looks identical to no release at all.

The keys are not interchangeable: uv reads `exclude-newer` as a
duration, pnpm reads `minimumReleaseAge` in **minutes** from
`pnpm-workspace.yaml`, and npm reads `min-release-age` in **days** from
`.npmrc` — a key pnpm ignores entirely.

Waiting out the window is the default. An exemption is narrow,
annotated, committed alone, and reverted when the block lapses.

## What one discovery tool misses

`ncu` reads `package.json`, so a `pnpm-workspace.yaml` catalog entry, an
`overrides` block, or a package held in `.ncurc` never appears in its
report. A clean run is not a current tree. The plugin checks those by
hand and reports holds that carry no recorded reason, which is how a
deliberate pin becomes indistinguishable from neglect.

## What this plugin does not do

Three dependency classes belong to sibling plugins, which own the
research that makes them safe. This plugin reports them as findings and
names the command:

- GitHub Actions `uses:` pins → `/github-actions:update-actions`
- ruff's floor and the rule fallout it produces → `/ruff:bump`
- Terraform versions, providers and lock files → `/terraform:bump-provider`

## Components

**Commands** — `update`, `update-package`, `update-toolchain`.

**Skill** — `updating-packages`, the phase structure the commands share:
inventory, discovery, research, plan gate, land in order, verify,
report.

**References** — `ecosystems.md` (detection, discovery and apply
commands, cooldown configuration), `commit-conventions.md` (subject
grammar, body anatomy, the empty-body rule), `upstream-links.md` (which
URLs each tool's bump cites), `follow-ups.md` (which bumps need a second
commit, and how to declare a knowingly-red intermediate).

## Prerequisites

`git`, and whichever ecosystem tooling the repositories actually use —
`uv`, `pnpm`, `ncu`, `npm`, `cargo`, `go`, `mise`. The plugin detects
what is present rather than assuming a stack. `gh` is needed for issue
creation and for verifying release URLs on GitHub.
