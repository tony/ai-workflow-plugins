# Post-update follow-ups

Some bumps are not finished when the lockfile moves. A formatter's
config carries the version it was written against; a compiler's output
is recorded in snapshots; a framework major ships a migration. Each of
those is a **separate commit that lands immediately after the bump**,
never folded into it.

The split exists so the bump reverts cleanly. Fold a snapshot
regeneration into the bump that caused it and reverting the bump also
reverts test data that may have been correct for other reasons.

## Which bumps trigger which follow-up

**Biome** — `biome.jsonc` carries a `$schema` pinned to the version it
was written against. A stale one makes Biome emit a version notice and
makes editor JSON validation disagree with the running binary. Run
`biome migrate` and land the config change separately:

```
biome.jsonc: Update to 2.5.5
```

**Tailwind CSS** — compiled-CSS snapshots record the shape of Tailwind's
output, which changes across minors even when the rendered result does
not. Regenerate them and land them separately.

**Any linter or formatter** — new or changed rules produce a diff across
files the bump never touched. That diff is its own commit, or several;
for ruff specifically it is `/ruff:bump`, which lands one commit per
rule.

**Framework majors** — a codemod or migration guide's output lands
separately from the version bump that required it.

**Type packages** — a `@types/*` major can surface type errors in code
that did not change. Fix them in their own commit and say whether the
errors are new or pre-existing.

## Declaring a red intermediate

When the bump commit leaves the tree failing and the follow-up fixes it,
**say so in the bump's body**. Name the command that fails and where.

This is the honest form. The alternatives are worse: bundling the two
loses the clean revert, and staying silent leaves a bisect landing on a
commit that fails for reasons its message does not mention.

An exemplar of the pair, from a Tailwind bump:

```
js(deps[dev]) bump tailwind, vite, babylon

why: Routine refresh from `ncu -u`. Tailwind 4.3.3 resolves CSS
nesting inside `compile()` rather than deferring it to Lightning
CSS (tailwindlabs/tailwindcss#20124), which reshapes the compiled
output the tailwind-plugin snapshots capture. The snapshots are
regenerated in the follow-up commit, so `pnpm test` fails in
packages/tailwind-plugin at this revision.

what:
- tailwindcss and @tailwindcss/vite 4.3.2 -> 4.3.3
- vite 8.1.4 -> 8.1.5
- @babylonjs/{core,inspector,loaders,materials} 9.16.2 -> 9.17.0
```

And the follow-up, which earns its length by proving the churn is
cosmetic rather than asserting it:

```
test(tailwind-plugin) regenerate CSS snapshots

why: Tailwind 4.3.3 flattens CSS nesting into `:is()` selectors and
merges adjacent at-rules while compiling
(tailwindlabs/tailwindcss#20124), so the recorded output no longer
matches. Comparing the two revisions declaration by declaration,
every CSS declaration is byte identical; only nesting structure and
at-rule grouping differ. Rendered output is unchanged, since
`@tailwindcss/vite` already ran Lightning CSS over the same input
and emitted flat CSS before this upgrade.

what:
- Re-record the four compiled-CSS snapshots against tailwindcss 4.3.3
```

Regenerating a snapshot is asserting the new output is correct. Read
enough of the diff to say why it moved, and put that in the body. A
snapshot refreshed without that check records a regression as the new
expected value.

## Quality gates

Run the project's own checks after each commit — the lint, format,
type-check and test commands its `AGENTS.md`, `CLAUDE.md`, `justfile`,
or CI workflow declares. Never substitute assumed commands for the ones
the project actually runs.

When something fails, establish whether it fails on trunk too before
attributing it to the bump. A pre-existing failure is reported as
pre-existing, not fixed and not concealed. Never report green without
having read the output that says so.
