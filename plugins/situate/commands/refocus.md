---
description: Re-derive what this work is for from its ticket and pull request, sort every commit into on-goal, load-bearing, and drift, name what the goal asked for that is still missing, and propose the correction
argument-hint: "[the goal, when the repo does not record one]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "AskUserQuestion"]
---

# Refocus

Work wanders. This finds out how far, in which direction, and whether
the wandering was wrong.

Read `${CLAUDE_PLUGIN_ROOT}/references/goal-derivation.md` first — it
defines the precedence for deriving the goal, why nothing is stored
between runs, the three-way classification, and the four correctives.
Read `${CLAUDE_PLUGIN_ROOT}/references/situation-sweep.md` for how to
resolve trunk, the base commit, tickets, and the pull request, and for
the read-only contract both commands share.

User arguments: $ARGUMENTS

## Context

Current branch:
`!git branch --show-current 2>/dev/null || echo "(detached HEAD)"`

Ahead / behind trunk:
`!git rev-list --left-right --count "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)"...HEAD 2>/dev/null || echo "(no comparison available)"`

Working tree:
`!git status --short 2>/dev/null | head -20 || echo "(unavailable)"`

Commits on this branch:
`!BASE=$(git merge-base HEAD "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)" 2>/dev/null); if [ -n "$BASE" ]; then git log --no-merges --format='%h %s' "$BASE..HEAD"; else echo "(no base commit resolved)"; fi`

## Procedure

### 1. Derive the goal

`$ARGUMENTS`, when given, is the goal. It is a statement from the user
and outranks every artifact.

Otherwise work down the precedence in the goal-derivation reference:
what the user stated earlier in this session, then the linked ticket's
acceptance criteria, then the pull request body, then the branch name
and its first commit.

Resolve ticket IDs only from commits, the branch name, and the pull
request body. Read the ticket body rather than its title — a title names
a topic, the criteria say what done means.

Say which source the goal came from. A goal from acceptance criteria and
a goal from a branch name are both goals, and the reader must be able to
tell them apart before acting on the assessment.

If no source yields one, stop and ask. Do not infer the goal from the
diff: a goal derived from the work cannot detect drift in that work,
because every commit matches it by construction.

### 2. Read what was actually done

Commits since the base, the diff behind them, and the uncommitted
changes. Uncommitted work counts — drift often lives there first,
because it has not yet had to justify itself in a commit message.

### 3. Classify

Sort each commit and each uncommitted change: on goal, load-bearing
detour, or off goal. Take the middle category seriously — a fixture
repair that unblocked the feature is correct work, and reporting it as
drift teaches the user to distrust the command.

For off-goal work, find the first commit where it started. That commit
usually explains the whole excursion.

### 4. Find the gap

Walk the goal's criteria one at a time and check each against the
branch. What was asked for and has no work behind it is drift as much as
work nobody asked for, and on a resumed ticket it is the half that is
invisible — the branch looks busy either way.

### 5. Propose the correction

Finish the gap, defer the off-goal work, drop it, or widen the goal.
Recommend one and say why.

Do not assume the goal wins. When the excursion was the better instinct,
the correction is to update the ticket or the pull request body to
match what is being built, not to revert good work for disagreeing with
a stale description.

## Rules

- Read-only. No commits, no pushes, no edits, no stashes, no branch
  switches, no `git fetch`. This runs when the user's read of the
  situation is itself in question; changing the situation mid-assessment
  is the one thing that cannot be undone by disagreeing with the report.
- Never write the goal to a file. It is re-derived every run.
- Cite only ticket IDs found in the commits, the branch name, or the
  pull request body.
- When the ticket and the pull request describe different things, report
  both readings rather than silently picking one.
- Separate what was read from what was inferred. "This commit does not
  serve the criteria" is read; "this was probably a rabbit hole" is
  inferred and gets marked.
- No local absolute paths, no third-party personal details.

## Output

Open with a one-line hero — `✓ On goal: <goal> · <n> commits`, or
`⚠ Drift: <what wandered>`, or `⚠ No goal recoverable` — then exactly
these sections:

1. `## Goal` — the goal in one or two sentences, and the source it came
   from with its confidence.
2. `## On track` — the work that serves the goal, grouped by area, with
   load-bearing detours named alongside what each unblocked.
3. `## Drift` — off-goal commits and uncommitted changes, where the
   excursion started, and the pattern behind it; or that there is none.
4. `## Gap` — criteria the goal asks for with nothing on the branch
   addressing them; or that there are none.
5. `## Realign` — the recommended correction and the reasoning, followed
   by the alternatives that were not recommended.

End with an `AskUserQuestion` panel offering the correctives as actions
— finish the gap, split the off-goal work to a follow-up, drop it, widen
the goal to match the work — so the user can choose without composing a
command. Skip the panel only in plan mode.
