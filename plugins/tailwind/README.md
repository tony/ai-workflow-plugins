# tailwind

Detect and fix inconsistent spacing in Tailwind CSS layouts — container fragmentation, margin/gap mixing, padding asymmetry, and more.

## Installation

Add the marketplace:

```console
/plugin marketplace add tony/ai-workflow-plugins
```

Install the plugin:

```console
/plugin install tailwind@ai-workflow-plugins
```

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| Tailwind Spacing Audit | `/tailwind:spacing-audit` | Systematically detect and fix inconsistent spacing in Tailwind CSS v4+ layouts |

## How It Works

The spacing audit follows a 5-step workflow:

1. **Detect framework** — Scan for `.tsx`, `.jsx`, `.vue`, `.svelte`, `.astro`, `.html`, `.erb`, `.blade.php` to determine the attribute name (`className` vs `class`) and file globs
2. **Structural audit** — Read the component and produce a spacing map annotating every spacing mechanism acting on the element group
3. **Classify anti-patterns** — Match against seven heuristics (H1-H7) covering container fragmentation, margin/gap mixing, padding asymmetry, fixed widths, wrapper nesting, hit target inconsistency, and space-x/gap collision
4. **Refactor** — Merge fragmented containers, choose one spacing authority per relationship, standardize envelopes, flatten wrappers
5. **Validate** — Re-draw the spacing map and confirm single authority, consistent containers, uniform envelopes, and hit targets

## Framework Support

The skill automatically detects which frameworks are in use and adjusts search patterns accordingly:

| Framework | File extensions | Attribute |
|-----------|----------------|-----------|
| React | `.tsx`, `.jsx` | `className` |
| Vue | `.vue` | `class`, `:class` |
| Svelte | `.svelte` | `class` |
| Astro | `.astro` | `class` |
| HTML | `.html` | `class` |
| Rails (ERB) | `.erb` | `class` |
| Laravel (Blade) | `.blade.php` | `class` |

## Arguments

Target specific files or components:

```console
/tailwind:spacing-audit src/components/TopNav.tsx
```

```console
/tailwind:spacing-audit src/layouts/
```

## Prerequisites

- A project using **Tailwind CSS** (v4+ recommended, v3 also works)
- Template files in any supported framework
