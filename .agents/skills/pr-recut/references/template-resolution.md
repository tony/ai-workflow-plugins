# PR Template Resolution

Shared procedure for commands that draft a PR description from scratch
(`/pr` and this skill). the `pr-refresh` skill never performs template
resolution — it preserves the existing description's structure and must
not discuss structure or templates at all.

## Precedence

1. **Template mentioned in the user's message.** If the user's message
   or command argument names a template (a file path, a repo-relative
   path, or a URL), read that file and use it. An explicit mention wins
   over everything below — no question needed. If the mentioned path
   does not exist, ask the user to correct it; do not silently fall
   back.

2. **Repository template.** Search the standard GitHub locations,
   case-insensitively:
   - `.github/pull_request_template.md`
   - `pull_request_template.md` (repo root)
   - `docs/pull_request_template.md`
   - `.github/PULL_REQUEST_TEMPLATE/*.md` (multi-template directory)

3. **No template found.** Use the gold-standard section patterns from
   the `/pr` command. Do not mention templates to the user in this
   case.

## When to ask

Ask via `ask-user-choice` — never guess — when:

- The multi-template directory contains more than one template and the
  user's message doesn't indicate which applies.
- Templates exist in more than one standard location and they differ.
- The user's mention is ambiguous (e.g., a name matching several
  files).

Offer the candidate templates as options, plus falling back to the
gold-standard structure.

## Blending rule

When a template is in play, the **template supplies the structure**:
its sections, their order, and its headings are kept verbatim,
including HTML comments and checklists. The gold-standard patterns
(bold impact labels, tables, verification commands, proportionality)
fill in the content *within* that structure. Add a section the template
lacks only when the diff clearly warrants it, and say so when
presenting the draft.
