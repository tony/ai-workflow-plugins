#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml>=6.0",
#     "rich>=13.0",
#     "typer>=0.15",
# ]
# ///
"""E2E plugin lifecycle tests for tony/skills.

Runs the full Claude plugin CLI lifecycle in an isolated sandbox:
validate -> marketplace add -> install -> disable/enable -> uninstall -> marketplace remove.

Sandboxing: Sets ``HOME`` to a temp directory so ``claude`` reads all config
from ``$HOME/.claude/`` without touching the real user config.

Examples
--------
Test with local marketplace source (default):

    uv run scripts/e2e.py

Test with GitHub source:

    uv run scripts/e2e.py --source github

Test both sources:

    uv run scripts/e2e.py --source both
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

import rich.console
import typer
import yaml
from _private_path import PrivatePath  # pyright: ignore[reportImplicitRelativeImport]

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_NAME = "skills"
GITHUB_SOURCE = "tony/skills"


def _discover_plugins() -> list[str]:
    """Find every plugin directory under ``plugins/``.

    Discovered rather than enumerated. Every static test iterates this list, so
    a hand-maintained roster does not fail when it falls behind — it silently
    stops testing whatever is missing from it.
    """
    plugins_dir = REPO_ROOT / "plugins"
    if not plugins_dir.is_dir():
        return []
    return sorted(
        d.name
        for d in plugins_dir.iterdir()
        if d.is_dir() and (d / ".claude-plugin" / "plugin.json").is_file()
    )


PLUGINS = _discover_plugins()

WEAVE_PRESENT_RESULTS = "../../references/present-results.md"
WEAVE_WORKER_REFERENCE = "../../references/worker-backends.md"
PORTABLE_HEADLESS_DEFAULT_MARKER = "<!-- portable: ask-user-choice=headless-default -->"
WEAVE_MUTATING_SKILLS = frozenset({"architecture", "execute", "prompt"})

app = typer.Typer(help="E2E plugin lifecycle tests for tony/skills.")
console = rich.console.Console()

Source = t.Literal["local", "github", "both"]
Host = t.Literal["claude", "codex", "both"]

CODEX_SKILL_ENTRY_RE = re.compile(r"^- (?P<id>[A-Za-z0-9:._-]+):", re.MULTILINE)

TestCase = tuple[str, t.Callable[[], None]]


class TestFailureError(Exception):
    """Raised when a test assertion fails."""


def _run_claude(args: list[str], sandbox: Path) -> subprocess.CompletedProcess[str]:
    """Run a ``claude`` CLI command with HOME set to *sandbox*.

    Parameters
    ----------
    args : list[str]
        Arguments to pass after ``claude``.
    sandbox : Path
        Temporary home directory for isolation.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The completed process result.
    """
    env = {**os.environ, "HOME": str(sandbox)}
    return subprocess.run(  # noqa: S603
        ["claude", *args],  # noqa: S607
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )


def _assert(condition: bool, msg: str) -> None:
    """Assert *condition* is truthy, raising `TestFailureError` on failure."""
    if not condition:
        raise TestFailureError(msg)


def _pass(label: str) -> None:
    console.print(f"  [green]✔[/green] {label}")


def _fail(label: str, detail: str) -> None:
    console.print(f"  [red]✘[/red] {label}")
    console.print(f"    [dim]{detail}[/dim]")


def _run_test(label: str, fn: t.Callable[[], None]) -> bool:
    """Run a single test, print pass/fail, return success bool."""
    try:
        fn()
        _pass(label)
    except TestFailureError as exc:
        _fail(label, str(exc))
        return False
    except subprocess.TimeoutExpired as exc:
        _fail(label, f"Command timed out ({exc.timeout:.0f}s)")
        return False
    return True


# ---------------------------------------------------------------------------
# Static validation helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict[str, t.Any]:
    """Parse YAML frontmatter from a markdown file.

    Returns an empty dict if no frontmatter is found.
    """
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    parsed = t.cast(
        "dict[str, t.Any] | None",
        yaml.safe_load(m.group(1)),
    )
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _assert_arguments_have_hint(path: Path, fm: dict[str, t.Any]) -> None:
    """Require Claude's invocation hint when a skill consumes arguments."""
    text = path.read_text(encoding="utf-8")
    body = text.split("\n---\n", maxsplit=1)[-1]
    if "$ARGUMENTS" not in body:
        return
    hint = fm.get("argument-hint")
    rel = path.relative_to(REPO_ROOT)
    _assert(
        isinstance(hint, str) and bool(hint.strip()),
        f"{rel}: skill consumes $ARGUMENTS but has no argument-hint",
    )


def _test_static_frontmatter() -> list[TestCase]:
    """Verify skill frontmatter has required fields and bare tool names.

    Skills are the only component that carries ``allowed-tools`` here, and a
    parenthesized pattern in one binds the entry to a single ecosystem's
    command line, which is what this repo's language-agnostic rule forbids.
    """
    tests: list[TestCase] = []

    for plugin in PLUGINS:
        commands_dir = REPO_ROOT / "plugins" / plugin / "skills"
        if not commands_dir.is_dir():
            continue
        for cmd_file in sorted(commands_dir.glob("*/SKILL.md")):

            def _check_frontmatter(p: Path = cmd_file) -> None:
                fm = _parse_frontmatter(p)
                _assert(
                    bool(fm),
                    f"{p.relative_to(REPO_ROOT)}: no YAML frontmatter found",
                )
                _assert(
                    "description" in fm,
                    f"{p.relative_to(REPO_ROOT)}: missing 'description' in frontmatter",
                )
                # Every skill here writes allowed-tools as a YAML list, so a
                # substring test against the parsed value asks whether "(" is
                # an element and is always False. Join first.
                raw = t.cast("object", fm.get("allowed-tools", ""))
                names: list[object] = (
                    t.cast("list[object]", raw) if isinstance(raw, list) else [raw]
                )
                allowed = " ".join(str(n) for n in names)
                if allowed:
                    rel = p.relative_to(REPO_ROOT)
                    detail = f"(no parenthesized patterns): {allowed}"
                    msg = f"{rel}: allowed-tools must use bare names {detail}"
                    _assert("(" not in allowed, msg)

            tests.append(
                (f"frontmatter: {plugin}/{cmd_file.parent.name}", _check_frontmatter),
            )

    return tests


