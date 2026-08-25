---
name: skill-style
description: "Use when writing, auditing, or trimming a SKILL.md, especially for bloated bodies, weak descriptions, or plugin-wide sweeps."
user-invocable: true
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Edit", "AskUserQuestion"]
argument-hint: "[skill paths/globs] [--audit] [--diff-only]"
---

# Skill style

One bar: a line stays only when its removal would change what the
agent does.

## Two ways in

### Routed while authoring

Someone is writing or editing a SKILL.md. Apply the rules below to
that draft as it is written. Touch no other file, propose no audit of
the rest of the catalog.

### Invoked by name with targets

Audit the named skills, edit them in place, print a diff. Never
commits, never pushes, never needs a clean tree.

## `$ARGUMENTS`

- `paths/globs` — skill directories or `SKILL.md` files. Expand
  through `git ls-files` when tracked, else as literal paths.
- `--audit` — report the ledger and change nothing.
- `--diff-only` — show the edits without writing them.

Empty `$ARGUMENTS` with no draft in play: ask which skills via
`AskUserQuestion`. Never default to the whole repository.

## The deletion test

Read the body one line at a time. For each, name the behavior that
changes when it is gone:

- A command that would not run, or would run with wrong arguments.
- A constraint the agent would violate — an ordering, a destructive
  step, a thing it must never do.
- A trigger that would stop firing.
- An output whose shape or format would drift.
- A fork the agent would take the wrong branch of.

Name one and the line stays. Name none and the line goes. *Adds
context*, *reads better*, *rounds it out*, and *harmless* are not
names — they are the absence of one.

Run it on whole blocks too. A section whose every line survives
individually still goes when the agent already does that by default;
the test asks what breaks, not what is true.

Record a ledger before editing — one row per cut, naming the line and
why nothing breaks. The ledger is the review surface, and it is what
you show under `--audit`.

## Lines the test never touches

The test judges claims. These are not claims:

- **YAML frontmatter.** Held to whether it routes, not to whether it
  changes behavior — the standard below, never the deletion test.
- **Fenced code blocks, and every character inside them.** Never
  reflow, reformat, shorten, modernize, or correct a command, path,
  flag, or snippet. Drop a whole fence only when a sibling fence
  teaches the same thing — never a line out of a fence's middle.
- **Literal commands, paths, and flags in prose.** Backtick them and
  leave them alone.
- **Section headings.** They are the navigation an agent skims.
- **Warnings on destructive or irreversible steps.** A cut here is
  paid for by someone else.

Where a fence and its prose say the same thing, the prose goes.

## Sections

Bodies are sections, never a wall.

- One `#` title, then `##` sections. A heading names the step or the
  decision, not the topic — never `Context`, `Details`, `Notes`, or
  `Misc`.
- Steps that must run in order are a numbered list. Otherwise ask
  whether the items reorder without changing meaning: siblings are
  bullets, an argument is prose.
- State the rule before its exceptions. Exceptions first leave the
  agent without the model they qualify.
- Prose runs at most three lines before a heading, a list, or a fence.
- One command per fence, `console` tag, `$ ` prefix, comments outside
  it.
- A fence says when to run it and what its result means. Cutting prose
  that repeats a command is not the same as shipping the fence bare.
- Prefer nested sections over tables. A table earns its place only
  when the data is genuinely matrix-shaped.

## Frontmatter and description

The description is the only text a host sees before deciding. Write it
in third person, saying both what the skill does and when to reach for
it, in the literal words a user would type.

- `name` — lowercase letters, numbers, hyphens; 64 characters or
  fewer. Gerunds and noun phrases both read well; `helper`, `utils`,
  and `tools` name nothing.
- `description` — 150 characters or fewer. Front-load the trigger.
  Never `I can help you…` or `You can use this to…`.
- Set `disable-model-invocation: true` when the skill only makes sense
  asked for by name, so it stays out of the routing corpus.

## Body budget

Keep the body under 500 lines. Past that — or for anything a task
needs only sometimes — move the detail into a reference file and link
it from the body. Keep every reference one level deep from the body:
an agent that follows a link to a link reads the second one partially.

## Steps

1. **Load the rubric and the house voice.** Read
   `../../references/skill-rubric.md`, then `./AGENTS.md` and
   `./CLAUDE.md`.
2. **Fix the description before touching a line of the body.**
3. **Measure.** Line counts locate the bloat:

   ```console
   $ git ls-files '*SKILL.md' | xargs wc -l | sort -n
   ```

4. **Run the deletion test** and build the ledger.
5. **Confirm, then edit.** Show the ledger and confirm via
   `AskUserQuestion` before writing. Skip under `--audit` or
   `--diff-only`.
6. **Diff.**

   ```console
   $ git diff --stat -- <targets>
   ```

7. **Test the trigger.** Write three prompts a user would actually
   type and confirm the description answers each; write one that must
   belong to a different skill and confirm it does. A description that
   fails this is not done.

## References

- `../../references/skill-rubric.md` — the full rule catalog, the
  anti-patterns, and the pre-ship checklist.
- `../../references/example-bloated.md` — a bloated skill with every
  defect named.
- `../../references/example-ideal.md` — the same skill, rewritten.

## While trimming, do not add bloat

Replacements are concrete and shorter than what they replace. Never
narrate the edit inside the file — no *simplified*, no *previously*,
no note that a section used to be longer. The skill states its current
instructions and nothing about how it got here.
