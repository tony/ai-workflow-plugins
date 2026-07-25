"""Rendering layer for the portable skill export.

``marketplace.py`` decides *which* components become portable skills and what
each one is named; this module decides *what each one says*. It takes a named
:class:`OutputSkill` plus the :class:`PortableIndex` of peer names and returns a
:class:`BuiltSkill` — the finished bytes for one ``.agents/skills/<name>/``
directory — without touching the output tree, the manifest, or the drift check.

The split follows the dependency direction: everything here is downstream of
discovery and upstream of writing, it reads only the source tree, and it needs
no third-party package. Frontmatter arrives already parsed on
:class:`SourceComponent`, so the caller owns YAML and this module owns markdown.
"""

# ruff: noqa: INP001

from __future__ import annotations

import dataclasses
import json
import re
import typing as t
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
"""Repository root, derived from this module's own location.

``marketplace.py`` derives the same value independently, so the render layer
imports nothing from its caller.
"""
PLUGINS_DIR = REPO_ROOT / "plugins"

SPEC_FRONTMATTER_KEYS = ("name", "description", "allowed-tools", "metadata")
"""Frontmatter keys the portable export is allowed to emit, in output order."""

RESOURCE_DIRS = ("references", "templates", "docs", "assets")
"""Plugin subdirectories whose files are vendored into an output skill."""

_MARKDOWN_SUFFIX = ".md"
_VENDOR_ROOT = "references"
_COMPONENT_DEPTH = 2
"""Segments in a plugin-relative component path, as in ``skills/<name>``."""
_DESCRIPTION_WRAP = 76

_ASK_TOKEN = "ask-user-choice"  # noqa: S105
"""Host-neutral stand-in for the Claude-only ``AskUserQuestion`` tool."""

_BASH_PROSE = "run this command and read the output:"

_TOKEN_RE = re.compile(
    r"""
      (?P<root>\$\{CLAUDE_PLUGIN_ROOT\}(?P<root_path>/[A-Za-z0-9._/-]+)?)
    | (?P<repo>(?<![A-Za-z0-9._/-])plugins/[a-z][a-z0-9-]*/[A-Za-z0-9._/-]*)(?::\d+(?:-\d+)?)?
    | (?P<res>(?<![A-Za-z0-9._/-])(?:references|templates|docs|assets)/[A-Za-z0-9._/-]+)
    | (?P<slash>(?<![A-Za-z0-9/])/[a-z][a-z0-9-]*:[a-z0-9][a-z0-9-]*)
    """,
    re.VERBOSE,
)
_SKILL_PHRASE = r"(this skill|the `[^`]+` skill)"
_PHRASE_FIXES = (
    (re.compile(r"\bthe (?=this skill\b)"), ""),
    (re.compile(r"\bthe (?=the `[^`]+` skill\b)"), ""),
    (re.compile(_SKILL_PHRASE + r"(?:[ \t]+slash)?(?:[ \t]+|[ \t]*\n[ \t]*)command\b"), r"\1"),
)
"""Repairs for the article and noun left behind when a slash command becomes a skill."""
# SPIKE: grammar repair by pattern, covering only the shapes this corpus produces
# ("the /p:c command", "the /p:c"). A new phrasing in a source file would slip through
# and read awkwardly; nothing detects that, so it needs a re-read after adding commands.

_BASH_LINE_RE = re.compile(r"^`!(?P<cmd>.+)`\s*$")
_INLINE_BANG_RE = re.compile(r"`!([^`\n]*)`")
_ASK_RE = re.compile(r"\bAskUserQuestion\b")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
# SPIKE: fence tracking is a plain open/close toggle. It ignores fence length and
# indentation rules, so a nested fence of a different length would desynchronize it.
# No component in plugins/ nests fences; a real implementation should tokenize.