def _test_static_plugin_structure() -> list[TestCase]:
    """Verify each plugin has required directory structure."""
    tests: list[TestCase] = []

    for plugin in PLUGINS:
        plugin_dir = REPO_ROOT / "plugins" / plugin

        def _check_structure(d: Path = plugin_dir, name: str = plugin) -> None:
            _assert(
                (d / ".claude-plugin" / "plugin.json").is_file(),
                f"{name}: missing .claude-plugin/plugin.json",
            )
            _assert(
                (d / "README.md").is_file(),
                f"{name}: missing README.md",
            )
            has_component = any(
                [
                    (d / "commands").is_dir(),
                    (d / "agents").is_dir(),
                    (d / "skills").is_dir(),
                    (d / "hooks").is_dir(),
                    (d / ".mcp.json").is_file(),
                    (d / ".lsp.json").is_file(),
                ],
            )
            _assert(
                has_component,
                f"{name}: no component directories or config files found",
            )

        tests.append((f"structure: {plugin}", _check_structure))

    return tests


def _test_static_agent_skill_frontmatter() -> list[TestCase]:
    """Verify agent and skill frontmatter has required fields."""
    tests: list[TestCase] = []

    for plugin in PLUGINS:
        agents_dir = REPO_ROOT / "plugins" / plugin / "agents"
        if agents_dir.is_dir():
            for agent_file in sorted(agents_dir.glob("*.md")):

                def _check_agent(p: Path = agent_file) -> None:
                    fm = _parse_frontmatter(p)
                    rel = p.relative_to(REPO_ROOT)
                    _assert(bool(fm), f"{rel}: no YAML frontmatter found")
                    _assert("name" in fm, f"{rel}: missing 'name' in frontmatter")
                    _assert(
                        "description" in fm,
                        f"{rel}: missing 'description' in frontmatter",
                    )

                tests.append(
                    (f"agent frontmatter: {plugin}/{agent_file.name}", _check_agent),
                )

        skills_dir = REPO_ROOT / "plugins" / plugin / "skills"
        if skills_dir.is_dir():
            for skill_file in sorted(skills_dir.glob("*/SKILL.md")):

                def _check_skill(p: Path = skill_file) -> None:
                    fm = _parse_frontmatter(p)
                    rel = p.relative_to(REPO_ROOT)
                    _assert(bool(fm), f"{rel}: no YAML frontmatter found")
                    _assert("name" in fm, f"{rel}: missing 'name' in frontmatter")
                    _assert(
                        "description" in fm,
                        f"{rel}: missing 'description' in frontmatter",
                    )
                    _assert_arguments_have_hint(p, fm)

                skill_name = skill_file.parent.name
                tests.append(
                    (f"skill frontmatter: {plugin}/{skill_name}", _check_skill),
                )

    return tests


def _test_static_marketplace_json() -> list[TestCase]:
    """Verify marketplace.json entries match PLUGINS and have required fields."""
    tests: list[TestCase] = []
    manifest_path = REPO_ROOT / ".claude-plugin" / "marketplace.json"

    def _check_marketplace() -> None:
        _assert(manifest_path.is_file(), "marketplace.json not found")
        data: dict[str, t.Any] = json.loads(  # pyright: ignore[reportAny]
            manifest_path.read_text(encoding="utf-8"),
        )
        plugins_list = t.cast(
            "list[dict[str, t.Any]]",
            data.get("plugins", []),
        )
        names = {p["name"] for p in plugins_list}

        for plugin in PLUGINS:
            _assert(plugin in names, f"Plugin '{plugin}' missing from marketplace.json")

        required_fields = {"name", "description", "version", "author", "category", "source"}
        for entry in plugins_list:
            entry_name = t.cast("str", entry.get("name", "<unnamed>"))
            for field in required_fields:
                _assert(
                    field in entry,
                    f"marketplace entry '{entry_name}': missing '{field}'",
                )
            source = t.cast("str", entry.get("source", ""))
            if source.startswith("./"):
                source_path = REPO_ROOT / source
                _assert(
                    source_path.is_dir(),
                    f"marketplace entry '{entry_name}': source path '{source}' does not exist",
                )

    tests.append(("marketplace.json validation", _check_marketplace))
    return tests


