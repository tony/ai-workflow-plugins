# Holding a package back

A hold is a decision to stay behind on purpose. It is the one part of a
dependency sweep that adds no version and still needs the most
explanation, because the next person to run the updater will see a
package that looks stale and try to fix it.

Every hold has a **condition that ends it**. Record the condition when
you add the hold, and release the hold when the condition is met. A hold
with no condition is indistinguishable from neglect, and outlives the
problem it was added for.

## Where holds live

npm-check-updates reads `.ncurc`, or `.ncurc.json`, `.ncurc.yaml`,
`.ncurc.yml`, `.ncurc.js`, `.ncurc.mjs`, `.ncurc.cjs`. The `reject`
array names packages `ncu` must not offer. Entries may be exact names,
globs (`*gatsby*`), or regex literals (`/.*react.*/`) — the regex form
is how a family of packages gets held together.

**A `"ncu"` key in `package.json` is not config.** Unlike most tools in
this ecosystem, `ncu` does not look there, so a `reject` array written
into `package.json` is silently ignored and the package keeps being
offered. Confirm a hold works rather than assuming the file was read.

**Config resolves next to the package file, not at the repository
root.** A workspace can therefore hold a package in one member and not
another, and often does — a monorepo may reject `@babylonjs/inspector`
in two packages that need a preview build while the rest of the tree
tracks releases normally.

So a root-only scan under-reports holds. Enumerate every config in the
tree:

```console
fd -H -t f '^\.ncurc' .
```

Releasing the last hold ends one of two ways, and both are in use:
`{"reject": []}` left in place so the next hold has somewhere to go, or
the file deleted outright. Neither is dead config to clean up. Follow
whichever the repository already does, and do not "tidy" an empty
`reject` array away — its absence and its emptiness mean the same thing
to `ncu` but not to the next reader.

## The reason cannot live in the file

`ncu` rejects unknown keys. Adding a `$comment` to a JSON `.ncurc` does
not document the hold, it breaks the tool:

```
Unknown option found in config file: $comment
error: unknown option '--$comment'
```

The commit message is therefore the only durable record of why a package
is held, which makes it load-bearing in a way most config commits are
not. Write it accordingly.

If a hold genuinely needs an inline explanation, use a format that
supports comments — `.ncurc.yml` or `.ncurc.js` — rather than inventing
a key the JSON parser will reject.

## Commit grammar

Scope by the file, and name the condition in the subject.

Adding a hold:

```
.ncurc: Ignore `@biomejs/biome` 2.3.5 -> 2.3.6 until they fix class methods
```

Releasing one, naming what fixed it:

```
.ncurc: Unignore `@biomejs/biome` (2.3.7 fixed issue)
```

The pair is the point. A reader finding the hold can search forward for
its release; a reader finding the release can search back for the
reason.

## What earns a hold

Each of these has been a real one. The shape they share is a condition
outside the repository that has not happened yet:

- **Upstream bug** — the release is broken for a use this project makes.
  Released when the fixing version ships.
- **Ecosystem catch-up** — a major that a framework this project depends
  on does not support yet.
- **Runtime floor** — a release that drops a runtime this project still
  supports. Released when the project drops it too.
- **Migration not yet done** — a major whose upgrade is real work,
  deliberately deferred.
- **Maintainer broke the package** — a release that changed something
  fundamental in a way that is not going to be reverted.

A hold is not a way to avoid reading release notes. If the reason is
"this looked risky", read the notes instead.

## Auditing holds

Every sweep checks the existing holds, not just the outdated packages.
For each entry in every `reject` array, report:

- The condition recorded in the commit that added it, and whether that
  condition is now met — a hold whose fixing version has shipped should
  be released in this run.
- Holds with no recoverable reason. Do not silently release these; a
  reason that was never written down might still be real. Surface them
  and let the user decide.
- Holds duplicated unevenly across workspace members, where one package
  rejects something its siblings do not. That is usually drift rather
  than intent.

A fleet-wide hold is added and released across every repository that
carries it. Both directions fan out, and both are easy to half-finish —
one real hold-release pair had to be applied twice, days apart, because
the first pass missed a file.

## Cooldown is not a hold

`ncu --cooldown <period>` and the ecosystem cooldown settings gate
releases by age, automatically, for every package. A hold names one
package and one condition. Do not use a `reject` entry to wait out a
cooldown — it will still be there long after the release ages in.
