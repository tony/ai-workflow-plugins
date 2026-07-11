# Ticket Detection, Branch Naming & Worktree Placement

How `/action:worktree` and `/action:worktrees` resolve tickets into
branch names and worktree paths at runtime. Shared by both commands —
via `${CLAUDE_PLUGIN_ROOT}/references/ticket-detection.md` — so the
singular and plural procedures cannot drift. Language-agnostic and
tracker-agnostic: Linear and GitHub are first-class, everything else
degrades gracefully.

## The read-only invariant (zero ticket write-back)

```
TICKETS ARE READ-ONLY
```

Neither command ever assigns, comments, transitions, labels,
estimates, or otherwise mutates a ticket — in any tracker, through
any tool. Every ticket operation is a read: title, description,
acceptance criteria, the ticket's branch-name field.

Rationale — **zero blowback**: a branch that goes nowhere unwinds
with `git worktree remove` and `git branch -D`, and nothing else in
the world needs undoing. No teammate was pinged, no board column
moved, no assignment has to be handed back. Linking still happens —
server-side, from naming (see § Server-side linking): the tracker
attaches the branch and PR to the ticket because the *name* carries
the ID, not because the plugin touched the ticket.

Concretely forbidden (non-exhaustive): tracker MCP mutation tools
(create/update comment, state change, assignee change),
`gh issue edit`, `gh issue comment`, `gh issue close`, and
`gh issue develop` — that last one *writes a linked-branch record to
the issue*; construct the same branch name locally instead. Jira and
GitLab equivalents are equally off-limits.

## Detection source ladder

Resolve which tracker and which ticket(s), in this order — the first
source that yields a concrete ticket wins:

1. **Explicit URL or ID in the user's prompt** — `TEA-123`, `#45`,
   a full issue URL, `owner/repo#45`.
2. **Conversation context** — the ticket already under discussion:
   pasted issue text, a link shared earlier, the item the user just
   agreed to work.
3. **Available MCP tools** — a tracker MCP server (Linear or
   otherwise) whose read tools can fetch or search issues.
4. **CLIs** — `gh` first-class (`gh issue view`, `gh issue list`);
   other tracker CLIs generically, read-only subcommands only.
5. **Repo remote heuristics** — `git remote get-url origin` pointing
   at github.com suggests GitHub issues; a tracker ID pattern
   recurring in recent branch names or commit trailers suggests that
   tracker.

When no source yields a ticket, ask — never invent an ID or fetch a
guessed one.

## Ticket systems

| System | ID pattern | Examples | Disambiguation |
|---|---|---|---|
| Linear | `[A-Z][A-Z0-9]*-\d+` | `TEA-123`, `OPS2-7` | Linear MCP tools present, or a linear.app URL |
| GitHub | `#\d+`, issue URL | `#482` | `gh` CLI + GitHub remote |
| Jira | `[A-Z][A-Z0-9]*-\d+` | `PROJ-42` | Jira CLI/MCP present, or an atlassian.net URL |
| GitLab | `#\d+`, `!\d+`, issue URL | `#17` | GitLab remote |
| Other | whatever the tool exposes | — | generic fallback below |

Linear and Jira share the `KEY-123` shape. When both integrations
are present and the prompt gives no URL, try the Linear MCP lookup
first (cheaper, structured); if the ID is unknown there, try the
other system; if both claim it, ask.

### Linear (first-class)

- **ID pattern**: per the table above. Match case-insensitively in
  prompts; display uppercased.
- **Fetch**: the Linear MCP server's read tools, when available —
  pull title, description, acceptance criteria, and the issue's
  `gitBranchName` field.
- **Branch name**: prefer `gitBranchName` — the copyable branch name
  from Linear's UI, which already encodes the team's Linear-side
  settings. Without MCP, reconstruct from the pattern: lowercased ID
  plus a kebab slug of the title (`tea-123-fix-login-redirect`),
  subject to the observed-norms adjustment below (teams commonly add
  or drop a `username/` prefix).
- **Auto-attach**: Linear links the branch and PR to the issue when
  the branch name or PR title contains the ID.

### GitHub (first-class)

- **References**: `#123`, bare issue numbers in context, full issue
  URLs, `owner/repo#123`.
- **Fetch**:

```
gh issue view <num> --json number,title,body,labels,url
```

  Add `--repo <owner>/<repo>` for cross-repo references.

- **Branch name default**: `<number>-<kebab-title-slug>`, e.g.
  `123-fix-login-redirect`.
- **Linking**: closing keywords in the PR body (`Fixes #123`,
  `Closes #123`). The issue closes when a human merges the PR — not
  when this plugin runs.