def _assert_weave_worker_reference(reference_path: Path) -> None:
    """Assert the shared weave worker protocol's strategy boundary."""
    _assert(reference_path.is_file(), "weave: missing references/worker-backends.md")
    text = reference_path.read_text(encoding="utf-8")
    subagent_label = "Adversarial sub-agents (Recommended)"
    cli_label = "Separate model CLIs"
    _assert(subagent_label in text, f"weave workers: missing '{subagent_label}'")
    _assert(cli_label in text, f"weave workers: missing '{cli_label}'")
    _assert(
        text.index(subagent_label) < text.index(cli_label),
        "weave workers: sub-agents must be the first choice",
    )
    _assert(
        "headless" in text.lower() and "`subagents`" in text,
        "weave workers: headless mode must default to subagents",
    )

    native_heading = "## Adversarial sub-agents"
    cli_heading = "## Separate model CLIs"
    _assert(native_heading in text, f"weave workers: missing '{native_heading}' section")
    _assert(cli_heading in text, f"weave workers: missing '{cli_heading}' section")
    native_text = text[text.index(native_heading) : text.index(cli_heading)]
    _assert(
        "host-native" in native_text and "independent" in native_text,
        "weave workers: native lanes must use independent host-native sub-agents",
    )
    _assert(
        "parallel" in native_text,
        "weave workers: native lanes must request parallel dispatch",
    )
    forbidden_invocations = ("agy --", "gemini -m", "codex exec", "agent -p", "claude -p")
    offenders = [token for token in forbidden_invocations if token in native_text]
    _assert(
        not offenders,
        f"weave workers: native path invokes model CLIs: {', '.join(offenders)}",
    )

    cli_text = text[text.index(cli_heading) :]
    _assert(
        "explicit" in cli_text and "CLI detection" in cli_text,
        "weave workers: model CLI detection must require explicit selection",
    )
    _assert(
        "Never switch" in text,
        "weave workers: backends must not cross-fallback without consent",
    )
    gpt_lanes = [line for line in text.splitlines() if line.startswith("- `gpt` carries")]
    _assert(bool(gpt_lanes), "weave workers: gpt lane mapping is missing")
    _assert(
        "`codex` CLI" in gpt_lanes[0],
        "weave workers: the gpt lane must name codex as its CLI executor",
    )

    role_ids = ("maintainer", "skeptic", "builder")
    missing_roles = [role for role in role_ids if f"- `{role}`" not in native_text]
    _assert(
        not missing_roles,
        f"weave workers: native artifact IDs are missing: {', '.join(missing_roles)}",
    )
    lifecycle_terms = ("<role>.md", "participants", "pass", "completion", "judg", "refinement")
    missing_lifecycle = [term for term in lifecycle_terms if term not in text.lower()]
    _assert(
        not missing_lifecycle,
        "weave workers: role artifacts do not span the full lifecycle: "
        + ", ".join(missing_lifecycle),
    )

    read_only_start = native_text.find("For project-read-only commands")
    mutating_start = native_text.find("For mutating commands")
    _assert(
        read_only_start >= 0 and mutating_start > read_only_start,
        "weave workers: native isolation contracts are missing",
    )
    read_only_text = native_text[read_only_start:mutating_start]
    mutating_text = native_text[mutating_start:]
    _assert(
        "isolated worktree" in read_only_text and "shared checkout" not in read_only_text,
        "weave workers: read-only roles need isolated worktrees",
    )
    _assert(
        "isolated worktree" in mutating_text,
        "weave workers: mutating roles need isolated worktrees",
    )
    _assert(
        "remove" in native_text and "worktree" in native_text,
        "weave workers: native worktree cleanup is not declared",
    )


def _weave_result_commands(commands_dir: Path) -> tuple[Path, ...]:
    """Derive weave commands that render through the shared result contract."""
    return tuple(
        path
        for path in sorted(commands_dir.glob("*/SKILL.md"))
        if WEAVE_PRESENT_RESULTS in path.read_text(encoding="utf-8")
    )


def _weave_ensemble_commands(commands_dir: Path) -> tuple[Path, ...]:
    """Derive ensemble commands from all shared result-rendering callers."""
    return tuple(
        path for path in _weave_result_commands(commands_dir) if path.parent.name != "fix-review"
    )


def _worker_selection(text: str, rel: Path) -> str:
    """Return a command's worker selection section."""
    heading = "## Worker selection"
    _assert(heading in text, f"{rel}: worker selection section is missing")
    return text.split(heading, 1)[1].split("\n---", 1)[0].lower()


def _session_contract_text(command_path: Path, text: str) -> str:
    """Resolve a local or explicitly inherited session template."""
    if '"session_id"' in text:
        return text
    inherited = re.search(
        r"Follow Phase 2 .*?\.\./([^`/]+)/SKILL\.md`",
        text,
        re.DOTALL,
    )
    _assert(
        inherited is not None,
        f"{command_path.relative_to(REPO_ROOT)}: session template is neither local nor inherited",
    )
    inherited_match = t.cast("re.Match[str]", inherited)
    inherited_path = command_path.parent.parent / inherited_match.group(1) / "SKILL.md"
    _assert(
        inherited_path.is_file(),
        f"{command_path.relative_to(REPO_ROOT)}: inherited session command is missing",
    )
    return inherited_path.read_text(encoding="utf-8")


def _result_call(text: str, rel: Path) -> str:
    """Return the caller assignments immediately following present-results."""
    _assert(WEAVE_PRESENT_RESULTS in text, f"{rel}: present-results caller is missing")
    tail = text.split(WEAVE_PRESENT_RESULTS, 1)[1]
    return "\n".join(tail.splitlines()[:24])


def _assert_weave_fix_review_contract(command_path: Path) -> None:
    """Assert fix-review supplies the non-ensemble result values."""
    text = command_path.read_text(encoding="utf-8")
    rel = command_path.relative_to(REPO_ROOT)
    result_call = _result_call(text, rel)
    expected = (
        ("`WORKER_BACKEND`", "null"),
        ("`PARTICIPANTS`", "[]"),
        ("`MODELS`", "null"),
    )
    for variable, value in expected:
        line = next(
            (line for line in result_call.splitlines() if variable in line),
            "",
        )
        _assert(
            value in line,
            f"{rel}: present-results requires {variable} = {value}",
        )


