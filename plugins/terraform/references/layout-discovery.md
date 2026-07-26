# Finding the modules, and knowing which kind they are

Shared by `/terraform:bump-provider`, `/terraform:bump-terraform`, and
`/terraform:refresh-lock`. Read before deciding what is in scope.

Terraform imposes no directory convention. A repository may keep one
root module at its top level, one in a subdirectory, one per
environment, a `modules/` tree that is never applied directly, or any
mixture. Nothing in the layout announces which is which, so classify by
signal and ask when the signals do not settle it.

## Search tracked files only

`terraform init` writes a cache to `.terraform/` next to each root
module, and `.terraform/modules/` holds **full copies of every module
source**, `versions.tf` and all. Those copies match every pattern a
real module matches.

They are gitignored, so `rg` skips them by default, but `find`,
`grep -r`, `fd -H`, and `git grep` on an unignored path do not. Editing
one reports a bump that the next `terraform init` erases.

Scope the search to tracked files:

```console
git ls-files -z -- '*.tf' '*.tofu' '*.tf.json'
```

Apply the same exclusion to `.terragrunt-cache/`, and to any vendor
directory the repository keeps.

## Classify by signal, never by name

`terraform/`, `infra/`, `deploy/`, `live/`, and `environments/` are all
conventions somebody made up. Treat the directory name as a hint for
where to look and never as the answer.

**Root module** — the directory holds a `backend` or `cloud` block, or
holds a `.terraform.lock.hcl`. These are the directories `terraform
init` runs in, and each one owns exactly one lock file.

**Child module** — the directory is named by a `module` block's
`source` as a local path, or sits under a `modules/` tree, and has
neither a backend nor a lock file. Child modules constrain versions but
own no lock file.

**Neither signal** — a root module using local state, with its lock
file untracked, looks exactly like a child module nobody calls. Ask
rather than guess. Guessing root runs `init` somewhere it does not
belong; guessing child leaves a lock file stale forever.

A directory can also be both: a module published for reuse that also
carries an `examples/` root for its own testing. Scope decisions apply
per directory, not per repository.

## The lock file belongs to the configuration, not the module

> The dependency lock file is a file that belongs to the configuration
> as a whole, rather than to each separate module in the configuration.
>
> — [Dependency Lock File](https://developer.hashicorp.com/terraform/language/files/dependency-lock)

A repository with four root modules has four lock files and needs four
`init` runs. A command that refreshes one of them and reports success
has left the other three pinned to whatever they were, and the drift is
invisible until somebody applies from a different directory.

## `.tofu` shadows `.tf`

OpenTofu reads both extensions, and same-named files do not merge:

> If both `foo.tf` and `foo.tofu` exist in the same directory, OpenTofu
> will only load `foo.tofu` and ignore `foo.tf`.
>
> — [OpenTofu Files](https://opentofu.org/docs/language/files/)

So a repository can carry a `versions.tf` that OpenTofu never reads.
Editing it changes nothing, `init` reports no drift, and the bump
appears to have worked. Whenever a directory holds any `.tofu` file,
resolve each base name before editing and write to the file the tool
actually loads.

## JSON syntax is not a text edit

`.tf.json` files express the same language as a JSON document. A
constraint there is a string inside nested objects, and the
line-oriented edits that work on HCL corrupt it. Parse, modify, and
re-serialise, or leave the file alone and report it.

## Other drivers wrap the CLI

Detect these before planning any `init`, because the wrapper owns the
lifecycle:

- **Terragrunt** — `terragrunt.hcl` or `root.hcl`. Provider blocks are
  frequently produced by `generate` blocks rather than committed as
  `.tf`, so the constraint you need to edit may not exist as a file
  yet. Terragrunt also runs `init` itself with its own caching.
- **Stacks** — `.tfstack.hcl` and `.tfdeploy.hcl`. Components declare
  providers in the stack configuration, and the deployment lifecycle is
  not `terraform init` at all.
- **Workspaces** — several states behind one root module. This changes
  nothing about pins or lock files; note it and move on.

## Repositories with no root module

A published module repository has provider constraints and no lock file
anywhere. Constraint bumps apply normally; there is nothing to refresh.
Say that plainly instead of reporting an empty run as a failure.

## What to ask

Ask through `AskUserQuestion`, once, with the findings already
gathered — never one directory at a time.

- More than one root module in scope: all of them, a named subset, or
  only the one containing the working directory.
- A directory whose signals do not classify it: root or child.
- Both `terraform` and `tofu` available, or repository signals that
  disagree with the binary on `PATH`: which drives, and therefore which
  registry resolves versions.
- Terragrunt or stacks present: drive through the wrapper, or operate
  on the underlying Terraform files directly.
- Root modules that disagree about the CLI version: converge them all,
  or move only the selected one and report the rest as drift.

Everything else is a judgment you can make from the signals. Asking
about all of it is as unhelpful as asking about none of it.