@dataclasses.dataclass(frozen=True)
class SourceComponent:
    """A skill or command in the source tree, before portable naming.

    Attributes
    ----------
    plugin : Path
        Plugin directory that owns the component.
    kind : str
        Either ``"skill"`` or ``"command"``.
    path : Path
        The ``SKILL.md`` or ``commands/<name>.md`` file.
    raw_name : str
        Undisambiguated component name.
    base : Path
        Directory that bare relative paths in the body resolve against.
    frontmatter : dict[str, Any]
        The file's parsed frontmatter, empty when absent or unparseable. Held
        here so the render layer never has to parse YAML itself; excluded from
        equality and hashing, for which ``path`` is the identity.
    """

    plugin: Path
    kind: str
    path: Path
    raw_name: str
    base: Path
    frontmatter: dict[str, t.Any] = dataclasses.field(compare=False)


@dataclasses.dataclass(frozen=True)
class OutputSkill:
    """One emitted ``.agents/skills/<name>/`` directory.

    Attributes
    ----------
    name : str
        Output directory name, also the emitted ``name`` frontmatter value.
    body : SourceComponent
        Component whose body becomes ``SKILL.md``.
    overview : SourceComponent or None
        Merged sibling whose body is vendored as a bundled overview.
    """

    name: str
    body: SourceComponent
    overview: SourceComponent | None


@dataclasses.dataclass
class PortableIndex:
    """Lookup tables shared by every skill build.

    Attributes
    ----------
    by_path : dict[Path, str]
        Source component file to output skill name.
    by_invocation : dict[tuple[str, str], str]
        ``(plugin name, component name)`` to output skill name.
    """

    by_path: dict[Path, str]
    by_invocation: dict[tuple[str, str], str]


@dataclasses.dataclass
class BuiltSkill:
    """A rendered output skill held in memory before it touches disk.

    Attributes
    ----------
    name : str
        Output directory name.
    files : dict[str, tuple[bytes, int]]
        Output-relative path to ``(content, permission bits)``.
    sources : list[str]
        Repo-relative paths of the components this skill was built from.
    vendored : dict[str, str]
        Output-relative bundled path to its repo-relative source path.
    external : list[str]
        Path-shaped tokens left verbatim because they name the user's project.
    unresolved : list[str]
        Host command references with no counterpart in the export.
    description : str
        Description the builder intended to emit, for round-trip verification.
    """

    name: str
    files: dict[str, tuple[bytes, int]]
    sources: list[str]
    vendored: dict[str, str]
    external: list[str]
    unresolved: list[str]
    description: str


def strip_frontmatter(text: str) -> str:
    r"""Return ``text`` without a leading YAML frontmatter block.

    Examples
    --------
    >>> strip_frontmatter("---\nname: a\n---\nbody\n")
    'body\n'
    >>> strip_frontmatter("body\n")
    'body\n'
    """
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    return text if end == -1 else text[end + 3 :].lstrip("\n")


def _read_body(path: Path) -> str:
    """Read a markdown file and return its body without frontmatter."""
    return strip_frontmatter(path.read_text(encoding="utf-8"))


def _fold_description(text: str) -> list[str]:
    r"""Wrap description text into the lines of a YAML folded block scalar.

    Parameters
    ----------
    text : str
        Description text; interior whitespace is collapsed to single spaces.

    Returns
    -------
    list[str]
        Indented lines to place under a ``>-`` scalar header.

    Examples
    --------
    >>> _fold_description("a  b\nc")
    ['  a b c']
    >>> len(_fold_description("word " * 40)) > 1
    True
    """
    words = text.split()
    lines: list[str] = []
    current = "  "
    for word in words:
        candidate = f"{current} {word}" if current.strip() else f"  {word}"
        if len(candidate) > _DESCRIPTION_WRAP and current.strip():
            lines.append(current)
            current = f"  {word}"
        else:
            current = candidate
    if current.strip():
        lines.append(current)
    return lines