def _assert_weave_worker_command(command_path: Path) -> None:
    """Assert one weave command resolves and gates its worker backend."""
    text = command_path.read_text(encoding="utf-8")
    rel = command_path.relative_to(REPO_ROOT)
    _assert(WEAVE_WORKER_REFERENCE in text, f"{rel}: worker backend protocol is not cited")
    operational_headings = (
        heading
        for heading in ("## Phase 0", "## Phase 1", "## Orchestration Plan")
        if heading in text
    )
    first_operation = min(text.index(heading) for heading in operational_headings)
    _assert(
        text.index(WEAVE_WORKER_REFERENCE) < first_operation,
        f"{rel}: worker backend must resolve before the first operational phase",
    )
    _assert(
        "--workers=subagents|model-clis" in text,
        f"{rel}: argument hint must expose --workers",
    )
    _assert(
        "`worker_backend == model-clis`" in text,
        f"{rel}: external model instructions are not gated",
    )
    _assert("agy --model" in text, f"{rel}: Antigravity CLI path was removed")
    _assert("codex exec" in text, f"{rel}: Codex CLI path was removed")

    selection = _worker_selection(text, rel)
    lifecycle_terms = (
        "whole session",
        "dispatch",
        "retry",
        "judg",
        "refinement",
        "artifact",
        "session metadata",
    )
    missing_lifecycle = [term for term in lifecycle_terms if term not in selection]
    _assert(
        not missing_lifecycle,
        f"{rel}: worker backend does not govern the whole lifecycle: "
        + ", ".join(missing_lifecycle),
    )
    _assert(
        PORTABLE_HEADLESS_DEFAULT_MARKER in text,
        f"{rel}: portable headless default needs a structured source marker",
    )

    session_text = _session_contract_text(command_path, text)
    session_lines = session_text.splitlines()
    session_id_line = next(
        (index for index, line in enumerate(session_lines) if '"session_id"' in line),
        -1,
    )
    session_start_line = next(
        (index for index, line in enumerate(session_lines) if '"event":"session_start"' in line),
        -1,
    )
    _assert(session_id_line >= 0, f"{rel}: session.json template is missing")
    _assert(session_start_line >= 0, f"{rel}: session_start event template is missing")
    session_template = "\n".join(session_lines[session_id_line : session_id_line + 24])
    session_event = "\n".join(session_lines[session_start_line : session_start_line + 4])
    for field in ('"worker_backend"', '"participants"'):
        _assert(field in session_template, f"{rel}: session.json omits {field}")
        _assert(field in session_event, f"{rel}: session_start event omits {field}")

    result_call = _result_call(text, rel)
    _assert(
        "`WORKER_BACKEND`" in result_call and "`worker_backend`" in result_call,
        f"{rel}: present-results omits WORKER_BACKEND",
    )
    _assert(
        "`PARTICIPANTS`" in result_call,
        f"{rel}: present-results omits PARTICIPANTS",
    )
    models_line = next(
        (line for line in result_call.splitlines() if "`MODELS`" in line),
        "",
    )
    _assert(
        "model-clis" in models_line and "null" in models_line,
        f"{rel}: MODELS must be conditional on model-clis and null otherwise",
    )

    if command_path.parent.name in WEAVE_MUTATING_SKILLS:
        heading = "## Native mutating lifecycle"
        _assert(heading in text, f"{rel}: native mutating lifecycle is missing")
        native_lifecycle = text.split(heading, 1)[1].split("\n## ", 1)[0].lower()
        required = (
            "`worker_backend == subagents`",
            "isolated worktree",
            "<participant>",
            "no worker runs in the main checkout",
            "capture",
            "adopt",
            "cleanup",
        )
        missing = [term for term in required if term not in native_lifecycle]
        _assert(
            not missing,
            f"{rel}: native mutating lifecycle is incomplete: {', '.join(missing)}",
        )


def _assert_weave_worker_portable_contract(commands_dir: Path) -> None:
    """Assert portable weave skills retain the worker strategy contract."""
    renderer_text = (REPO_ROOT / "scripts" / "_portable_render.py").read_text(encoding="utf-8")
    _assert(
        PORTABLE_HEADLESS_DEFAULT_MARKER in renderer_text,
        "portable renderer must consume the structured headless-default marker",
    )
    _assert(
        'if "documented headless default" in body' not in renderer_text,
        "portable renderer must not infer behavior from prose",
    )
    source_worker_reference = (
        REPO_ROOT / "plugins" / "weave" / "references" / "worker-backends.md"
    ).read_text(encoding="utf-8")

    for command_path in _weave_ensemble_commands(commands_dir):
        skill_name = f"weave-{command_path.parent.name}"
        skill_dir = REPO_ROOT / ".agents" / "skills" / skill_name
        skill_path = skill_dir / "SKILL.md"
        rel = skill_path.relative_to(REPO_ROOT)
        _assert(skill_path.is_file(), f"{rel}: portable skill is missing")
        text = skill_path.read_text(encoding="utf-8")
        _assert(
            "references/worker-backends.md" in text,
            f"{rel}: portable skill omits the worker backend protocol",
        )
        _assert(
            "Honor a documented headless default" in text,
            f"{rel}: portable choice guidance conflicts with the headless default",
        )
        _assert(
            (skill_dir / "references" / "worker-backends.md").is_file(),
            f"{rel}: worker backend reference was not bundled",
        )
        bundled_worker_reference = (skill_dir / "references" / "worker-backends.md").read_text(
            encoding="utf-8"
        )
        _assert(
            bundled_worker_reference == source_worker_reference,
            f"{rel}: bundled worker backend reference is stale",
        )


def _test_static_weave_worker_backends() -> list[TestCase]:
    """Verify every weave ensemble resolves its worker backend before execution."""
    weave_dir = REPO_ROOT / "plugins" / "weave"
    commands_dir = weave_dir / "skills"
    reference_path = weave_dir / "references" / "worker-backends.md"
    result_commands = _weave_result_commands(commands_dir)
    ensemble_commands = _weave_ensemble_commands(commands_dir)
    tests: list[TestCase] = [
        (
            "weave worker backend: shared protocol",
            lambda: _assert_weave_worker_reference(reference_path),
        ),
        (
            "weave worker backend: command coverage",
            lambda: _assert(
                set(result_commands) == set(commands_dir.glob("*/SKILL.md")),
                "weave worker backend: every command must declare its result contract",
            ),
        ),
    ]

    tests.extend(
        (
            f"weave worker backend: {command_path.parent.name}",
            lambda p=command_path: _assert_weave_worker_command(p),
        )
        for command_path in ensemble_commands
    )

    fix_review_path = commands_dir / "fix-review" / "SKILL.md"
    tests.append(
        (
            "weave worker backend: fix-review result contract",
            lambda: _assert_weave_fix_review_contract(fix_review_path),
        ),
    )
    tests.append(
        (
            "weave worker backend: portable contract",
            lambda: _assert_weave_worker_portable_contract(commands_dir),
        ),
    )
    return tests


