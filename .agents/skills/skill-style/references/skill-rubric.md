# Skill writing rubric

The rules a SKILL.md is held to, and the reasoning behind the ones
whose reasoning is not obvious. Drawn from Anthropic's skill-authoring
best practices and OpenAI's build-skills guidance, which agree on every
point that matters here.

## Contents

- The deletion test, worked
- What the test never touches
- Naming
- Descriptions
- Sections and headings
- Progressive disclosure
- Degrees of freedom
- Workflows and feedback loops
- Terminology
- Anti-patterns
- Trigger testing
- Pre-ship checklist

## The deletion test, worked

Delete the line. Name what the agent now does differently. No name, no
line.

A line survives when its absence costs one of these:

- **A command.** Without it the agent invents a flag, or runs the right
  binary the wrong way.
- **A constraint.** An ordering, a destructive step, a prohibition —
  something the agent would otherwise violate while behaving
  reasonably.
- **A trigger.** Vocabulary in the description that a user's phrasing
  matches.
- **An output contract.** The shape, format, or section order of what
  gets produced.
- **A fork.** A decision point where both branches look defensible and
  only one is right here.

Worked examples, all from real skill bodies.

Cut — the agent already knows what a lockfile is:

```markdown
A lockfile records the exact resolved version of every dependency so
that installs are reproducible across machines. Most ecosystems ship
one.
```

Keep — names a constraint the agent would otherwise violate:

```markdown
Refresh the lockfile in its own commit. A lockfile bundled with a
source change makes the diff unreviewable.
```

Cut — restates the heading above it:

```markdown
## Running the tests

This section explains how to run the tests.
```

Keep — a fork with two defensible branches:

```markdown
Tracked file? Expand through `git ls-files`. Untracked? Treat the
argument as a literal path.
```

Cut — hedging that changes nothing:

```markdown
It is generally considered a good practice to review the output
carefully before proceeding, as this can help catch issues early.
```

Keep — the same idea as an instruction with a consequence:

```markdown
Confirm the plan before writing. An unreviewed batch edit is not
revertable file by file.
```

The trap is that every cut line above is *true*. Truth is not the bar;
changed behavior is.

### Block-level ablation

Run the test on whole sections too. A section whose lines each survive
in isolation still goes when the section as a whole describes the
agent's default behavior. "Analyze the code, then suggest
improvements" survives line by line and teaches nothing.

### The ledger

Before editing, write one row per proposed cut: the line, and the
reason nothing breaks. Cuts you cannot justify in a row are cuts you
have not tested. Under an audit-only run, the ledger is the entire
deliverable.

## What the test never touches

The test judges claims. These are not claims:

**YAML frontmatter.** The host injects `name` and `description` alone
before deciding whether to load the body. A perfect body behind a weak
description is never read.

**Fenced code blocks, and every character inside them.** Never reflow,
reformat, shorten, modernize, or fix a command, path, flag, or
snippet. A command in a skill is a quotation: the author verified it
against a real system, and an edit silently unverifies it. A whole
fence may be dropped when a sibling fence teaches the same thing —
never a line out of a fence's middle.

**Literal commands, paths, and flags in prose.** Backtick them and
leave the characters alone.

**Section headings.** An agent skims headings to decide what to read.
Headings are navigation, not prose, and a body of undifferentiated
paragraphs gets read partially or not at all.

**Warnings on destructive or irreversible steps.** The cost of cutting
one is paid by someone else, later, in a way no review catches.

Where a fence and its surrounding prose say the same thing, the prose
is what goes.

## Naming

`name` takes lowercase letters, numbers, and hyphens, 64 characters or
fewer. It cannot contain XML tags, and it cannot contain the reserved
words `anthropic` or `claude`.

Gerunds read best — `processing-pdfs`, `analyzing-spreadsheets`,
`writing-documentation`. Noun phrases (`pdf-processing`) and
imperatives (`process-pdfs`) are both fine. Pick one shape and keep it
across a catalog.

`helper`, `utils`, `tools`, `documents`, `data`, and `files` name
nothing. A name that would fit twenty skills identifies none of them.

One job per skill. A name you cannot write without an "and" is two
skills, and splitting it is what lets either one route.

## Descriptions

The description is the only text that competes for the router's
attention. It decides whether the skill is ever used.

- **Third person, always.** The description lands in a system prompt.
  `I can help you process Excel files` and `You can use this to
  process Excel files` both confuse the point of view. Write
  `Processes Excel files and generates reports`.
- **What it does and when to reach for it.** Both halves. A
  description with no trigger clause never fires.
- **The user's literal words.** A router matches text, not meaning. If
  people say "repo" and the description says "repository", the match
  is weaker than it looks. Write both where both get typed.
- **Front-load the trigger.** The first clause is what survives
  truncation and skimming.
- **150 characters or fewer**, non-empty, no XML tags.

Working descriptions:

```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

```yaml
description: Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.
```

Descriptions that route nothing: `Helps with documents`, `Processes
data`, `Does stuff with files`.

Where a host supports it, set `disable-model-invocation: true` on a
skill that only makes sense when asked for by name. It keeps the
skill invocable while removing it from the corpus every other
description competes in.

## Sections and headings

- One `#` title. Everything under it is `##`, with `###` only where a
  section genuinely branches.
- A heading names the step or the decision — `Resolve targets`, `When
  the tree is dirty` — not the topic. `Context`, `Details`, `Notes`,
  `Misc`, and `Thoughts` name a container and promise nothing; an
  agent skimming headings learns the shape of the file from them, and
  those four teach it nothing.
