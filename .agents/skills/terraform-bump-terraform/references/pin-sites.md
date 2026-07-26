# Every place a version is pinned

Shared by the `terraform-bump-provider` skill and this skill.
Read before writing any version string.

## Constraints combine across the whole configuration

> The root module and any child modules can constrain the Terraform
> version and any provider versions the modules use. Terraform
> considers these constraints equal, and only proceeds if all are met.
>
> — [Version Constraints](https://developer.hashicorp.com/terraform/language/expressions/version-constraints)

This is the rule that makes a partial edit worse than no edit. Raise
the root module's `aws` constraint to `~> 6.57.0` while a child module
still says `~> 6.56.0`, and the two cannot both be satisfied: `init`
fails outright, or — where the constraints merely overlap — resolves to
something neither file names. Either way the reviewer reads a diff that
claims a version the configuration does not use.

Every declaration of a provider moves in one commit, or none does.

## Finding the declarations

Constraints live in a `terraform` block's `required_providers`, in any
`.tf` or `.tofu` file. `versions.tf`, `terraform.tf`, `providers.tf`,
and `main.tf` are the common names and none of them are required.
Search for the block, not the filename.

Identity is the **source address**, not the local name. Two modules can
call the same provider by different local names, and — rarely, but it
is the case that breaks things — the same local name can point at
different source addresses in different modules. Match on `source`.

Source addresses take the form `[<HOSTNAME>/]<NAMESPACE>/<TYPE>` and
default to `registry.terraform.io`. When a user names a provider
loosely, resolve it against the addresses the repository actually
declares and ask if more than one matches.

## Read the operator before replacing it

The operator already in the file encodes an intent. Preserve it, and
check whether the target version even requires an edit:

- `~> 6.56.0` allows `6.56.4` but not `6.57.0`. Moving to a new minor
  requires editing the constraint.
- `~> 6.56` allows `6.57.0` but not `7.0.0`. Moving within the major
  requires no edit at all — refreshing the lock is the whole change.
- `>= 6.0` or `>= 6.0, < 7.0` already admits the target. Rewriting it
  as `~> 6.57.0` silently narrows what the module accepts, which is a
  policy change wearing a version bump's clothing.
- `= 6.56.0` is a deliberate exact pin. Move it exactly.

When the existing constraint is a range or a compound expression, the
new form is a judgment call rather than a substitution. Ask.

**Do not normalise operators repository-wide as a side effect.** A bump
that also converts every `>=` to `~>` is two changes, and the second
one was not requested.

## Root modules and reusable modules pin differently

> A module intended to be used as the root of a configuration [...]
> should also specify the maximum provider version it is intended to
> work with, to avoid accidental upgrades to incompatible new versions.

> Do not use `~>` (or other maximum-version constraints) for modules
> you intend to reuse across many configurations [...] Specify a
> minimum version, document any known incompatibilities, and let the
> root module manage the maximum version.
>
> — [Provider Requirements](https://developer.hashicorp.com/terraform/language/providers/requirements)

So a floor in a reusable module is correct, not drift. Raising it to a
ceiling constrains every configuration that consumes the module,
including ones outside this repository. Leave floors alone unless the
new version is genuinely the minimum the module now needs, and say why
in the body when you move one.

## The CLI version has pin sites outside `.tf` entirely

`required_version` appears in the `terraform` block of every module
that declares one — root and child alike, and they combine by the same
rule. Beyond those:

- `.terraform-version` — tfenv, and read by several CI actions.
- `.tool-versions` — asdf and mise, as a `terraform` or `opentofu` line.
- `mise.toml` and `.mise.toml` — under `[tools]`.
- Workflow files — `hashicorp/setup-terraform` with `terraform_version`,
  `opentofu/setup-opentofu` with `tofu_version`, and any container image
  tag that carries the version in its name.
- `Dockerfile` and `devcontainer.json` image tags, and task-runner
  variables in a `Makefile` or `justfile`.

Two things make these easy to miss, and both have to be got right or
the search reports a clean repository that is not one.

**Match at any depth.** A git pathspec with no leading wildcard anchors
to the repository root, so `Makefile` finds the top-level one and
silently skips the per-module one sitting beside a root module — which,
in a repository whose root modules live in subdirectories, is the one
that matters. A leading `*` covers both. `just` also searches
case-insensitively and accepts a leading dot, so `justfile`, `Justfile`,
and `.justfile` are all live names; `:(icase)` handles the variants
without listing them.

**Filter on a version, not on the tool's name.** A task runner pins
through a variable named for the tool's abbreviation rather than the
tool, so `TF_VERSION := 1.11.0` contains no substring a
`terraform|tofu` filter matches, and the file is found and then
discarded. Widening the filter to the abbreviation alone fails the
other way: a `justfile` that wraps `terraform init`, `terraform plan`,
and `terraform apply` matches on every line and buries the real pins.

Require the tool name *and* a version-shaped number on the same line.
That keeps `TF_VERSION := 1.11.0`, `terraform_version: 1.14.0`, and
`FROM hashicorp/terraform:1.13.0`, and drops a task runner that only
invokes the CLI.

The dedicated version files fail differently again: `.terraform-version`
holds a bare version number and nothing else, matching no name-based
filter at all. Read those by path and take every line.

These drift apart quietly. The configuration says one version, the
version manager installs another, and CI installs a third; whichever
runs first decides what "clean" means, and the disagreement surfaces as
a failure on somebody else's pull request. Inventory all of them,
report every disagreement found *before* the bump, and move them
together.

An exact `required_version` is a hard gate, not a preference. A module
pinned `= 1.14.5` refuses to initialise under 1.15.8 with `Unsupported
Terraform Core version`, so a repository whose root modules disagree
about the CLI has root modules that cannot all be run from one machine.

## Resolve the version and its changelog from the registry

Ask the registry rather than recalling a version, and confirm it exists
before writing it anywhere. The registry protocol defines a versions
endpoint, and every registry implements it — so this is the gate:

```console
curl -s https://registry.terraform.io/v1/providers/hashicorp/aws/versions | jq -r '.versions[].version'
```

Swap the host for `registry.opentofu.org` when OpenTofu drives the
repository. A source address carrying a non-default hostname is a
private registry: read `providers.v1` out of
`https://<hostname>/.well-known/terraform.json` and build the path from
that prefix rather than assuming the public one.

`registry.terraform.io` additionally serves a metadata endpoint
carrying the release tag and the provider's own repository, which is
what makes a changelog link derivable for any provider instead of only
the handful somebody remembered to hardcode:

```console
curl -s https://registry.terraform.io/v1/providers/hashicorp/aws | jq '{version, tag, source, published_at}'
```

That one is an extension, not protocol:

> The public Terraform Registry implements a superset of the API
> described on this page [...] Third-party implementations should not
> include those extensions.
>
> — [Provider Registry Protocol](https://developer.hashicorp.com/terraform/internals/provider-registry-protocol)

It returns 404 on `registry.opentofu.org` and on private registries.
Where it is unavailable, confirm the version through the versions
endpoint and find the provider's repository another way before citing a
changelog — never construct a repository URL from the source address
and hope.

For the CLI itself, releases are enumerated at
`https://releases.hashicorp.com/terraform/index.json`, and OpenTofu
publishes GitHub releases.

Cite the release notes at the tag the registry reported, not at a
branch — the link has to still mean the same thing in a year.
