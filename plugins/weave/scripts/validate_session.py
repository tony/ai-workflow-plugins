#!/usr/bin/env python3
"""Validate weave session artifacts. v1 scope: brainstorm-and-refine.

Stdlib-only Python ``>=3.12`` validator for the artifact tree produced by
``/weave:brainstorm-and-refine``. Checks ``session.json`` shape,
``events.jsonl`` ordering, required directory layout, repo-fingerprint
integrity, and the ``latest`` symlink. The validator is **shape-only** by
design: it does not evaluate output quality, judging quality, or reasoning
correctness. See ``plugins/weave/docs/repo-guard-protocol.md`` for the
fingerprint format the ``--check-repo`` flag references.

Notes
-----
For users without Python ``>=3.12`` natively (e.g. Ubuntu 22.04, older macOS),
the alternate shebang below provisions an ephemeral interpreter via ``uv``::

    #!/usr/bin/env -S uv run --script
    # /// script
    # requires-python = ">=3.12"
    # dependencies = []
    # ///

The default exit policy is best-effort (exit ``0`` even on errors) so
automation paths (post-phase invocation, ``Stop`` hook) never block the
host. Pass ``--strict`` for human-driven manual invocation where exit ``2``
on errors is wanted.

Examples
--------
Validate a specific session::

    >>> import subprocess
    >>> result = subprocess.run(
    ...     ["python3", str(THIS_SCRIPT), "--help"],
    ...     capture_output=True,
    ...     text=True,
    ...     check=False,
    ... )
    >>> result.returncode
    0
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

THIS_SCRIPT = Path(__file__).resolve()
"""Absolute path to this validator script (used in doctests)."""

REQUIRED_SESSION_FIELDS: frozenset[str] = frozenset(
    {
        "schema_version",
        "session_id",
        "command",
        "status",
        "phase",
        "branch",
        "ref",
        "models",
        "judge_mode",
        "variants_per_model",
        "pass_count",
        "completed_passes",
        "prompt_summary",
        "created_at",
        "updated_at",
    },
)
"""Required keys in ``session.json`` for the brainstorm-and-refine command."""

STATUS_VALUES: frozenset[str] = frozenset({"in_progress", "completed", "failed"})
"""Valid values for ``session.json[status]``."""

PHASE_VALUES: frozenset[str] = frozenset(
    {"brainstorm", "refine", "complete", "brainstorm_only"},
)
"""Valid values for ``session.json[phase]``."""

KNOWN_EVENTS: frozenset[str] = frozenset(
    {
        "session_start",
        "brainstorm_to_refine",
        "pass_complete",
        "session_complete",
        "repo_guard_violation",
        "repo_guard_final",
        "validation_error",
    },
)
"""Recognized event names. Unknown names warn (or error with ``--strict-events``)."""

EXIT_OK = 0
"""Exit code for success or best-effort fallback."""

EXIT_INTERNAL = 1
"""Exit code for internal validator failure (e.g. no session selected)."""

EXIT_VALIDATION = 2
"""Exit code for validation errors when ``--strict`` is set."""

JsonDict = dict[str, object]
"""Type alias for a JSON object after isinstance narrowing."""


def _load_json_object(path: Path) -> JsonDict | None:
    """Load a JSON object from ``path`` and return it typed as ``JsonDict``.

    Parameters
    ----------
    path
        File to read.

    Returns
    -------
    JsonDict | None
        Parsed object, or ``None`` if the file is missing, invalid JSON,
        or not a JSON object.
    """
    try:
        raw = cast("object", json.loads(path.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(raw, dict):
        return None
    return cast("JsonDict", raw)


@dataclass
class Finding:
    """A single validator finding.

    Parameters
    ----------
    level
        Severity level: ``"error"`` or ``"warning"``.
    message
        Human-readable message for the user. Routed to stderr.
    """

    level: str
    message: str


@dataclass
class Validator:
    """Validate a weave session directory.

    Parameters
    ----------
    session_dir
        Absolute path to the session directory under ``$AI_AIP_ROOT``.
    check_repo
        When ``True``, compare current ``git`` HEAD/status against
        ``repo-fingerprint.txt``. Failures emit warnings (not errors) so
        worktrees and missing-git environments do not break validation.
    strict_events
        When ``True``, treat unknown event types as errors instead of
        warnings.
    """

    session_dir: Path
    check_repo: bool = False
    strict_events: bool = False
    findings: list[Finding] = field(default_factory=list)
    session: JsonDict = field(default_factory=dict)
    events: list[JsonDict] = field(default_factory=list)

    def err(self, message: str) -> None:
        """Record an error-level finding."""
        self.findings.append(Finding("error", message))

    def warn(self, message: str) -> None:
        """Record a warning-level finding."""
        self.findings.append(Finding("warning", message))

    def validate(self) -> list[Finding]:
        """Run all validation passes and return findings.

        Returns
        -------
        list[Finding]
            All findings recorded during validation.
        """
        if not self.session_dir.is_dir():
            self.err(f"not a directory: {self.session_dir}")
            return self.findings
        self._validate_session_json()
        self._validate_events_jsonl()
        self._validate_paths()
        self._validate_fingerprint()
        self._validate_latest_symlink()
        return self.findings

    def _validate_session_json(self) -> None:
        """Validate ``session.json`` shape and required fields."""
        path = self.session_dir / "session.json"
        if not path.is_file():
            self.err(f"missing file: {path}")
            return
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            self.err(f"cannot read {path}: {exc}")
            return
        try:
            raw = cast("object", json.loads(text))
        except json.JSONDecodeError as exc:
            self.err(f"invalid json: {path}: {exc}")
            return
        if not isinstance(raw, dict):
            self.err(f"expected object: {path}")
            return
        data: JsonDict = cast("JsonDict", raw)
        self.session = data
        for key in sorted(REQUIRED_SESSION_FIELDS - data.keys()):
            self.err(f"session.json missing required key: {key}")
        if data.get("command") != "brainstorm-and-refine":
            self.err("v1 validator only supports brainstorm-and-refine")
        if data.get("session_id") != self.session_dir.name:
            self.err("session_id does not match directory name")
        status = data.get("status")
        if status not in STATUS_VALUES:
            self.err(f"invalid session status: {status!r}")
        phase = data.get("phase")
        if phase not in PHASE_VALUES:
            self.err(f"invalid session phase: {phase!r}")
        completed = data.get("completed_passes")
        total = data.get("pass_count")
        if isinstance(completed, int) and isinstance(total, int) and completed > total:
            self.err(f"completed_passes ({completed}) > pass_count ({total})")
        # Additive: extra keys are silently allowed.

    def _validate_events_jsonl(self) -> None:
        """Validate ``events.jsonl`` line-by-line and across the stream."""
        path = self.session_dir / "events.jsonl"
        if not path.is_file():
            self.err(f"missing file: {path}")
            return
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            self.err(f"cannot read {path}: {exc}")
            return
        for n, raw in enumerate(lines, start=1):
            self._validate_event_line(path, n, raw)
        if self.events and self.events[0].get("event") != "session_start":
            self.err("first event must be session_start")
        self._validate_pass_event_exactness()

    def _validate_event_line(self, path: Path, line_no: int, raw: str) -> None:
        """Validate a single line of ``events.jsonl``."""
        if not raw.strip():
            return
        try:
            decoded = cast("object", json.loads(raw))
        except json.JSONDecodeError as exc:
            self.err(f"invalid jsonl at {path}:{line_no}: {exc}")
            return
        if not isinstance(decoded, dict):
            self.err(f"expected object at {path}:{line_no}")
            return
        event: JsonDict = cast("JsonDict", decoded)
        if "event" not in event or "timestamp" not in event:
            self.err(f"missing event/timestamp at {path}:{line_no}")
            return
        event_name = event.get("event")
        if isinstance(event_name, str) and event_name not in KNOWN_EVENTS:
            msg = f"unknown event type at {path}:{line_no}: {event_name}"
            if self.strict_events:
                self.err(msg)
            else:
                self.warn(msg)
        self.events.append(event)
        # Additive: extra keys per event are allowed.

    def _validate_pass_event_exactness(self) -> None:
        """Verify ``pass_complete`` events match ``1..completed_passes``."""
        completed = self.session.get("completed_passes", 0)
        if not isinstance(completed, int):
            return
        seen: set[int] = set()
        for ev in self.events:
            if ev.get("event") != "pass_complete":
                continue
            pass_num = ev.get("pass")
            if isinstance(pass_num, int) and 1 <= pass_num <= completed:
                if pass_num in seen:
                    self.err(f"duplicate pass_complete event for pass {pass_num}")
                seen.add(pass_num)
            else:
                msg = "pass_complete event with out-of-range pass={!r} (expected 1..{})"
                self.err(msg.format(pass_num, completed))
        for n in range(1, completed + 1):
            if n not in seen:
                self.err(f"missing pass_complete event for pass {n}")

    def _validate_paths(self) -> None:
        """Validate required directory tree and pass artifacts."""
        # metadata.md and context-packet.md per brainstorm-and-refine.md Steps 8-9.
        # repo-fingerprint.txt per repo-guard-protocol.md Layer 2.
        required = (
            "metadata.md",
            "context-packet.md",
            "repo-fingerprint.txt",
            "brainstorm/prompts",
            "brainstorm/outputs",
            "brainstorm/stderr",
            "refine",
        )
        for rel in required:
            target = self.session_dir / rel
            if not target.exists():
                self.err(f"missing required path: {target}")
        # Phase-aware artifacts: each completed pass has judge.md and woven.md.
        # In-progress pass directory (completed_passes + 1) is intentionally not validated.
        completed = self.session.get("completed_passes", 0)
        if isinstance(completed, int):
            for n in range(1, completed + 1):
                pass_dir = self.session_dir / "refine" / f"pass-{n:04d}"
                for artifact in ("judge.md", "woven.md"):
                    if not (pass_dir / artifact).is_file():
                        self.err(f"missing pass artifact: {pass_dir / artifact}")
        # refine/final.md required ONLY on the full-completion path.
        # The brainstorm_only early-exit (transition gate "None") completes
        # the session without writing final.md; that is valid.
        if self.session.get("status") == "completed" and self.session.get("phase") == "complete":
            final_md = self.session_dir / "refine" / "final.md"
            if not final_md.is_file():
                self.err(f"completed session missing: {final_md}")

    def _validate_fingerprint(self) -> None:
        """Validate ``repo-fingerprint.txt`` shape and (with --check-repo) freshness."""
        fp_path = self.session_dir / "repo-fingerprint.txt"
        if not fp_path.is_file():
            return  # already reported by _validate_paths
        try:
            text = fp_path.read_text(encoding="utf-8")
        except OSError as exc:
            self.err(f"cannot read {fp_path}: {exc}")
            return
        if "head:" not in text or "status:" not in text:
            self.err("repo-fingerprint.txt must contain head: and status: sections")
        if not self.check_repo:
            return
        self._check_repo_freshness(text)

    def _check_repo_freshness(self, fingerprint_text: str) -> None:
        """Compare current git HEAD/status to ``repo-fingerprint.txt``."""
        # --check-repo only works against sessions under $AIP_ROOT.
        # parents[2] is $AIP_ROOT/repos/<slug>--<id>; repo.json lives there.
        repo_json_path = self.session_dir.parents[2] / "repo.json"
        repo_data = _load_json_object(repo_json_path)
        if repo_data is None:
            self.warn(f"--check-repo cannot resolve repo.json at {repo_json_path}")
            return
        toplevel_value = repo_data.get("toplevel")
        if not isinstance(toplevel_value, str):
            self.warn("--check-repo: repo.json missing string 'toplevel' field")
            return
        toplevel = Path(toplevel_value)
        try:
            head_proc = subprocess.run(  # noqa: S603
                ["git", "-C", str(toplevel), "rev-parse", "HEAD"],  # noqa: S607
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            status_proc = subprocess.run(  # noqa: S603
                ["git", "-C", str(toplevel), "status", "--porcelain"],  # noqa: S607
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            self.warn(f"git probe failed (worktree?): {exc}")
            return
        head = head_proc.stdout.strip()
        status = status_proc.stdout.rstrip("\n")
        if f"head: {head}" not in fingerprint_text:
            self.err("current repository HEAD differs from repo-fingerprint.txt")
        _, _, tail = fingerprint_text.partition("status:")
        # tail.strip() (not strip("\n")) absorbs trailing spaces and \r on Windows.
        expected = "" if tail.strip() == "(clean)" else tail.strip()
        if status.strip() != expected:
            self.err("current repository status differs from repo-fingerprint.txt")

    def _validate_latest_symlink(self) -> None:
        """Validate the ``latest`` symlink for completed sessions."""
        # latest is only updated on session completion. In-progress sessions
        # legitimately have no latest pointer.
        if self.session.get("status") != "completed":
            return
        latest = self.session_dir.parent / "latest"
        if not latest.exists():
            self.warn("completed session has no latest symlink")
            return
        if latest.resolve() != self.session_dir:
            self.warn("latest symlink does not point to this completed session")


def aip_root() -> Path:
    """Resolve the AI-AIP storage root.

    Returns
    -------
    Path
        Absolute path to the root storage directory, derived from
        ``$AI_AIP_ROOT``, ``$XDG_STATE_HOME``, or the platform default.
    """
    if value := os.environ.get("AI_AIP_ROOT"):
        return Path(value)
    if value := os.environ.get("XDG_STATE_HOME"):
        return Path(value) / "ai-aip"
    return Path.home() / ".local" / "state" / "ai-aip"


def resolve_latest_in_progress(command: str) -> Path | None:
    """Find the latest in-progress session for ``command`` in the current repo.

    Hook-safe: returns ``None`` when ``git rev-parse --show-toplevel`` fails
    (no git, no repo, or other process error). Matches via
    ``repo.json.toplevel`` to avoid cross-matching unrelated repos that
    share a basename.

    Parameters
    ----------
    command
        Command family to search (e.g. ``"brainstorm-and-refine"``).

    Returns
    -------
    Path | None
        Path to the latest in-progress session directory, or ``None`` if
        none found.
    """
    try:
        toplevel_proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    toplevel_str = toplevel_proc.stdout.strip()
    if not toplevel_str:
        return None
    repo_toplevel = Path(toplevel_str)
    for repo_dir in aip_root().glob("repos/*"):
        repo_data = _load_json_object(repo_dir / "repo.json")
        if repo_data is None:
            continue
        toplevel_value = repo_data.get("toplevel")
        if not isinstance(toplevel_value, str) or Path(toplevel_value) != repo_toplevel:
            continue
        candidates = sorted((repo_dir / "sessions" / command).glob("*"))
        for path in reversed(candidates):
            session_data = _load_json_object(path / "session.json")
            if session_data is None:
                continue
            if session_data.get("status") == "in_progress":
                return path
    return None


@dataclass
class _CliArgs:
    """Parsed CLI arguments with explicit types."""

    session_dir: Path | None
    latest_in_progress: str | None
    check_repo: bool
    strict: bool
    strict_events: bool


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser configured for the validator's CLI surface.
    """
    parser = argparse.ArgumentParser(
        description="Validate weave session artifacts (shape-only, not output quality).",
    )
    _ = parser.add_argument("session_dir", nargs="?", type=Path)
    _ = parser.add_argument(
        "--latest-in-progress",
        metavar="COMMAND",
        help="Find the latest in-progress session for COMMAND",
    )
    _ = parser.add_argument(
        "--check-repo",
        action="store_true",
        help="Compare current repo state against repo-fingerprint.txt",
    )
    _ = parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 on validation errors (default: best-effort, exit 0)",
    )
    _ = parser.add_argument(
        "--strict-events",
        action="store_true",
        help="Treat unknown event types as errors instead of warnings",
    )
    return parser


