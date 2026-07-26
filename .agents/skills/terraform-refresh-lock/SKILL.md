---
name: terraform-refresh-lock
description: >-
  Refresh every root module's .terraform.lock.hcl within the constraints
  already written — no credentials needed, platform coverage preserved, and
  the versions that actually moved reported per module
allowed-tools: ["Bash", "Read", "Grep", "Glob", "AskUserQuestion"]
metadata:
  argument-hint: "[--root-module <dir>...] [--audit-only] [--no-commit]"
  source: "plugins/terraform/commands/refresh-lock.md"
---

# Refresh Terraform lock files

Re-resolve providers to the newest versions the existing constraints
allow, in every root module, and report what actually moved.

This changes no constraint. When a provider will not move, the
constraint is what is holding it — use the `terraform-bump-provider` skill.

Use the `terraform-bumping-terraform` skill for the
phase structure, and these two references for the parts that go wrong:
`references/layout-discovery.md` and
`references/lock-and-init.md`.

User arguments: $ARGUMENTS

## Context

Repository — run this command and read the output:

```bash
git remote get-url origin 2>/dev/null || echo "(not a git repository)"
```

Providers each committed lock holds, and the most platforms any one of them tracks — run this command and read the output:

```bash
git ls-files -- '*.terraform.lock.hcl' 2>/dev/null | while read -r f; do printf '%s: providers=%s max_platforms_per_provider=%s\n' "$f" "$(grep -c '^provider ' "$f")" "$(awk '/^provider /{n=0} /"h1:/{n++; if(n>m) m=n} END{print m+0}' "$f")"; done | grep . || echo "(no committed lock file — nothing to refresh)"
```

Directories with a backend or cloud block — run this command and read the output:

```bash
git grep -lE '^[[:space:]]*(backend[[:space:]]+"|cloud[[:space:]]*\{)' -- '*.tf' '*.tofu' 2>/dev/null | xargs -r -n1 dirname | sort -u | grep . || echo "(none)"
```

Tooling available — run this command and read the output:

```bash
{ command -v terraform >/dev/null 2>&1 && terraform -version | head -1; command -v tofu >/dev/null 2>&1 && tofu -version | head -1; } 2>/dev/null | grep . || echo "(neither terraform nor tofu on PATH)"
```

## Procedure

### 1. Discover every root module

Run the skill's discovery phase. A repository routinely has several
root modules and therefore several lock files; refreshing one and
reporting success is the failure this command exists to prevent.

`--root-module` limits the run to the named directories. A directory
holding a backend block but no committed lock file is a finding — its
lock is either untracked or was never created.

A repository with no lock file anywhere is a module repository with
nothing to refresh. Say so; it is not a failure.

### 2. Record the starting state

Per root module: the version selected for each provider, and how many
platforms each provider's entry tracks. Both are needed afterwards —
the first to report what moved, the second to detect a narrowed file.

### 3. Present the plan and wait

Show the root modules to be refreshed and how many platforms each lock
tracks. With `--audit-only`, stop here — nothing is written.

### 4. Refresh, one root module at a time

Per the lock reference: `-chdir` rather than a subshell `cd`, and
`-backend=false -input=false -upgrade` so the run needs no cloud
credentials and cannot stall on a prompt.

Compare each lock's per-provider platform count afterwards against what
it was before. Selecting a new version records only the running
platform's hash, which silently discards coverage somebody established
deliberately — and because the file names no platforms, a count that
dropped is a stop signal, not something to reconstruct by guessing.

A root module that fails to refresh does not stop the others. Record
the failure and continue.

### 5. Commit

One commit for the lock files. They are generated output; keep them out
of any commit carrying authored changes. With `--no-commit`, leave them
in the working tree and say what would have been committed.

### 6. Verify and report

Read each lock back and compare the selected versions to the starting
state. Report per root module what moved, what did not, and — where a
provider stayed put — whether a constraint is holding it.

Run the detected tool's `fmt -check -recursive` — `tofu` where OpenTofu
drives the repository — and whatever gates the repository defines for
itself. Never report a gate as passing without reading the output that
says so.

## Rules

- Every root module is refreshed, not only the first one found.
- Constraints are never edited by this command.
- A lock file never comes back tracking fewer platforms than it had.
- A failure in one root module never silently ends the run.
- Success is read out of the lock file, never inferred from an exit
  code.

## Output

Open with a one-line hero (`✓ N of M lock files moved` or `⚠ Audit
only: M lock files found`), then exactly these sections:

1. `## Root modules` — every one discovered, and any directory with a
   backend but no committed lock file.
2. `## Changes` — per root module and provider: the version before and
   after, and the platform count tracked before and after.
3. `## Held back` — providers that did not move, and the constraint
   holding each.
4. `## Verification` — the gates run and their real results.
5. `## Failures` — root modules that could not be refreshed, and why.

End with an `ask-user-choice` panel offering next steps — for example:
bump a constraint that is holding a provider back, restore
multi-platform coverage, commit an untracked lock file, or stop here.
Skip the panel only in plan mode.


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
