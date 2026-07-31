# Writing the replacement messages

A recut is only worth doing if the new messages are better than the
ones they replace. That takes two things the original commits do not
carry on their own: the project's own conventions, and the reasoning
behind the code.

Verified against git 2.43.

## Part 1 — Match the project's style

Never impose a house style. Discover the one already in use, and when
the repository has no single style, say so and ask rather than forcing
a plurality rule onto every commit.

### Declared conventions win

Read these in order and stop at the first that actually specifies a
format: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md` (root and
`.github/`), then a `commit.template` file.

The convention doc is often at a path no fixed list contains, linked
from `CONTRIBUTING.md` rather than inlined. Follow markdown links one
hop before concluding nothing is declared.

A checked-in `.gitmessage` is a specification to read, not a message
to reuse: `commit.template` has no effect at all when the message
comes from `-m` or `-F`.

Machine-enforced conventions are declarations too. Probe for
commitlint (its config may live in `package.json`, `package.yaml`,
`.commitlintrc*`, or `commitlint.config.*`), commitizen (`.cz.toml`,
`cz.toml`, `.cz.json`, `cz.yaml`, `pyproject.toml`), `.gitlint`,
`.conform.yaml`, and a `conventional-pre-commit` hook in
`.pre-commit-config.yaml`. A checked-in `.githooks/` directory is
evidence of intent, not an active gate — it does nothing until someone
sets `core.hooksPath` locally.

### Otherwise mine the history

Anchor the sample at the fork point. Mining `git log HEAD` on the
branch under recut samples the mess you were asked to fix.

```
git log --no-merges -n 200 --format='%B' "$(git merge-base HEAD <base-ref>)"
```

Sample 100 to 200 non-merge commits. Twenty can invert a binary signal
outright — one real repository reads a 0% PR-suffix rate at 20 commits
and 87% at 200.

What to measure, and the trap in each:

- **Subject length.** Take line 1 of `%B`. `%s` space-folds a
  multi-line first paragraph into one line and inflates the number.
- **Prefix grammar.** Whether subjects match a Conventional Commits
  prefix, or a custom scheme. Build the actual vocabulary rather than
  assuming.
- **A `(#N)` suffix.** Measure it separately on merges and on ordinary
  commits. Merge style and branch style legitimately differ: a repo
  can carry `(#N)` on every merge subject and none of its branch
  commits, in which case the recut must not add one.
- **Body rate and wrap width.** Whether commits carry bodies at all,
  and the real wrap column rather than an assumed 72.
- **Trailers.** Filter keys against a `^[A-Za-z][A-Za-z0-9-]*$` shape,
  or a bare URL on the last line parses as a trailer with key `https`.

Exclude bot authors, whose machine style skews every statistic. And
check `git rev-parse --is-shallow-repository` first: a shallow clone
yields a one-commit sample and a confident, wrong profile.

### Writing the message so it survives

`git commit -F -` with a quoted heredoc is the editor-free way to
supply a multi-paragraph message.

Two settings can silently mangle it. `commit.cleanup=strip` deletes
body lines beginning with the comment character — a line starting
`#123` simply vanishes, with no warning and no editor involved. Read
`commit.cleanup` and `core.commentChar`, or pass `--cleanup=verbatim`
and own message hygiene entirely.

`prepare-commit-msg` runs on `-m` and `-F` commits and is **not**
suppressed by `--no-verify`, so a repo hook can rewrite what you
wrote. Re-read what actually landed:

```
git log -1 --format=%B
```

Rebase replay never fires the `commit-msg` hook, so a recut can land
messages the project's own linter would reject. Run the linter
yourself as a per-commit gate.

## Part 2 — Recover the intent

Gather all of this **before** collapsing the branch. After the soft
reset the original commits are only reachable through the backup ref.

### The commits themselves

The original messages are the primary source, however poor. Read them
whole, not just subjects:

```
git log --no-merges --format='%H%n%B' <base>..HEAD
```

Harvest trailers so attribution survives the rebuild — `Co-authored-by`
especially, which is how GitHub assigns credit:

```
git log --format='%(trailers:only=true,unfold=true)' <base>..HEAD
```

Two more git-native sources are usually ignored. `git notes` may carry
rationale, and `git stash list` may hold abandoned approaches that
explain why the landed approach looks the way it does. Notes do not
survive the recut on their own: `reset --soft` plus `commit` is not a
rewrite as far as git is concerned, so no note is copied. Carry
anything worth keeping into the message itself, which is the only
place that is durable and visible to everyone — notes are neither
pushed nor fetched without an explicit refspec.

### The pull request and its review

```
gh pr view <n> --json title,body,commits,reviews,comments,closingIssuesReferences
```

Review threads carry the reasoning that never made it into a commit,
and they are the one source holding another person's opinion. Grouping
and the resolved/outdated flags are only exposed through GraphQL;
REST returns the comments ungrouped.

An empty `closingIssuesReferences` does not mean there is no ticket —
it means GitHub never resolved a link. Also scan the PR body, commit
trailers, subject prefixes, and the branch name.

### Linked tickets

Resolve GitHub issues through `gh issue view`. For other trackers, use
whatever MCP server the session has connected, read-only; fall back to
a tracker CLI, and when neither exists, ask for the ticket text rather
than skipping the context.

Preserve linkage through the rewrite, and prefer a trailer for it. A
`Refs: PROJ-12` trailer survives reflow; a Jira Smart Commit directive
does not, because those are line-scoped and re-wrapping a message
during a recut can break a transition that used to fire. Linear often
carries the linkage in the branch name alone, so promote the
identifier into a trailer before a later squash loses it.

Closing keywords are a special case: moving `Closes #12` between the
PR body, a commit subject, and an intermediate commit changes what
actually closes on merge. Leave a closing keyword where it was.

### The session that wrote the code

When the repository does not explain itself — an approach with no
recorded rationale, work resumed after a gap — the conversation that
produced the code may still exist locally.

```
uvx agentgrep search --only-here --branch "$(git branch --show-current)" --limit 20 <terms>
```

Derive the search terms from what the earlier sources already found:
the feature name, the ticket ID, the module the diff concentrates in.
Generic words return generic noise. Search prompts before
conversations — the default scope returns what the user asked for,
which is the record of intent.

This layer is opt-in and never a hard dependency. Transcripts also age
out; a branch older than the retention window simply has none, which
is not the same as there having been no intent.

A prior conversation is evidence of **intent**, not of **state**. A
plan discussed three weeks ago may have shipped, been abandoned, or
been reversed, and the transcript reads identically in all three
cases. Check every finding against the diff in front of you; when they
disagree, the code wins.

### Privacy — this is a hard gate

A transcript is an unredacted record of everything that passed through
a tool: file contents, command output, pasted text, environment. The
base rate of leakable material in one is high, not hypothetical.

**Extract the claim and re-state it in your own words. Never copy a
span.**

Never carry any of this into a commit message: credentials and tokens;
absolute local paths and usernames; internal hostnames, IPs, and
private URLs; the contents of `.env`, key, or config files; verbatim
command output; third-party names, emails, and customer data;
unredacted stack traces; or any file body quoted by a tool result.

The same applies to the reasoning itself. Abandoned approaches and
intermediate branch states shape the message but do not belong in it
unless users of a published release actually experienced the old
behavior.

## What a recut message owes the reader

The subject says what changed. The body says why it had to, in the
project's own format, at a length proportional to the change.

The commit message is the right home for branch-internal narrative —
the renames, the attempt that was reverted, the reason a simpler
approach did not work. That material belongs here precisely because it
does not belong in the code, the README, or the pull request
description.

If the body is getting long enough to describe two things, that is the
signal to split the commit rather than to keep writing.
