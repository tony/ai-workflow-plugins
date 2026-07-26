# Action pinning and tag verification

Shared by `/github-actions:update-action` and
`/github-actions:update-actions`. Read before writing any version
string into a workflow.

## Inventory pins from trunk, not the working tree

Read workflow content through `git show <trunk>:<path>`. A checkout
may sit on a feature branch, and auditing that branch reports pins the
default branch does not have.

Cover `.github/workflows/**` and `.github/actions/**` — composite
actions pin versions too, and they are the ones most often missed.

**Word-splitting trap.** In zsh, an unquoted scalar expands as a single
word; in bash it splits on IFS. A loop over a captured file list
therefore works for repos with one workflow file and silently produces
a bogus multi-line ref for repos with two, dropping them from the audit
with no error. The audit then reports the fleet is clean. Always pipe
into `while read -r` instead of iterating an unquoted variable.

## Resolve the latest version

Ask the registry, not memory:

```console
gh api repos/<owner>/<action>/releases/latest --jq .tag_name
```

Some actions publish no releases at all, only tags. Fall back to
listing refs when `releases/latest` returns nothing.

## Verify the target tag exists

A pin naming a tag that does not exist breaks every workflow that
references it. Confirm before writing, and gate on exit status:

```console
gh api repos/<owner>/<action>/git/ref/tags/<tag> >/dev/null 2>&1
```

Piping `gh api` into `jq` or `sed` before checking the status swallows
the 404 and reports a missing tag as present. Check the exit code.

Not every action publishes a floating major. `astral-sh/setup-uv`
stopped after v7 and upstream declined to add more, so `@v9` does not
resolve while `@v9.0.0` does. Re-check per action rather than trusting
any list.

## Dereference annotated tags before comparing

`.object.sha` on an annotated tag returns the tag object, not the
commit it points at. Comparing two tags by that field makes identical
tags look different — and can lead to "correcting" research that was
right. Dereference when the type is `tag`:

```console
gh api repos/<owner>/<action>/git/tags/<tag-object-sha> --jq .object.sha
```

This is how to confirm claims like "the floating v6 tag now points at
the v7 commit", which change whether a bump is a behaviour change or a
label correction.

## Choose the pin, preserving the repo's shape

Default to the major-level float: it collects security and bug-fix
patches without a commit per patch release, and keeps dependabot noise
down.

**Currently a major float** (`@v6`) — move to the next major float
(`@v7`).

**Currently an exact patch** (`@v4.0.1`) — repin to the float (`@v4`)
when it exists and resolves to at least that patch. Say `repin X -> Y`
in the subject; "from 4.0.1 to 4" reads as a downgrade otherwise.

**Currently a commit SHA with a version comment** — move the SHA *and*
the trailing comment together. Leaving a stale `# v8.1.0` next to a v9
SHA is worse than no comment.

**No major tag upstream** — pin the exact release and explain why in
the commit body, so a later reader does not "fix" it to a float that
does not exist.

## Check the gates the research surfaces

Before writing a body that claims an upgrade is safe, confirm the claim
against the actual workflows. Recurring ones worth grepping:

- `pull_request_target` or `workflow_run` combined with an explicit
  `ref:`/`repository:` pointing at fork data — gates newer
  `actions/checkout` majors.
- A package manager declared via `devEngines` rather than
  `packageManager`, or a missing committed lockfile — gates newer
  `pnpm/action-setup` and `actions/setup-node` majors.
- Long-removed inputs still present: `file:`, `plugin:`,
  `always-auth`, `save-always`, `pip-install`.
- `runs-on` values — self-hosted runners gate every bump that moves an
  action to a newer Node runtime.

A fleet-wide fact is not a per-repo fact. If the body says "this repo
authenticates via OIDC" and one repo uses static keys, that is a false
statement committed permanently to that repo's history. Override the
body wherever the general claim does not hold.
