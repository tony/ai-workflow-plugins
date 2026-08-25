---
name: rebuild
description: "Use when rebuilding a bloated tracker item whose epic or Jira ticket hard-codes implementation, restates a spec, or cites counts and line numbers."
---

# Rebuild a ticket

Rebuild one live tracker item against the content contract. Not a trim — a
rebuild, at the altitude the item should have been written at.

Argument: `$ARGUMENTS` — a URL, an identifier, or nothing (then ask).

## Read first

- `../../references/contract.md` — the three tenses.
- `../../references/hierarchy.md` — what kind of object this
  is, in this provider.
- `../../references/altitude.md` — which sections that kind
  of object should carry.
- `../../references/resolve.md` — how to establish the above.
- The provider's own file, indexed in `hierarchy.md` under Provider files — reference
  syntax, read and write mechanics.

## Core principle

Nothing valuable is deleted. It is kept, relocated, or demoted.

An overgrown ticket is usually not padded. It is a document, a research note,
and a work item that got filed as one object. The fix is to separate them,
not to compress them.

## Phase 1 — Fetch and preserve

Resolve the provider and identifier per `resolve.md`, then fetch the live
item with its comments. Comments matter: the decision that supersedes the
body is often in one.

Write the original body to a scratch file outside the working tree before
touching anything.

```bash
ORIGINAL=$(mktemp "${TMPDIR:-/tmp}"/ticket-original-XXXXXX.md)
```

Some providers keep edit history and some do not. Do not rely on the tracker
to hold your undo.

## Phase 2 — Resolve the altitude it should be

Establish the current semantic role, then ask whether the content matches it.
A `work_item` carrying a nine-section design is a `delivery_group` plus a
`document` that were filed as one issue.

The altitude the item *should* be is the finding, not a detail. State it.

## Phase 3 — Audit

Classify every part of the existing body into exactly one bucket. Do not skip
this into a rewrite; the buckets are what you show the user.

**Keep.** Passes the cost-to-relearn filter — a measurement with its
conditions, a dead end with its reason, a retracted number with what was
actually measured, an absorbed-item list with why each folded in, a live
blocker that changes what happens first. Also keep load-bearing links.

**Cut.** Recoverable from the repository. File sizes, insertion counts, line
counts, test counts, what got renamed, which module was split, how long a
draft was. Also the sequence of hypotheses that led to a finding, and any
narration of revisions that happened before the item was published.

**Relocate.** Valuable, but not at this altitude. A design restated from an
ADR, a research pass with prior-art citations, an implementation sketch. This
goes to a `document`, and the item links to it. Offer to create the document
where the provider has one, or to write it into the repository where it does
not.

**Demote.** Future-tense content that is not existential. A definition-of-done
checklist becomes a small set of invariants plus intent labelled non-binding.
Most checklist items demote; a couple survive as invariants; any that encode
a technical decision are cut outright and the reasoning goes to intent.

**Repair.** References that rot or misfire — `blob/main` links, line anchors
on unpinned refs, bare cross-container references, bare identifiers that are
ambiguous out of context. Rewrite them per the two-axis rule and the provider
file. Re-saving a body can re-fire every reference in it, so check the
provider file before assuming an edit is silent.

## Phase 4 — Find what is missing

Most overgrown items are also missing something. Check for all of these:

- No invariants at all, because everything was stated as a requirement.
- An outcome that never says what changes for whom.
- Evidence asserted without a reproduction or a version.
- Children or absorbed items referenced in prose but never linked.
- A superseding decision that lives only in a comment.

Absence is a finding. Report it with the rest.

## Phase 5 — Rebuild

Write the new body from the audit, not by editing the old text. Take the
section list from `altitude.md` for the role the item should be.

Then verify the future tense specifically. Every surviving invariant passes
the test: *if violated, is the work pointless, or is a neighbour broken?*

Sanitize for local paths, hostnames, emails, tokens, and internal URLs. Then
run the mechanical checks, resolving the registry at the first hit:

1. `../../../pr/references/signatures.yml`
2. `../../../slop/references/signatures.yml`

An installed plugin caches under a version directory, so a sibling sits one
level further out than those paths suggest. Glob the version segment rather
than hard-coding it, and run the glob through `sh` — zsh treats an unmatched
glob as a fatal error and would abort before reaching the flat-layout
fallback.

No hit means one line saying so, then continue on judgment.

Render the new body the way the provider will.

## Phase 6 — Present

Show, in this order:

1. A hero line: the role it is, the role it should be, and the bucket counts.
2. **Kept** — what survived, and why each item could not be re-derived.
3. **Cut** — what went, grouped by reason.
4. **Relocated** — what moved, and where it is going.
5. **Demoted** — the old definition of done beside the new invariants.
6. **Missing** — what the item never had.
7. The full rebuilt title and body.

Then offer, via `AskUserQuestion`: update the item, update and also create the
relocated document, print the body only, revise a named section, or drop it.

## Phase 7 — Update

Only on explicit approval, and only through the provider's documented write
path with the body passed from a file.

Where no write backend exists, print the approved body to paste and say that
is what is happening.

When a document was relocated, create it first and land its link in the
rebuilt body before the item is updated, so the item never points at
something that does not exist yet.

Report the URL, keep the scratch original until the user confirms, then
remove it.

## Rules

- One item per run. No bulk passes.
- Never update without showing the full diff and the bucket breakdown.
- Never delete content that belongs in the relocate bucket. If the user
  declines the document, keep the content in place and say it is staying.
- Never rewrite comments, only the body. Comments are other people's words.
- Never close, reassign, relabel, or reparent the item. Rewriting a body is
  the whole mandate.
- Never `@mention` anyone in a rebuilt body, including mentions that were in
  the original. Re-saving a body can re-send mail.
- Never invent a reference syntax or a link that was not verifiable.

## Common mistakes

**Compressing instead of separating.** A 40,000-character research issue does
not become a good issue by getting shorter. It becomes a document plus a
short issue that links to it.

**Deleting the retraction.** A note saying which circulating numbers are
wrong looks like clutter and is the most expensive thing in the body.

**Treating every checklist item as an invariant.** Most are intent. Keeping
them all as invariants is the failure being fixed, restated in new
vocabulary.

**Rewriting at the altitude it was filed at.** If the audit says it is the
wrong kind of object, rebuilding it as a better version of the wrong kind of
object solves nothing.