def _test_static_weave_timeouts() -> list[TestCase]:
    """Verify weave command timeout multipliers are consistent (0.5x/1.5x)."""
    tests: list[TestCase] = []
    weave_commands_dir = REPO_ROOT / "plugins" / "weave" / "skills"
    if not weave_commands_dir.is_dir():
        return tests

    timeout_pattern = re.compile(
        r'"Default \((\d+)s\)".*\n.*"Quick — (\d+)s".*\n.*"Long — (\d+)s"',
    )

    for cmd_file in _weave_ensemble_commands(weave_commands_dir):

        def _check_timeouts(p: Path = cmd_file) -> None:
            rel = p.relative_to(REPO_ROOT)
            text = p.read_text(encoding="utf-8")
            # A command may carry the block itself or inherit the phase that
            # holds it. Returning on a miss would exempt whichever commands the
            # pattern cannot follow, which is the opposite of a check.
            found = timeout_pattern.search(text) or timeout_pattern.search(
                _session_contract_text(p, text),
            )
            _assert(found is not None, f"{rel}: no timeout block, local or inherited")
            m = t.cast("re.Match[str]", found)
            default = int(m.group(1))
            quick = int(m.group(2))
            long_ = int(m.group(3))
            _assert(
                quick == default // 2,
                f"{rel}: Quick={quick}s but expected {default // 2}s (0.5x {default}s)",
            )
            expected_long = default + default // 2
            _assert(
                long_ == expected_long,
                f"{rel}: Long={long_}s but expected {expected_long}s (1.5x {default}s)",
            )

        tests.append((f"weave timeouts: {cmd_file.parent.name}", _check_timeouts))

    return tests


def _test_static_weave_stderr_redirects() -> list[TestCase]:
    """Verify fallback agent CLI uses append (2>>) not overwrite (2>)."""
    tests: list[TestCase] = []
    weave_commands_dir = REPO_ROOT / "plugins" / "weave" / "skills"
    if not weave_commands_dir.is_dir():
        return tests

    def _check_redirects() -> None:
        bad_files: list[str] = []
        for cmd_file in sorted(weave_commands_dir.glob("*/SKILL.md")):
            text = cmd_file.read_text(encoding="utf-8")
            for line in text.splitlines():
                if "agent " in line and '2>"$SESSION_DIR' in line:
                    bad_files.append(str(cmd_file.relative_to(REPO_ROOT)))
                    break
        _assert(
            len(bad_files) == 0,
            f"Agent fallbacks using 2> instead of 2>>: {', '.join(bad_files)}",
        )

    tests.append(("weave stderr redirects", _check_redirects))
    return tests


def _test_static_agy_invocations() -> list[TestCase]:
    """Verify agy invocations put -p last and weave commands add </dev/null."""
    tests: list[TestCase] = []
    weave_commands_dir = REPO_ROOT / "plugins" / "weave" / "skills"
    flag_order_files = [
        REPO_ROOT / "plugins" / "model-cli" / "README.md",
        REPO_ROOT / "plugins" / "model-cli" / "skills" / "agy" / "SKILL.md",
        *sorted(weave_commands_dir.glob("*/SKILL.md")),
    ]
    # agy's -p/--print/--prompt is a Go-style value-flag: it must come last, or it
    # swallows the next flag as the prompt. Flag a print-flag right after `agy`, or a
    # print-flag immediately followed by another `--flag`.
    bad_order = re.compile(r"agy\s+(?:-p|--print|--prompt)\b|(?:-p|--print|--prompt)\s+--")

    def _check_flag_order() -> None:
        offenders: list[str] = []
        for path in flag_order_files:
            if not path.is_file():
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            for num, line in enumerate(lines, 1):
                if "agy " in line and " --model" in line and bad_order.search(line):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{num}")
        _assert(
            not offenders,
            f"agy -p/--print must come after every other flag: {', '.join(offenders)}",
        )

    def _check_stdin_guard() -> None:
        offenders: list[str] = []
        if weave_commands_dir.is_dir():
            for cmd_file in sorted(weave_commands_dir.glob("*/SKILL.md")):
                lines = cmd_file.read_text(encoding="utf-8").splitlines()
                for num, line in enumerate(lines, 1):
                    if (
                        "agy --model" in line
                        and '>"$SESSION_DIR' in line
                        and "</dev/null" not in line
                    ):
                        offenders.append(f"{cmd_file.relative_to(REPO_ROOT)}:{num}")
        _assert(
            not offenders,
            f"weave agy invocations missing </dev/null stdin guard: {', '.join(offenders)}",
        )

    def _check_exit_status() -> None:
        # The disposable-worktree wrapper appends `git worktree remove` after agy;
        # without capturing the run's status it would mask agy's exit code. Every
        # wrapper must therefore capture `rc=$?` and `exit "$rc"` after cleanup.
        offenders: list[str] = []
        if weave_commands_dir.is_dir():
            for cmd_file in sorted(weave_commands_dir.glob("*/SKILL.md")):
                lines = cmd_file.read_text(encoding="utf-8").splitlines()
                for num, line in enumerate(lines, 1):
                    if 'worktree add -q --detach "$AGY_RO_WT"' in line and 'exit "$rc"' not in line:
                        offenders.append(f"{cmd_file.relative_to(REPO_ROOT)}:{num}")
        _assert(
            not offenders,
            f'agy wrappers must preserve exit status (rc=$?; exit "$rc"): {", ".join(offenders)}',
        )

    def _check_gpt_lane_fallback() -> None:
        # The agy → gemini → agent fallback chain belongs to the Antigravity lane.
        # A GPT sub-agent section must not route failures through it (that would
        # land a Google result in outputs/gpt.md); GPT falls back to agent.
        offenders: list[str] = []
        if weave_commands_dir.is_dir():
            for cmd_file in sorted(weave_commands_dir.glob("*/SKILL.md")):
                heading = ""
                lines = cmd_file.read_text(encoding="utf-8").splitlines()
                for num, line in enumerate(lines, 1):
                    if line.startswith("### "):
                        heading = line
                    elif "GPT" in heading and "agy → gemini → agent" in line:
                        offenders.append(f"{cmd_file.relative_to(REPO_ROOT)}:{num}")
        _assert(
            not offenders,
            f"GPT sections must not use the agy fallback chain: {', '.join(offenders)}",
        )

    tests.append(("agy flag order (-p last)", _check_flag_order))
    tests.append(("agy stdin guard (</dev/null)", _check_stdin_guard))
    tests.append(("agy exit-status preserved", _check_exit_status))
    tests.append(("GPT lane fallback (not agy chain)", _check_gpt_lane_fallback))
    return tests


