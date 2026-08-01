# Dependency commit conventions

Shared by every command in this plugin. A dependency commit is read
years later by someone deciding whether a version is safe to move again,
so the body carries the reasoning and the links, not an inventory of the
diff.

Defer to the project's own `AGENTS.md` or `CLAUDE.md` when it states a
subject format. What follows is the shape to use when the project does
not say otherwise.

## Subject grammar

```
<scope>(deps[<group>]) <what moved>
```

The scope names the ecosystem, not the tool: `py` for Python, `js` for
JavaScript and TypeScript, `rs`, `go`. The bracketed group names the
dependency group the change lands in — `dev`, `docs`, `lint` — and is
omitted when the change is not scoped to one.

Toolchain pins are scoped by the file they live in instead, because the
file is what the reader greps for:

```
.tool-versions(<tool>) <tool> <old> -> <new>
.nvmrc(nodejs) <old> -> <new>
```

Use an ASCII `->` for a version transition. Keep the subject at 64
characters or fewer.

## The four tracks

Each track has its own commit. They are never merged, and they land in
this order within a session.

### Toolchain and runtime

One tool per commit, even when a single edit to `.tool-versions` moves
three tools. Each bump reverts on its own, and a reader bisecting a
runtime regression needs the tools separated.

A single commit may span several releases of that one tool. When it
does, link every release in the span, not just the endpoint — the
intermediate ones are where the regression usually is.

The body is a link block and nothing else. See `upstream-links.md` for
which URLs each tool takes.

### Package manager and engines

`packageManager` and `engines` in `package.json` pin the toolchain, so
they move on their own:

```
js(deps) pnpm <old> -> <new>
chore(package[engines]) require Node >=<version>
```

A package-manager bump takes a link block. An `engines` bump takes a
`why:`/`what:` body, because a floor exists for a reason and the reason
is not recoverable from the diff.

### Named package bumps

One commit per package, or per release train when packages must move
together. A release train needs the body to say *why* they are coupled —
a peer contract, a bundled dependency, a shared compiler — otherwise the
next reader will split them.

The body is `why:` then `what:`. The `why:` explains what the release
changes for *this* repository; the `what:` lists the manifests touched
and what the lockfile did. Close with links when the release notes are
worth reaching.

A package earns its own commit when any of these hold:

- The version crosses a major.
- It is a linter, formatter, or compiler whose output changes.
- It needs a follow-up commit — see `follow-ups.md`.
- The change is a floor or constraint in the manifest, not just a
  lockfile move.
- It is a workspace sibling this repository also publishes.
- It carries a security fix.

Everything else belongs in the bulk refresh.

### Bulk lockfile refresh

```
py(deps[dev]) Bump dev packages
js(deps[dev]) Bump dev packages
```

**The body is empty.** Nothing worth saying is not already in the
lockfile diff, and a generated inventory of package names is noise that
makes the commits that *do* carry reasoning harder to find.

An in-range refresh that touches no manifest is a different commit
again, and it does take a short body naming what moved:

```
chore(deps) pnpm update: refresh in-range transitives
```

### Catalog and override pins

A version pinned in `pnpm-workspace.yaml` under `catalog:` is invisible
to `ncu`, so it is bumped by hand and scoped to the file it lives in:

```
deps(catalog) @biomejs/biome 2.5.3 -> 2.5.4
```

Say in the body that the tool missed it. A reader who runs `ncu` and
sees nothing outstanding needs to know why this commit exists.

## Body anatomy

Wrap body lines at 72 characters. Separate `why:` and `what:` with a
blank line.

### Link blocks

Style follows link count, not preference.

**One link** goes inline on a single line:

```
See also: https://nodejs.org/en/blog/release/v25.2.0
```

**Two or more** put `See also:` on its own line, then one hyphen bullet
per URL:

```
See also:
- https://pnpm.io/blog/releases/11.17
- https://github.com/pnpm/pnpm/releases/tag/v11.17.0
```

When a commit moves more than one tool, group the bullets under the tool
they belong to, so a reader chasing one of them is not sorting URLs by
hostname.

### Cooldown

State the cooldown when it is load-bearing — that a release is being
taken now because it cleared the window, or that a newer release exists
and is deliberately excluded because it has not. A reader comparing the
commit against the registry will otherwise think the bump was stale on
arrival.

Never write a claim into a body that has not been checked against the
repository the commit lands in. A fleet-wide fact is not a per-repo
fact, and a false claim committed to history stays false.

Never add an AI signature, a generated-by footer, or a tool URL. These
have shipped into permanent history before and cannot be removed without
a rewrite.

## Writing the message

Multi-line messages go through a heredoc or a file. Passing a
multi-line string to `git commit -m` through an interactive shell has
collapsed bodies into the subject line, producing commits whose subject
runs to several hundred characters with the link block inlined.

```console
git commit -F - <<'EOF'
js(deps[dev]) @biomejs/biome 2.5.3 -> 2.5.4

why: Track latest Biome patch release (published 2026-07-15, now past
the 3-day supply-chain cooldown).

what:
- Bump @biomejs/biome in root, lib, wc (exact) and site (caret)
- Lockfile: biome + platform CLI binaries 2.5.3 -> 2.5.4
EOF
```

## Exemplars

These are real commits from repositories this convention was derived
from. Match their density, not their length.

A named bump whose body earns its place by naming the coupling:

```
js(deps) Astro 7.0.9 + MDX 7.0.3 + Satteri 0.3.4

why: These ship as one release train: astro 7.0.8 bundles
markdown-satteri 0.3.4, and @astrojs/mdx 7.0.3's highlighter contract
(codeToHast) matches satteri 0.3.4 despite the loose ^0.3.1 peer
range (upstream PR #17341), so bumping them together keeps the
resolved graph coherent.

what:
- astro ^7.0.7 -> ^7.0.9 (compiler-rs 0.3.1 slot/client:only fixes,
  dev-server no longer full-reloads first visit, island hydration
  retry fix)
- @astrojs/mdx ^7.0.2 -> ^7.0.3 (custom `pre` components reach
  highlighted code blocks; inert here — expressive-code owns blocks)
- @astrojs/markdown-satteri ^0.3.3 -> ^0.3.4 (codeToHast switch,
  drops makeFragmentNode export and plugin `mdx` option)
- astro 7.1.1 exists but stays excluded by the 3-day release cooldown
```

A toolchain bump, link block only:

```
.tool-versions(just) just 1.55.1 -> 1.57.0

- just
  - https://github.com/casey/just/blob/1.57.0/CHANGELOG.md
  - https://github.com/casey/just/releases/tag/1.56.0
  - https://github.com/casey/just/releases/tag/1.57.0
```

A drift consolidation, where the reason is the drift itself:

```
js(deps[dev]) Unify Biome to 2.5.3

why: Biome versions had drifted (2.4.16 in colors +
vite-plugin-webfont-preload, 2.5.2 elsewhere). A single version keeps
lint/format behavior identical across packages and collapses two copies
of the toolchain (+ platform binaries) in the lockfile into one.

what:
- Bump @biomejs/biome to 2.5.3 in root + 7 packages
- biome migrate: config $schema 2.5.2 -> 2.5.3
- Consolidate two Biome versions to one in pnpm-lock.yaml
- No new diagnostics: biome lint/check/format all clean
```
