---
name: bumping-terraform
description: Use when Terraform or OpenTofu provider constraints are out of date, when a `.terraform.lock.hcl` needs refreshing, when a `required_version` CLI pin needs moving, or when asked which root modules in a repository are stuck on stale provider versions.
---

# Bumping Terraform

Find the root modules, move every declaration of a version together,
refresh each root module's lock file without narrowing it, and verify
the selected version actually changed.

Three reference files carry the parts that must not drift between this
skill and the plugin's commands:

- `${CLAUDE_PLUGIN_ROOT}/references/layout-discovery.md` — classifying
  root and child modules by signal, the `.terraform/` cache trap,
  `.tofu` shadowing, other drivers, and what to ask about.
- `${CLAUDE_PLUGIN_ROOT}/references/pin-sites.md` — every file a
  provider or CLI version is pinned in, how constraints combine across
  modules, operator preservation, and registry lookups.
- `${CLAUDE_PLUGIN_ROOT}/references/lock-and-init.md` — per-root-module
  `init`, `-backend=false`, the platform-narrowing trap, blocked
  resolvers, and verification gates.

## Core principle

Constraints from every module in a configuration must all be satisfied
at once. So the unit of work is the configuration, not the file — a
bump that edits some declarations of a provider and not others produces
a configuration that either refuses to initialise or quietly resolves
to a version no file names.

Every declaration moves in one commit, or none does.

## Scope

The current repository. Discover its root modules rather than assuming
one, and confirm the set with the user when there is more than one.

Never widen scope as a side effect: a bump is not the moment to
normalise operators repository-wide, adopt platforms the lock never
tracked, or reformat modules the change did not touch.

## Phase 1 — Discover the layout

Follow the discovery reference. Enumerate tracked `.tf`, `.tofu`, and
`.tf.json` files, classify each directory as a root module, a child
module, or ambiguous, and detect whether Terraform, OpenTofu,
Terragrunt, or stacks drives the repository.

Record, per directory: kind, lock file presence, how many platforms
that lock already tracks per provider, and the providers and
`required_version` it declares. That inventory is the unit of work for everything after.

Ask about the ambiguities the reference enumerates — all of them at
once, after the inventory exists, never one directory at a time.

## Phase 2 — Resolve the target and confirm it exists

Ask the registry, not memory. Confirm the version is published and
record its tag and source repository, which is where the changelog link
comes from. Use the registry the detected tool actually resolves
against, and service discovery for a private one.

Nothing proceeds past this phase on an unconfirmed version. A version
string written before it is known to exist is the expensive failure
this ordering prevents.

## Phase 3 — Inventory the pin sites and predict the change

Find every declaration of the thing being moved across the whole
configuration, per the pin-sites reference, including the CLI pin sites
that live outside `.tf` entirely.

Then work out which sites actually need editing. A constraint that
already admits the target needs no edit, and rewriting it anyway
narrows what the module accepts — a policy change wearing a version
bump's clothing. Reusable modules keep their floors.

Report drift found *before* the bump as its own finding: root modules
disagreeing about the CLI version, a `.tool-versions` that contradicts
`required_version`, pin sites that disagree with each other. That drift
is usually the more valuable discovery, and it is invisible once the
bump has overwritten it.

## Orchestration Plan

Before any file is written, enter plan mode — `EnterPlanMode` in Claude
Code, `/plan` or `Shift+Tab` in Cursor, Codex, and Gemini — and present
a plan covering:

- The root modules in scope, and any directory whose classification the
  user settled.
- The target version, and the evidence it exists.
- Every pin site to be edited, the operator each one keeps, and the
  sites deliberately left alone with the reason.
- Which lock files will be refreshed, and how many platforms each
  currently tracks.
- The commits this produces and whether they will be pushed.
- Drift found that this run will not fix.

Present it and wait for approval. Exit plan mode before Phase 4.

If plan mode is unavailable, the phase structure still applies: finish
discovery, resolution, and inventory, and confirm scope with the user
before writing anything.

## Phase 4 — Edit the constraints

All sites in one commit. Preserve each site's existing operator, and
write to the file the tool actually loads where `.tofu` shadows `.tf`.

The body says what moved and why, and cites the release notes at the
tag the registry reported. Follow the project's own commit conventions
from AGENTS.md or CLAUDE.md for the subject format.

## Phase 5 — Refresh the locks

Per root module, following the lock reference: `-chdir`,
`-backend=false`, `-input=false`, `-upgrade`. Then compare each lock's
per-provider platform count against what it was before the run. The
lock file records no platform names, so a count that dropped is a stop
signal rather than something to reconstruct: get the names from
wherever the repository writes them down, and never guess a list.

Lock files land as their own commit, separate from the constraints.
They are generated output, and a reviewer reads them differently from
an authored change.

## Phase 6 — Verify

Confirm the selected version actually moved, per root module, by
reading it back out of the lock file rather than inferring it from an
exit code. Name the root modules that did not move and why.

Run `terraform fmt -check -recursive` and, per initialised root module,
`terraform validate`. Then run whatever gates the repository defines
for itself. If something fails, establish whether it failed before the
bump too; pre-existing failures are reported, not concealed and not
fixed as a side effect.

Never report a gate as passing without having read the output that says
so.

## Common mistakes

**Assuming one root module.** The commonest layout in a repository that
has grown is several, each with its own lock file, and a run that
refreshes one reports success while leaving the rest stale.

**Editing the root module's constraint only.** A child module's cap
holds the whole configuration back, and the diff claims a version that
is not in use.

**Searching untracked files.** `.terraform/modules/` holds copies of
module sources that match every pattern a real module matches. Edits
there vanish on the next `init`.

**Forcing `~>` everywhere.** A floor in a reusable module is correct;
converting it to a ceiling constrains every configuration that consumes
that module, including ones outside this repository.

**Refreshing a multi-platform lock on one platform.** Selecting a new
version records only the running platform's hash, discarding coverage
somebody established deliberately.

**Running `plan` to verify a bump.** It needs credentials, reaches live
infrastructure, and reports pre-existing drift as though the bump
caused it.

**Reporting success from an exit code.** A constraint edit and a lock
refresh can both succeed while the selected version stays exactly where
it was.
