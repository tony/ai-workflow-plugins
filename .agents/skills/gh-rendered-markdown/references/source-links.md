# Source links

How to link so the link still works. Shared by the
`rendered-markdown` skill and the `gh-create-issue` skill.

A link that has rotted is worse than no link: it resolves, it looks
authoritative, and it points at unrelated code. Three years is the
horizon to write for.

## Link everything that has a URL

Every project, package, specification, standard, command, error code,
issue, commit, release, and document that names a thing a reader could
look up. The first mention carries the link; later mentions do not
need to repeat it.

A reader who has to search for what you meant is a reader you sent
away.

## Pin every reference into a repository

### A release tag first

```
https://github.com/OWNER/REPO/blob/v2.40.0/README.md
```

Most durable, and it tells the reader which released version the claim
held for.

### Otherwise a 7-character commit reachable from trunk

```
https://github.com/OWNER/REPO/blob/9a29b1a/src/index.ts
```

Use when there is no tag, or the claim is about unreleased code. Never
a pull-request head — it can be rebased or garbage-collected.

### Never a branch

`blob/main/…` rots silently. The file moves, the lines shift, and the
anchor lands on unrelated code while still returning 200. Reserve it
for a living document meant to always show the latest state, such as a
contributing guide.

### Line anchors only on a pinned ref

`#L120` for a line and `#L120-L145` for a range. On a file GitHub
renders rather than displays — markdown, reStructuredText — the anchor
needs `?plain=1` before the fragment or it has nothing to attach to.

```
https://github.com/OWNER/REPO/blob/9a29b1a/README.md?plain=1#L14
```

A line-range permalink unfurls into a code snippet only inside its own
repository. Filing across repositories, quote the lines in a fence
next to the link.

### Resolving the ref

Newest tag of a repository you have not cloned:

```
gh release list --repo OWNER/REPO --limit 1 --exclude-drafts --exclude-pre-releases --json tagName --jq '.[0].tagName'
```

A repository can have thousands of tags and no releases at all, in
which case that command prints nothing. Fall back to the tags
themselves:

```
git ls-remote --tags --refs --sort=-v:refname https://github.com/OWNER/REPO
```

Version sort puts a prerelease above its own release, so `v1.2.0-rc1`
outranks `v1.2.0`. Read the list, do not take the first line.

A tag pins content only by convention — git allows a tag to be moved,
and a move never propagates to anyone who already fetched it. When the
link is evidence for a quoted line, resolve it to a commit:

```
gh api repos/OWNER/REPO/commits/v2.40.0 --jq .sha
```

That endpoint resolves lightweight and annotated tags alike. Do not
use `git/ref/tags/<tag>`: on an annotated tag it returns the tag
object's SHA, and a blob URL built on it 404s.

Confirm before publishing:

```
curl -s -o /dev/null -w '%{http_code}\n' -L 'https://github.com/OWNER/REPO/blob/v2.40.0/README.md'
```

## Let GitHub do the linking where it already does

Inside issue, pull request, discussion, and comment bodies — not in
repository files, and not in wikis.

### Same repository: write the bare reference

`#123` for an issue or pull request, and a 7-character commit ref for
a commit. Both autolink with no markdown syntax. Issues and pull
requests share one number space, so `#123` may land on either — do not
assert which in prose.

Wrapping a reference in `[text](url)` suppresses the shortening;
wrapping it in backticks suppresses the link. Use both deliberately.

### Another repository: link it explicitly

```
[REPO#123](https://github.com/OWNER/REPO/issues/123)
```

GitHub would also autolink a bare `OWNER/REPO#123`, but the explicit
form says the same thing in a repository file, in a tracker that is
not GitHub, and in a body someone copies elsewhere.

### Tracker keys: check whether the repository resolves them

A key like `TIK-111` renders as plain text unless a repository admin
configured a custom autolink for that prefix, and the feature exists
only on paid plans. When it is configured, write the bare key. When it
is not, write a full markdown link.

`GET /repos/{owner}/{repo}/autolinks` needs admin and returns 404 for
everyone else, which is indistinguishable from "none configured".
Render the token instead — the preview applies the repository's real
autolinks:

```
gh api --method POST /markdown -f mode=gfm -f context=OWNER/REPO -f text='TIK-111'
```

### Unresolvable references render as plain text

A wrong issue number or a SHA that is not in the repository produces
no link and no error. Confirm anything you did not copy from a live
page.

## Naming an open-source project

On first mention, give the reader the whole set: repository, homepage,
documentation, the changelog at the release in question, and the
package-registry page. Research it — do not reconstruct URLs from
memory.

Render it as the project name linked to its primary home, with the
rest in parentheses:

```
[vitest](https://vitest.dev) — [repo](https://github.com/vitest-dev/vitest), [docs](https://vitest.dev/guide/), [v4.1.10 release notes](https://github.com/vitest-dev/vitest/releases/tag/v4.1.10), [npm](https://www.npmjs.com/package/vitest)
```

Drop a slot that genuinely does not exist rather than pointing two
slots at the same page.

### Resolving the set from a registry

npm, including `repository.directory` for a package inside a monorepo:

```
curl -s https://registry.npmjs.org/PKG/latest | jq '{version, homepage, repository, bugs}'
```

PyPI, where the link set is maintainer-labeled free text:

```
curl -s https://pypi.org/pypi/PROJECT/json | jq '.info | {package_url, home_page, project_urls}'
```

crates.io, which requires an identifying user agent:

```
curl -s -A 'issue-authoring' https://crates.io/api/v1/crates/CRATE | jq '.crate | {homepage, documentation, repository, default_version}'
```

RubyGems, the one registry with a first-class changelog field:

```
curl -s https://rubygems.org/api/v1/gems/GEM.json | jq '{homepage_uri, source_code_uri, documentation_uri, changelog_uri}'
```

Go, resolving version, tag ref, and commit in one call:

```
curl -s https://proxy.golang.org/MODULE/@latest
```

Second-source the repository itself, since a registry records what was
true at publish time:

```
gh repo view OWNER/REPO --json url,homepageUrl,description,isArchived
```

### Changelog at the release, never at trunk

```
https://github.com/OWNER/REPO/releases/tag/v2.40.0
```

Copy that URL from the API rather than building it. Monorepo tags
carry prefixes and encodings that are not derivable from a version
number — `@changesets/cli@2.31.1` becomes `%40changesets/cli%402.31.1`
in a URL, Go submodules tag as `module1/v1.2.3`.

```
gh api repos/OWNER/REPO/releases/tags/v2.40.0 --jq '{tag_name, html_url}'
```

`/releases/latest` moves on every publish and means different things
in the API and the web UI. It is never the right link for a claim
about a specific version. When a project publishes no releases, link a
tag-pinned `CHANGELOG` file, or a `/compare/<old>...<new>` URL.

## What rots

- A repository rename redirects, until someone re-creates the old name
  under the old owner. Then it silently points somewhere else.
- A branch rename redirects normal URLs but not raw file URLs.
- A registry-recorded repository URL can predate a rename; it resolves
  only through that redirect.
- `npm` `repository.url` is a VCS URL (`git+https://….git`), not a
  browsable link. `homepage` is often just the README anchor.
- Registry web pages reject non-browser clients — npmjs.com and
  crates.io both return 403 to `curl`, crates.io citing its data
  access policy. Validate those through the JSON APIs above, not with
  a status check.
- Unauthenticated GitHub API calls are capped at 60 per hour per IP.
  Route them through `gh`.
