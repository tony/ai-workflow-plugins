#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pydantic>=2.0",
#     "rich>=13.0",
#     "typer>=0.15",
#     "pyyaml>=6.0",
# ]
# ///
"""Marketplace management CLI for tony/skills.

Validates marketplace manifests, plugin structures, and command frontmatter.
Syncs the marketplace manifest with discovered plugin directories.

Examples
--------
Lint the marketplace:

>>> import subprocess
>>> result = subprocess.run(
...     ["python", "scripts/marketplace.py", "lint"],
...     capture_output=True,
...     text=True,
...     cwd=REPO_ROOT,
...     env={**os.environ, "CI": ""},
... )
>>> "errors" in result.stdout.lower() or result.returncode == 0
True

``CI`` is cleared so this exercises one path regardless of where it runs.
Under ``CI`` a missing ``claude`` binary is an error, and ``lint`` reports
counts as ``N error(s) found.`` rather than ``0 errors found.`` -- neither
substring the assertion looks for, so the doctest would fail for a reason
that has nothing to do with the manifest.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import typing as t
from pathlib import Path

import pydantic
import rich.console
import rich.markup
import rich.table
import typer
import yaml
from _portable_render import (  # pyright: ignore[reportImplicitRelativeImport]
    RESOURCE_DIRS,
    SPEC_FRONTMATTER_KEYS,
    TOKEN_RE,
    BuiltSkill,
    OutputSkill,
    PortableIndex,
    SkillBuilder,
    SourceComponent,
    fenced_blocks,
    has_verbatim_fences,
    strip_frontmatter,
)
from _private_path import PrivatePath  # pyright: ignore[reportImplicitRelativeImport]

RESERVED_MARKETPLACE_NAMES = frozenset(
    {
        "claude-code-marketplace",
        "claude-code-plugins",
        "claude-plugins-official",
        "anthropic-marketplace",
        "anthropic-plugins",
        "agent-skills",
        "life-sciences",
    }
)
"""Names explicitly reserved by the Claude Code plugin system."""

_PLUGIN_RELATED_WORDS = frozenset(
    {
        "plugin",
        "plugins",
        "marketplace",
        "tools",
        "extensions",
    }
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = REPO_ROOT / "plugins"
README_PATH = REPO_ROOT / "README.md"
SHARED_REFERENCES_DIR = REPO_ROOT / "shared-references"

SHARED_REFERENCES: dict[str, tuple[str, ...]] = {
    "verification-gates.md": ("action", "respond", "spike"),
    "quality-gates.md": ("pr", "slop"),
    "signatures.yml": ("pr", "slop"),
    "slop-taxonomy.md": ("pr", "slop"),
}
"""Canonical reference docs fanned out to more than one plugin.

Each key is a file in ``shared-references/``; each value names the plugins
whose ``plugins/<plugin>/references/<key>`` receives a byte-identical copy.
``shared-refs`` writes the copies; ``shared-refs --check`` fails when a copy
has drifted from its source, so no plugin needs a hand-written note telling
editors to update the sibling copies by hand.

Only whole-file, byte-identical duplicates belong here. A basename that
recurs across ``plugins/*/references/`` but carries plugin-specific content
(diverged wording, a different config filename per consumer) is not a
candidate for this table -- forcing it to match would erase the legitimate
difference. ``fd -e md . plugins/*/references/ | xargs -n1 basename | sort |
uniq -c | awk '$1>1'`` lists every recurring basename; only the ones that are
still byte-identical after a manual diff should be added here.
"""

README_ROW_RE = re.compile(
    r"^\| \[(?P<name>[^\]]+)\]\(plugins/[^)]*\) \| (?P<cat>[^|]+) \| (?P<desc>.+?) \|[ \t]*\r?$",
    re.MULTILINE,
)
"""A plugin row in the README table. The table is hand-maintained, so it
drifts from the manifest unless something compares the two.

Trailing whitespace and a carriage return are tolerated because neither
changes what the row says. ``$`` matches before ``\\n``, so a CRLF checkout
puts ``\\r`` where the pattern would otherwise demand ``|`` — without the
``\\r?`` every row fails to match at once, and each plugin is reported
missing rather than the line endings being reported."""


app = typer.Typer(
    help="Marketplace management CLI for tony/skills.",
    invoke_without_command=True,
)
console = rich.console.Console()


@app.callback()
def _main(ctx: typer.Context) -> None:  # pyright: ignore[reportUnusedFunction]
    """Marketplace management CLI for tony/skills."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


class Author(pydantic.BaseModel):
    """Author metadata for a plugin or marketplace.

    Examples
    --------
    >>> Author(name="Test", email="test@example.com")
    Author(name='Test', email='test@example.com', url=None)
    """

    name: str
    email: str | None = None
    url: str | None = None


Category = t.Literal[
    "database",
    "deployment",
    "design",
    "development",
    "learning",
    "monitoring",
    "productivity",
    "security",
    "testing",
]


class PluginEntry(pydantic.BaseModel):
    """A plugin entry in the marketplace manifest.

    Examples
    --------
    >>> entry = PluginEntry(
    ...     name="test",
    ...     description="A test plugin",
    ...     version="1.0.0",
    ...     author=Author(name="Test"),
    ...     source="./plugins/test",
    ...     category="development",
    ... )
    >>> entry.name
    'test'

    Invalid categories are rejected:

    >>> try:
    ...     PluginEntry(
    ...         name="bad",
    ...         description="Bad",
    ...         version="1.0.0",
    ...         author=Author(name="Test"),
    ...         source="./plugins/bad",
    ...         category="invalid-category",
    ...     )
    ... except pydantic.ValidationError:
    ...     print("rejected")
    rejected
    """

    name: str
    description: str
    version: str
    author: Author
    source: str
    category: Category
    tags: list[str] | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] | None = None
    strict: bool | None = None


class MarketplaceMetadata(pydantic.BaseModel):
    """Marketplace metadata block (required by ``claude plugin validate``).

    ``pluginRoot`` is the base path Claude Code applies to relative plugin
    sources. It must be declared here so ``sync --write`` round-trips it
    instead of dropping it: third-party skill installers key off its exact
    spelling to decide whether to walk ``plugins/*/skills``.

    Examples
    --------
    >>> MarketplaceMetadata(description="Test marketplace")
    MarketplaceMetadata(description='Test marketplace', pluginRoot=None)

    >>> MarketplaceMetadata(description="Test", pluginRoot=".").pluginRoot
    '.'
    """

    description: str
    pluginRoot: str | None = None  # noqa: N815


class MarketplaceManifest(pydantic.BaseModel):
    """Top-level marketplace manifest schema.

    Examples
    --------
    >>> manifest = MarketplaceManifest(
    ...     name="test-marketplace",
    ...     metadata=MarketplaceMetadata(description="Test"),
    ...     owner=Author(name="Test"),
    ...     plugins=[],
    ... )
    >>> manifest.name
    'test-marketplace'
    """

    name: str
    description: str | None = None
    metadata: MarketplaceMetadata
    owner: Author
    plugins: list[PluginEntry]


class PluginJson(pydantic.BaseModel):
    """Individual plugin.json schema.

    Examples
    --------
    >>> pj = PluginJson(name="test", description="A test plugin")
    >>> pj.name
    'test'
    """

    name: str
    description: str
    author: Author | None = None
    version: str | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] | None = None


class CodexPluginJson(pydantic.BaseModel):
    """A plugin's ``.codex-plugin/plugin.json``, Codex's required entry point.

    ``skills`` names the default location rather than relying on it, so the
    manifest states where Codex looks instead of leaving it implicit.

    Examples
    --------
    >>> CodexPluginJson(name="commit", version="0.0.1", description="d").skills
    './skills/'
    """

    name: str
    version: str
    description: str
    author: Author | None = None
    homepage: str | None = None
    license: str | None = None
    skills: str = "./skills/"


class CodexSource(pydantic.BaseModel):
    """A local plugin source in Codex's marketplace format."""

    source: t.Literal["local"] = "local"
    path: str


class CodexPolicy(pydantic.BaseModel):
    """Install and authentication policy for one Codex marketplace entry."""

    installation: t.Literal["AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"] = "AVAILABLE"
    authentication: t.Literal["ON_INSTALL", "ON_FIRST_USE"] = "ON_INSTALL"


class CodexPluginEntry(pydantic.BaseModel):
    """One plugin in Codex's marketplace manifest."""

    name: str
    source: CodexSource
    policy: CodexPolicy
    category: str


class CodexInterface(pydantic.BaseModel):
    """Install-surface metadata for a Codex marketplace."""

    displayName: str  # noqa: N815


class CodexMarketplace(pydantic.BaseModel):
    """Top-level schema for ``.agents/plugins/marketplace.json``."""

    name: str
    interface: CodexInterface
    plugins: list[CodexPluginEntry]


