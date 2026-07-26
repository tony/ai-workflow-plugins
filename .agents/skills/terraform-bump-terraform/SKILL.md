---
name: terraform-bump-terraform
description: >-
  Move the Terraform or OpenTofu CLI version across every module and every
  pin site outside the configuration — version manager files, CI workflows,
  container images — and report the sites that disagreed
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "WebSearch", "WebFetch", "AskUserQuestion"]
metadata:
  argument-hint: "[version] [--root-module <dir>...] [--audit-only] [--no-lock] [--no-commit]"
  source: "plugins/terraform/commands/bump-terraform.md"
---

# Bump the Terraform CLI

Move `required_version` across every module that declares one, along
with the version manager files, CI workflows, and images that pin the
same CLI somewhere else.

Use the `terraform-bumping-terraform` skill for the
phase structure. It reads the same three references this command does,
so the two cannot drift:
`references/layout-discovery.md`,
`references/pin-sites.md`, and
`references/lock-and-init.md`.

To move a provider, use the `terraform-bump-provider` skill.

User arguments: $ARGUMENTS

## Context

Repository — run this command and read the output:

```bash
git remote get-url origin 2>/dev/null || echo "(not a git repository)"
```

`required_version` by file — run this command and read the output:

```bash
git grep -nE '^[[:space:]]*required_version' -- '*.tf' '*.tofu' 2>/dev/null | sed -E 's/[[:space:]]+/ /g' | grep . || echo "(none declared)"
```

Pin sites outside the configuration — run this command and read the output:

```bash
{ git ls-files -- '*.terraform-version' '*.tool-versions' '*mise.toml' 2>/dev/null | xargs -r git grep -n '' -- 2>/dev/null; git ls-files -- '.github/workflows/*' '.devcontainer/*' ':(icase)*dockerfile*' ':(icase)*makefile*' ':(icase)*justfile*' 2>/dev/null | xargs -r git grep -nEi '(terraform|opentofu|tofu|tf[_-]?version).*[0-9]+\.[0-9]+' -- 2>/dev/null; } | head -30 | grep . || echo "(none found)"
```

Installed and available — run this command and read the output:

```bash
{ command -v terraform >/dev/null 2>&1 && terraform -version | head -1; command -v tofu >/dev/null 2>&1 && tofu -version | head -1; } 2>/dev/null | grep . || echo "(neither terraform nor tofu on PATH)"
```

Latest releases — run this command and read the output:

```bash
curl -s --max-time 10 https://releases.hashicorp.com/terraform/index.json 2>/dev/null | jq -r '.versions | keys_unsorted[]' 2>/dev/null | grep -vE 'alpha|beta|rc' | sort -V | tail -3 | grep . || echo "(registry unreachable — resolve before writing)"
```

## Procedure

Follow the skill's phases. This command supplies the target and the
scope.

### 1. Resolve the target version

If the user named a version, confirm it is published. Otherwise present
the latest stable release alongside the version installed locally, and
confirm which to write — they are frequently different, and pinning to
a version nobody has installed makes every module unusable until
somebody installs it.

Resolve against OpenTofu's releases instead when the repository is
driven by `tofu`.

### 2. Discover the layout

Run the skill's discovery phase. `--root-module` limits the run to the
named directories.

### 3. Inventory every pin site

Both kinds, per the pin-sites reference: `required_version` in every
module, and the pins that live outside the configuration entirely —
`.terraform-version`, `.tool-versions`, `mise.toml`, workflow files
using `setup-terraform` or `setup-opentofu`, container image tags,
devcontainer configuration, Makefile variables.

### 4. Report the drift before overwriting it

Root modules that disagree about the CLI, a version manager file that
contradicts the configuration, CI installing a third version — surface
all of it as a finding first. This is usually the most valuable thing
the run discovers, and the bump erases the evidence.

An exact pin is a hard gate: a module pinned `= 1.14.5` refuses to
initialise under any other version with `Unsupported Terraform Core
version`. Root modules that disagree are root modules that cannot all
be run from one machine.

When they disagree, ask: converge every root module on the target, or
move only the selected ones and report the rest as outstanding drift.

### 5. Distinguish root modules from reusable ones

Root modules take the repository's existing shape — an exact pin stays
exact, a pessimistic constraint stays pessimistic.

Reusable modules take floors. Raising a reusable module's `>=` to a
ceiling constrains every configuration that consumes it, including ones
outside this repository, so leave those alone unless the new version is
genuinely the minimum the module now needs — and say why in the body
when you move one.

### 6. Present the plan and wait

Show every site to be edited with the form it keeps, every site left
alone with the reason, the drift found, and whether lock files will be
refreshed. With `--audit-only`, stop here — nothing is written.

### 7. Edit, commit, verify

All pin sites in one commit. Then, unless `--no-lock`, refresh each
root module's lock as a separate commit — a CLI bump can change the
lock file's own format. With `--no-commit`, leave the working tree
alone and say what would have been committed.

Verify by initialising each root module and confirming it accepts the
new version, then run the repository's own gates.

## Rules

- No version string is written before the release is confirmed to exist.
- Every pin site moves in the same commit, or none does.
- Configuration edits and lock files are separate commits.
- Reusable modules keep floors; only root modules take ceilings.
- Drift is reported before it is overwritten.
- A lock file never comes back tracking fewer platforms than it had.
- Untracked files are never edited, and `.terraform/` is never searched.

## Output

Open with a one-line hero (`✓ terraform <old> -> <new> across N pin
sites` or `⚠ Audit only: N sites disagree`), then exactly these
sections:

1. `## Target` — the resolved version, how it was confirmed, the
   version installed locally, and the changelog link.
2. `## Layout` — root modules and child modules discovered, and which
   tool drives the repository.
3. `## Sites` — every pin found, inside the configuration and outside
   it, and whether each was edited or left alone with the reason.
4. `## Locks` — per root module: whether the lock was refreshed, and
   the platform count tracked before and after.
5. `## Verification` — the gates run and their real results, including
   whether each root module now initialises.
6. `## Drift` — every disagreement found before the bump, and every one
   still outstanding after it.

End with an `ask-user-choice` panel offering next steps — for example:
converge the root modules still on an older pin, add the version to a
version manager file the repository lacks, align the CI workflow, or
stop here. Skip the panel only in plan mode.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
