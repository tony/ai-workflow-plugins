---
name: tailwind-spacing-audit
description: >-
  This skill should be used when the user mentions uneven spacing, alignment
  issues, inconsistent gaps between elements, mixed margin/gap strategies,
  navbar or toolbar spacing problems, or asks to "clean up", "normalize", or
  "audit" spacing in a Tailwind component. This skill also applies when reviewing UI code
  where flex/grid containers use a mix of gap-*, margin (m*, me-*, ms-*),
  padding, and fixed widths to space sibling elements — even if the user
  doesn't explicitly say "spacing." If someone pastes a nav bar, toolbar,
  header, or action bar and says "something looks off," this skill is almost
  certainly what they need.
user-invocable: true
argument-hint: <file-or-directory-to-audit>
---

# Tailwind Spacing Audit & Refactor

Systematically detect and fix inconsistent spacing in Tailwind CSS v4+ layouts. The root
cause of most spacing bugs is **fragmented spacing authority** — multiple competing
mechanisms (gap, margin, padding, fixed widths) controlling the space between the same set
of visual peers.

Use `$ARGUMENTS` as the target scope. If `$ARGUMENTS` is empty, ask the user which
component or file to audit.

## Philosophy

Good spacing has one property: **a single source of truth per spacing relationship.** Every
pair of adjacent items should have exactly one class/mechanism determining the space between
them. When `gap-2` appears on a parent AND `me-1` on a child AND `ms-2` on a sibling, three
competing authorities produce visual noise.

The goal is never "make all numbers the same" — it's to ensure each spacing decision is
intentional, non-redundant, and traceable to one mechanism.

## Workflow

### Step 0: Detect Framework

Before auditing, detect the project's templating framework to determine which attribute
name and file globs to use throughout the audit.

Scan the project for template files:

- `*.tsx` / `*.jsx` — React (`className=`)
- `*.vue` — Vue (`class=`, `:class=`)
- `*.svelte` — Svelte (`class=`)
- `*.astro` — Astro (`class=`)
- `*.html` — plain HTML (`class=`)
- `*.erb` — Rails ERB (`class=`)
- `*.blade.php` — Laravel Blade (`class=`)

Use the detected attribute name(s) and file globs for all subsequent search commands. If
multiple frameworks are present, search across all of them.

For React projects, use `className=` in search patterns. For all other frameworks, use
`class=`. When both React and non-React templates exist, use `(class|className)=` to
match both.

### Step 1: Structural Audit

Before touching any code, read `references/heuristics.md` for the full detection checklist.
Scan the component and produce a **spacing map** — a brief annotation of every spacing
mechanism acting on the group of elements the user is concerned about:

```
[LinkedIn] --gap-1--> [Wrench] --gap-1--> [Babylon.js] --me-1+flex--> [Theme(me-2)]
            ^ parent gap                   ^ margin leak    ^ separate container
```

This makes fragmentation visible. Call out:
- How many distinct spacing mechanisms are active between visual peers
- Which items live in different containers but appear to be in the same visual group
- Any fixed widths (`w-*`) on items whose siblings are content-sized

### Step 2: Classify Anti-Patterns

Read `references/patterns.md` for the full catalog with before/after examples. The most
common patterns, in order of frequency:

1. **Container fragmentation** — Visually related items split across sibling containers
   with different spacing strategies. The #1 cause of "it looks uneven."
2. **Margin/gap mixing** — A flex parent uses `gap-*` but children also carry `m*-*`.
3. **Padding asymmetry** — Peer interactive elements with different `px-*` values.
4. **Fixed width on content-adaptive items** — One item has `w-24` while siblings size
   to content, creating uneven internal whitespace.
5. **Wrapper nesting** — Unnecessary `<div>` with flex alignment classes wrapping a single
   child, adding an extra layout level that obscures the true spacing. Uses `className`
   in React (`<div className="flex items-center">`) or `class` in other frameworks
   (`<div class="flex items-center">`).

### Step 3: Refactor

Apply these principles in order of priority:

**3a. Merge fragmented containers.** If items belong to the same visual group, place them
in the same flex container. One parent, one `gap-*` value. Remove outer margin classes
(`me-*`, `ms-*`) that were compensating for the split.

**3b. Choose one spacing authority per relationship.** Between any two adjacent items,
exactly one of these should be active — never more:
- `gap-*` on the parent (preferred for uniform spacing)
- Margin on a specific child (only for intentional exceptions)
- Padding inside the child (for internal spacing, not between-item spacing)

**3c. Standardize interactive element envelopes.** Buttons, links, and toggles that are
visual peers should share:
- The same height class (e.g., all `h-8` or all `h-12`)
- The same horizontal padding (e.g., all `px-2`)
- Content sizing (no `w-*` unless every peer also has the same fixed width)

**3d. Flatten unnecessary wrappers.** If a `<div>` wraps a single interactive child purely
for alignment, check whether the child can receive the alignment classes directly. Common
in navbars where each button got wrapped in a single-child alignment div during incremental
development.

**3e. Preserve intentional spacing breaks.** Not every spacing difference is a bug. A
visual separator (like a divider between nav groups) is intentional asymmetry. Ask before
normalizing something that might be a deliberate design choice.

### Step 4: Validate

After refactoring, re-draw the spacing map and confirm:
- [ ] Every pair of adjacent items has exactly one spacing authority
- [ ] All items in the same visual group share one parent container
- [ ] Interactive elements have consistent envelope classes
- [ ] No `w-*` on items that should be content-sized (unless all peers match)
- [ ] Hit targets (clickable area) are consistent across peer elements

## Tailwind v4 Specifics

Tailwind v4 changed how spacing works in important ways:

- `gap-*` is the canonical way to space flex/grid children. Prefer it over margins.
- Arbitrary values use `gap-[12px]` syntax if the scale doesn't have what's needed, but
  prefer scale values (`gap-1` = 4px, `gap-2` = 8px, `gap-3` = 12px, `gap-4` = 16px).
- `space-x-*` and `space-y-*` still exist but are margin-based under the hood. Prefer
  `gap-*` for new code; flag `space-*` as a migration opportunity when found alongside
  `gap-*`.
- CSS logical properties: `me-*` (margin-inline-end) and `ms-*` (margin-inline-start)
  replace `mr-*`/`ml-*` in LTR/RTL-aware code. The anti-pattern is the same regardless
  of physical vs logical naming.

## Output Format

When presenting findings:

1. **Spacing map** — The visual annotation showing current spacing mechanisms
2. **Anti-patterns found** — Numbered list with pattern name and specific elements involved
3. **Proposed refactor** — The actual code change, shown as a focused diff or before/after.
   Only change spacing-related classes; don't rewrite unrelated markup.
4. **Validation checklist** — The Step 4 checklist filled in for the refactored code

When the fix is straightforward, collapse steps 1-4 into a concise explanation + code.
Don't over-formalize simple cases.

## Reference Files

For detailed detection logic and worked examples, consult:

- **`references/heuristics.md`** — Seven detection heuristics (H1-H7) with Tailwind class
  patterns and search commands for codebase-wide scanning
- **`references/patterns.md`** — Anti-pattern catalog with before/after examples for each
  pattern, plus a quick decision tree for diagnosing spacing issues

## What This Skill Does NOT Cover

- Color, typography, or non-spacing visual design
- Responsive breakpoint strategy (though spacing changes should preserve existing breakpoints)
- Component API design or prop architecture
- Tailwind config or theme customization
- Animation or transition timing
