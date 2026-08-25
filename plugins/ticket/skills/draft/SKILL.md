---
name: draft
description: "Use when asked to file a Linear issue or regression, draft a Jira epic, open a GitLab issue, or create a Shortcut story or tracker document."
---

# Draft a ticket

Write work into a tracker so that someone picking it up in a year needs
nothing from you, and so that the code still gets to make the decisions the
code should make.

Argument: `$ARGUMENTS` — a description, a URL, a provider name, a pasted
finding, or nothing.

For a plain GitHub bug report, `gh:create-issue` is more specialized; hand
off to it when it is installed and the target is a GitHub `work_item`. This
skill covers every other provider, and every altitude above and below a
single issue.

## Read first

- `../../references/contract.md` — the three tenses.
- `../../references/hierarchy.md` — what kind of object this
  is, in this provider.
- `../../references/altitude.md` — which sections that kind
  of object carries.
- `../../references/resolve.md` — how to establish the above
  from evidence.
- The provider's own file, indexed in `hierarchy.md` under Provider files —
  its hierarchy, reference syntax, and filing mechanics.

## Core principle

Evidence before prose, and altitude before evidence.

Most bad tickets are not badly written. They are written at the wrong
altitude — a design document filed as an epic, a research note filed as an
issue, an implementation plan filed as a goal. Settle what the object is
before deciding what goes in it.

## Phase 1 — Resolve the target

Establish the provider, the scope container, and the semantic role, following
`resolve.md`. Do not infer the provider from key shape: `#123` and `ENG-123`
each fit several trackers.

When the role is ambiguous between two levels, ask. The difference between a
`delivery_group` and a `work_item` changes almost every section, and guessing
wrong produces a body that reads as either bloated or empty.

## Phase 2 — Decide it belongs in this tracker, publicly

A vulnerability does not. For a public repository, check the security policy
before anything else and follow its private path if the finding is a security
defect.

Stop and ask when the evidence cannot be sanitized. An internal log carrying
customer data does not become fileable by trimming it.

## Phase 3 — Preflight the container

Read the project's own conventions before imposing any: issue templates and
forms, required fields, work types actually configured in this instance,
labels that exist. Instance configuration beats the provider defaults in
the provider file; when they disagree, follow the instance and record the
deviation.

A template's structure wins over the section order in `altitude.md`. Fill it
in rather than restructuring it, and apply the contract to what you put in
its fields.

## Phase 4 — Look for the thing that already exists

Search open and closed items. A closed one is often the answer, and a
duplicate of a closed item is a regression report, which is a better and
different thing to file.

Read the candidate before dismissing it. When one matches, say so, stop, and
offer to comment on it with the new evidence instead.

## Phase 5 — Gather

For a defect: the smallest sequence that reproduces it, actually run; exact
versions; the verbatim error; the code that causes it, pinned.

For a proposal: what is awkward or impossible today, shown concretely.

For provenance: apply the cost-to-relearn filter from `contract.md`. Mine
merged changes, closed items, and the current conversation for findings that
cannot be recovered from the repository — measurements with their conditions,
dead ends with reasons, retracted numbers with what was actually measured.
Drop everything a reader gets by opening the file or reading the log.

Reproduce before writing. An unreproduced defect is filed as an observation,
and says so.

## Phase 6 — Draft

Take the section list from `altitude.md` for the resolved role. Include only
sections you have content for; never invent one.

Write references per `contract.md`'s two-axis rule and the provider file:
bare where the renderer resolves it, fully qualified across containers, and
titled where a bare identifier would be ambiguous. Suppressing the
backreference is a separate question with a per-provider answer — do not
assume a titled link is the quiet form, because on GitHub and GitLab it is
not.

Use the provider's native noun for every object you name. Never write `Epic`
for a Linear Project or `Pull Request` for a GitLab merge request.

Then check the future tense specifically. Every invariant must pass the test:
*if violated, is the work pointless, or is a neighbour broken?* Demote
everything else to intent and label it non-binding. If the draft contains a
checkbox list of technical outcomes, it is wrong — rewrite it.

## Phase 7 — Sanitize, then check, then preview

Reread the whole body for local absolute paths, hostnames, emails, tokens,
and internal URLs, including inside every pasted log. This is a gate.

Resolve the slop registry for the mechanical checks. First hit wins:

1. `../../../pr/references/signatures.yml`
2. `../../../slop/references/signatures.yml`

An installed plugin caches under a version directory, so a sibling sits one
level further out than those paths suggest. Glob the version segment rather
than hard-coding it, and run the glob through `sh` — zsh treats an unmatched
glob as a fatal error and would abort before reaching the flat-layout
fallback.

No hit means no registry: say so in one line and continue with judgment
alone. The check is non-blocking by design.

Render the body the way the provider will before showing it. Markdown
dialects differ, and a details block that lost its blank line renders as
literal asterisks.

## Phase 8 — Present, then file

Show the full title and body. Then offer, via `AskUserQuestion`: file it,
print the body only, revise a named section, or drop it.

File through a real backend when the provider file says one exists, passing
the body from a file rather than an inline argument so fences, HTML, and `$`
survive shell quoting. Where no backend exists, print the approved body for
the user to paste and say plainly that is what is happening.

Return the URL when there is one, then offer the next step: open it, add a
comment, or start a branch for it.

## Rules

- Read-only until the filing gate. No commits, no pushes, no edits to
  existing items.
- Never file without showing the full title and body first.
- Never invent a version, an error string, a line number, a link, or a
  reference syntax. Unverified goes in marked unverified, or comes out.
- Never `@mention` anyone in a generated body. Mentions send mail.
- Never synthesize a hierarchy level the provider does not have.
- Language-agnostic: discover how to build, run, and test from `AGENTS.md`,
  `CLAUDE.md`, or `CONTRIBUTING.md`.

## Common mistakes

**Filing the design instead of the work.** If a paragraph would survive being
replaced by a link to a document, replace it. Write the document if it does
not exist yet.

**Filing the investigation instead of the finding.** The reader needs what
reproduces it, not the hypotheses that led there.

**A definition of done that decides the implementation.** "Storage engine
chosen" is not a delivery anyone experiences. It is a vote, cast before the
code had a say.

**A threshold as a gate.** A number in the future tense is a guess wearing a
uniform. If a floor is existential, state it as what a user notices.

**Borrowing another provider's noun.** Calling a Linear Project an Epic, or a
GitLab merge request a pull request, is a correctness error.

**Reporting a symptom with no version.** It ages into an item nobody can
close, because nobody can tell whether it still happens.
