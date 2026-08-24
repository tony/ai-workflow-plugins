#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0",
#     "typer>=0.15",
# ]
# ///
"""Install this marketplace into every agent CLI installed on this machine.

Each host caches an unpacked plugin tree keyed by name and version, so
installing over an unchanged version is a no-op. Every host is therefore wiped
before it is re-added: plugins uninstalled, marketplace removed, marketplace
re-added, plugins reinstalled. That sequence refreshes edited skills while the
version stays at ``0.0.1``, which is the state a working tree is normally in.

Examples
--------
Reinstall the working tree into every detected host:

    uv run scripts/install.py

Preview the exact commands without running them:

    uv run scripts/install.py --dry-run

Install the published marketplace instead of the working tree:

    uv run scripts/install.py --source tony/skills
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import typing as t
from pathlib import Path

import rich.console
import rich.table
import typer

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MANIFEST = REPO_ROOT / ".claude-plugin" / "marketplace.json"
GITHUB_SOURCE = "tony/skills"
STEP_TIMEOUT = 300

HOST_HELP = (
    "Host to install into (repeatable). Defaults to every detected host that "
    "can read a local directory."
)
SOURCE_HELP = (
    "Marketplace source: a local path, owner/repo, or git URL. Defaults to this working tree."
)

app = typer.Typer(add_completion=False, help=__doc__)
console = rich.console.Console()


class Step(t.NamedTuple):
    """One CLI invocation in a host's plan.

    ``fatal`` steps abort the host on failure. Wipe steps are not fatal: a host
    that never had the marketplace fails every uninstall, and that is the
    expected first run rather than an error.
    """

    argv: tuple[str, ...]
    fatal: bool

    def render(self) -> str:
        """Return the step as a copy-pasteable shell command.

        Examples
        --------
        >>> Step(("codex", "plugin", "add", "commit@skills"), fatal=True).render()
        'codex plugin add commit@skills'
        """
        return " ".join(self.argv)


@dataclasses.dataclass(frozen=True)
class Host:
    """An agent CLI this marketplace can be installed into.

    Attributes
    ----------
    key : str
        Name used for ``--host``.
    binary : str
        Executable looked up on ``PATH``.
    label : str
        Human-readable name for output.
    local_source : bool
        Whether the host can install from a local directory. Cursor indexes a
        marketplace server-side from a git URL against the signed-in account,
        so it cannot see a working tree and is never selected by default.
    """

    key: str
    binary: str
    label: str
    local_source: bool = True


HOSTS: tuple[Host, ...] = (
    Host("claude", "claude", "Claude Code"),
    Host("codex", "codex", "Codex"),
    Host("grok", "grok", "Grok"),
    Host("agy", "agy", "Antigravity"),
    Host("cursor", "agent", "Cursor", local_source=False),
)

HOSTS_BY_KEY = {host.key: host for host in HOSTS}
DEFAULT_HOST_KEYS = tuple(host.key for host in HOSTS if host.local_source)


def _manifest() -> dict[str, t.Any]:
    """Return the parsed marketplace manifest."""
    return t.cast(
        "dict[str, t.Any]",
        json.loads(CLAUDE_MANIFEST.read_text(encoding="utf-8")),
    )


def marketplace_name() -> str:
    """Return the marketplace name the hosts resolve ``plugin@name`` against."""
    return t.cast("str", _manifest()["name"])


def plugin_names() -> list[str]:
    """Return every plugin listed in the marketplace manifest.

    Read from the manifest rather than from ``plugins/`` because the manifest
    is what a host resolves against: a directory missing from it cannot be
    installed, and asking for it fails the run.
    """
    entries = t.cast("list[dict[str, t.Any]]", _manifest()["plugins"])
    return [t.cast("str", entry["name"]) for entry in entries]


def grok_source_name(source: str) -> str:
    """Return the name Grok will file *source* under.

    Grok names a marketplace source after its directory or repository, not
    after the ``name`` field in the manifest the way Claude Code and Codex do.

    Examples
    --------
    >>> grok_source_name("/home/user/work/skills")
    'skills'
    >>> grok_source_name("tony/skills")
    'skills'
    >>> grok_source_name("https://github.com/tony/skills.git")
    'skills'
    """
    trimmed = source.rstrip("/").removesuffix(".git")
    return trimmed.rsplit("/", maxsplit=1)[-1]


def plan_claude(source: str, market: str, plugins: list[str]) -> list[Step]:
    """Return the wipe-and-install plan for Claude Code.

    Examples
    --------
    >>> for step in plan_claude(".", "skills", ["commit"]):
    ...     print(step.render())
    claude plugin uninstall commit@skills -y
    claude plugin marketplace remove skills
    claude plugin marketplace add .
    claude plugin install commit@skills -y
    """
    steps = [
        Step(("claude", "plugin", "uninstall", f"{name}@{market}", "-y"), fatal=False)
        for name in plugins
    ]
    steps.append(Step(("claude", "plugin", "marketplace", "remove", market), fatal=False))
    steps.append(Step(("claude", "plugin", "marketplace", "add", source), fatal=True))
    steps.extend(
        Step(("claude", "plugin", "install", f"{name}@{market}", "-y"), fatal=True)
        for name in plugins
    )
    return steps


def plan_codex(source: str, market: str, plugins: list[str]) -> list[Step]:
    """Return the wipe-and-install plan for Codex.

    Examples
    --------
    >>> for step in plan_codex(".", "skills", ["commit"]):
    ...     print(step.render())
    codex plugin remove commit@skills
    codex plugin marketplace remove skills
    codex plugin marketplace add .
    codex plugin add commit@skills
    """
    steps = [
        Step(("codex", "plugin", "remove", f"{name}@{market}"), fatal=False) for name in plugins
    ]
    steps.append(Step(("codex", "plugin", "marketplace", "remove", market), fatal=False))
    steps.append(Step(("codex", "plugin", "marketplace", "add", source), fatal=True))
    steps.extend(
        Step(("codex", "plugin", "add", f"{name}@{market}"), fatal=True) for name in plugins
    )
    return steps


def plan_grok(source: str, market: str, plugins: list[str]) -> list[Step]:
    """Return the wipe-and-install plan for Grok.

    Removing the source cascades into uninstalling its plugins, so no per-plugin
    wipe is needed. ``market`` is ignored: Grok files the source under its own
    derived name.

    Examples
    --------
    >>> for step in plan_grok("/w/skills", "skills", ["commit"]):
    ...     print(step.render())
    grok plugin marketplace remove skills
    grok plugin marketplace add /w/skills
    grok plugin install commit@skills --trust
    """
    del market
    name = grok_source_name(source)
    steps = [Step(("grok", "plugin", "marketplace", "remove", name), fatal=False)]
    steps.append(Step(("grok", "plugin", "marketplace", "add", source), fatal=True))
    steps.extend(
        Step(("grok", "plugin", "install", f"{plugin}@{name}", "--trust"), fatal=True)
        for plugin in plugins
    )
    return steps


def plan_agy(source: str, market: str, plugins: list[str]) -> list[Step]:
    """Return the wipe-and-install plan for Antigravity.

    Antigravity has no marketplace that reads a repository manifest; its
    marketplace is Google's hosted one. It does recognize a ``plugins/``
    directory and installs every plugin under it, which reaches the same end
    state, so the whole tree is installed in one call.

    Examples
    --------
    >>> for step in plan_agy("/w/skills", "skills", ["commit"]):
    ...     print(step.render())
    agy plugin uninstall commit
    agy plugin install /w/skills
    """
    del market
    steps = [Step(("agy", "plugin", "uninstall", name), fatal=False) for name in plugins]
    steps.append(Step(("agy", "plugin", "install", source), fatal=True))
    return steps


def plan_cursor(source: str, market: str, plugins: list[str]) -> list[Step]:
    """Return the wipe-and-install plan for Cursor.

    Cursor re-indexes a marketplace on its own servers against the signed-in
    account, so it takes a git URL and never a working tree. Plugins arrive
    with the marketplace rather than one call each.

    Examples
    --------
    >>> for step in plan_cursor("https://github.com/tony/skills.git", "skills", ["commit"]):
    ...     print(step.render())
    agent plugin marketplace remove skills
    agent plugin marketplace add https://github.com/tony/skills.git
    agent plugin marketplace update skills
    """
    del plugins
    return [
        Step(("agent", "plugin", "marketplace", "remove", market), fatal=False),
        Step(("agent", "plugin", "marketplace", "add", source), fatal=True),
        Step(("agent", "plugin", "marketplace", "update", market), fatal=False),
    ]


PLANNERS: dict[str, t.Callable[[str, str, list[str]], list[Step]]] = {
    "claude": plan_claude,
    "codex": plan_codex,
    "grok": plan_grok,
    "agy": plan_agy,
    "cursor": plan_cursor,
}


def resolve_source(host: Host, local: str, remote: str) -> str:
    """Return the source string *host* should be pointed at.

    A host that cannot read a local directory gets the git remote regardless of
    what the run asked for, because the alternative is a command that fails.

    Examples
    --------
    >>> resolve_source(HOSTS_BY_KEY["codex"], "/w/skills", "tony/skills")
    '/w/skills'
    >>> resolve_source(HOSTS_BY_KEY["cursor"], "/w/skills", "tony/skills")
    'https://github.com/tony/skills.git'
    """
    if host.local_source:
        return local
    if remote.startswith(("http://", "https://", "git@")):
        return remote
    return f"https://github.com/{remote}.git"


@dataclasses.dataclass
class HostResult:
    """What happened to one host during a run."""

    host: Host
    installed: int = 0
    wiped: int = 0
    wipe_steps: int = 0
    failure: str | None = None
    skipped: str | None = None


def run_step(step: Step) -> subprocess.CompletedProcess[str]:
    """Run one step, capturing output."""
    return subprocess.run(  # noqa: S603
        step.argv,
        capture_output=True,
        text=True,
        timeout=STEP_TIMEOUT,
        check=False,
        env=os.environ.copy(),
    )


def execute(host: Host, steps: list[Step], *, verbose: bool) -> HostResult:
    """Run *steps* for *host*, stopping at the first fatal failure."""
    result = HostResult(host=host)
    result.wipe_steps = sum(1 for step in steps if not step.fatal)
    for step in steps:
        completed = run_step(step)
        ok = completed.returncode == 0
        if ok and step.fatal:
            result.installed += 1
        elif ok:
            result.wiped += 1
        if verbose or (not ok and step.fatal):
            marker = "[green]ok[/green]" if ok else "[red]fail[/red]"
            console.print(f"  {marker} [dim]{step.render()}[/dim]")
        if not ok and step.fatal:
            detail = (completed.stderr or completed.stdout).strip().splitlines()
            result.failure = detail[-1] if detail else f"exit {completed.returncode}"
            console.print(f"  [red]{result.failure}[/red]")
            break
    return result


def summarize(results: list[HostResult]) -> None:
    """Print one row per host."""
    table = rich.table.Table(title="Install summary")
    table.add_column("Host")
    table.add_column("Wiped", justify="right")
    table.add_column("Installed", justify="right")
    table.add_column("Status")
    for result in results:
        if result.skipped is not None:
            status = f"[dim]skipped: {result.skipped}[/dim]"
        elif result.failure is not None:
            status = f"[red]failed: {result.failure}[/red]"
        else:
            status = "[green]ok[/green]"
        table.add_row(
            result.host.label,
            f"{result.wiped}/{result.wipe_steps}",
            str(result.installed),
            status,
        )
    console.print(table)


@app.command()
def install(
    host: t.Annotated[
        list[str] | None,
        typer.Option("--host", help=HOST_HELP),
    ] = None,
    source: t.Annotated[
        str | None,
        typer.Option("--source", help=SOURCE_HELP),
    ] = None,
    dry_run: t.Annotated[
        bool,
        typer.Option("--dry-run", help="Print the commands without running them."),
    ] = False,
    verbose: t.Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Print every command as it runs."),
    ] = False,
) -> None:
    """Wipe and reinstall this marketplace on each selected host."""
    keys = list(host) if host else list(DEFAULT_HOST_KEYS)
    unknown = [key for key in keys if key not in HOSTS_BY_KEY]
    if unknown:
        console.print(f"[red]Unknown host(s): {', '.join(unknown)}[/red]")
        console.print(f"Known: {', '.join(HOSTS_BY_KEY)}")
        raise typer.Exit(code=2)

    local = source or str(REPO_ROOT)
    remote = source or GITHUB_SOURCE
    market = marketplace_name()
    plugins = plugin_names()

    console.print(f"[bold]{market}[/bold]: {len(plugins)} plugins")
    console.print(f"Source: {local}\n")

    results: list[HostResult] = []
    for key in keys:
        selected = HOSTS_BY_KEY[key]
        host_source = resolve_source(selected, local, remote)
        steps = PLANNERS[key](host_source, market, plugins)

        if shutil.which(selected.binary) is None:
            results.append(HostResult(host=selected, skipped="CLI not found"))
            continue

        console.print(f"[bold]{selected.label}[/bold] [dim]({host_source})[/dim]")
        if dry_run:
            for step in steps:
                console.print(f"  [dim]{step.render()}[/dim]")
            results.append(HostResult(host=selected, skipped="dry run"))
            continue
        results.append(execute(selected, steps, verbose=verbose))

    console.print()
    summarize(results)
    if any(result.failure for result in results):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
