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
"""Marketplace management CLI for ai-workflow-plugins.

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
... )
>>> "errors" in result.stdout.lower() or result.returncode == 0
True
"""

from __future__ import annotations

import dataclasses
import json
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

app = typer.Typer(
    help="Marketplace management CLI for ai-workflow-plugins.",
    invoke_without_command=True,
)
console = rich.console.Console()


@app.callback()
def _main(ctx: typer.Context) -> None:  # pyright: ignore[reportUnusedFunction]
    """Marketplace management CLI for ai-workflow-plugins."""
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

    Examples
    --------
    >>> MarketplaceMetadata(description="Test marketplace")
    MarketplaceMetadata(description='Test marketplace')
    """

    description: str


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

    >>> validate_marketplace_name("ai-workflow-plugins")
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
        md_files = sorted(commands_dir.glob("*.md"))
        if not md_files:
            errors.append(f"[{name}] No .md files in commands/")
        for md_file in md_files:
            fm = parse_frontmatter(md_file)
            if fm is None:
                errors.append(f"[{name}] commands/{md_file.name}: Missing YAML frontmatter")
            elif "description" not in fm:
                errors.append(
                    f"[{name}] commands/{md_file.name}: Frontmatter missing 'description'"
                )

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
    """Run ``claude plugin validate`` on the repo and each plugin, printing status."""
    if shutil.which("claude") is None:
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

    # Run claude plugin validate if CLI is available
    cli_errors, cli_warnings = _lint_claude_validate()
    errors.extend(cli_errors)
    warnings.extend(cli_warnings)

    # Report results
    console.print()
    if warnings:
        for warning in warnings:
            console.print(f"[yellow]Warning:[/yellow] {warning}")

    if errors:
        for error in errors:
            console.print(f"[red]Error:[/red] {error}")
        console.print(f"\n[red bold]{len(errors)} error(s) found.[/red bold]")
        raise SystemExit(1)

    console.print("[green bold]0 errors found.[/green bold]")


@app.command()
def sync(*, write: bool = False, check: bool = False) -> None:
    """Compare discovered plugins with marketplace manifest.

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

    if not additions and not removals:
        console.print("[green]Marketplace manifest is in sync with plugins/.[/green]")
        return

    table = rich.table.Table(title="Sync Report")
    table.add_column("Status", style="bold")
    table.add_column("Plugin")

    for name in additions:
        table.add_row("[green]+ Add[/green]", name)
    for name in removals:
        table.add_row("[red]- Remove[/red]", name)

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
        plugin_dir = PLUGINS_DIR / name
        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
        raw = t.cast(
            "dict[str, t.Any]",
            json.loads(plugin_json_path.read_text(encoding="utf-8")),
        )
        plugin_meta = PluginJson.model_validate(raw)
        new_entry = PluginEntry(
            name=plugin_meta.name,
            description=plugin_meta.description,
            version=plugin_meta.version or "1.0.0",
            author=plugin_meta.author or manifest.owner,
            source=f"./plugins/{name}",
            category="development",
        )
        manifest.plugins.append(new_entry)
        msg = (
            f"[yellow]Warning:[/yellow] Plugin '{name}' defaulting to"
            " category='development' — update marketplace.json if needed"
        )
        console.print(msg)

    # Remove missing plugins
    manifest.plugins = [e for e in manifest.plugins if e.name not in removals]

    # Write updated manifest
    raw_out: dict[str, t.Any] = manifest.model_dump(mode="json")
    raw_out["$schema"] = "https://anthropic.com/claude-code/marketplace.schema.json"
    output = json.dumps(raw_out, indent=2) + "\n"
    _ = MARKETPLACE_PATH.write_text(output, encoding="utf-8")
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


