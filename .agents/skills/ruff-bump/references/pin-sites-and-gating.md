# Pin sites and resolver gating

Two things go wrong when raising a linter's version floor across repositories: you miss a place the version is written, so CI keeps running the old one; or the resolver refuses to install the new one and you spend the debugging budget on the wrong layer.

## Every place a linter version can be pinned

A repository frequently pins the same tool in more than one file, and they drift. Find all of them before editing any of them. Search the whole tree for the tool's name, then check each hit against this list:

**Python project metadata.** `pyproject.toml` — dependency groups (`[dependency-groups]`), extras (`[project.optional-dependencies]`), and legacy tool-specific sections. A repo often lists the linter in both a broad `dev` group and a narrow `lint` group; both need raising or CI and local development diverge.

**Requirements files.** `requirements*.txt`, `requirements/*.txt`, constraints files. Frequently the file CI actually installs from, even when `pyproject.toml` looks authoritative.

**Pre-commit configuration.** `.pre-commit-config.yaml` pins the linter by git tag under a `rev:` key, entirely independently of the Python dependency graph. This is the single most commonly missed site: the project metadata says the new version, pre-commit keeps running the old one, and the two disagree about what is clean. The tag convention is usually `v`-prefixed even when the package version is not.

**Runtime and tool-version managers.** `.tool-versions`, `mise.toml`/`.mise.toml`, `.python-version`-adjacent tool pins, `flake.nix`, `Dockerfile` install lines.

**CI workflow files.** A workflow that installs the linter directly — rather than through the project's dependency graph — pins it in the workflow itself, sometimes as a bare version string in a `with:` block or an install command.

**Node-side wrappers.** Some polyglot repos install the linter through a JavaScript package manager as well; `package.json` will carry its own pin.

**Editor and container configuration.** `.vscode/`, `.devcontainer/`, and similar. Not load-bearing for CI, but a stale pin here makes a contributor's editor disagree with the build.

Raise every site in the same commit. A partial bump is worse than none: it produces a repo where two tools disagree about what "clean" means, and the disagreement surfaces as a mystery CI failure on somebody else's pull request.

## Prefer a floor to an exact pin

Write `>=` rather than `==` for the version constraint. The lockfile already reproduces one exact version for anyone using the lock; the constraint exists to stop a contributor whose environment resolved something older from producing a locally-clean run that fails CI. An exact pin in the constraint duplicates the lockfile's job and turns every future bump into a wider diff.

Pre-commit is the exception — its `rev:` is a single tag by design, so it takes an exact tag.

## When the resolver cannot see the release

A newly published version can be invisible to the resolver for reasons that have nothing to do with your constraint. Diagnose which one before working around it:

**Publication cooldown.** Some resolvers support a supply-chain setting that hides releases younger than some threshold, on the theory that most malicious uploads are detected and yanked within hours. If a global or per-user configuration sets such a cooldown, a release published inside the window simply does not exist as far as resolution is concerned. This is the most common cause and the most confusing, because the package index shows the version plainly while the resolver insists there is no such release.

**Index lag.** A private mirror or proxy has not synchronized yet. Nothing to work around; wait or repoint the index.

**Constraint conflict.** A transitive dependency or a constraints file caps the version. The resolver usually says so, but the message can be buried.

**Platform gaps.** The release exists but has no wheel for a platform in the resolution matrix.

### Gating on a cooldown, correctly

If the blocker is a cooldown and the work genuinely cannot wait for it to lapse, the exemption must be explicit, narrow, and *temporary*:

- Exempt only the one package, never the cooldown globally. A resolver that supports cooldowns generally supports a per-package override.
- Prefer an override form that does not bake a date into the repository. A date ages into the lockfile and quietly stops meaning anything; a boolean exemption does not.
- Mark it in the file itself as temporary, with the reason and the condition for removing it. The next reader has no way to distinguish a deliberate permanent exemption from a workaround somebody forgot.
- Land it as its own commit, first in the branch, so reverting it is a single revert rather than a surgical edit.
- State the removal as a pre-merge requirement in the pull request body. A permanent exemption silently opts that package out of the supply-chain guard forever, which is a real security regression traded for a few hours of convenience.
- Compute when the cooldown lapses — publication timestamp plus the configured window — and say so, so the reviewer knows how long the workaround needs to live.

The version floor, not the exemption, is what holds the upgrade. Once the cooldown lapses the exemption is pure liability, which is why it is worth the separate commit.
