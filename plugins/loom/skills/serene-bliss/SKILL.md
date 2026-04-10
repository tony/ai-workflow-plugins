---
name: serene-bliss
description: >-
  Use when the user wants to brainstorm and refine developer-experience,
  documentation, or tooling UX work through a "serene DX" aesthetic lens
  — three fixed variants that sweep across DX Bliss (frictionless),
  DX Serenity (calm clarity), and DX Sublimity (showcase-grade novelty).
  Triggers on phrases like "serene bliss", "DX bliss", "DX serenity",
  "DX sublimity", "reader happiness", "make this serene", "serene
  developer experience", or "serene DX". Runs
  /loom:brainstorm-and-refine with three aesthetic variant lenses and a
  concrete reference anchor.
user-invocable: true
argument-hint: "<prompt> [--passes=N] [--timeout=N|none] [--mode=fast|balanced|deep] [--judge=host|round-robin]"
---

# Loom Serene Bliss

A three-lens aesthetic brainstorm-and-refine pipeline for DX, documentation,
and developer-tooling UX work. Each of the three loom variant slots carries
a different serene-DX lens, so a single invocation yields three
independent aesthetic takes before the refine phase picks and polishes the
strongest.

## When to Use

- Sphinx / MyST / docs site polish (badge styling, navigation, code
  fixture showcases, dark mode, mobile responsiveness)
- CLI / TUI output design — where logging and user-facing output need
  distinct visual channels
- Developer-tooling UX (error messages, empty states, onboarding flows)
- Component galleries, docs landing pages, and reference implementations
  where the output is consumed by humans reading docs

Do **not** use this for implementation work without a reference anchor
named in the prompt — serene-DX prompts need something concrete to
compare against.

## The Three Serene Lenses

| Slot | Lens | Aesthetic | Ask of each model |
|------|------|-----------|-------------------|
| 1 | **DX Bliss** | Frictionless, delightful, zero-friction | "Make this feel effortless. Does every interaction feel weightless?" |
| 2 | **DX Serenity** | Calm, unhurried, information-architectural clarity | "Make this feel like a quiet library. Does the reader's eye rest naturally?" |
| 3 | **DX Sublimity** | Awe-inducing, showcase-grade, novel | "Make this feel like a first. Would this be memorable enough to screenshot?" |

The lenses are exhaustive for serene-DX work — pick one aesthetic per
invocation, not all four of the source-skill quality keywords. "Reader
happiness" collapses into Serenity here; use it as a trigger phrase, not
a fourth slot.

## How to Invoke

Run the `/loom:serene-bliss` command. It is a locked preset of
`/loom:brainstorm-and-refine` that fixes `--variants=3` and a compound
preamble mapping each variant slot to one of the three lenses.

```
/loom:serene-bliss "<user-prompt>" [--passes=N] [--timeout=N|none] [--mode=fast|balanced|deep] [--judge=host|round-robin]
```

The command locks `--variants` and `--preamble`; do not override
either. For the canonical compound preamble text and the delegation
contract, see `plugins/loom/commands/serene-bliss.md`.

## Context Packet Expectations

Loom builds a standard context packet for every invocation. For
serene-DX work, make sure the host surfaces these fields before
invoking, so each lens has something concrete to react to:

- **Reference anchor** — a file path, URL, or snippet of a known-good
  implementation to compare against (e.g., `libtmux-mcp/custom.css`,
  a reference Sphinx theme, a CLI whose output you admire).
- **Current state** — the file, markup, or screenshot description of
  what looks ugly or broken right now. Name the ugly element
  explicitly; "the badges look like an eyesore" beats "improve the
  badges."
- **Constraint envelope** — what must NOT change (branch, file scope,
  no mutations) and what must be preserved (accessibility, WCAG,
  dark mode, `NO_COLOR` / `FORCE_COLOR` handling, mobile
  responsiveness).
- **Technology stack** — Sphinx + MyST, Furo variables, React +
  Tailwind, Python stdlib-only, etc. Each lens responds differently
  to what's idiomatic in the stack.
- **Known gaps / unknowns** — open questions the models should
  address rather than hand-wave past.

## Anti-Patterns

- **No reference anchor.** Prompting for bliss / serenity / sublimity
  without a concrete comparison target produces generic advice from
  every lens. Always name a known-good implementation.
- **No constraint envelope.** Without explicit "do not modify files"
  and stack boundaries, models will start proposing edits instead of
  design critique.
- **Mixing quality keywords in one invocation.** The three slots
  already cover the range. Don't rephrase the prompt to ask for
  "bliss and serenity and sublimity at once" — that defeats the
  lens-differentiation that makes the brainstorm phase useful.
- **Using this for implementation tasks.** Serene-bliss is a
  design-research pattern. For actual code changes, run
  `/loom:execute` or `/loom:prompt` instead.