def _render_frontmatter(name: str, description: str, tools: object, meta: dict[str, str]) -> str:
    """Render the portable frontmatter block, spec keys only.

    Parameters
    ----------
    name : str
        Output skill name.
    description : str
        Skill description.
    tools : object
        ``allowed-tools`` value carried over from the source, or None.
    meta : dict[str, str]
        ``metadata`` string map (provenance and the original argument hint).

    Returns
    -------
    str
        The frontmatter block including its delimiters.
    """
    lines = ["---", f"name: {name}", "description: >-", *_fold_description(description)]
    if tools is not None:
        lines.append(f"allowed-tools: {json.dumps(tools)}")
    if meta:
        lines.append("metadata:")
        lines.extend(f"  {key}: {json.dumps(value)}" for key, value in sorted(meta.items()))
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def _convert_bash_lines(text: str) -> str:
    r"""Turn whole-line ``\`!cmd\``` blocks into prose plus a fenced command.

    Parameters
    ----------
    text : str
        Markdown body.

    Returns
    -------
    str
        Body with every inline-bash line replaced.

    Examples
    --------
    >>> print(_convert_bash_lines("Branch:\n`!git branch`\n"), end="")
    Branch — run this command and read the output:
    <BLANKLINE>
    ```bash
    git branch
    ```

    Without a preceding label the prose stands on its own line:

    >>> print(_convert_bash_lines("Intro text\n`!git status`\n"), end="")
    Intro text
    Run this command and read the output:
    <BLANKLINE>
    ```bash
    git status
    ```
    """
    out: list[str] = []
    fenced = False
    for line in text.split("\n"):
        if _FENCE_RE.match(line):
            fenced = not fenced
            out.append(line)
            continue
        match = None if fenced else _BASH_LINE_RE.match(line)
        if match is None:
            out.append(line)
            continue
        _attach_bash_prose(out)
        out.extend(["```bash", match.group("cmd"), "```"])
    return "\n".join(out)


def _attach_bash_prose(out: list[str]) -> None:
    """Attach the run-this-command prose to the label preceding a bash block."""
    index = len(out) - 1
    while index >= 0 and not out[index].strip():
        index -= 1
    if index >= 0 and out[index].rstrip().endswith(":"):
        out[index] = f"{out[index].rstrip().removesuffix(':')} — {_BASH_PROSE}"
    else:
        out.append("Run this command and read the output:")
    if out and out[-1].strip():
        out.append("")


def _widen_inline_bang(text: str) -> str:
    r"""Re-fence leftover inline ``\`!x\``` spans so backtick and bang never touch.

    Parameters
    ----------
    text : str
        Markdown body.

    Returns
    -------
    str
        Body where each remaining span uses padded double backticks, which
        CommonMark renders identically.

    Examples
    --------
    >>> _widen_inline_bang("a `!` glyph")
    'a `` ! `` glyph'
    """
    out: list[str] = []
    fenced = False
    for line in text.split("\n"):
        if _FENCE_RE.match(line):
            fenced = not fenced
            out.append(line)
            continue
        out.append(line if fenced else _INLINE_BANG_RE.sub(r"`` !\1 ``", line))
    return "\n".join(out)


def _describe_source_path(plugin_name: str, rel: str) -> str:
    """Describe an in-repo source coordinate as prose carrying no path token.

    Parameters
    ----------
    plugin_name : str
        Owning plugin.
    rel : str
        Path inside that plugin.

    Returns
    -------
    str
        Prose replacement.

    Examples
    --------
    >>> _describe_source_path("pr", "references/quality-gates.md")
    "the pr plugin's quality-gates reference"
    >>> _describe_source_path("commit", "hooks/")
    "the commit plugin's hooks/ directory"

    A path deeper than ``<kind>/<name>`` describes its leaf, so a stale
    coordinate cannot be laundered into a confident claim about a component
    that does not exist:

    >>> _describe_source_path("pr", "skills/deslop/references/quality-gates.md")
    "the pr plugin's quality-gates reference"
    """
    parts = [p for p in rel.split("/") if p]
    if not parts:
        return f"the {plugin_name} plugin"
    if rel.endswith("/"):
        return f"the {plugin_name} plugin's {parts[-1]}/ directory"
    kinds = {
        "references": "reference",
        "templates": "template",
        "docs": "doc",
        "commands": "command",
        "skills": "skill",
        "hooks": "hook",
    }
    if len(parts) == _COMPONENT_DEPTH and parts[0] == "skills":
        return f"the {plugin_name} plugin's {parts[1]} skill"
    stem = parts[-1].split(".")[0]
    kind = kinds.get(parts[-2] if len(parts) > 1 else parts[0], "file")
    return f"the {plugin_name} plugin's {stem} {kind}"


