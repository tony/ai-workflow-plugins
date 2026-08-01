# Upstream links

Which URLs a bump cites, per tool. A link block exists so the next
reader can answer "what did this actually change" without going hunting,
so it points at the release notes for the exact version, never at a
project's front page.

## Rules

**Pin the version into the path.** `blob/<version>/CHANGELOG.md` is
stable; `blob/main/CHANGELOG.md` silently drifts to describe a release
the commit never took, which is worse than no link.

**Link every release in the span.** A bump from 0.11.17 to 0.11.19 cites
0.11.17, 0.11.18 and 0.11.19. The intermediate releases are where a
regression usually entered, and the reader has no other way to find
them.

**Verify before writing.** A link that 404s is indistinguishable from a
version that was never published. Check the URL resolves — for a
GitHub-hosted project, `gh api repos/<owner>/<repo>/releases/tags/<tag>`
gates on exit status.

**Order the block as the reader reads it.** Changelog first when the
project keeps a good one, release notes first when it does not.

## Per-tool

**uv** — `https://github.com/astral-sh/uv/releases/tag/<version>` and
`https://github.com/astral-sh/uv/blob/<version>/CHANGELOG.md`

**just** — `https://github.com/casey/just/blob/<version>/CHANGELOG.md`
and `https://github.com/casey/just/releases/tag/<version>`

**pnpm** — `https://pnpm.io/blog/releases/<major.minor>` and
`https://github.com/pnpm/pnpm/releases/tag/v<version>`. The blog post is
per minor, so a patch bump within a minor cites the same post as the
minor that opened it.

**Node.js** — `https://nodejs.org/en/blog/release/v<version>`

**Python** —
`https://docs.python.org/release/<version>/whatsnew/changelog.html#python-<version-with-dashes>`,
plus `https://devguide.python.org/versions/` when the support window is
part of the reason. A version's release schedule PEP belongs in the
block when the bump is about the schedule rather than the content: PEP
745 for 3.14, PEP 596 for the 3.9 end of life.

**Go** — `https://go.dev/blog/go<major.minor>` and
`https://tip.golang.org/doc/go<major.minor>`. Both are per minor; a
patch bump cites the minor's pages.

**poetry** —
`https://github.com/python-poetry/poetry/blob/<version>/CHANGELOG.md`
and `https://github.com/python-poetry/poetry/releases/tag/<version>`

**Biome** — tagged per package rather than by bare version, and its
changelog is not at the repository root. The tag is
`@biomejs/biome@<version>`, which needs percent-encoding in a URL:

```
https://github.com/biomejs/biome/releases/tag/%40biomejs%2Fbiome%40<version>
```

```
https://github.com/biomejs/biome/blob/%40biomejs%2Fbiome%40<version>/packages/%40biomejs/biome/CHANGELOG.md
```

A Biome bump usually needs a `biome.jsonc` follow-up — see
`follow-ups.md`.

**ruff** — `https://astral.sh/blog/ruff-v<version>` for a minor,
otherwise `https://github.com/astral-sh/ruff/releases/tag/<version>`.
Rule-level changes take the rule's own documentation page at
`https://docs.astral.sh/ruff/rules/<rule-name>/`. Bumping ruff's floor
is `/ruff:bump`, not this plugin.

**Terraform and providers** —
`https://github.com/hashicorp/terraform/releases/tag/v<version>`, and
for a provider its registry page plus its changelog at the tag. Bumping
providers is `/terraform:bump-provider`, not this plugin.

**GitHub Actions** — `https://github.com/<owner>/<action>/releases/tag/<tag>`
for every major in the span. Bumping action pins is
`/github-actions:update-actions`, not this plugin.

## Packages with no changelog

Fall back in this order: the release notes on the forge, the tag's
compare view against the previous tag, then the registry's release page
(`https://pypi.org/project/<name>/<version>/`,
`https://www.npmjs.com/package/<name>/v/<version>`).

If none of those say anything useful, say so in the body rather than
padding the block with a link that answers nothing. "No release notes
published; diff reviewed at <compare-url>" is more honest and more
useful than a bare repository URL.

## Workspace siblings you publish

A package published from a repository you also own gets the registry
release page and, when the change is worth explaining, a summary written
from the source rather than copied from a changelog that may not exist
yet. These bumps carry the richest bodies in practice, because the
author knows exactly what changed and why the consumer should care.
