---
description: Loom serene bliss — brainstorm-and-refine preset with three fixed DX aesthetic lenses (Bliss, Serenity, Sublimity)
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Write", "Task", "AskUserQuestion"]
argument-hint: "<prompt> [--passes=N] [--timeout=N|none] [--mode=fast|balanced|deep] [--judge=host|round-robin]"
---

# Loom Serene Bliss

A locked preset of `/loom:brainstorm-and-refine` for developer-experience,
documentation, and tooling-UX design work. Three variant slots are fixed
to three serene-DX aesthetic lenses — **DX Bliss**, **DX Serenity**, and
**DX Sublimity** — so a single invocation yields three independent
aesthetic takes before the refine phase picks and polishes the strongest.

This is a **project-read-only** command. It delegates to the
brainstorm-and-refine procedure, which is itself read-only; session
artifacts land under `$AI_AIP_ROOT`, outside your repository.

The prompt comes from `$ARGUMENTS`. If no prompt is provided, ask the
user what DX artifact, docs page, or tooling surface they want to
brainstorm and refine under the serene lens.

---

## The Three Serene Lenses

| Slot | Lens | Aesthetic | Ask of each model |
|------|------|-----------|-------------------|
| 1 | **DX Bliss** | Frictionless, delightful, zero-friction | "Make this feel effortless. Does every interaction feel weightless?" |
| 2 | **DX Serenity** | Calm, unhurried, information-architectural clarity | "Make this feel like a quiet library. Does the reader's eye rest naturally?" |
| 3 | **DX Sublimity** | Awe-inducing, showcase-grade, novel | "Make this feel like a first. Would this be memorable enough to screenshot?" |

The three slots are exhaustive for serene-DX work. "Reader happiness"
collapses into Serenity; there is no fourth slot.

---

## Compound Preamble (source of truth)

The compound `--preamble` value sent to brainstorm-and-refine is a
single paragraph (no embedded newlines) for shell-quoting safety. This
file is the canonical location — the `loom:serene-bliss` skill
references this block rather than duplicating it.

```
You are a developer-experience design expert. Apply the Serene DX aesthetic lens matching your variant slot. Variant 1 → DX Bliss: frictionless, delightful, zero-friction; make it feel effortless. Variant 2 → DX Serenity: calm, unhurried, information-architectural; make it feel like a quiet library. Variant 3 → DX Sublimity: awe, novel extensions, showcase-grade; make it feel like a first. Compare the current state to any concrete reference implementation named in the prompt, and name what is ugly or broken. Do NOT modify any files — research only.
```

Loom prepends `"Variant N of M:"` to this string automatically for each
variant, so the compound preamble's slot directives route each model to
the correct lens via its variant number.

---

## Argument Handling

Scan `$ARGUMENTS` for `--name=value` flags anywhere in the text. Flags
are stripped from the prompt text before sending to models, identical
to brainstorm-and-refine's flag handling.

**Reserved flags** — if the user passed either of these, print one
warning line and strip them:

- `--variants=*` — serene-bliss locks `--variants=3`; the three-lens
  contract depends on it.
- `--preamble=*` — serene-bliss locks the compound preamble above.
  Users who want a custom preamble should run `/loom:brainstorm-and-refine`
  directly instead.

Warning line format (printed once, at the start of execution if either
flag was seen):

> "Note: `--variants` and/or `--preamble` were ignored — serene-bliss
> locks both. Run `/loom:brainstorm-and-refine` directly for full
> control."

**Passthrough flags** — forward unchanged to brainstorm-and-refine:

- `--passes=N`
- `--timeout=N|none`
- `--mode=fast|balanced|deep`
- `--judge=host|round-robin`

---

## Execution

Execute the full procedure documented in
`plugins/loom/commands/brainstorm-and-refine.md` with these parameter
overrides:

1. `variant_count = 3` (overriding any `--variants` from `$ARGUMENTS`)
2. `user_preamble = <Compound Preamble block above>` (overriding any
   `--preamble` from `$ARGUMENTS`)
3. All other passthrough flags (`--passes`, `--timeout`, `--mode`,
   `--judge`) apply as documented in brainstorm-and-refine.

Do not re-implement brainstorm-and-refine's phases here. Read
`plugins/loom/commands/brainstorm-and-refine.md` with the Read tool and
follow every phase (context gathering, session directory setup, parallel
variant dispatch, transition gate, refine cycle, artifact persistence)
verbatim, using the overrides above in place of Phase 1's flag parsing
for `variant_count` and `user_preamble`. This mirrors the existing
cross-reference precedent at `plugins/loom/commands/brainstorm-and-refine.md`
line 647, where that command defers to `/loom:refine` Phase 4 Step 1 for
the External Judge Protocol.

---

## Relationship to the skill

The `loom:serene-bliss` skill at
`plugins/loom/skills/serene-bliss/SKILL.md` auto-discovers on serene-DX
vocabulary ("serene bliss", "DX bliss", "DX serenity", "DX sublimity",
"reader happiness", etc.) and routes to this command. The skill owns
the trigger surface; this command owns the execution contract and the
canonical preamble text.
