# Refreshing lock files without wrecking them

Shared by all three commands. Read before running `init` anywhere.

Every command below names `terraform`. Substitute `tofu` throughout when
OpenTofu drives the repository — the subcommands, flags, and lock file
format are the same, and phase 1 of the procedure is what establishes
which binary applies.

## One run per root module

Each root module owns one `.terraform.lock.hcl`, and `init` only ever
touches the one in the directory it runs in. Four root modules need
four runs. Use `-chdir` rather than a subshell `cd`, so a failure
partway through does not leave the working directory somewhere
unexpected:

```console
terraform -chdir=<root-module-dir> init -backend=false -upgrade -input=false
```

Child modules have no lock file. Running `init` in one is not an error,
but it produces nothing to commit.

## `-backend=false` removes the credential requirement

Provider installation and lock maintenance do not need the backend.
Passing `-backend=false` skips backend initialisation while still
resolving providers and writing the lock file, so lock refreshes work
against an S3-, GCS-, or HCP-backed configuration with no cloud
credentials present at all.

Backends are also where a refresh fails for reasons that have nothing
to do with the bump — expired credentials, a state lock somebody else
holds, a role that cannot be assumed from this machine. Skipping the
backend keeps those failures out of a run that never needed it.

Use `-input=false` too. Without it, a missing backend variable turns a
batch run into a process waiting forever on a prompt nobody sees.

## `-upgrade` ignores the lock, by design

> Upgrade all previously-selected plugins to the newest version that
> complies with the configuration's version constraints. This will
> cause Terraform to ignore any selections recorded in the dependency
> lock file, and to take the newest available version matching the
> configured version constraints.
>
> — [terraform init](https://developer.hashicorp.com/terraform/cli/commands/init)

Which is why the constraint edit has to land first. `-upgrade` obeys
the constraints; it does not overrule them. A `~> 6.56.0` left in any
module of the configuration holds the whole thing at `6.56.x` no matter
how many times the command runs.

## Selecting a new version narrows the lock to one platform

`h1:` hashes are per-platform. `terraform init` records them only for
the platform it runs on, and teams that need more use
`terraform providers lock -platform=...` to pre-populate the set.

Re-running `-upgrade` against an already-selected version preserves the
platforms already recorded. **Selecting a different version does not.**
A lock tracking `linux_amd64` and `darwin_arm64` comes back tracking
only the platform that ran the bump — no warning, no error, and the
diff looks like an ordinary version change.

The `zh:` hashes still cover the official release archives, so a
registry-signed provider keeps verifying elsewhere. What is lost is the
deliberate multi-platform coverage: the next `init` on another platform
mutates the lock file to add its own hash back, which fails outright
under `-lockfile=readonly` or any CI step that checks the tree is
clean.

The lock file names no platforms. Each provider block holds one flat
list of opaque `h1:` and `zh:` strings with no platform metadata
attached, so how *many* platforms a provider tracks is readable and
*which* ones are not — while `providers lock -platform=` requires exact
names.

Use the count as a tripwire. Take the highest `h1:` count of any single
provider before the run, and compare it after:

```console
awk '/^provider /{n=0} /"h1:/{n++; if(n>m) m=n} END{print m+0}' <root-module-dir>/.terraform.lock.hcl
```

Count per provider, not per file: a repository-wide total multiplies
providers by platforms, so seven providers on one platform and one
provider on seven are indistinguishable.

If the count dropped, stop and get the platform names from wherever the
repository actually writes them down — a `providers lock` invocation in
CI, a Makefile or justfile target, or the user — then restore them:

```console
terraform -chdir=<root-module-dir> providers lock -platform=linux_amd64 -platform=darwin_arm64
```

Never infer the list. A repository that only ever tracked one platform
should keep tracking one, and guessing a set both drops platforms it had
and adds platforms it never wanted.

## When the resolver cannot see the version

The registry shows a version the resolver refuses to find. Diagnose the
layer before working around it:

- A `provider_installation` block in the CLI configuration —
  `.terraformrc`, `terraform.rc`, or wherever `TF_CLI_CONFIG_FILE`
  points — with a `filesystem_mirror` or `network_mirror` that only
  carries what somebody mirrored.
- `TF_PLUGIN_CACHE_DIR`, which serves a stale copy when the mirror
  cannot be reached.
- A private registry requiring credentials this machine does not have.
- A provider whose new release genuinely has no build for this
  platform.

Report which layer is blocking. Do not edit a mirror configuration to
route around a supply-chain control as a side effect of a version bump.

## Confirm the lock actually moved

The constraint edit and the lock refresh can both succeed while the
selected version stays put — a child module cap, a mirror serving an
older release, a constraint that was already satisfied. Read the
version out of the lock file and compare it to the target rather than
inferring success from a zero exit code:

```console
grep -A2 'provider "<provider-source-address>"' <root-module-dir>/.terraform.lock.hcl
```

Read the file, not `terraform providers`. That subcommand prints the
requirements tree — the *constraints*, which the run just wrote — so it
matches the target by construction and reports success whatever the
lock actually says. It also needs an initialised backend, which
`-backend=false` deliberately skipped.

Report the real selected version per root module, including the ones
that did not move and why.

## Verification gates

`terraform validate` requires an initialised directory, so it runs
after `init` and reports per root module. `terraform fmt -check
-recursive` runs anywhere and catches formatting the edits introduced.

Beyond those, run the checks the repository itself defines in its
`AGENTS.md`, `CLAUDE.md`, or CI workflow — a `tflint` pass, a policy
check, a `plan` against a sandbox. Never substitute assumed commands
for the ones the project actually runs, and never report a gate as
passing without having read the output that says so.

A `plan` is not a verification step for a version bump unless the
project asks for it: it needs backend credentials, it reaches live
infrastructure, and a non-empty plan is frequently pre-existing drift
rather than anything the bump caused.
