# terraform

Move [Terraform](https://developer.hashicorp.com/terraform) and
[OpenTofu](https://opentofu.org/) versions through a repository whose
layout you have not seen before — find the root modules by signal
rather than by convention, move every declaration of a version
together because Terraform requires all of them to be satisfied at
once, and refresh each lock file without quietly narrowing the
platforms it covers.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install terraform@ai-workflow-plugins
```

## Commands

| Command | Description |
|---------|-------------|
| `/terraform:bump-provider <provider> [version]` | Move a provider across every module that declares it, then refresh the affected lock files |
| `/terraform:bump-terraform [version]` | Move the CLI version across every module and every pin site outside the configuration |
| `/terraform:refresh-lock` | Re-resolve providers within the constraints already written, in every root module |

With no version, each bump targets the latest stable release and
confirms it before writing it anywhere. `--audit-only` reports the
predicted work and writes nothing. `--root-module <dir>` limits a run
to named root modules instead of all of them. `--no-commit` leaves the
result in the working tree; `--no-lock` skips the lock refresh.

The `bumping-terraform` skill carries the same procedure and runs
without a slash command, for when the request arrives as "the providers
here are ancient" rather than as a command.

## Why this isn't just editing a version string

**A repository usually has more than one root module.** Each one owns
its own `.terraform.lock.hcl` and needs its own `init`. Nothing in the
directory layout says which directories those are — `terraform/`,
`infra/`, and `environments/` are conventions somebody made up — so the
plugin classifies by signal: a backend or cloud block, or a committed
lock file. A run that assumes one root module refreshes one lock file
and reports success while the rest stay exactly where they were, and
the drift stays invisible until somebody applies from another
directory.

**Constraints combine across every module, so a partial edit is worse
than no edit.** Terraform considers a root module's constraints and
every child module's constraints equal and proceeds only if all are
met. Raise the root to `~> 6.57.0` while a child module still says
`~> 6.56.0` and the configuration either refuses to initialise or
resolves to something neither file names — while the diff claims a
version that is not in use. Every declaration moves in one commit, or
none does.

**Selecting a new version narrows the lock file to one platform.**
`h1:` hashes are per-platform, and teams that need several use
`terraform providers lock -platform=...` to record them. Re-running
`-upgrade` against an already-selected version keeps that set; selecting
a *different* version does not. The coverage disappears with no warning
and a diff that looks like an ordinary version change, and the next
`init` on another platform rewrites the file — which fails under
`-lockfile=readonly` or any CI step asserting a clean tree. The lock
file records no platform *names*, only opaque per-platform hashes, so
the plugin counts them per provider before and after the run and treats
a drop as a stop signal rather than guessing a list to restore.

**The operator already in the file is a decision, not noise.**
`~> 6.56` already admits `6.57.0`, so the whole change is a lock
refresh. `>= 6.0` already admits everything in the major, and
rewriting it as `~> 6.57.0` narrows what the module accepts — a policy
change wearing a version bump's clothing. HashiCorp's own guidance is
that reusable modules should carry floors and let the root module set
the ceiling, so a `>=` in a shared module is correct rather than drift.

**The CLI is pinned in files that are not Terraform files.**
`.terraform-version`, `.tool-versions`, `mise.toml`, a
`setup-terraform` step, a container image tag. They drift apart
quietly: the configuration says one version, the version manager
installs another, CI installs a third, and whichever runs first decides
what "clean" means. An exact `required_version` is a hard gate — a
module pinned `= 1.14.5` refuses to initialise under 1.15.8 — so root
modules that disagree are root modules that cannot all be run from one
machine.

**Searching the repository naively edits files that get deleted.**
`.terraform/modules/` holds full copies of every module source,
`versions.tf` and all, and they match every pattern a real module
matches. They are gitignored, so `rg` skips them and `find`, `grep -r`,
and `git grep` on an unignored path do not. An edit there reports a
bump that the next `init` erases.

**OpenTofu reads `.tofu` files in preference to same-named `.tf`
files.** A repository can carry a `versions.tf` that the tool never
loads, where an edit changes nothing and `init` reports no drift.

## Components

| Path | Purpose |
|------|---------|
| `commands/bump-provider.md` | Move one provider across every module that declares it |
| `commands/bump-terraform.md` | Move the CLI version across configuration and non-configuration pin sites |
| `commands/refresh-lock.md` | Re-resolve within existing constraints, every root module |
| `skills/bumping-terraform/SKILL.md` | The shared phase structure, model-invocable without a slash command |
| `references/layout-discovery.md` | Classifying root and child modules by signal, the `.terraform/` cache trap, `.tofu` shadowing, Terragrunt and stacks, and what to ask about |
| `references/pin-sites.md` | Every file a provider or CLI version is pinned in, how constraints combine, operator preservation, and registry lookups |
| `references/lock-and-init.md` | Per-root-module `init`, `-backend=false`, the platform-narrowing trap, blocked resolvers, and verification gates |

## Prerequisites

- `git`, and a repository with tracked Terraform or OpenTofu files
- A `terraform` or `tofu` binary on `PATH` for lock refreshes; the
  plugin detects which drives the repository and resolves versions
  against that tool's registry
- Network access to the provider registry, or to whichever private
  registry the source addresses name
- No cloud credentials — lock refreshes run with `-backend=false`
- The project's own quality-check commands, as its `AGENTS.md` /
  `CLAUDE.md` or CI workflow defines them; the plugin reads them rather
  than assuming a toolchain