def load_marketplace() -> MarketplaceManifest:
    """Load and validate the marketplace manifest.

    Returns
    -------
    MarketplaceManifest
        The parsed and validated manifest.

    Raises
    ------
    SystemExit
        If the manifest file is missing or invalid.
    """
    if not MARKETPLACE_PATH.exists():
        console.print(f"[red]Error:[/red] {PrivatePath(MARKETPLACE_PATH)} not found")
        raise SystemExit(1)
    raw = t.cast("dict[str, t.Any]", json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8")))
    return MarketplaceManifest.model_validate(raw)


def validate_marketplace_name(name: str) -> list[str]:
    """Check a marketplace name against reserved name restrictions.

    Returns a list of error messages (empty if the name is valid).

    Parameters
    ----------
    name : str
        The marketplace name to validate.

    Returns
    -------
    list[str]
        Error messages for any violations found.

    Examples
    --------
    Reserved names are rejected:

    >>> validate_marketplace_name("claude-plugins-official")
    ["Marketplace name 'claude-plugins-official' is reserved"]

    Names containing 'claude' with plugin-related words are rejected:

    >>> errs = validate_marketplace_name("claude-plugins")
    >>> len(errs) == 1 and "impersonates" in errs[0]
    True

    Names containing 'anthropic' are rejected:

    >>> errs = validate_marketplace_name("anthropic-tools-v2")
    >>> len(errs) == 1 and "anthropic" in errs[0]
    True

    Non-reserved names pass:

    >>> validate_marketplace_name("skills")
    []
    """
    errors: list[str] = []

    if name in RESERVED_MARKETPLACE_NAMES:
        errors.append(f"Marketplace name '{name}' is reserved")
        return errors

    if "anthropic" in name:
        errors.append(
            f"Marketplace name '{name}' impersonates an official marketplace (contains 'anthropic')"
        )
        return errors

    if "official" in name:
        errors.append(
            f"Marketplace name '{name}' impersonates an official marketplace (contains 'official')"
        )
        return errors

    if "claude" in name:
        for word in _PLUGIN_RELATED_WORDS:
            if word in name:
                msg = (
                    f"Marketplace name '{name}' impersonates an official"
                    f" marketplace (contains 'claude' with '{word}')"
                )
                errors.append(msg)
                return errors

    return errors


def discover_plugins() -> list[Path]:
    """Find all plugin directories under plugins/.

    Returns
    -------
    list[Path]
        Sorted list of directories containing .claude-plugin/plugin.json.
    """
    if not PLUGINS_DIR.exists():
        return []
    return sorted(
        d
        for d in PLUGINS_DIR.iterdir()
        if d.is_dir() and (d / ".claude-plugin" / "plugin.json").exists()
    )


def parse_frontmatter(path: Path) -> dict[str, t.Any] | None:
    r"""Parse YAML frontmatter from a markdown file.

    Parameters
    ----------
    path : Path
        Path to the markdown file.

    Returns
    -------
    dict[str, Any] or None
        Parsed frontmatter dict, or None if no frontmatter found.

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile, os
    >>> d = tempfile.mkdtemp()
    >>> p = Path(d) / "test.md"
    >>> _ = p.write_text("---\ndescription: hello\n---\n# Title\n")
    >>> result = parse_frontmatter(p)
    >>> result["description"]
    'hello'
    >>> p2 = Path(d) / "no_fm.md"
    >>> _ = p2.write_text("# No frontmatter\n")
    >>> parse_frontmatter(p2) is None
    True
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    fm_text = text[3:end].strip()
    try:
        loaded = t.cast("object", yaml.safe_load(fm_text))
    except yaml.YAMLError:
        return None
    if isinstance(loaded, dict):
        return t.cast("dict[str, t.Any]", loaded)
    return None


def _validate_commands_dir(plugin_name: str, commands_dir: Path) -> list[str]:
    """Validate commands/*.md frontmatter in a plugin directory."""
    errors: list[str] = []
    md_files = sorted(commands_dir.glob("*.md"))
    if not md_files:
        errors.append(f"[{plugin_name}] No .md files in commands/")
    for md_file in md_files:
        fm = parse_frontmatter(md_file)
        if fm is None:
            errors.append(f"[{plugin_name}] commands/{md_file.name}: Missing YAML frontmatter")
        elif "description" not in fm:
            errors.append(
                f"[{plugin_name}] commands/{md_file.name}: Frontmatter missing 'description'"
            )
    return errors


def _validate_agents_dir(plugin_name: str, agents_dir: Path) -> list[str]:
    """Validate agents/*.md frontmatter in a plugin directory."""
    errors: list[str] = []
    for md_file in sorted(agents_dir.glob("*.md")):
        fm = parse_frontmatter(md_file)
        if fm is None:
            errors.append(f"[{plugin_name}] agents/{md_file.name}: Missing YAML frontmatter")
        else:
            errors.extend(
                f"[{plugin_name}] agents/{md_file.name}: Frontmatter missing '{field}'"
                for field in ("name", "description")
                if field not in fm
            )
    return errors


def _validate_skills_dir(plugin_name: str, skills_dir: Path) -> list[str]:
    """Validate skills/*/SKILL.md frontmatter in a plugin directory."""
    errors: list[str] = []
    for skill_subdir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
        skill_md = skill_subdir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"[{plugin_name}] skills/{skill_subdir.name}/: Missing SKILL.md")
            continue
        fm = parse_frontmatter(skill_md)
        if fm is None:
            errors.append(
                f"[{plugin_name}] skills/{skill_subdir.name}/SKILL.md: Missing YAML frontmatter"
            )
        else:
            prefix = f"[{plugin_name}] skills/{skill_subdir.name}/SKILL.md"
            errors.extend(
                f"{prefix}: Frontmatter missing '{field}'"
                for field in ("name", "description")
                if field not in fm
            )
    return errors


def _validate_mcp_json(plugin_name: str, path: Path) -> list[str]:
    """Validate .mcp.json structural requirements.

    Parameters
    ----------
    plugin_name : str
        Plugin name for error messages.
    path : Path
        Path to the .mcp.json file.

    Returns
    -------
    list[str]
        Error messages (empty if valid).

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> d = tempfile.mkdtemp()
    >>> p = Path(d) / ".mcp.json"
    >>> _ = p.write_text('{"server": {"type": "http", "url": "http://localhost"}}')
    >>> _validate_mcp_json("test", p)
    []

    Non-dict top-level is rejected:

    >>> _ = p.write_text('[]')
    >>> _validate_mcp_json("test", p)
    ['[test] .mcp.json: top-level value must be an object']

    Non-dict server entries are rejected:

    >>> _ = p.write_text('{"server": "bad"}')
    >>> _validate_mcp_json("test", p)
    ["[test] .mcp.json: server entry 'server' must be an object"]
    """
    errors: list[str] = []
    try:
        data = t.cast("object", json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        errors.append(f"[{plugin_name}] .mcp.json: invalid JSON: {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"[{plugin_name}] .mcp.json: top-level value must be an object")
        return errors

    servers = t.cast("dict[str, object]", data)
    for key, value in servers.items():
        if not isinstance(value, dict):
            errors.append(f"[{plugin_name}] .mcp.json: server entry '{key}' must be an object")
    return errors


def _validate_lsp_json(plugin_name: str, path: Path) -> list[str]:
    """Validate .lsp.json structural requirements.

    Parameters
    ----------
    plugin_name : str
        Plugin name for error messages.
    path : Path
        Path to the .lsp.json file.

    Returns
    -------
    list[str]
        Error messages (empty if valid).

    Examples
    --------
    >>> from pathlib import Path
    >>> import tempfile
    >>> d = tempfile.mkdtemp()
    >>> p = Path(d) / ".lsp.json"
    >>> data = '{"pyright": {"command": "pyright-langserver",'
    >>> data += ' "extensionToLanguage": {".py": "python"}}}'
    >>> _ = p.write_text(data)
    >>> _validate_lsp_json("test", p)
    []

    Non-dict top-level is rejected:

    >>> _ = p.write_text('[]')
    >>> _validate_lsp_json("test", p)
    ['[test] .lsp.json: top-level value must be an object']

    Missing required fields are reported:

    >>> _ = p.write_text('{"pyright": {"command": "pyright-langserver"}}')
    >>> _validate_lsp_json("test", p)
    ["[test] .lsp.json: server 'pyright' missing required field 'extensionToLanguage'"]

    >>> _ = p.write_text('{"pyright": {"extensionToLanguage": {".py": "python"}}}')
    >>> _validate_lsp_json("test", p)
    ["[test] .lsp.json: server 'pyright' missing required field 'command'"]
    """
    errors: list[str] = []
    try:
        data = t.cast("object", json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        errors.append(f"[{plugin_name}] .lsp.json: invalid JSON: {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"[{plugin_name}] .lsp.json: top-level value must be an object")
        return errors

    servers = t.cast("dict[str, object]", data)
    for key, value in servers.items():
        if not isinstance(value, dict):
            errors.append(f"[{plugin_name}] .lsp.json: server entry '{key}' must be an object")
            continue
        errors.extend(
            f"[{plugin_name}] .lsp.json: server '{key}' missing required field '{field}'"
            for field in ("command", "extensionToLanguage")
            if field not in value
        )
    return errors


def _is_runtime_instruction(rel: Path) -> bool:
    """Whether a plugin-relative file is loaded into a host's context at runtime.

    Instruction text is read with the *user's* project as the working directory,
    so a repo-relative path in it addresses nothing. A plugin's ``README.md`` and
    its dated design specs are read on GitHub instead, where a repo-relative path
    is the correct address and rewriting it would break the link.

    Parameters
    ----------
    rel : Path
        Path relative to the plugin directory.

    Returns
    -------
    bool
        True when the file ships as instructions rather than as repo prose.

    Examples
    --------
    >>> from pathlib import Path
    >>> _is_runtime_instruction(Path("commands/deslop.md"))
    True
    >>> _is_runtime_instruction(Path("README.md"))
    False

    A spec under ``docs/specs/`` describes the repo's own layout, so its
    ``plugins/...`` coordinates are the subject matter:

    >>> _is_runtime_instruction(Path("docs/specs/2026-05-17-plan-handoff.md"))
    False

    A doc a command loads at runtime is not exempt just for living in ``docs/``:

    >>> _is_runtime_instruction(Path("docs/repo-guard-protocol.md"))
    True
    """
    if rel.parts == ("README.md",):
        return False
    return rel.parts[:2] != ("docs", "specs")


# SPIKE: the split above is by name, not by reachability. The exact question is
# whether any command or skill can reach the file, which the portable export
# already answers when it walks a bundle. Wiring that walk in would let a spec
# that a command actually loads be checked, and would stop a new prose directory
# from silently opting itself out.


def _citation_error(owner: str, token: str, *, exists: bool, runtime: bool) -> str | None:
    """Report why a repo-relative plugin citation is wrong, or None if it is fine.

    Parameters
    ----------
    owner : str
        Name of the plugin whose file contains the citation.
    token : str
        The cited path, without any trailing ``:line`` suffix.
    exists : bool
        Whether the cited path resolves in this repo.
    runtime : bool
        Whether the citing file ships as instructions (see
        :func:`_is_runtime_instruction`).

    Returns
    -------
    str or None
        Error text, or None when the citation is legitimate.

    Examples
    --------
    A file citing its own plugin by repo path breaks on install, because the host
    resolves the path against the user's project:

    >>> _citation_error("pr", "plugins/pr/commands/review-pr.md", exists=True, runtime=True)
    "cites its own plugin by repo path; use '${CLAUDE_PLUGIN_ROOT}/commands/review-pr.md'"

    A citation into a *different* plugin has no ``${CLAUDE_PLUGIN_ROOT}`` spelling
    — that variable only ever names the citing plugin — so it is left alone:

    >>> _citation_error("weave", "plugins/pr/commands/deslop.md", exists=True, runtime=True) is None
    True

    Repo prose may address its own plugin, since it is read in the repo:

    >>> _citation_error("weave", "plugins/weave/README.md", exists=True, runtime=False) is None
    True

    A path that resolves nowhere is an error in any file, in any direction:

    >>> _citation_error("slop", "plugins/pr/references/gone.md", exists=False, runtime=True)
    'cites a path that does not exist'
    """
    if not exists:
        return "cites a path that does not exist"
    _, _, remainder = token.partition("/")
    cited, _, rel = remainder.partition("/")
    if runtime and cited == owner:
        return f"cites its own plugin by repo path; use '${{CLAUDE_PLUGIN_ROOT}}/{rel}'"
    return None


def _validate_path_citations(plugin_name: str, plugin_dir: Path) -> list[str]:
    """Check every ``plugins/...`` path a plugin's files cite.

    Two failures, both invisible until someone installs the plugin: a file
    pointing into its own plugin by repo path, and a path that resolves nowhere.

    Parameters
    ----------
    plugin_name : str
        Plugin name for error messages.
    plugin_dir : Path
        Path to the plugin directory.

    Returns
    -------
    list[str]
        Error messages (empty if valid).
    """
    errors: list[str] = []
    for path in sorted(plugin_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(plugin_dir)
        runtime = _is_runtime_instruction(rel)
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in TOKEN_RE.finditer(line):
                token = match.group("repo")
                if token is None:
                    continue
                trimmed = token.rstrip(".,;:")
                exists = (REPO_ROOT / token).exists() or (REPO_ROOT / trimmed).exists()
                problem = _citation_error(plugin_name, trimmed, exists=exists, runtime=runtime)
                if problem is not None:
                    errors.append(f"[{plugin_name}] {rel}:{lineno}: '{token}' {problem}")
    return errors


def validate_plugin_dir(plugin_dir: Path) -> list[str]:
    """Validate a single plugin directory structure.

    Parameters
    ----------
    plugin_dir : Path
        Path to the plugin directory.

    Returns
    -------
    list[str]
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    name = plugin_dir.name

    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        errors.append(f"[{name}] Missing .claude-plugin/plugin.json")
    else:
        try:
            raw = t.cast(
                "dict[str, t.Any]",
                json.loads(plugin_json_path.read_text(encoding="utf-8")),
            )
            pj = PluginJson.model_validate(raw)
            if pj.name != name:
                errors.append(
                    f"[{name}] plugin.json name '{pj.name}' does not match directory name '{name}'"
                )
        except (json.JSONDecodeError, pydantic.ValidationError) as exc:
            errors.append(f"[{name}] Invalid plugin.json: {exc}")

    readme_path = plugin_dir / "README.md"
    if not readme_path.exists():
        errors.append(f"[{name}] Missing README.md")

    # Check for at least one component directory or config file
    component_dirs = ["commands", "agents", "skills", "hooks"]
    config_files = [".mcp.json", ".lsp.json"]
    has_component = any((plugin_dir / d).exists() for d in component_dirs) or any(
        (plugin_dir / f).exists() for f in config_files
    )
    if not has_component:
        msg = f"[{name}] No component directory or config file found"
        errors.append(msg)

    # Validate commands/*.md frontmatter
    commands_dir = plugin_dir / "commands"
    if commands_dir.exists():
        errors.extend(_validate_commands_dir(name, commands_dir))

    # Validate agents/*.md and skills/*/SKILL.md frontmatter
    agents_dir = plugin_dir / "agents"
    if agents_dir.exists():
        errors.extend(_validate_agents_dir(name, agents_dir))

    skills_dir = plugin_dir / "skills"
    if skills_dir.exists():
        errors.extend(_validate_skills_dir(name, skills_dir))

    # Validate hooks/hooks.json exists when hooks/ is present
    hooks_dir = plugin_dir / "hooks"
    if hooks_dir.exists():
        hooks_json = hooks_dir / "hooks.json"
        if not hooks_json.exists():
            errors.append(f"[{name}] hooks/ exists but missing hooks.json")

    # Validate .mcp.json structure
    mcp_json_path = plugin_dir / ".mcp.json"
    if mcp_json_path.exists():
        errors.extend(_validate_mcp_json(name, mcp_json_path))

    # Validate .lsp.json structure
    lsp_json_path = plugin_dir / ".lsp.json"
    if lsp_json_path.exists():
        errors.extend(_validate_lsp_json(name, lsp_json_path))

    errors.extend(_validate_path_citations(name, plugin_dir))

    return errors


def _run_claude_validate(path: Path) -> tuple[list[str], list[str]]:
    """Run ``claude plugin validate`` and return (errors, warnings).

    Returns empty lists if the CLI is not available.

    Parameters
    ----------
    path : Path
        Path to validate (marketplace root or plugin directory).

    Returns
    -------
    tuple[list[str], list[str]]
        (errors, warnings) extracted from validate output.
    """
    if shutil.which("claude") is None:
        return [], []
    result = subprocess.run(  # noqa: S603
        ["claude", "plugin", "validate", str(path)],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    marker = "\u276f"
    findings = [
        line.strip().removeprefix(marker).strip()
        for line in result.stdout.splitlines()
        if marker in line
    ]
    if result.returncode != 0:
        return [f"claude validate: {f}" for f in findings], []
    return [], [f"claude validate: {f}" for f in findings]


def _lint_claude_validate() -> tuple[list[str], list[str]]:
    """Run ``claude plugin validate`` on the repo and each plugin, printing status.

    A missing CLI is a skip locally and an error under CI. Skipping silently in
    CI turns the only schema-level check into a no-op while the job still
    reports zero errors, which is how a manifest that fails validation reached
    the default branch unnoticed.
    """
    if shutil.which("claude") is None:
        if os.environ.get("CI"):
            return ["claude validate: CLI not found (required under CI)"], []
        console.print("\n[dim]Skipping claude plugin validate (CLI not found)[/dim]")
        return [], []

    console.print("\n[bold]Running claude plugin validate...[/bold]")
    all_errors: list[str] = []
    all_warnings: list[str] = []
    for path in [REPO_ROOT, *discover_plugins()]:
        ve, vw = _run_claude_validate(path)
        all_errors.extend(ve)
        all_warnings.extend(vw)
    if not all_errors:
        console.print("  [green]OK[/green]")
    return all_errors, all_warnings


def check_readme_table(manifest: MarketplaceManifest, readme: str) -> list[str]:
    r"""Compare the README plugin table against the manifest.

    The manifest is the source of truth and the table is written by hand, so
    the table silently under-reports what the marketplace ships. Nothing else
    in CI reads it.

    Rows are matched on name, then on the two fields a reader acts on:
    category and description. A row that disagrees is worse than a missing
    one, because it looks authoritative.

    Examples
    --------
    >>> def _manifest(*entries: PluginEntry) -> MarketplaceManifest:
    ...     return MarketplaceManifest(
    ...         name="m",
    ...         metadata=MarketplaceMetadata(description="d"),
    ...         owner=Author(name="T"),
    ...         plugins=list(entries),
    ...     )
    >>> entry = PluginEntry(
    ...     name="commit",
    ...     description="Create git commits",
    ...     version="1.0.0",
    ...     author=Author(name="T"),
    ...     source="./plugins/commit",
    ...     category="development",
    ... )
    >>> row = "| [commit](plugins/commit/) | Development | Create git commits |"
    >>> check_readme_table(_manifest(entry), row)
    []

    A plugin with no row is reported:

    >>> check_readme_table(_manifest(entry), "no table here")
    ["README plugin table is missing a row for 'commit'"]

    So is a row whose description drifted from the manifest:

    >>> stale = "| [commit](plugins/commit/) | Development | Old blurb |"
    >>> check_readme_table(_manifest(entry), stale)
    ["README row 'commit': description does not match marketplace.json"]

    And a row naming a plugin the marketplace does not list:

    >>> ghost = "| [gone](plugins/gone/) | Development | Removed |"
    >>> check_readme_table(_manifest(entry), ghost + "\n" + row)
    ["README row 'gone' names a plugin that is not in marketplace.json"]

    A plugin listed twice is reported rather than deduplicated. Keying rows
    by name alone would let the second row mask the first, so a table
    carrying two contradictory rows could report nothing at all:

    >>> check_readme_table(_manifest(entry), row + "\n" + row)
    ["README plugin table lists 'commit' more than once"]

    Trailing whitespace and CRLF endings do not change what a row says, so
    neither may fail the match. A CRLF checkout would otherwise report every
    plugin missing at once, naming the wrong cause for all of them:

    >>> check_readme_table(_manifest(entry), row + "  ")
    []
    >>> check_readme_table(_manifest(entry), row + "\r\n")
    []
    """
    rows: dict[str, re.Match[str]] = {}
    duplicates: list[str] = []
    for match in README_ROW_RE.finditer(readme):
        if match["name"] in rows:
            duplicates.append(match["name"])
        else:
            rows[match["name"]] = match

    errors = [
        f"README plugin table lists '{name}' more than once" for name in sorted(set(duplicates))
    ]
    errors.extend(
        f"README plugin table is missing a row for '{entry.name}'"
        for entry in manifest.plugins
        if entry.name not in rows
    )
    errors.extend(
        f"README row '{name}' names a plugin that is not in marketplace.json"
        for name in sorted(rows.keys() - {entry.name for entry in manifest.plugins})
    )
    for entry in manifest.plugins:
        row = rows.get(entry.name)
        if row is None:
            continue
        if row["cat"].strip().casefold() != entry.category.casefold():
            errors.append(f"README row '{entry.name}': category does not match marketplace.json")
        if row["desc"].strip() != entry.description.strip():
            errors.append(f"README row '{entry.name}': description does not match marketplace.json")
    return errors


@app.command()
def lint() -> None:
    """Validate the marketplace manifest and all plugin directories."""
    errors: list[str] = []
    warnings: list[str] = []

    # Validate marketplace manifest
    console.print("[bold]Validating marketplace manifest...[/bold]")
    try:
        manifest = load_marketplace()
        console.print(f"  Manifest: [green]OK[/green] ({len(manifest.plugins)} plugins)")
    except SystemExit:
        errors.append("Marketplace manifest not found or invalid")
        manifest = None

    if manifest is not None:
        # Validate marketplace name against reserved names
        name_errors = validate_marketplace_name(manifest.name)
        errors.extend(name_errors)

        # Validate each plugin entry's source path
        for entry in manifest.plugins:
            source_path = REPO_ROOT / entry.source
            if not source_path.exists():
                errors.append(
                    f"Marketplace entry '{entry.name}': source path '{entry.source}' does not exist"
                )

        # Check for duplicate plugin names
        seen_names: dict[str, int] = {}
        for entry in manifest.plugins:
            seen_names[entry.name] = seen_names.get(entry.name, 0) + 1
        for dup_name, count in sorted(seen_names.items()):
            if count > 1:
                errors.append(
                    f"Duplicate plugin name '{dup_name}' appears {count} times in marketplace.json"
                )

        # Validate each plugin directory
        console.print("\n[bold]Validating plugin directories...[/bold]")
        discovered = discover_plugins()
        for plugin_dir in discovered:
            plugin_errors = validate_plugin_dir(plugin_dir)
            if plugin_errors:
                errors.extend(plugin_errors)
            else:
                console.print(f"  {plugin_dir.name}: [green]OK[/green]")

        # Check for plugins not in marketplace
        manifest_names = {e.name for e in manifest.plugins}
        discovered_names = {d.name for d in discovered}
        undiscovered = discovered_names - manifest_names
        warnings.extend(
            f"Plugin '{name}' exists in plugins/ but is not listed in marketplace.json"
            for name in sorted(undiscovered)
        )

        # Check the README table, which nothing else in CI reads
        console.print("\n[bold]Validating README plugin table...[/bold]")
        readme_errors = check_readme_table(manifest, README_PATH.read_text(encoding="utf-8"))
        errors.extend(readme_errors)
        if not readme_errors:
            console.print(f"  Table: [green]OK[/green] ({len(manifest.plugins)} rows)")

    # Run claude plugin validate if CLI is available
    cli_errors, cli_warnings = _lint_claude_validate()
    errors.extend(cli_errors)
    warnings.extend(cli_warnings)

    # Report results
    console.print()
    if warnings:
        for warning in warnings:
            console.print(f"[yellow]Warning:[/yellow] {rich.markup.escape(warning)}")

    if errors:
        for error in errors:
            console.print(f"[red]Error:[/red] {rich.markup.escape(error)}")
        console.print(f"\n[red bold]{len(errors)} error(s) found.[/red bold]")
        raise SystemExit(1)

    console.print("[green bold]0 errors found.[/green bold]")


def _serialize_manifest(manifest: MarketplaceManifest) -> str:
    """Render *manifest* as the JSON text ``sync --write`` puts on disk.

    Unset optional fields are omitted rather than written as ``null``.
    ``claude plugin validate`` rejects a null wherever the schema expects a
    concrete type, so serializing them makes ``lint`` fail on this writer's
    own output. Dropping them loses nothing: every optional is declared
    ``... | None = None``, and the validator refuses null for all of them, so
    no field can carry a null worth round-tripping.

    Non-ASCII is written through instead of escaped, keeping em dashes in
    descriptions readable rather than rewriting every one of them.

    Examples
    --------
    >>> manifest = MarketplaceManifest(
    ...     name="test-marketplace",
    ...     metadata=MarketplaceMetadata(description="One — two"),
    ...     owner=Author(name="Test"),
    ...     plugins=[],
    ... )
    >>> text = _serialize_manifest(manifest)

    Unset optionals are absent, not null:

    >>> "null" in text
    False
    >>> '"pluginRoot"' in text
    False

    Set values survive, with the em dash written through rather than escaped:

    >>> "One — two" in text
    True

    A set optional round-trips, ``pluginRoot`` above all: third-party skill
    installers key off its exact spelling, so dropping it would break them.

    >>> manifest.metadata.pluginRoot = "."
    >>> '"pluginRoot": "."' in _serialize_manifest(manifest)
    True

    No root-level ``$schema`` is written. ``claude plugin validate`` rejected
    unknown root keys in Claude Code v2.1.76 and broke CI for four days; the
    key was dropped from the manifest then, and emitting it here would put it
    back on the next write. Current versions tolerate it again, but the
    validator's strictness is upstream and not ours to depend on.

    >>> "$schema" in _serialize_manifest(manifest)
    False
    """
    raw_out: dict[str, t.Any] = manifest.model_dump(mode="json", exclude_none=True)
    return json.dumps(raw_out, indent=2, ensure_ascii=False) + "\n"


def _load_plugin_json(plugin_dir: Path) -> PluginJson:
    """Read and validate one plugin's manifest.

    Parameters
    ----------
    plugin_dir : Path
        A directory under ``plugins/`` holding ``.claude-plugin/plugin.json``.

    Returns
    -------
    PluginJson
        The parsed manifest.

    Examples
    --------
    >>> plugin_dir = discover_plugins()[0]
    >>> _load_plugin_json(plugin_dir).name == plugin_dir.name
    True
    """
    raw = t.cast(
        "dict[str, t.Any]",
        json.loads((plugin_dir / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")),
    )
    return PluginJson.model_validate(raw)


def _homepage_prefix(manifest: MarketplaceManifest) -> str | None:
    """Learn the homepage prefix the manifest's existing entries agree on.

    Returns the text preceding ``/plugins/<name>``, so a new entry can be
    given the same shape. Disagreement returns None rather than a guess: a
    wrong homepage is worse than an absent one, and the entry stays valid
    either way.

    Examples
    --------
    >>> def _entry(name: str, homepage: str | None) -> PluginEntry:
    ...     return PluginEntry(
    ...         name=name,
    ...         description="d",
    ...         version="1.0.0",
    ...         author=Author(name="T"),
    ...         source=f"./plugins/{name}",
    ...         category="development",
    ...         homepage=homepage,
    ...     )
    >>> def _manifest(*entries: PluginEntry) -> MarketplaceManifest:
    ...     return MarketplaceManifest(
    ...         name="m",
    ...         metadata=MarketplaceMetadata(description="d"),
    ...         owner=Author(name="T"),
    ...         plugins=list(entries),
    ...     )
    >>> _homepage_prefix(_manifest(_entry("a", "https://x/tree/main/plugins/a")))
    'https://x/tree/main'

    Entries that disagree yield nothing:

    >>> _homepage_prefix(
    ...     _manifest(
    ...         _entry("a", "https://x/tree/main/plugins/a"),
    ...         _entry("b", "https://y/tree/main/plugins/b"),
    ...     )
    ... ) is None
    True

    So does a manifest whose entries set no homepage:

    >>> _homepage_prefix(_manifest(_entry("a", None))) is None
    True
    """
    prefixes = {
        entry.homepage[: -len(suffix)]
        for entry in manifest.plugins
        if entry.homepage and entry.homepage.endswith(suffix := f"/plugins/{entry.name}")
    }
    return prefixes.pop() if len(prefixes) == 1 else None


def _common_license(manifest: MarketplaceManifest) -> str | None:
    """Return the license every entry that declares one agrees on.

    Examples
    --------
    >>> def _entry(name: str, lic: str | None) -> PluginEntry:
    ...     return PluginEntry(
    ...         name=name,
    ...         description="d",
    ...         version="1.0.0",
    ...         author=Author(name="T"),
    ...         source=f"./plugins/{name}",
    ...         category="development",
    ...         license=lic,
    ...     )
    >>> def _manifest(*entries: PluginEntry) -> MarketplaceManifest:
    ...     return MarketplaceManifest(
    ...         name="m",
    ...         metadata=MarketplaceMetadata(description="d"),
    ...         owner=Author(name="T"),
    ...         plugins=list(entries),
    ...     )
    >>> _common_license(_manifest(_entry("a", "MIT"), _entry("b", "MIT")))
    'MIT'
    >>> _common_license(_manifest(_entry("a", "MIT"), _entry("b", "Apache-2.0"))) is None
    True
    """
    licenses = {entry.license for entry in manifest.plugins if entry.license}
    return licenses.pop() if len(licenses) == 1 else None


def _new_entry(name: str, plugin_meta: PluginJson, manifest: MarketplaceManifest) -> PluginEntry:
    """Build the entry ``sync --write`` adds for a newly discovered plugin.

    Split out of the write loop so what the writer emits can be asserted.
    CI runs ``sync --check`` and never ``sync --write``, so the writer and
    the linter have twice disagreed unnoticed — once emitting ``null`` for
    every unset optional, once re-adding a ``$schema`` key that had been
    deliberately removed. Both reached trunk.

    Examples
    --------
    >>> manifest = MarketplaceManifest(
    ...     name="m",
    ...     metadata=MarketplaceMetadata(description="d"),
    ...     owner=Author(name="Owner"),
    ...     plugins=[
    ...         PluginEntry(
    ...             name="existing",
    ...             description="d",
    ...             version="1.0.0",
    ...             author=Author(name="Owner"),
    ...             source="./plugins/existing",
    ...             category="development",
    ...             homepage="https://example.test/tree/main/plugins/existing",
    ...             license="MIT",
    ...         )
    ...     ],
    ... )
    >>> meta = PluginJson(name="fresh", description="A fresh plugin")
    >>> entry = _new_entry("fresh", meta, manifest)

    The fields no gate checks are the ones that go missing, so assert them:

    >>> entry.homepage
    'https://example.test/tree/main/plugins/fresh'
    >>> entry.license
    'MIT'

    The author falls back to the marketplace owner when the plugin sets none:

    >>> entry.author.name
    'Owner'

    What the writer emits must survive serialization without nulls, which is
    what ``claude plugin validate`` rejects:

    >>> manifest.plugins.append(entry)
    >>> text = _serialize_manifest(manifest)
    >>> "null" in text
    False
    >>> '"license": "MIT"' in text
    True
    >>> '"homepage": "https://example.test/tree/main/plugins/fresh"' in text
    True

    A marketplace with no convention yet gets neither field rather than a
    guess, and still serializes cleanly:

    >>> bare = MarketplaceManifest(
    ...     name="m",
    ...     metadata=MarketplaceMetadata(description="d"),
    ...     owner=Author(name="Owner"),
    ...     plugins=[],
    ... )
    >>> first = _new_entry("first", meta, bare)
    >>> (first.homepage, first.license)
    (None, None)
    >>> bare.plugins.append(first)
    >>> "null" in _serialize_manifest(bare)
    False
    """
    prefix = _homepage_prefix(manifest)
    return PluginEntry(
        name=plugin_meta.name,
        description=plugin_meta.description,
        version=plugin_meta.version or "1.0.0",
        author=plugin_meta.author or manifest.owner,
        source=f"./plugins/{name}",
        category="development",
        homepage=f"{prefix}/plugins/{name}" if prefix is not None else None,
        license=_common_license(manifest),
    )


@app.command()
def sync(*, write: bool = False, check: bool = False) -> None:
    """Compare discovered plugins with marketplace manifest.

    Drift is a plugin present on one side only, or an entry whose description
    no longer matches its ``plugin.json``. Descriptions are the listing users
    read, and nothing else in CI compares them.

    Parameters
    ----------
    write : bool
        If True, update marketplace.json with discovered plugins.
    check : bool
        If True, exit with code 1 when drift is detected (for CI).

    Examples
    --------
    The ``--check`` flag is designed for CI pipelines:

    >>> import subprocess
    >>> result = subprocess.run(
    ...     ["python", "scripts/marketplace.py", "sync", "--check"],
    ...     capture_output=True,
    ...     text=True,
    ...     cwd=REPO_ROOT,
    ... )
    >>> result.returncode == 0  # 0 means in sync
    True
    """
    manifest = load_marketplace()
    discovered = discover_plugins()

    manifest_names = {e.name for e in manifest.plugins}
    discovered_names = {d.name for d in discovered}

    additions = sorted(discovered_names - manifest_names)
    removals = sorted(manifest_names - discovered_names)
    stale = sorted(
        entry.name
        for entry in manifest.plugins
        if entry.name in discovered_names
        and entry.description != _load_plugin_json(PLUGINS_DIR / entry.name).description
    )

    if not additions and not removals and not stale:
        console.print("[green]Marketplace manifest is in sync with plugins/.[/green]")
        return

    table = rich.table.Table(title="Sync Report")
    table.add_column("Status", style="bold")
    table.add_column("Plugin")

    for name in additions:
        table.add_row("[green]+ Add[/green]", name)
    for name in removals:
        table.add_row("[red]- Remove[/red]", name)
    for name in stale:
        table.add_row("[yellow]~ Description[/yellow]", name)

    console.print(table)

    if check:
        msg = (
            "\n[red bold]Marketplace manifest is out of sync.[/red bold]"
            " Run 'sync --write' to update."
        )
        console.print(msg)
        raise SystemExit(1)

    if not write:
        console.print("\nRun with [bold]--write[/bold] to update marketplace.json.")
        return

    # Add new plugins
    for name in additions:
        new_entry = _new_entry(name, _load_plugin_json(PLUGINS_DIR / name), manifest)
        manifest.plugins.append(new_entry)
        msg = (
            f"[yellow]Warning:[/yellow] Plugin '{name}' defaulting to"
            " category='development' — update marketplace.json if needed"
        )
        console.print(msg)

    # Remove missing plugins
    manifest.plugins = [e for e in manifest.plugins if e.name not in removals]

    # Refresh drifted descriptions
    for entry in manifest.plugins:
        if entry.name in stale:
            entry.description = _load_plugin_json(PLUGINS_DIR / entry.name).description

    # Write updated manifest
    _ = MARKETPLACE_PATH.write_text(_serialize_manifest(manifest), encoding="utf-8")
    console.print(f"\n[green]Updated {PrivatePath(MARKETPLACE_PATH)}[/green]")


@app.command(name="check-outdated")
def check_outdated() -> None:
    """Compare versions between plugin.json and marketplace entries."""
    manifest = load_marketplace()

    table = rich.table.Table(title="Version Comparison")
    table.add_column("Plugin")
    table.add_column("Marketplace Version")
    table.add_column("plugin.json Version")
    table.add_column("Status")

    has_mismatch = False

    for entry in manifest.plugins:
        plugin_dir = PLUGINS_DIR / entry.name
        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"

        if not plugin_json_path.exists():
            table.add_row(entry.name, entry.version, "[red]missing[/red]", "[red]ERROR[/red]")
            has_mismatch = True
            continue

        raw = t.cast(
            "dict[str, t.Any]",
            json.loads(plugin_json_path.read_text(encoding="utf-8")),
        )
        plugin_meta = PluginJson.model_validate(raw)
        local_version = plugin_meta.version or "(not set)"

        if plugin_meta.version != entry.version:
            table.add_row(
                entry.name,
                entry.version,
                local_version,
                "[yellow]MISMATCH[/yellow]",
            )
            has_mismatch = True
        else:
            table.add_row(entry.name, entry.version, local_version, "[green]OK[/green]")

    console.print(table)

    if has_mismatch:
        console.print("\n[yellow]Version mismatches found.[/yellow]")
    else:
        console.print("\n[green]All versions match.[/green]")


class SharedReferenceTarget(pydantic.BaseModel):
    """One fan-out copy: a canonical source and the plugin that receives it."""

    basename: str
    plugin: str
    source: Path
    dest: Path


def _shared_reference_targets() -> list[SharedReferenceTarget]:
    """List every (source, destination) pair ``shared-refs`` manages.

    Returns
    -------
    list[SharedReferenceTarget]
        One entry per plugin listed in ``SHARED_REFERENCES``, in table order.

    Examples
    --------
    One target per (basename, plugin) pair, so the count is the total fan-out:

    >>> targets = _shared_reference_targets()
    >>> len(targets) == sum(len(p) for p in SHARED_REFERENCES.values())
    True

    Every target reads from ``shared-references/`` and writes into the
    receiving plugin, which is what makes a copy regenerable rather than
    hand-maintained:

    >>> all(t.source == SHARED_REFERENCES_DIR / t.basename for t in targets)
    True
    >>> all(t.dest.parts[-3:] == (t.plugin, "references", t.basename) for t in targets)
    True

    A basename is never fanned into the same plugin twice:

    >>> pairs = [(t.basename, t.plugin) for t in targets]
    >>> len(pairs) == len(set(pairs))
    True
    """
    return [
        SharedReferenceTarget(
            basename=basename,
            plugin=plugin,
            source=SHARED_REFERENCES_DIR / basename,
            dest=PLUGINS_DIR / plugin / "references" / basename,
        )
        for basename, plugins in SHARED_REFERENCES.items()
        for plugin in plugins
    ]


@app.command(name="shared-refs")
def shared_refs(*, check: bool = False) -> None:
    """Fan out canonical reference docs to the plugins that consume them.

    Each entry in ``SHARED_REFERENCES`` names a file under
    ``shared-references/`` and the plugins whose ``references/`` directory
    gets a byte-identical copy, so every plugin stays installable alone
    while only one place needs an edit.

    Parameters
    ----------
    check : bool
        If True, verify every fanned-out copy still matches its source and
        exit 1 on the first drift instead of writing anything (for CI).

    Examples
    --------
    >>> import subprocess
    >>> result = subprocess.run(
    ...     ["python", "scripts/marketplace.py", "shared-refs", "--check"],
    ...     capture_output=True,
    ...     text=True,
    ...     cwd=REPO_ROOT,
    ... )
    >>> result.returncode == 0  # 0 means every copy matches its source
    True
    """
    targets = _shared_reference_targets()
    errors: list[str] = []

    for target in targets:
        if not target.source.is_file():
            missing = (
                f"shared-refs: canonical source '{PrivatePath(target.source)}' is missing"
                f" (needed for {PrivatePath(target.dest)})"
            )
            errors.append(missing)
            continue
        content = target.source.read_bytes()
        if not check:
            target.dest.parent.mkdir(parents=True, exist_ok=True)
            _ = target.dest.write_bytes(content)
            continue
        if not target.dest.is_file():
            absent = (
                f"shared-refs: '{PrivatePath(target.dest)}' is missing"
                " (run 'shared-refs' to generate it)"
            )
            errors.append(absent)
        elif target.dest.read_bytes() != content:
            drifted = (
                f"shared-refs: '{PrivatePath(target.dest)}' has drifted from"
                f" '{PrivatePath(target.source)}' (run 'shared-refs' to refresh it)"
            )
            errors.append(drifted)

    if not check:
        basenames = len(SHARED_REFERENCES)
        wrote = (
            f"[green]Wrote {len(targets)} fanned-out cop{'y' if len(targets) == 1 else 'ies'}"
            f" from {basenames} canonical source{'s' if basenames != 1 else ''}.[/green]"
        )
        console.print(wrote)
        return

    if errors:
        for error in errors:
            console.print(f"[red]Error:[/red] {rich.markup.escape(error)}")
        console.print(f"\n[red bold]{len(errors)} error(s) found.[/red bold]")
        raise SystemExit(1)
    clean = (
        f"[green bold]0 errors found.[/green bold] {len(targets)} fanned-out"
        " copies match their source."
    )
    console.print(clean)


AGENTS_DIR = REPO_ROOT / ".agents"
PORTABLE_SKILLS_DIR = AGENTS_DIR / "skills"
PORTABLE_MANIFEST_PATH = AGENTS_DIR / "portable-manifest.json"

CODEX_MARKETPLACE_PATH = AGENTS_DIR / "plugins" / "marketplace.json"
"""Codex's native marketplace manifest.

Codex prefers this over ``.claude-plugin/marketplace.json``, which it accepts
only as a legacy fallback. Both ship so neither host depends on the other's
spelling.
"""

CODEX_MANIFEST_REL = Path(".codex-plugin") / "plugin.json"

CODEX_MARKETPLACE_DISPLAY_NAME = "Skills from Tony"
"""Label Codex shows in its marketplace picker.

Names the owner because the manifest name alone is generic in a picker listing
several marketplaces; the manifest description is a full sentence, too long for
a picker row.
"""


def _collect_sources() -> list[SourceComponent]:
    """Collect every skill and command in the source tree.

    Each component carries its parsed frontmatter, which is the only YAML the
    render layer needs from the source tree.

    Returns
    -------
    list[SourceComponent]
        Deterministically ordered components.
    """
    found: list[SourceComponent] = []
    for plugin in discover_plugins():
        skills_dir = plugin / "skills"
        if skills_dir.exists():
            for skill_dir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
                md = skill_dir / "SKILL.md"
                if not md.exists():
                    continue
                fm = parse_frontmatter(md) or {}
                raw = str(fm.get("name") or skill_dir.name)
                found.append(SourceComponent(plugin, "skill", md, raw, skill_dir, fm))
        commands_dir = plugin / "commands"
        if commands_dir.exists():
            found.extend(
                SourceComponent(plugin, "command", md, md.stem, plugin, parse_frontmatter(md) or {})
                for md in sorted(commands_dir.glob("*.md"))
            )
    return found


def _merge_units(group: list[SourceComponent]) -> list[tuple[SourceComponent, SourceComponent]]:
    """Pair same-plugin skill/command duplicates into single units.

    A skill and a command with the same name inside one plugin are two entry
    points to one feature: the command carries the procedure, the skill carries
    the trigger phrasing. A flat skill namespace can only hold one, so they
    merge. Returns ``(body, overview)`` pairs where overview may repeat body.

    Parameters
    ----------
    group : list[SourceComponent]
        Components sharing a raw name.

    Returns
    -------
    list[tuple[SourceComponent, SourceComponent]]
        One entry per output skill.
    """
    units: list[tuple[SourceComponent, SourceComponent]] = []
    commands = [c for c in group if c.kind == "command"]
    skills = [c for c in group if c.kind == "skill"]
    for command in commands:
        mate = next((s for s in skills if s.plugin == command.plugin), None)
        if mate is not None:
            skills.remove(mate)
            units.append((command, mate))
        else:
            units.append((command, command))
    units.extend((skill, skill) for skill in skills)
    return units


def _qualify(plugin: str, raw_name: str) -> str:
    """Namespace an output name with the plugin that owns it.

    Portable skills install into a directory shared with every other pack a
    user has, so a bare name such as ``this`` or ``scan`` is unsafe there.
    Names that already lead with the plugin keep their form rather than
    doubling it.

    Parameters
    ----------
    plugin : str
        Owning plugin name.
    raw_name : str
        Component name before namespacing.

    Returns
    -------
    str
        The namespaced output name.

    Examples
    --------
    >>> _qualify("merge-pr", "this")
    'merge-pr-this'
    >>> _qualify("pytest-optimizer", "00-scan")
    'pytest-optimizer-00-scan'
    >>> _qualify("commit", "commit")
    'commit'
    >>> _qualify("changelog", "changelog-rewrite-aggressively")
    'changelog-rewrite-aggressively'
    """
    if raw_name == plugin or raw_name.startswith(f"{plugin}-"):
        return raw_name
    return f"{plugin}-{raw_name}"


def _assign_names(sources: list[SourceComponent]) -> tuple[list[OutputSkill], PortableIndex]:
    """Resolve output names and build the peer lookup index.

    Parameters
    ----------
    sources : list[SourceComponent]
        Every discovered component.

    Returns
    -------
    tuple[list[OutputSkill], PortableIndex]
        Output skills and the shared lookup index.
    """
    groups: dict[str, list[SourceComponent]] = {}
    for component in sources:
        groups.setdefault(component.raw_name, []).append(component)

    skills: list[OutputSkill] = []
    index = PortableIndex(by_path={}, by_invocation={})
    for raw_name in sorted(groups):
        units = _merge_units(groups[raw_name])
        for body, overview in units:
            name = _qualify(body.plugin.name, raw_name)
            skills.append(OutputSkill(name, body, None if overview is body else overview))
            for member in {body, overview}:
                index.by_path[member.path] = name
                index.by_invocation[(member.plugin.name, member.raw_name)] = name
                stem = member.base.name if member.kind == "skill" else member.path.stem
                index.by_invocation[(member.plugin.name, stem)] = name
    skills.sort(key=lambda s: s.name)
    return skills, index


def _build_portable() -> list[BuiltSkill]:
    """Render every output skill in memory.

    Returns
    -------
    list[BuiltSkill]
        One entry per emitted ``.agents/skills/<name>/`` directory.
    """
    sources = _collect_sources()
    skills, index = _assign_names(sources)
    return [SkillBuilder(skill, index).build() for skill in skills]


def _external_paths(built: list[BuiltSkill]) -> dict[str, list[str]]:
    """Map each path left verbatim to the skills that mention it."""
    external: dict[str, list[str]] = {}
    for skill in built:
        for token in skill.external:
            external.setdefault(token, []).append(skill.name)
    return dict(sorted(external.items()))


def _portable_manifest(built: list[BuiltSkill]) -> dict[str, t.Any]:
    """Summarize provenance, bundling, and duplication for the emitted tree."""
    duplication: dict[str, int] = {}
    unresolved: dict[str, list[str]] = {}
    for skill in built:
        for source in skill.vendored.values():
            duplication[source] = duplication.get(source, 0) + 1
        for token in skill.unresolved:
            unresolved.setdefault(token, []).append(skill.name)
    return {
        "generator": "scripts/marketplace.py portable",
        "skills": [
            {
                "name": s.name,
                "sources": s.sources,
                "bundled": dict(sorted(s.vendored.items())),
                "bytes": sum(len(content) for content, _ in s.files.values()),
            }
            for s in built
        ],
        "duplication": dict(sorted(duplication.items(), key=lambda kv: (-kv[1], kv[0]))),
        "external_paths": _external_paths(built),
        "unresolved_host_commands": dict(sorted(unresolved.items())),
    }


def _write_portable(built: list[BuiltSkill], dest: Path, manifest_path: Path) -> None:
    """Write the emitted tree, replacing any previous contents."""
    if dest.exists():
        shutil.rmtree(dest)
    for skill in built:
        skill_dir = dest / skill.name
        for rel, (content, mode) in sorted(skill.files.items()):
            path = skill_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_bytes(content)
            path.chmod(mode)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _ = manifest_path.write_text(
        json.dumps(_portable_manifest(built), indent=2) + "\n", encoding="utf-8"
    )


def _check_drift(built: list[BuiltSkill]) -> list[str]:
    """Compare the on-disk tree with a fresh render, including permission bits."""
    errors: list[str] = []
    expected: dict[str, tuple[bytes, int]] = {
        f"{skill.name}/{rel}": payload for skill in built for rel, payload in skill.files.items()
    }
    if not PORTABLE_SKILLS_DIR.exists():
        return ["portable: .agents/skills/ has not been generated (run 'portable')"]
    actual = sorted(p for p in PORTABLE_SKILLS_DIR.rglob("*") if p.is_file())
    actual_rel = {str(p.relative_to(PORTABLE_SKILLS_DIR)) for p in actual}
    errors.extend(
        f"portable: stale output file '{rel}'" for rel in sorted(actual_rel - set(expected))
    )
    for rel, (content, mode) in sorted(expected.items()):
        path = PORTABLE_SKILLS_DIR / rel
        if not path.is_file():
            errors.append(f"portable: missing output file '{rel}'")
        elif path.read_bytes() != content:
            errors.append(f"portable: '{rel}' differs from a fresh render")
        elif path.stat().st_mode & 0o777 != mode:
            errors.append(
                f"portable: '{rel}' has mode {path.stat().st_mode & 0o777:o}, want {mode:o}"
            )
    return errors


def _check_invariants(built: list[BuiltSkill], sources: list[SourceComponent]) -> list[str]:
    """Verify the portable-tree contract against the rendered output."""
    errors: list[str] = []
    covered = {source for skill in built for source in skill.sources}
    errors.extend(
        f"portable: source component '{c.path.relative_to(REPO_ROOT)}' has no output skill"
        for c in sources
        if str(c.path.relative_to(REPO_ROOT)) not in covered
    )
    seen: set[str] = set()
    for skill in built:
        if skill.name in seen:
            errors.append(f"portable: duplicate output skill name '{skill.name}'")
        seen.add(skill.name)
        errors.extend(_check_one_skill(skill))
    return errors


def _check_one_skill(skill: BuiltSkill) -> list[str]:
    """Verify frontmatter, forbidden tokens, and bundled-path resolution."""
    errors: list[str] = []
    text = skill.files["SKILL.md"][0].decode("utf-8")
    for rel, (content, _mode) in sorted(skill.files.items()):
        body = strip_frontmatter(content.decode("utf-8", errors="replace"))
        if "CLAUDE_PLUGIN_ROOT" in body:
            errors.append(f"portable: [{skill.name}] '{rel}' still references CLAUDE_PLUGIN_ROOT")
        if "`!" in body:
            errors.append(f"portable: [{skill.name}] '{rel}' still contains an inline-bash span")
        if re.search(r"(?<![A-Za-z0-9._/-])plugins/[a-z]", body):
            errors.append(f"portable: [{skill.name}] '{rel}' still contains an in-repo path")
        climb = re.search(
            r"(?<![A-Za-z0-9._/-])(?:\.\./)+(?:" + "|".join(RESOURCE_DIRS) + r")/",
            body,
        )
        if climb is not None:
            # A source skill reaches its plugin's shared files by climbing out of
            # its own directory, and the flattened export severs that climb. Only
            # a climb into a resource directory is a bundle path; '../myproject'
            # names a sibling of the user's own checkout and must survive intact.
            errors.append(f"portable: [{skill.name}] '{rel}' still climbs out of the skill")
    errors.extend(_check_frontmatter(skill, text))
    errors.extend(
        f"portable: [{skill.name}] bundled path '{rel}' was not emitted"
        for rel in sorted(skill.vendored)
        if rel not in skill.files
    )
    errors.extend(_check_body_paths(skill))
    errors.extend(_check_verbatim_fences(skill))
    return errors


def _check_verbatim_fences(skill: BuiltSkill) -> list[str]:
    """Verify a verbatim source's fenced blocks shipped byte-identical.

    Nothing else catches a regression here. A rewritten quote is still valid
    markdown, still resolves every path, and still passes every other
    invariant — it is simply no longer what the person typed, which is the
    one property the marker exists to hold.
    """
    errors: list[str] = []
    for rel, src_rel in sorted(skill.vendored.items()):
        source = REPO_ROOT / src_rel
        if source.suffix != ".md" or rel not in skill.files:
            continue
        try:
            raw = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not has_verbatim_fences(raw):
            continue
        shipped = skill.files[rel][0].decode("utf-8", errors="replace")
        if fenced_blocks(raw) != fenced_blocks(shipped):
            altered = "is marked verbatim but its fenced blocks were altered on export"
            errors.append(f"portable: [{skill.name}] '{rel}' {altered}")
    return errors


def _check_frontmatter(skill: BuiltSkill, text: str) -> list[str]:
    """Verify the emitted frontmatter carries only spec keys and the right name."""
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp) / "SKILL.md"
        _ = temp.write_text(text, encoding="utf-8")
        fm = parse_frontmatter(temp)
    if fm is None:
        return [f"portable: [{skill.name}] SKILL.md has no parseable frontmatter"]
    emitted = t.cast("str | None", fm.get("name"))
    if emitted != skill.name:
        errors.append(f"portable: [{skill.name}] frontmatter name is '{emitted}'")
    emitted_description = " ".join(t.cast("str", fm.get("description", "")).split())
    if not emitted_description:
        errors.append(f"portable: [{skill.name}] frontmatter has no description")
    elif emitted_description != skill.description:
        errors.append(f"portable: [{skill.name}] description does not survive a YAML round trip")
    errors.extend(
        f"portable: [{skill.name}] frontmatter carries non-spec key '{key}'"
        for key in sorted(fm)
        if key not in SPEC_FRONTMATTER_KEYS
    )
    return errors


def _check_body_paths(skill: BuiltSkill) -> list[str]:
    """Verify every bundled-shaped relative path resolves inside the skill.

    ``docs/`` is the one ambiguous prefix in this repo: weave owns
    ``docs/repo-guard-protocol.md`` while slop and pr quote ``docs/install.md``
    as a file in the *user's* project. An unresolved ``docs/`` path is reported
    rather than failed; every other prefix must resolve.

    SPIKE: that escape hatch is prefix-wide, so a genuinely broken ``docs/`` link
    inside a plugin would be reported as external instead of failing the check.
    Closing it needs the sources to distinguish bundle docs from project docs.
    """
    errors: list[str] = []
    known = set(skill.files)
    external = set(skill.external)
    pattern = re.compile(
        r"(?<![A-Za-z0-9._/-])(?:" + "|".join(RESOURCE_DIRS) + r")/[A-Za-z0-9._/-]+"
    )
    for rel, (content, _mode) in sorted(skill.files.items()):
        body = strip_frontmatter(content.decode("utf-8", errors="replace"))
        for match in pattern.finditer(body):
            token = match.group(0)
            if token in known or token.rstrip(".,;:") in known:
                continue
            if token.startswith("docs/") and token in external:
                continue
            errors.append(f"portable: [{skill.name}] '{rel}' references unbundled '{token}'")
    return errors


def _dump_json(model: pydantic.BaseModel) -> str:
    """Serialize a generated manifest the way it is written to disk."""
    raw: dict[str, t.Any] = model.model_dump(mode="json", exclude_none=True)
    return json.dumps(raw, indent=2, ensure_ascii=False) + "\n"


def _codex_files() -> dict[str, bytes]:
    """Lay out every generated Codex manifest, keyed by repo-relative path.

    Identity mirrors ``.claude-plugin/plugin.json`` so the two manifests cannot
    describe one plugin differently; ``homepage`` and ``license`` live only on
    the marketplace entry and are read from there.

    Returning the whole set as bytes lets the writer and the drift check work
    from one description, so they cannot disagree about what belongs on disk.
    """
    manifest = load_marketplace()
    entries = {entry.name: entry for entry in manifest.plugins}
    codex_marketplace = CodexMarketplace(
        name=manifest.name,
        interface=CodexInterface(displayName=CODEX_MARKETPLACE_DISPLAY_NAME),
        plugins=[
            CodexPluginEntry(
                name=entry.name,
                source=CodexSource(path=entry.source),
                policy=CodexPolicy(),
                # Codex documents its categories capitalized; the value is the
                # same one the Claude manifest already validates.
                category=entry.category.title(),
            )
            for entry in manifest.plugins
        ],
    )
    files = {
        str(CODEX_MARKETPLACE_PATH.relative_to(REPO_ROOT)): _dump_json(codex_marketplace).encode(
            "utf-8"
        )
    }
    for plugin_dir in discover_plugins():
        meta = _load_plugin_json(plugin_dir)
        entry = entries.get(plugin_dir.name)
        codex_json = CodexPluginJson(
            name=meta.name,
            # Codex keys its install cache on the version, so one is required
            # even where the Claude manifest leaves it unset.
            version=meta.version or "0.0.0",
            description=meta.description,
            author=meta.author or (entry.author if entry is not None else None),
            homepage=meta.homepage or (entry.homepage if entry is not None else None),
            license=meta.license or (entry.license if entry is not None else None),
        )
        rel = plugin_dir.relative_to(REPO_ROOT) / CODEX_MANIFEST_REL
        files[str(rel)] = _dump_json(codex_json).encode("utf-8")
    return files


def _check_codex_drift(files: dict[str, bytes]) -> list[str]:
    """Compare the committed Codex manifests against a fresh generation."""
    errors: list[str] = []
    # Globbing the real tree rather than deriving from discover_plugins(): a
    # directory that lost its .claude-plugin/plugin.json is skipped by
    # discovery, so deriving both sides from it can never report the orphaned
    # Codex manifest it leaves behind.
    actual = {
        str(p.relative_to(REPO_ROOT))
        for p in [*PLUGINS_DIR.glob(f"*/{CODEX_MANIFEST_REL}"), CODEX_MARKETPLACE_PATH]
        if p.is_file()
    }
    errors.extend(f"codex: stale manifest '{rel}'" for rel in sorted(actual - set(files)))
    for rel, content in sorted(files.items()):
        path = REPO_ROOT / rel
        if not path.is_file():
            errors.append(f"codex: missing manifest '{rel}'")
        elif path.read_bytes() != content:
            errors.append(f"codex: '{rel}' differs from a fresh render")
    return errors


@app.command()
def portable(*, check: bool = False) -> None:
    """Emit ``.agents/skills/`` and the Codex manifests this repo ships.

    Each skill becomes one portable skill directory. Files a skill reaches by
    climbing out of its own directory are copied in and the links rewritten, so
    each output skill is self-contained. Copies are deliberate: the manifest at
    ``.agents/portable-manifest.json`` records how many times each source is
    duplicated.

    The Codex side needs no such copy. Codex reads ``skills/`` in place, so all
    it takes is a ``.codex-plugin/plugin.json`` per plugin naming that directory
    and a marketplace manifest in Codex's own format.

    Parameters
    ----------
    check : bool
        If True, verify the committed tree matches a fresh render and satisfies
        the portable contract; exit 1 on any finding.
    """
    sources = _collect_sources()
    built = _build_portable()
    codex_files = _codex_files()
    if not check:
        _write_portable(built, PORTABLE_SKILLS_DIR, PORTABLE_MANIFEST_PATH)
        for rel, content in sorted(codex_files.items()):
            path = REPO_ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_bytes(content)
        console.print(f"[green]Wrote {len(codex_files)} Codex manifests[/green]")
        total = sum(len(c) for s in built for c, _ in s.files.values())
        files = sum(len(s.files) for s in built)
        summary = (
            f"[green]Wrote {len(built)} skills, {files} files, {total:,} bytes"
            f" to {PrivatePath(PORTABLE_SKILLS_DIR)}[/green]"
        )
        console.print(summary)
        return

    errors = _check_invariants(built, sources) + _check_drift(built)
    errors.extend(_check_codex_drift(codex_files))
    manifest = json.dumps(_portable_manifest(built), indent=2) + "\n"
    if not PORTABLE_MANIFEST_PATH.exists():
        errors.append("portable: .agents/portable-manifest.json is missing")
    elif PORTABLE_MANIFEST_PATH.read_text(encoding="utf-8") != manifest:
        errors.append("portable: .agents/portable-manifest.json is stale")

    if errors:
        for error in errors:
            console.print(f"[red]Error:[/red] {rich.markup.escape(error)}")
        console.print(f"\n[red bold]{len(errors)} error(s) found.[/red bold]")
        raise SystemExit(1)
    for token, users in _external_paths(built).items():
        note = (
            f"[yellow]Note:[/yellow] '{rich.markup.escape(token)}' names a file in the"
            f" user's project, not in the bundle; left verbatim in {len(users)} skill(s)"
        )
        console.print(note)
    clean = (
        f"[green bold]0 errors found.[/green bold] {len(built)} portable skills,"
        f" {sum(len(s.files) for s in built)} files."
    )
    console.print(clean)


if __name__ == "__main__":
    app()