- Ordered steps are a numbered list. For anything else, apply the
  reorder test: if the items can be resequenced without changing what
  they mean, they are siblings and belong in bullets. If reordering
  breaks them, they are an argument — write prose. Bulleting a causal
  chain hides the causality that was the point.
- State the rule before its exceptions. An agent that meets the edge
  case first has no model to hang it on, and generalizes the exception
  into the rule.
- One command per fence, comments outside it. Say what the fence is
  for before it, and what its result means after. Cutting prose that
  restates a command is not the same as shipping a fence with nothing
  telling the agent when to run it.
- Prefer nested sections over tables. Repeated semantic headings diff
  and wrap cleanly; a table earns its place only when the data is
  genuinely matrix-shaped and stable.
- No coded labels — `[R1]`, `Option B`, `A1`. A reader should not have
  to decode an index.

## Progressive disclosure

Only the metadata of every installed skill is preloaded; OpenAI's
runtime caps that shared listing at 2% of the context window, or 8,000
characters where the window is unknown. The body loads when the skill
is selected, and bundled files load only when something reads them.

That gives a budget shaped like a funnel:

- **Description:** spend it on triggers.
- **Body:** under 500 lines. Everything a task needs *every* time.
- **Reference files:** everything a task needs *sometimes*. They cost
  nothing until read, so they can be long.

Keep every reference one level deep from the body. An agent that
follows a link out of a file it already followed a link into tends to
preview rather than read it — `head -100` instead of the whole thing —
and acts on a fragment. Link `reference/forms.md` from the body, and
never from inside another reference.

Give a reference file longer than 100 lines a contents list at the
top, so a partial read still shows the full scope of what is there.

Each layer answers a question the one above it did not. A reference
that restates the body in longer words is paid for twice and read
once; it should carry the cases, the worked examples, and the
exceptions the body only names.

Name files for their content: `form-validation-rules.md`, not
`doc2.md`. Organize by domain, so a question about sales loads the
sales file and nothing else.

## Degrees of freedom

Match specificity to how fragile the task is.

**High freedom — prose instructions.** Many valid approaches, decisions
depend on context. A code review is an open field.

**Medium freedom — a parameterized pattern.** A preferred shape
exists, variation is fine.

**Low freedom — the exact command, no parameters.** Fragile,
order-dependent, or destructive work is a narrow bridge. Give the
literal invocation and say not to vary it.

Over-specifying an open field wastes tokens and fights the model.
Under-specifying a narrow bridge is how data gets lost.

Reach for instructions before scripts. Ship a script when the work
needs deterministic behavior or external tooling the agent cannot
reproduce — not to spare it work it would do correctly anyway.

## Workflows and feedback loops

For a multi-step procedure, give a checklist the agent can copy and
tick off, then a section per step. Steps skipped silently are steps
that were never made checkable.

Pair anything quality-critical with a loop: produce, validate, fix,
re-validate, and only then proceed. The validator can be a script or a
reference file the agent checks itself against — the loop is what
raises quality, not the mechanism.

For batch or destructive work, add a verifiable intermediate: have the
agent write its plan to a file, validate the file, and only then
execute. Errors surface before anything is touched.

## Terminology

Pick one term per concept and repeat it. Mixing "field", "box",
"element", and "control" for one thing forces the reader to prove they
are the same. Consistency is not style here; it is parseability.

## Anti-patterns

**Time-sensitive statements.** `Before August 2025, use the old API`
is wrong forever after. Put superseded behavior in a collapsed "old
patterns" section, or leave it out.

**Too many options.** `Use pypdf, or pdfplumber, or PyMuPDF, or…`
makes the agent choose badly. Give one default and one named escape
hatch for the case that needs it.

**Windows-style paths.** `scripts\helper.py` breaks on Unix.
Forward slashes everywhere.

**Assumed installs.** Say what to install before showing what to
import.

**Bare MCP tool names.** Qualify them as `ServerName:tool_name`, or
the agent fails to find the tool once a second server is connected.

**Explaining the domain.** The agent knows what a PDF, a lockfile, a
rebase, and a pivot table are. Skills carry what the agent cannot
know: your conventions, your constraints, your commands.

**Narrating the skill's own history.** No `previously`, no
`simplified`, no note that a section used to be longer. The file is
the current instruction set.

## Trigger testing

A description is not finished until it has been tested as a router
input.

1. Write three prompts a user would actually type — their words, not
   the skill's.
2. Confirm this skill is the right answer to each.
3. Write one prompt that belongs to a neighboring skill, and confirm
   it goes there instead.
4. When a positive fails, the fix is almost always vocabulary: the
   user's word is missing from the description.

Beyond routing, build evaluations before writing the body. Run the
task without the skill first and record where the agent actually
fails; write only enough instruction to close those gaps. Skills
written from imagined failures document problems nobody has.

Test with every model tier the skill will run on. Opus needs less
explanation than Haiku, and a body tuned to one is wrong for the
other.

## Pre-ship checklist

- Description is third person, states what and when, and carries the
  user's literal words.
- Every body line survives the deletion test.
- Body is under 500 lines; the rest is in reference files.
- References are one level deep, and any over 100 lines opens with a
  contents list.
- Code fences are byte-identical to what was verified.
- Sections are headed, and ordered work is numbered.
- One term per concept.
- No time-sensitive claims, no option menus, no backslash paths.
- Three positive trigger prompts and one negative all land correctly.