def _parse_args(argv: list[str] | None = None) -> _CliArgs:
    """Parse argv into a strongly-typed ``_CliArgs`` record."""
    namespace = build_parser().parse_args(argv)
    return _CliArgs(
        session_dir=cast("Path | None", namespace.session_dir),
        latest_in_progress=cast("str | None", namespace.latest_in_progress),
        check_repo=cast("bool", namespace.check_repo),
        strict=cast("bool", namespace.strict),
        strict_events=cast("bool", namespace.strict_events),
    )


def main(argv: list[str] | None = None) -> int:
    """Run the validator from the command line.

    Parameters
    ----------
    argv
        Argument list (used in tests). Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code: ``0`` on success or best-effort fallback, ``2`` on
        validation errors (only when ``--strict``), ``1`` on internal failure.
    """
    args = _parse_args(argv)
    target: Path | None = args.session_dir
    if target is None and args.latest_in_progress is not None:
        target = resolve_latest_in_progress(args.latest_in_progress)
    if target is None:
        if args.latest_in_progress is not None:
            return EXIT_OK  # Hook-safe: no in-progress session => no-op.
        print("error: no session selected", file=sys.stderr)
        return EXIT_INTERNAL
    findings = Validator(
        session_dir=target,
        check_repo=args.check_repo,
        strict_events=args.strict_events,
    ).validate()
    for finding in findings:
        print(f"{finding.level}: {finding.message}", file=sys.stderr)
    errors = sum(1 for f in findings if f.level == "error")
    warnings = sum(1 for f in findings if f.level == "warning")
    print(
        f"validate-session: {errors} error(s), {warnings} warning(s)",
        file=sys.stderr,
    )
    print(
        "note: validates artifact shape only - not output quality.",
        file=sys.stderr,
    )
    return EXIT_VALIDATION if (errors and args.strict) else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
