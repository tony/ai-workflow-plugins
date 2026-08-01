# Ecosystem discovery and apply

Shared by this skill, the `package-updater-update-package` skill,
and the `package-updater-update-toolchain` skill. Read before running anything
that resolves a version.

Detect an ecosystem by the files present, never by the project's name or
its language tag. A repository can carry several at once — a Python
package with a docs site has both `uv.lock` and `pnpm-lock.yaml`, and
each one updates on its own track with its own commit.

Run the project's own wrapper when it has one. A `justfile`, `Makefile`,
or `package.json` script named for the update is the maintained path,
and it may do more than the raw command below.

## Python with uv

Marked by `uv.lock` beside `pyproject.toml`.

Discovery and apply are usually one step here — the upgrade resolves and
reports in the same run, and the lockfile diff is the report. Use a
separate discovery pass when you need to decide before writing:

```console
uv lock --upgrade --dry-run
```

```console
uv tree --outdated --depth 1
```

**Apply** the bulk refresh:

```console
uv sync --all-extras --dev --upgrade
```

**Apply** to one package, leaving everything else pinned:

```console
uv lock --upgrade-package <name>
```

The lockfile is `uv.lock` and it is the only artifact the bulk refresh
commits. Confirm the lock actually moved rather than assuming the
constraint was enough — a floor raised in `pyproject.toml` does nothing
until the resolver rewrites the lock.

## Python with poetry or pip

Marked by `poetry.lock`, or by `requirements*.txt` with no lock at all.

Poetry discovers with `poetry show --outdated` and applies with
`poetry update`. A bare requirements file has no resolver of its own;
find outdated pins with `uv pip list --outdated` against the active
environment and edit the file directly.

## Node with pnpm

Marked by `pnpm-lock.yaml`.

**Discover** with `ncu`, which reads manifests rather than the installed
tree. Run it bare to report without writing:

```console
ncu
```

`pnpm outdated` reads the installed tree instead and reports a different
set; prefer `ncu` so discovery and apply agree on what "outdated" means.

**Apply** the manifest bump, then rebuild the tree from clean:

```console
ncu -u
```

```console
rm -rf node_modules packages/*/node_modules
```

```console
pnpm install
```

In a workspace, `ncu -u` only reaches the root manifest. Recurse to the
members:

```console
pnpm --recursive exec ncu -u
```

Projects that do this often wrap both halves in a script — an
`update:all` that runs `ncu -u` at the root and then recursively. Use
the project's script when it has one.

**Apply** an in-range refresh, which moves transitives without touching
any manifest:

```console
pnpm update
```

Those are two different commits with two different meanings. `ncu -u`
edits `package.json` and lands as a dependency bump; `pnpm update` edits
only the lockfile and lands as an in-range transitive refresh.

### What ncu cannot see

**Catalog entries.** A version pinned in `pnpm-workspace.yaml` under
`catalog:` is not in any `package.json`, so `ncu` never reports it.
Check the catalog by hand on every sweep, or the workspace silently
stops tracking its own pinned tools.

**Overrides and resolutions.** Same problem, same fix.

### Holding a package back

`.ncurc` carries a `reject` array of packages `ncu` must not offer. It
resolves next to the package file, so a workspace member can hold a
package its siblings track — a root-only scan under-reports holds.

Adding and releasing a hold are both commits, and both name the
condition. See `holds.md` for the lifecycle, the commit grammar, and why
the reason cannot be written into the file itself.

For a one-off exclusion that is not worth checking in, `ncu -u -x <name>`.

## Node with npm or yarn

`npm outdated` and `npm update`; `yarn outdated` and `yarn up`. The
lockfile is `package-lock.json` or `yarn.lock`. Everything else in the
pnpm section applies unchanged, except the cooldown key.

## Rust

Marked by `Cargo.lock`.

**Never run `cargo-outdated`.** It allocates without bound — around
18 GB resident — and on a memory-constrained host such as WSL the OOM
killer takes the machine down, losing whatever else was running. The
cost is paid by starting the process, so there is no safe way to try it
and see. Do not offer it as an option, and do not run it to check
whether the problem still reproduces.

Discover with the resolver instead:

```console
cargo update --dry-run
```

Or read the `Cargo.lock` diff directly, which is what the dry run
prints anyway.

`cargo update` applies an in-range refresh, touching only the lockfile.
Raising a version in `Cargo.toml` is a manifest edit and a separate
commit; `cargo upgrade` does it but ships in `cargo-edit`, so confirm
the subcommand exists before putting it in a plan.

## Go

Marked by `go.mod`. `go list -m -u all` reports available upgrades;
`go get -u ./...` followed by `go mod tidy` applies them. Both `go.mod`
and `go.sum` are committed together.

## When a project has no established procedure

Some ecosystems here are documented from their own tooling rather than
from a procedure this project has settled on. Say so in the plan rather
than presenting an untested command as routine, and prefer the smallest
reversible step: report what is outdated, propose the command, and let
the user confirm before the first run in that repository.

## Runtime and toolchain pins

Marked by `.tool-versions`, `.nvmrc`, `.python-version`, or a
`mise.toml`. These pin the tools that resolve everything above, so they
move first and on their own — see `commit-conventions.md` for the
one-tool-per-commit rule.

Discover with the version manager that reads the file:

```console
mise outdated
```

For a tool with no manager entry, ask the vendor's own release feed
rather than memory, and confirm the version exists before writing it.

`packageManager` and `engines` in `package.json` are toolchain pins too,
despite living in a manifest. They never ride along with a dependency
bump.

## Supply-chain cooldown

A cooldown makes the resolver ignore releases younger than a threshold,
which limits exposure to compromised uploads that get yanked within
hours. It is configured per ecosystem and the keys are not
interchangeable.

**uv** reads `exclude-newer` as a duration string (`"3 days"`), from
`uv.toml` in the project or from the user's config file. Requires uv
0.9.17 or newer. It stamps the window into the lockfile as
`exclude-newer-span`, so an existing `uv.lock` records the cooldown it
was resolved under.

**pnpm** reads `minimumReleaseAge` from `pnpm-workspace.yaml`, in
**minutes**. Setting it explicitly forces strict mode, which fails an
install when a pinned range's only matches are too young; pair it with
`minimumReleaseAgeStrict: false` to fall back to the newest available
instead. Individual versions are let through with
`minimumReleaseAgeExclude`.

**npm** reads `min-release-age` from `.npmrc`, as an **integer number of
days**. Requires npm 11.10.0 or newer. pnpm ignores this key entirely,
so a repository using pnpm must set its own.

`ncu` honours npm's key and says so in its output — a run that prints
`Using min-release-age from .npmrc: 3 days` is filtering, and versions
it marks `[cooldown]` exist but are gated. Do not report those as
current.

Check for a cooldown before reporting a package as current. A release
published inside the window is invisible to the resolver, and an update
run that does not know this will report the tree as up to date when it
is merely gated.

### Exempting a package

Only when the resolver genuinely cannot see a release that is needed
now. An exemption is a hole in a supply-chain guard, so keep it small
and temporary:

- Narrow it to the one package and the one version.
- Annotate it where it lives, with the condition for removing it.
- Land it as its own commit, so it reverts cleanly.
- Say in the body when the block lapses, and revert it then.

Skip this entirely when the resolver can already see the release.
Waiting out a three-day window costs nothing; a permanent exemption
nobody remembers to remove costs the guard.