AGENTS_DIR = REPO_ROOT / ".agents"
PORTABLE_SKILLS_DIR = AGENTS_DIR / "skills"
PORTABLE_MANIFEST_PATH = AGENTS_DIR / "portable-manifest.json"

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
    """

    plugin: Path
    kind: str
    path: Path
    raw_name: str
    base: Path


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


def _split_body(path: Path) -> tuple[dict[str, t.Any], str]:
    """Split a markdown file into its frontmatter mapping and its body.

    Parameters
    ----------
    path : Path
        Markdown file to split.

    Returns
    -------
    tuple[dict[str, Any], str]
        Parsed frontmatter (empty when absent) and the body text.
    """
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(path) or {}
    if not text.startswith("---"):
        return fm, text
    end = text.find("---", 3)
    if end == -1:
        return fm, text
    return fm, text[end + 3 :].lstrip("\n")


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


def _collect_sources() -> list[SourceComponent]:
    """Collect every skill and command in the source tree.

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
                found.append(SourceComponent(plugin, "skill", md, raw, skill_dir))
        commands_dir = plugin / "commands"
        if commands_dir.exists():
            found.extend(
                SourceComponent(plugin, "command", md, md.stem, plugin)
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
    >>> _qualify("changelog", "changelog-recut")
    'changelog-recut'
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
        fm, body = _split_body(body_src.path)
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
        desc_fm = parse_frontmatter(overview.path) if overview is not None else fm
        raw_description = t.cast("str", (desc_fm or fm).get("description", "")).strip()
        origin = overview if overview is not None else self._skill.body
        description = self._rewrite_tokens(raw_description, origin.plugin, origin.base)
        self._description = description
        meta = {"source": ", ".join(self._source_paths())}
        hint = t.cast("str | None", fm.get("argument-hint") or (desc_fm or {}).get("argument-hint"))
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
        _, text = _split_body(overview.path)
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
            raw = src.read_text(encoding="utf-8")
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


def _strip_frontmatter(text: str) -> str:
    r"""Return ``text`` without a leading YAML frontmatter block.

    Examples
    --------
    >>> _strip_frontmatter("---\nname: a\n---\nbody\n")
    'body\n'
    >>> _strip_frontmatter("body\n")
    'body\n'
    """
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    return text if end == -1 else text[end + 3 :].lstrip("\n")


def _check_one_skill(skill: BuiltSkill) -> list[str]:
    """Verify frontmatter, forbidden tokens, and bundled-path resolution."""
    errors: list[str] = []
    text = skill.files["SKILL.md"][0].decode("utf-8")
    for rel, (content, _mode) in sorted(skill.files.items()):
        body = _strip_frontmatter(content.decode("utf-8", errors="replace"))
        if "CLAUDE_PLUGIN_ROOT" in body:
            errors.append(f"portable: [{skill.name}] '{rel}' still references CLAUDE_PLUGIN_ROOT")
        if "`!" in body:
            errors.append(f"portable: [{skill.name}] '{rel}' still contains an inline-bash span")
        if re.search(r"(?<![A-Za-z0-9._/-])plugins/[a-z]", body):
            errors.append(f"portable: [{skill.name}] '{rel}' still contains an in-repo path")
    errors.extend(_check_frontmatter(skill, text))
    errors.extend(
        f"portable: [{skill.name}] bundled path '{rel}' was not emitted"
        for rel in sorted(skill.vendored)
        if rel not in skill.files
    )
    errors.extend(_check_body_paths(skill))
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
        body = _strip_frontmatter(content.decode("utf-8", errors="replace"))
        for match in pattern.finditer(body):
            token = match.group(0)
            if token in known or token.rstrip(".,;:") in known:
                continue
            if token.startswith("docs/") and token in external:
                continue
            errors.append(f"portable: [{skill.name}] '{rel}' references unbundled '{token}'")
    return errors


@app.command()
def portable(*, check: bool = False) -> None:
    """Emit ``.agents/skills/`` so non-Claude agents can consume this repo.

    Every skill and command becomes one portable skill directory. Files a
    component reaches through ``${CLAUDE_PLUGIN_ROOT}`` or a plugin-relative
    path are copied into that directory and the links rewritten, so each
    output skill is self-contained. Copies are deliberate: the manifest at
    ``.agents/portable-manifest.json`` records how many times each source is
    duplicated.

    Parameters
    ----------
    check : bool
        If True, verify the committed tree matches a fresh render and satisfies
        the portable contract; exit 1 on any finding.
    """
    sources = _collect_sources()
    built = _build_portable()
    if not check:
        _write_portable(built, PORTABLE_SKILLS_DIR, PORTABLE_MANIFEST_PATH)
        total = sum(len(c) for s in built for c, _ in s.files.values())
        files = sum(len(s.files) for s in built)
        summary = (
            f"[green]Wrote {len(built)} skills, {files} files, {total:,} bytes"
            f" to {PrivatePath(PORTABLE_SKILLS_DIR)}[/green]"
        )
        console.print(summary)
        return

    errors = _check_invariants(built, sources) + _check_drift(built)
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
