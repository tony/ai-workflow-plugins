---
name: situate-what
description: >-
  Say what is going on in five lines or less — the session, the branch, the
  pull request and ticket if they exist — with numbered options when there
  is a real choice to make
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
metadata:
  argument-hint: "[what you are confused about]"
  source: "plugins/situate/commands/what.md"
---

# What

The reader is disoriented. End that in five lines.

Read `references/brief.md` first — it defines the
five-line budget, what earns a line, the option lines, and the evidence
tiers that keep this cheap enough to ask casually.

User arguments: $ARGUMENTS

## Context

Current branch — run this command and read the output:

```bash
git branch --show-current 2>/dev/null || echo "(detached HEAD)"
```

Ahead / behind trunk — run this command and read the output:

```bash
git rev-list --left-right --count "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)"...HEAD 2>/dev/null || echo "(no comparison available)"
```

Working tree — run this command and read the output:

```bash
git status --short 2>/dev/null | head -20 || echo "(unavailable)"
```

Commits since trunk — run this command and read the output:

```bash
BASE=$(git merge-base HEAD "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)" 2>/dev/null); if [ -n "$BASE" ]; then git log --no-merges --format='%h %s' "$BASE..HEAD" | head -15; else echo "(no base commit resolved)"; fi
```

## Procedure

### 1. Read what was actually asked

Empty `$ARGUMENTS` means the whole situation: what this session has been
doing, and where the repository stands.

An argument narrows it to that subject, and narrowing is the point —
`this skill the test failure` answers about the test failure and
spends no lines on branch position.

### 2. Answer from the session first

The conversation is the highest-value evidence and the cheapest. When
the confusion is about what just happened — a command that ran, a
decision taken, why the work moved — the answer is already in context
and needs no tools at all.

The context block above is local git, already gathered. It measures from
trunk, which is the cheap approximation this command is built on — on a
branch stacked over another branch that range carries the parent's
commits too, so treat the count as approximate and say so rather than
re-resolving the base for a five-line answer.

Go beyond the block only for the paid tier in the brief reference: a
pull request when the branch has one, a ticket when an ID appears in the
branch name, a commit, or the pull request body.

### 3. Write the brief

Five lines maximum, ranked as the brief reference sets out: the blocker
first, then position, then what just happened, then what it is for, then
what is outstanding. Stop early when the situation runs out.

Then numbered single-line options — only when there is a real fork.

## Rules

- Read-only, and the same contract as `/situate`: no commits, no edits,
  no branch switches, no `git fetch`.
- Five lines is a ceiling on the body, not a target. Three good lines is
  a better answer.
- No headings, no preamble, no bullets in the body, no closing summary.
- Never spend a line reporting that a layer was checked and was quiet.
- One hedged inference at most. Two means say what is unknown instead.
- No `ask-user-choice` panel — the options are plain numbered lines. A
  modal is heavier than the answer it would follow, and this command is
  often reached ambiently, mid-thought.
- If the branch has wandered from what it was for, do not diagnose it
  here. Say so in a line and offer the `situate-refocus` skill as an option.
- No local absolute paths, no third-party personal details.

## Output

The body, then the options. Nothing else — no title, no framing
sentence, no offer to go deeper.

```
⚠ CI is red on PR #12: the type-check job fails on three files this branch added.
feat-brief-mode, 4 commits ahead of main, 2 files uncommitted.
This session rewrote the output contract and has not re-run the gates since.
The ticket asks for a terse mode; the terse mode works, the failing types do not.

1. Fix the three type errors and push
2. Show the failing job output
3. Stash the uncommitted work and check whether the branch alone is green
```


## Portability notes

- `ask-user-choice` — present the listed options and wait for the user to pick one. Hosts with a structured multiple-choice tool (Claude Code's `AskUserQuestion`) should use it; otherwise print a numbered list and wait for a numbered reply. Never proceed on an assumed answer.
- `$ARGUMENTS` — the text the user passed when invoking this skill. If your host does not substitute it, read it as the user's request in the current turn, and ask when there is none.
- Bundled files — every relative path in this skill points at a file shipped inside this skill directory. Read them from here, not from the host's plugin tree.