def _fix_phrases(text: str) -> str:
    """Repair the article and noun a slash-to-skill rewrite leaves behind.

    Examples
    --------
    >>> _fix_phrases("Run the this skill command with your prompt.")
    'Run this skill with your prompt.'
    >>> _fix_phrases("See the the `refine` skill command.")
    'See the `refine` skill.'
    """
    for pattern, repl in _PHRASE_FIXES:
        text = pattern.sub(repl, text)
    return text


def _plugin_of(path: Path) -> Path | None:
    """Return the plugin directory containing ``path``, or None."""
    try:
        rel = path.relative_to(PLUGINS_DIR)
    except ValueError:
        return None
    if not rel.parts:
        return None
    return PLUGINS_DIR / rel.parts[0]


class SkillBuilder:
    """Render one output skill, vendoring every resource it reaches.

    Resources (``references/``, ``templates/``, ``docs/``, ``assets/``) are
    copied into the output directory and their links rewritten to plain
    relative paths. Peer components (other commands and skills) are not
    copied; they are named, because the export emits them as sibling skills.
    """

    def __init__(self, skill: OutputSkill, index: PortableIndex) -> None:
        self._skill: OutputSkill = skill
        self._index: PortableIndex = index
        self._in_code: bool = False
        self._files: dict[str, tuple[bytes, int]] = {}
        self._vendored: dict[Path, str] = {}
        self._pending: list[tuple[Path, Path]] = []
        self._external: set[str] = set()
        self._unresolved: set[str] = set()
        self._notes: set[str] = set()
        self._description: str = ""

    def build(self) -> BuiltSkill:
        """Render the skill and everything it bundles.

        Returns
        -------
        BuiltSkill
            In-memory output, ready to be written or compared.
        """
        body_src = self._skill.body
        fm = body_src.frontmatter
        body = _read_body(body_src.path)
        sources = [str(body_src.path.relative_to(REPO_ROOT))]
        body = self._transform_markdown(body, body_src.plugin, body_src.base)
        if self._skill.overview is not None:
            body = self._attach_overview(body)
            sources.append(str(self._skill.overview.path.relative_to(REPO_ROOT)))
        text = self._render(fm, body + self._portability_notes(body))
        self._files["SKILL.md"] = (text.encode("utf-8"), 0o644)
        self._drain()
        return BuiltSkill(
            name=self._skill.name,
            files=self._files,
            sources=sources,
            vendored={rel: str(src.relative_to(REPO_ROOT)) for src, rel in self._vendored.items()},
            external=sorted(self._external),
            unresolved=sorted(self._unresolved),
            description=" ".join(self._description.split()),
        )

    def _render(self, fm: dict[str, t.Any], body: str) -> str:
        """Render frontmatter plus body for the skill's ``SKILL.md``."""
        overview = self._skill.overview
        desc_fm = overview.frontmatter if overview is not None else fm
        raw_description = t.cast("str", (desc_fm or fm).get("description", "")).strip()
        origin = overview if overview is not None else self._skill.body
        description = self._rewrite_tokens(raw_description, origin.plugin, origin.base)
        self._description = description
        meta = {"source": ", ".join(self._source_paths())}
        hint = t.cast("str | None", fm.get("argument-hint") or desc_fm.get("argument-hint"))
        if hint is not None:
            meta["argument-hint"] = hint
        header = _render_frontmatter(self._skill.name, description, fm.get("allowed-tools"), meta)
        return header + body

    def _source_paths(self) -> list[str]:
        """List the repo-relative sources feeding this skill."""
        paths = [self._skill.body.path]
        if self._skill.overview is not None:
            paths.append(self._skill.overview.path)
        return [str(p.relative_to(REPO_ROOT)) for p in paths]

    def _attach_overview(self, body: str) -> str:
        """Vendor the merged sibling's body and link it from under the title."""
        overview = self._skill.overview
        if overview is None:
            return body
        text = _read_body(overview.path)
        rel = self._allocate(f"{_VENDOR_ROOT}/overview.md")
        self._vendored[overview.path] = rel
        rendered = self._transform_markdown(text, overview.plugin, overview.base)
        self._files[rel] = (rendered.encode("utf-8"), 0o644)
        pointer = f"*Selection guidance for this skill is bundled at `{rel}`.*"
        lines = body.split("\n")
        for position, line in enumerate(lines):
            if line.startswith("# "):
                lines[position + 1 : position + 1] = ["", pointer]
                return "\n".join(lines)
        return f"{pointer}\n\n{body}"

    def _drain(self) -> None:
        """Transform and store every queued resource, following links onward."""
        while self._pending:
            src, plugin = self._pending.pop(0)
            rel = self._vendored[src]
            mode = src.stat().st_mode & 0o777
            try:
                raw = src.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # An assets/ image or font carries no paths to rewrite; copy it
                # through untouched rather than failing the whole export.
                self._files[rel] = (src.read_bytes(), mode)
                continue
            base = plugin
            if src.suffix == _MARKDOWN_SUFFIX:
                text = self._transform_markdown(raw, plugin, base)
            else:
                # SPIKE: non-markdown resources get path rewriting but not the
                # inline-bash or choice-prompt transforms, on the assumption that a
                # .sh/.py/.yml payload never carries them. The check greps every
                # emitted file for both, so a future one would fail loudly.
                text = self._rewrite_tokens(raw, plugin, base)
            self._files[rel] = (text.encode("utf-8"), mode)

    def _transform_markdown(self, text: str, plugin: Path, base: Path) -> str:
        """Apply every portability transform to a markdown body."""
        text = _convert_bash_lines(text)
        text = _widen_inline_bang(text)
        text = self._rewrite_fenced(text, plugin, base)
        if _ASK_RE.search(text):
            self._notes.add("ask")
        return _ASK_RE.sub(_ASK_TOKEN, text)

    def _portability_notes(self, body: str) -> str:
        """Build the trailing notes block for whatever degraded forms were used."""
        ask_note = (
            f"- `{_ASK_TOKEN}` — present the listed options and wait for the user to"
            " pick one. Hosts with a structured multiple-choice tool (Claude Code's"
            " `AskUserQuestion`) should use it; otherwise print a numbered list and wait"
            " for a numbered reply. Never proceed on an assumed answer."
        )
        args_note = (
            "- `$ARGUMENTS` — the text the user passed when invoking this skill. If"
            " your host does not substitute it, read it as the user's request in the"
            " current turn, and ask when there is none."
        )
        bundle_note = (
            "- Bundled files — every relative path in this skill points at a file"
            " shipped inside this skill directory. Read them from here, not from the"
            " host's plugin tree."
        )
        bullets: list[str] = []
        if "ask" in self._notes:
            bullets.append(ask_note)
        if "$ARGUMENTS" in body:
            bullets.append(args_note)
        if self._vendored:
            bullets.append(bundle_note)
        if not bullets:
            return ""
        return "\n\n## Portability notes\n\n" + "\n".join(bullets) + "\n"

    def _allocate(self, preferred: str) -> str:
        """Pick a free output-relative path, disambiguating on basename clashes.

        SPIKE: first writer keeps the plain name and later ones get prefixed, so the
        assignment depends on traversal order. It is reproducible because the traversal
        is sorted, but a symmetric scheme would name both copies for their source.
        """
        if preferred not in self._files and preferred not in self._vendored.values():
            return preferred
        head, _, tail = preferred.rpartition("/")
        counter = 2
        while True:
            candidate = f"{head}/{counter}-{tail}"
            if candidate not in self._files and candidate not in self._vendored.values():
                return candidate
            counter += 1

    def _vendor(self, src: Path, plugin: Path) -> str:
        """Queue a resource for copying and return its output-relative path."""
        known = self._vendored.get(src)
        if known is not None:
            return known
        rel_in_plugin = src.relative_to(plugin)
        top = rel_in_plugin.parts[0] if rel_in_plugin.parts[0] in RESOURCE_DIRS else _VENDOR_ROOT
        preferred = f"{top}/{src.name}"
        if any(rel == preferred for rel in self._vendored.values()):
            preferred = f"{top}/{plugin.name}-{src.name}"
        rel = self._allocate(preferred)
        self._vendored[src] = rel
        self._pending.append((src, plugin))
        return rel

    def _rewrite_fenced(self, text: str, plugin: Path, base: Path) -> str:
        """Rewrite tokens line by line, tracking fenced blocks.

        Inside a fence a slash invocation is a usage example, so it becomes the
        bare skill name rather than a prose phrase.
        """
        lines: list[str] = []
        self._in_code = False
        for line in text.split("\n"):
            if _FENCE_RE.match(line):
                self._in_code = not self._in_code
                lines.append(line)
                continue
            lines.append(self._rewrite_tokens(line, plugin, base))
        self._in_code = False
        return _fix_phrases("\n".join(lines))

    def _rewrite_tokens(self, text: str, plugin: Path, base: Path) -> str:
        """Rewrite every host-specific path or slash token in ``text``."""
        out: list[str] = []
        pos = 0
        for match in _TOKEN_RE.finditer(text):
            start, end = match.start(), match.end()
            quoted = start > 0 and text[start - 1] == "`" and text[end : end + 1] == "`"
            replacement, drop_quotes = self._replace(match, plugin, base)
            if replacement is None:
                continue
            if drop_quotes and quoted and pos <= start - 1:
                out.append(text[pos : start - 1])
                pos = end + 1
            else:
                out.append(text[pos:start])
                pos = end
            out.append(replacement)
        out.append(text[pos:])
        return _fix_phrases("".join(out))

    def _replace(self, match: re.Match[str], plugin: Path, base: Path) -> tuple[str | None, bool]:
        """Resolve one matched token to its replacement text."""
        if match.group("slash") is not None:
            return self._replace_slash(match.group("slash"))
        if match.group("repo") is not None:
            return self._replace_repo(match.group("repo"))
        if match.group("root") is not None:
            raw = match.group("root_path")
            if raw is None:
                return "the plugin root", False
            return self._replace_path(raw.lstrip("/"), plugin, plugin)
        return self._replace_path(match.group("res"), plugin, base)

    def _replace_slash(self, token: str) -> tuple[str | None, bool]:
        """Rewrite a ``/plugin:name`` host invocation to a portable skill name."""
        plugin_name, _, component = token.lstrip("/").partition(":")
        name = self._index.by_invocation.get((plugin_name, component))
        if name is None:
            self._unresolved.add(token)
            return None, False
        if self._in_code:
            return name, False
        if name == self._skill.name:
            return "this skill", True
        return f"the `{name}` skill", True

    def _replace_repo(self, token: str) -> tuple[str | None, bool]:
        """Rewrite an in-repo source coordinate; never vendor through one."""
        _, _, remainder = token.partition("/")
        plugin_name, _, rel = remainder.partition("/")
        target = REPO_ROOT / token
        name = self._index.by_path.get(target)
        if name is not None:
            return (
                ("this skill", True) if name == self._skill.name else (f"the `{name}` skill", True)
            )
        return _describe_source_path(plugin_name, rel), True

    def _replace_path(self, raw: str, plugin: Path, base: Path) -> tuple[str | None, bool]:
        """Vendor a resource path, name a peer component, or leave it verbatim."""
        for candidate in (raw, raw.rstrip(".,;:")):
            resolved = self._resolve(candidate, plugin, base)
            if resolved is None:
                continue
            target, owner = resolved
            name = self._index.by_path.get(target)
            if name is not None:
                if name == self._skill.name:
                    return "this skill", True
                return f"the `{name}` skill", True
            suffix = raw[len(candidate) :]
            return self._vendor(target, owner) + suffix, False
        self._external.add(raw)
        return None, False

    def _resolve(self, raw: str, plugin: Path, base: Path) -> tuple[Path, Path] | None:
        """Resolve a relative reference to an existing file and its owning plugin."""
        for root in (base, plugin):
            target = (root / raw).resolve()
            if not target.is_file():
                continue
            owner = _plugin_of(target)
            if owner is None:
                continue
            return target, owner
        return None


__all__ = [
    "RESOURCE_DIRS",
    "SPEC_FRONTMATTER_KEYS",
    "BuiltSkill",
    "OutputSkill",
    "PortableIndex",
    "SkillBuilder",
    "SourceComponent",
    "strip_frontmatter",
]