### Generic fallback (Jira, GitLab, others)

- **ID patterns**: `[A-Z]+-\d+` (Jira-style), `#\d+` (GitLab issues),
  or whatever pattern the conversation supplies.
- **Fetch**: whatever CLI or MCP server is present (`jira`, `glab`,
  …), read-only subcommands only. When none exists, ask the user to
  paste the ticket body rather than skipping context.
- **Branch name**: generic kebab slug — `<id-lowercased>-<kebab-title>`.

### Kebab-slug algorithm

Wherever a `<kebab-title-slug>` is called for:

1. Lowercase the title.
2. Replace every non-alphanumeric run with a single `-`.
3. Trim leading/trailing `-`.
4. Truncate at a word boundary to keep the whole branch name ≤ 60
   characters.

## Branch-name precedence ladder

Resolve the branch name by the first rung that yields one:

1. **Explicit user prompt** — `--branch=<name>` or a name stated in
   the request. Verbatim, no adjustment.
2. **User/project system instructions** — branch-naming conventions
   in the project's AGENTS.md / CLAUDE.md / CONTRIBUTING first, then
   the user's global norms.
3. **Ticket-system default** — Linear's `gitBranchName`; GitHub's
   `<number>-<kebab-title-slug>`. *Skipped for multi-ticket branches*
   (see below).
4. **Observed repo norms** — mine the team's actual pattern:

```
git branch -r
```

```
git log --merges --oneline -50
```

   Look for prefix families (`feat/`, `fix/`, `username/`), where the
   ticket ID sits, and slug style. Observed norms are also an
   **adjuster** for rung 3: when history shows no `username/`
   prefixes, offer the Linear name with the prefix trimmed; when
   every branch carries a `feat/`-style prefix, offer the ticket
   default with one. Name the adjustment in the plan so the user sees
   what was inferred.
5. **Kebab-slug fallback** — a kebab slug of the goal, when no
   ticket, no convention, and no norms exist.

Whatever rung wins, validate the name before deriving paths from it:

```
git check-ref-format --branch <name>
```

An invalid name from a slugged title (illegal characters, trailing
dot, `..`) is re-slugged and re-validated; an invalid explicit name
(rung 1) is a question back to the user, never a silent rewrite.

**Multi-ticket (crosscutting) branches** skip rung 3: no single
ticket's name should claim a branch that carries several. Propose a
**theme slug** instead (e.g. `auth-error-handling` for three auth
tickets) and confirm it at the plan gate. The ticket IDs still ride
in commit messages and the PR title/body, so server-side linking
fires for every ticket on the branch.

## Worktree placement & path sanitization

Two placements — the placement axis:

- **`--local` (default)** — a visible sibling of the repo:

```
{repo_path}-{sanitized_branch}/
```

  Derivation: take the absolute repo path
  (`git rev-parse --show-toplevel`), strip any trailing slash, append
  `-`, then append the branch name with every `/` flattened to `-`.
  The flattening applies to the **directory name only** — the git
  branch keeps its slashes.

  Example: repo at `/work/shop`, branch `feat/tea-123-login` →
  worktree `/work/shop-feat-tea-123-login/`, branch still
  `feat/tea-123-login`.

- **`--temp`** — the host's native temp-worktree mechanism when one
  exists (e.g. Claude Code's worktree isolation for subagents) —
  **but only if it can put the work on the computed branch name**.
  Branch naming is load-bearing (it is how Linear auto-attaches); a
  mechanism that cannot honor it is disqualified. Otherwise a temp
  root outside the repo:

```
${TMPDIR:-/tmp}/action-worktrees/<repo-name>/<sanitized-branch>/
```

  Same sanitization rule for `<sanitized-branch>`. The path is
  deterministic, so `--temp` re-runs land on the same worktree and
  resume per the idempotency ladder.

Branch names are git-valid before they reach this section
(`git check-ref-format` runs at the end of the precedence ladder), so
`/` is the only character that needs flattening — do not otherwise
rewrite the name.

## Server-side linking (how zero write-back still links)

| Tracker | Carrier | Effect |
|---|---|---|
| Linear | ticket ID in the branch name and PR title | Linear auto-attaches the branch/PR to the issue |
| GitHub | closing keyword in the PR body (`Fixes #123`) | issue links immediately, closes when a human merges |
| Generic | ID in the branch name, PR title, and commit bodies | whatever the tracker's own git integration picks up |

Commit bodies name the ticket ID(s) they advance — the project's
commit conventions win on exact form. Closing keywords belong in the
PR body, never in commit subjects.