# ---------------------------------------------------------------------------
# Test case builders
# ---------------------------------------------------------------------------


def _test_validate(sandbox: Path) -> list[TestCase]:
    """Build validate test cases."""
    tests: list[TestCase] = []

    def _validate_marketplace() -> None:
        r = _run_claude(["plugin", "validate", str(REPO_ROOT)], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        _assert("error" not in r.stdout.lower(), f"Unexpected errors: {r.stdout}")

    tests.append(("validate marketplace", _validate_marketplace))

    for plugin in PLUGINS:
        plugin_path = str(REPO_ROOT / "plugins" / plugin)

        def _validate_plugin(p: str = plugin_path, name: str = plugin) -> None:
            r = _run_claude(["plugin", "validate", p], sandbox)
            _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
            _assert("error" not in r.stdout.lower(), f"Unexpected errors in {name}: {r.stdout}")

        tests.append((f"validate plugin: {plugin}", _validate_plugin))

    return tests


def _test_marketplace_add(sandbox: Path, source: str) -> list[TestCase]:
    """Build marketplace add/list test cases."""
    tests: list[TestCase] = []

    def _marketplace_add() -> None:
        r = _run_claude(["plugin", "marketplace", "add", source], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")

    tests.append(("marketplace add", _marketplace_add))

    def _marketplace_list() -> None:
        r = _run_claude(["plugin", "marketplace", "list"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        _assert(
            MARKETPLACE_NAME in r.stdout,
            f"'{MARKETPLACE_NAME}' not in marketplace list: {r.stdout}",
        )

    tests.append(("marketplace list", _marketplace_list))

    return tests


def _test_install(sandbox: Path) -> list[TestCase]:
    """Build plugin install + list test cases."""
    tests: list[TestCase] = []

    for plugin in PLUGINS:
        ref = f"{plugin}@{MARKETPLACE_NAME}"

        def _install(r_ref: str = ref, name: str = plugin) -> None:
            r = _run_claude(["plugin", "install", r_ref], sandbox)
            _assert(r.returncode == 0, f"install {name}: exit {r.returncode}: {r.stdout}{r.stderr}")

        tests.append((f"install: {plugin}", _install))

    def _plugin_list_all() -> None:
        r = _run_claude(["plugin", "list"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        for plugin in PLUGINS:
            _assert(plugin in r.stdout, f"'{plugin}' not in plugin list: {r.stdout}")

    tests.append((f"plugin list ({len(PLUGINS)} installed)", _plugin_list_all))

    return tests


def _test_disable_enable(sandbox: Path) -> list[TestCase]:
    """Build disable/enable cycle test cases for the first plugin."""
    tests: list[TestCase] = []
    target = PLUGINS[0]
    target_ref = f"{target}@{MARKETPLACE_NAME}"

    def _disable() -> None:
        r = _run_claude(["plugin", "disable", target_ref], sandbox)
        _assert(r.returncode == 0, f"disable: exit {r.returncode}: {r.stdout}{r.stderr}")
        r2 = _run_claude(["plugin", "list"], sandbox)
        _assert(r2.returncode == 0, f"list after disable: exit {r2.returncode}")
        _assert("disabled" in r2.stdout.lower(), f"Expected 'disabled' in list: {r2.stdout}")

    tests.append((f"disable: {target}", _disable))

    def _enable() -> None:
        r = _run_claude(["plugin", "enable", target_ref], sandbox)
        _assert(r.returncode == 0, f"enable: exit {r.returncode}: {r.stdout}{r.stderr}")
        r2 = _run_claude(["plugin", "list"], sandbox)
        _assert(r2.returncode == 0, f"list after enable: exit {r2.returncode}")
        _assert("enabled" in r2.stdout.lower(), f"Expected 'enabled' in list: {r2.stdout}")

    tests.append((f"enable: {target}", _enable))

    return tests


def _test_uninstall(sandbox: Path) -> list[TestCase]:
    """Build plugin uninstall + empty list test cases."""
    tests: list[TestCase] = []

    for plugin in PLUGINS:
        ref = f"{plugin}@{MARKETPLACE_NAME}"

        def _uninstall(r_ref: str = ref, name: str = plugin) -> None:
            r = _run_claude(["plugin", "uninstall", r_ref], sandbox)
            _assert(
                r.returncode == 0,
                f"uninstall {name}: exit {r.returncode}: {r.stdout}{r.stderr}",
            )

        tests.append((f"uninstall: {plugin}", _uninstall))

    def _plugin_list_empty() -> None:
        r = _run_claude(["plugin", "list"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        for plugin in PLUGINS:
            _assert(
                plugin not in r.stdout,
                f"'{plugin}' still in plugin list after uninstall: {r.stdout}",
            )

    tests.append(("plugin list (0 installed)", _plugin_list_empty))

    return tests


def _test_marketplace_remove(sandbox: Path) -> list[TestCase]:
    """Build marketplace remove + empty list test cases."""
    tests: list[TestCase] = []

    def _marketplace_remove() -> None:
        r = _run_claude(["plugin", "marketplace", "remove", MARKETPLACE_NAME], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")

    tests.append(("marketplace remove", _marketplace_remove))

    def _marketplace_list_empty() -> None:
        r = _run_claude(["plugin", "marketplace", "list"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        _assert(
            MARKETPLACE_NAME not in r.stdout,
            f"'{MARKETPLACE_NAME}' still in marketplace list: {r.stdout}",
        )

    tests.append(("marketplace list (empty)", _marketplace_list_empty))

    return tests


# ---------------------------------------------------------------------------
# Codex plugin lifecycle
# ---------------------------------------------------------------------------


def _run_codex(
    args: list[str],
    sandbox: Path,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a ``codex`` CLI command against a throwaway Codex home.

    ``CODEX_HOME`` holds Codex's config, marketplace snapshots, and plugin
    cache. ``HOME`` is redirected too, so a skill already installed under the
    developer's own ``~/.agents/skills`` cannot satisfy an assertion that a
    plugin was supposed to. Codex refuses a ``CODEX_HOME`` that does not exist
    rather than creating it, so both directories are made up front.
    """
    home = sandbox / "home"
    codex_home = sandbox / "codex"
    for directory in (home, codex_home):
        directory.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "HOME": str(home), "CODEX_HOME": str(codex_home)}
    return subprocess.run(  # noqa: S603
        ["codex", *args],  # noqa: S607
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd is not None else None,
        timeout=300,
        check=False,
    )


def _codex_skill_ids() -> dict[str, list[str]]:
    """Map each plugin to the skill IDs Codex should expose for it.

    Keyed on the frontmatter ``name`` rather than the directory, because that
    is what Codex prefixes with the plugin name to build the invocable ID.
    """
    ids: dict[str, list[str]] = {}
    for plugin in PLUGINS:
        skills = REPO_ROOT / "plugins" / plugin / "skills"
        if not skills.is_dir():
            continue
        names = [
            t.cast("str", _parse_frontmatter(md).get("name", md.parent.name))
            for md in sorted(skills.glob("*/SKILL.md"))
        ]
        if names:
            ids[plugin] = sorted(f"{plugin}:{name}" for name in names)
    return ids


def _declared_codex_version(plugin: str) -> str:
    """Return the version a plugin's Codex manifest declares."""
    manifest = REPO_ROOT / "plugins" / plugin / ".codex-plugin" / "plugin.json"
    declared: dict[str, t.Any] = json.loads(  # pyright: ignore[reportAny]
        manifest.read_text(encoding="utf-8"),
    )
    return t.cast("str", declared["version"])


def _codex_prompt_skill_ids(sandbox: Path, project: Path) -> set[str]:
    """Return every skill ID Codex puts in front of the model, in *project*."""
    result = _run_codex(["debug", "prompt-input"], sandbox, cwd=project)
    _assert(
        result.returncode == 0,
        f"debug prompt-input: exit {result.returncode}: {result.stderr[-400:]}",
    )
    messages = t.cast("list[dict[str, t.Any]]", json.loads(result.stdout))
    blocks = [
        t.cast("str", block.get("text", ""))
        for message in messages
        for block in t.cast("list[dict[str, t.Any]]", message.get("content", []))
    ]
    text = "\n".join(blocks)
    start = text.find("<skills_instructions>")
    _assert(start >= 0, "prompt carries no skills block")
    end = text.find("</skills_instructions>", start)
    # Falling back to the rest of the prompt would let any "- foo:bar:" bullet
    # downstream count as a delivered skill, turning a malformed prompt into a
    # pass.
    _assert(end > start, "skills block is not closed")
    catalog = text[start:end]
    return {m.group("id") for m in CODEX_SKILL_ENTRY_RE.finditer(catalog)}


def _test_static_codex_manifests() -> list[TestCase]:
    """Verify every plugin declares a Codex manifest over a populated skills dir."""
    tests: list[TestCase] = []
    marketplace = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"

    def _check_marketplace() -> None:
        _assert(marketplace.is_file(), "Codex marketplace.json not found")
        data: dict[str, t.Any] = json.loads(  # pyright: ignore[reportAny]
            marketplace.read_text(encoding="utf-8"),
        )
        entries = t.cast("list[dict[str, t.Any]]", data.get("plugins", []))
        names = {t.cast("str", e["name"]) for e in entries}
        for plugin in PLUGINS:
            _assert(plugin in names, f"'{plugin}' missing from Codex marketplace.json")
        for entry in entries:
            name = t.cast("str", entry.get("name", "<unnamed>"))
            source = t.cast("dict[str, t.Any]", entry.get("source", {}))
            path = t.cast("str", source.get("path", ""))
            _assert(path.startswith("./"), f"Codex entry '{name}': path must start with './'")
            _assert((REPO_ROOT / path).is_dir(), f"Codex entry '{name}': '{path}' does not exist")
            policy = t.cast("dict[str, t.Any]", entry.get("policy", {}))
            for f in ("installation", "authentication"):
                _assert(f in policy, f"Codex entry '{name}': policy missing '{f}'")

    tests.append(("Codex marketplace.json validation", _check_marketplace))

    for plugin in PLUGINS:

        def _check_manifest(name: str = plugin) -> None:
            d = REPO_ROOT / "plugins" / name
            manifest = d / ".codex-plugin" / "plugin.json"
            _assert(manifest.is_file(), f"{name}: missing .codex-plugin/plugin.json")
            data: dict[str, t.Any] = json.loads(  # pyright: ignore[reportAny]
                manifest.read_text(encoding="utf-8"),
            )
            for field in ("name", "version", "description", "skills"):
                _assert(field in data, f"{name}: Codex manifest missing '{field}'")
            skills = t.cast("str", data["skills"])
            target = d / skills.removeprefix("./")
            _assert(target.is_dir(), f"{name}: skills path '{skills}' does not exist")
            _assert(any(target.glob("*/SKILL.md")), f"{name}: '{skills}' holds no SKILL.md")

        tests.append((f"codex manifest: {plugin}", _check_manifest))

    return tests


def _test_codex_lifecycle(sandbox: Path) -> list[TestCase]:
    """Build the Codex marketplace add -> install -> prompt -> remove cases."""
    tests: list[TestCase] = []
    project = sandbox / "project"
    expected = _codex_skill_ids()

    def _marketplace_add() -> None:
        r = _run_codex(["plugin", "marketplace", "add", str(REPO_ROOT), "--json"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        payload = t.cast("dict[str, t.Any]", json.loads(r.stdout))
        added = t.cast("str | None", payload.get("marketplaceName"))
        _assert(added == MARKETPLACE_NAME, f"marketplace name is {added!r}")

    tests.append(("codex marketplace add", _marketplace_add))

    def _list_available() -> None:
        r = _run_codex(["plugin", "list", "--available", "--json"], sandbox)
        _assert(r.returncode == 0, f"exit {r.returncode}: {r.stdout}{r.stderr}")
        payload = t.cast("dict[str, t.Any]", json.loads(r.stdout))
        available = t.cast("list[dict[str, t.Any]]", payload.get("available", []))
        listed = {t.cast("str", p["name"]): p for p in available}
        for plugin in PLUGINS:
            _assert(plugin in listed, f"'{plugin}' not offered by Codex")
            # Codex falls back to .claude-plugin/plugin.json when the Codex
            # manifest is absent, so a non-null version proves nothing; a
            # mismatch is what catches the two manifests disagreeing.
            want = _declared_codex_version(plugin)
            got = t.cast("str | None", listed[plugin].get("version"))
            _assert(got == want, f"'{plugin}': Codex reports {got!r}, manifest declares {want!r}")

    tests.append((f"codex list --available ({len(PLUGINS)} offered)", _list_available))

    for plugin in PLUGINS:

        def _install(name: str = plugin) -> None:
            r = _run_codex(["plugin", "add", f"{name}@{MARKETPLACE_NAME}", "--json"], sandbox)
            _assert(r.returncode == 0, f"install {name}: exit {r.returncode}: {r.stderr[-300:]}")

        tests.append((f"codex install: {plugin}", _install))

    def _skills_reach_model() -> None:
        project.mkdir(parents=True, exist_ok=True)
        seen = _codex_prompt_skill_ids(sandbox, project)
        missing = sorted(i for ids in expected.values() for i in ids if i not in seen)
        _assert(not missing, f"{len(missing)} skill(s) never reached the model: {missing[:8]}")

    total = sum(len(v) for v in expected.values())
    tests.append((f"codex skills reach the model ({total} IDs)", _skills_reach_model))

    def _teardown() -> None:
        for plugin in PLUGINS:
            r = _run_codex(["plugin", "remove", f"{plugin}@{MARKETPLACE_NAME}"], sandbox)
            _assert(r.returncode == 0, f"remove {plugin}: exit {r.returncode}: {r.stderr[-200:]}")
        r = _run_codex(["plugin", "marketplace", "remove", MARKETPLACE_NAME], sandbox)
        _assert(r.returncode == 0, f"marketplace remove: exit {r.returncode}: {r.stderr[-200:]}")
        r2 = _run_codex(["plugin", "marketplace", "list"], sandbox)
        _assert(MARKETPLACE_NAME not in r2.stdout, f"still configured: {r2.stdout}")

    tests.append((f"codex remove ({len(PLUGINS)} plugins) and marketplace", _teardown))
    return tests


def _run_codex_suite() -> tuple[int, int]:
    """Run the Codex lifecycle in a sandbox that outlives no single test."""
    console.print("\n[bold]Host: codex[/bold]")
    sandbox = Path(tempfile.mkdtemp(prefix="codex-e2e-"))
    try:
        tests = _test_codex_lifecycle(sandbox)
        return sum(_run_test(name, fn) for name, fn in tests), len(tests)
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------


def _run_suite(source_type: t.Literal["local", "github"]) -> tuple[int, int]:
    """Run the full test suite for one source type.

    Returns
    -------
    tuple[int, int]
        (passed, total) counts.
    """
    if source_type == "local":
        source = str(REPO_ROOT)
        label = f"local ({PrivatePath(REPO_ROOT)})"
    else:
        source = GITHUB_SOURCE
        label = f"github ({GITHUB_SOURCE})"

    console.print(f"\n[bold]Source: {label}[/bold]")

    sandbox = Path(tempfile.mkdtemp(prefix="claude-e2e-"))
    try:
        tests: list[TestCase] = []
        tests.extend(_test_validate(sandbox))
        tests.extend(_test_marketplace_add(sandbox, source))
        tests.extend(_test_install(sandbox))
        tests.extend(_test_disable_enable(sandbox))
        tests.extend(_test_uninstall(sandbox))
        tests.extend(_test_marketplace_remove(sandbox))

        passed = sum(_run_test(name, fn) for name, fn in tests)
        total = len(tests)
        return passed, total
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


@app.command()
def main(
    source: t.Annotated[Source, typer.Option(help="Source type: local, github, or both")] = "local",
    host: t.Annotated[
        Host, typer.Option(help="Host CLI to exercise: claude, codex, or both")
    ] = "both",
) -> None:
    """Run E2E plugin lifecycle tests against the Claude and Codex CLIs."""
    console.print("[bold]E2E Plugin Lifecycle Tests[/bold]")
    console.print("=" * 40)

    # Run static validation tests first (no CLI needed)
    console.print("\n[bold]Static Validation[/bold]")
    static_tests: list[TestCase] = []
    static_tests.extend(_test_static_frontmatter())
    static_tests.extend(_test_static_plugin_structure())
    static_tests.extend(_test_static_agent_skill_frontmatter())
    static_tests.extend(_test_static_marketplace_json())
    static_tests.extend(_test_static_codex_manifests())
    static_tests.extend(_test_static_weave_worker_backends())
    static_tests.extend(_test_static_weave_timeouts())
    static_tests.extend(_test_static_weave_stderr_redirects())
    static_tests.extend(_test_static_agy_invocations())
    static_passed = sum(_run_test(name, fn) for name, fn in static_tests)
    static_total = len(static_tests)

    total_passed = static_passed
    total_tests = static_total

    if host in {"claude", "both"}:
        if shutil.which("claude") is None:
            console.print(
                "\n[yellow]Warning:[/yellow] 'claude' CLI not found in PATH -- skipping CLI tests",
            )
        else:
            sources: list[t.Literal["local", "github"]]
            if source == "both":
                sources = ["local", "github"]
            else:
                sources = [source]

            for src in sources:
                passed, total = _run_suite(src)
                total_passed += passed
                total_tests += total

    if host in {"codex", "both"}:
        if shutil.which("codex") is None:
            console.print(
                "\n[yellow]Warning:[/yellow] 'codex' CLI not found in PATH -- skipping Codex tests",
            )
        else:
            passed, total = _run_codex_suite()
            total_passed += passed
            total_tests += total

    console.print()
    if total_passed == total_tests:
        console.print(f"[green bold]{total_passed}/{total_tests} tests passed[/green bold]")
    else:
        failed = total_tests - total_passed
        console.print(f"[red bold]{failed}/{total_tests} tests failed[/red bold]")
        raise SystemExit(1)


if __name__ == "__main__":
    app()
