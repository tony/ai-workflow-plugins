# Version matrix

The available toolbox depends on the installed pytest and plugins. `00-scan`
probes once and writes the resolved result to `capabilities.json`; later phases
use only what exists.

## Detection procedure

1. Read the pytest version:

   ```bash
   python -c "import pytest; print(pytest.__version__)"
   ```

2. Probe flags that may be absent (cheaper and more reliable than version math
   for CLI options):

   ```bash
   pytest --help 2>/dev/null | rg -- '--durations-min|--import-mode|--dist|--sw-reset'
   ```

3. Probe plugin presence and version:

   ```bash
   python -c "import importlib.metadata as m; [print(d, m.version(d)) for d in ('pytest-xdist','pytest-randomly','pytest-timeout') if (lambda: True)()]" 2>/dev/null || true
   ```

4. For API features, import-probe:

   ```bash
   python -c "import pytest; print(hasattr(pytest, 'StashKey'))"
   ```

5. Record each feature as `{available, version, flag, fallback}` in
   `capabilities.json`. When a feature is unavailable, the phase silently uses the
   listed fallback rather than failing.

## Feature gates

| Feature | Min version | Detect | Fallback when absent |
|---------|-------------|--------|----------------------|
| `--durations=N` profiler | pytest 2.2 | always present in modern pytest | none needed |
| `perf_counter`-based `CallInfo.duration` | pytest 6.0 | `pytest --version` ≥ 6.0 | pre-6.0 duration is `time.time()` delta (coarser) — widen the noise band |
| `--durations-min` | pytest 6.1 | `pytest --help \| rg -- '--durations-min'` | threshold hard-coded at `0.005s`; post-filter rows yourself |
| Explicit `--durations-min` respected under `-vv` | pytest 8.4 | `pytest --version` ≥ 8.4 | drop `-vv`, rely on explicit `--durations-min` |
| In-core subtests (extra per-subtest `call` rows) | pytest 9.0 | `pytest --version` ≥ 9.0 OR `pytest-subtests` installed | one `call` row per item; de-dup nodeids when bucketing |
| `junit_duration_report` ini (`call` vs total) | pytest 4.1 | `rg junit_duration_report` in `--help`/docs | older JUnit reports total (setup+call+teardown) only |
| `--import-mode=importlib` | pytest 6.0 | `pytest --help \| rg -- '--import-mode'` | default `prepend` mode (mutates `sys.path`; needs unique test filenames) |
| `Stash` / `StashKey` (typed per-run store) | pytest 7.0 | `python -c 'import pytest; print(pytest.StashKey)'` | `config.cache` (JSON) cross-run; attach attrs to config/session within-run |
| `--sw-reset` (stepwise reset) | pytest 8.4 | `pytest --help \| rg -- '--sw-reset'` | `--sw` / `--sw-skip` (stepwise itself dates to 5.x) |
| Callable (dynamic) fixture `scope` | pytest 5.2 | `@pytest.fixture(scope=<callable>)` | hardcode the scope, or gate via a CLI flag read inside the fixture |
| Mark-on-fixture is a hard collection error | pytest 9.0 | `pytest --version`; `pytest --collect-only -q` | pre-9 it is a warning that still collects; the fix (skip in body) is identical |
| `pytest.register_fixture` (imperative) | pytest 9.1 | calls to `pytest.register_fixture(...)` | `@pytest.fixture` decorator (declarative) |
| `tmp_path` / `tmp_path_factory` | pytest 3.9 | `rg 'tmp_path\|tmp_path_factory'` | legacy `tmpdir`/`tmpdir_factory` (`py.path.local`) on very old pytest |
| `--strict-markers` | pytest 4.5 | `rg 'strict-markers\|--strict'` addopts | older pytest used `--strict`; or `PytestUnknownMarkWarning` |
| `pytest11` entry point (ship fixtures as a plugin) | all modern | `[project.entry-points.pytest11]` in pyproject | `pytest_plugins = ('pkg.module',)` explicit import |
| `pytest-xdist` parallel (`-n auto`, `workerinput`) | pytest-xdist 2.1 | `importlib.metadata.version('pytest-xdist')` | run serially; `worker_id` returns `master` when `workerinput` absent |
| `--dist=loadgroup` + `xdist_group` mark | pytest-xdist 2.5 | `pytest --help \| rg -- '--dist'` | `loadscope` (group by module/class) or `loadfile` |
| `--dist=worksteal` + `-n logical` | pytest-xdist 3.0 | `pytest -n2 --dist=worksteal --co` | `--dist=load` (default); `-n auto` (physical cores) |
| `pytest-randomly` (order-independence detector) | plugin install | `importlib.metadata.version('pytest-randomly')` | run subsets/single tests in isolation and reversed order manually |
| `pytest-deadfixtures` (`--dead-fixtures`/`--dup-fixtures`) | run via `uvx` | `uvx --with pytest-deadfixtures --from pytest pytest --dead-fixtures` | built-in `--fixtures` vs `--fixtures-per-test` diff (zero-dependency) |
| `pytest-timeout` (`--timeout-method=thread`) | pytest-timeout 2.0 | `rg 'pytest-timeout\|^timeout =\|--timeout'` pyproject | no global timeout; rely on the CI job timeout |
| Strict type checker covers `tests/` | tooling (not pytest) | `[tool.mypy] strict=true` incl. tests, or pyright config incl. tests | phrase the gate as "the project strict checker includes the test directory" |

## Notes

- Prefer **probing a flag** (`--help | rg`) over comparing version strings: it is
  robust to backports, vendored builds, and plugins that add or remove options.
- A `setup` durations row is the **whole setup chain** for an item in every pytest
  version; per-fixture attribution (H03) always needs the opt-in timing plugin,
  regardless of version.
- When duration precision is coarse (pre-6.0), the noise band widens
  automatically because `01-benchmark` measures it per project — there is no fixed
  jitter figure to quote.
