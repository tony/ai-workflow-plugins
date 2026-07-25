# Heuristic catalog

Detection rules `H01`–`H44`. Each has a **signal** (the smell), a **detect** recipe
(the exact command or inspection), an **action** (the fix), a **risk**/**effort**
estimate, and the **goal(s)** it addresses (1–11 from the project brief).

`00-scan` runs the detectors and emits one hypothesis per firing rule. Risk and
effort here are *priors*; `01-benchmark` replaces the impact estimate with a
measurement and `02-plan` scores the result against the rubric.

Commands assume features exist; gate them through `version-matrix.md` first.
Replace `pytest` with the project's resolved test command.

## A. Profiling and measurement (goals 1, 2, 7)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H01 | Rank slowest **test bodies** | `pytest --durations=25 --durations-min=0.005 -p no:randomly`; keep rows whose 2nd token is `call` | Report top `call` rows; root-cause in-test work (I/O, bootstrap, sleep) confirmed by cheap fixtures in `--setup-show` | low / trivial | 1 |
| H02 | Rank slowest **fixture setup/teardown** | `pytest --durations=0 --durations-min=0.01`; keep rows where token is `setup` or `teardown` | Rank those rows; a lone large `setup` on one nodeid is a higher-scope fixture billed to its first consumer, not that test's fault | low / trivial | 2 |
| H03 | Shared higher-scope fixture cost mis-attributed to one test | `--setup-show` shows an `S`/`P`/`M`/`C`-scope fixture with one large setup row on the first item that triggers it | Attribute the cost to the fixture; confirm per-fixture via the opt-in `pytest11` timing plugin (pytest core has no per-fixture timer) | low / small | 2, 5 |
| H04 | Want the complete unfiltered picture on a small suite | `pytest --durations=0 --durations-min=0` (equivalent to `--durations=0 -vv`) | Capture every setup/call/teardown row incl. `0.00s`; bucket by phase token; persist to `baseline.json` | low / trivial | 1, 2 |
| H05 | Durations vary run-to-run; fast rows unstable | Re-run the same durations command N ≥ 3× and diff top rows; compute median + MAD noise band | Run serially (no `-n`), raise `--durations-min` above the floor; only count a delta that exceeds the band | low / small | 1, 2, 6 |
| H06 | Profiling must be clean and not mutate the repo | Baseline command includes `-p no:cacheprovider` and omits `-n`/xdist | Disable cacheprovider and parallelism while measuring, for reproducible wall-time and one fewer timed hook per phase | low / trivial | 1, 2, 6 |
| H07 | Need machine-readable per-test timing for the store | `pytest --junit-xml=report.xml -o junit_duration_report=call` | Parse `testcase@time` from XML instead of scraping the human table; store structured timings | low / small | 1, 2, 7, 11 |

## B. Fixtures: unused, duplicate, scope, autouse (goals 3, 4, 5)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H08 | Fixture defined but never requested (and not autouse) | Diff defined set (`pytest --fixtures -v`, strip `site-packages`/`_pytest`) minus used closures (`pytest -o addopts='' --fixtures-per-test`); cross-check `uvx pytest-deadfixtures --dead-fixtures` | Delete the dead fixture, or wire it to its intended test | medium / trivial | 4 |
| H09 | Candidate "unused" fixture may be requested dynamically | `rg 'getfixturevalue\(["\x27]<name>'` and bare `<name>` string refs before deleting | **Guard:** never delete a fixture reachable via `request.getfixturevalue` or a string mark; static scans cannot see it | medium / trivial | 4 |
| H10 | Expensive function-scoped fixture re-runs once per test | `pytest --setup-plan`; count `SETUP` rows per `F` fixture; > 1 with an I/O body (net/db/docker/subprocess/sleep/build) | Raise scope to module/session (or class/package) when the value is shared and not test-mutated; verify the `SETUP` count drops | medium / small | 5, 6 |
| H11 | Two fixtures with identical/near-identical bodies | `uvx pytest-deadfixtures --dup-fixtures`; or name collisions: `pytest --fixtures -v` names, `sort`, `uniq -d` | Consolidate into one fixture in the nearest shared conftest; document intentional overrides | medium / small | 3, 4 |
| H12 | Autouse fixture runs for every test but most don't need it | `rg 'autouse\s*=\s*True'`; `pytest --setup-plan`, its `SETUP` count ≈ total tests | Drop autouse, opt-in the subset via `@pytest.mark.usefixtures`; keep autouse only for cheap universal setup (env/time/global reset) | high / medium | 4, 5, 6 |
| H13 | Parametrized/indirect fixture pays setup once per param per test | `pytest --setup-show \| rg 'SETUP .* <name>\['`; many repeated `[param]` setups | Move the param to a higher-scoped fixture, or cache the per-param resource at module/session scope and select from it | medium / medium | 2, 5 |
| H41 | Fixture/test requests a dependency it never uses | Diff signature params against names used in the body; flag params with 0 in-body uses that are not autouse side-effect fixtures | Drop unused params; if a side-effect is intended, make it `autouse`/`usefixtures` and document it | low / trivial | 4 |
| H42 | conftest with no fixtures/hooks, or dead assign-then-overwrite | Per conftest: `rg -c 'def \|@pytest.fixture\|pytest_'` == 0; `ruff` `F841` for computed-then-overwritten bindings | Delete the empty conftest; remove the dead first assignment (preserve dropped kwargs) | low / trivial | 3 |
| H43 | `@pytest.mark.*` stacked on a `@pytest.fixture` | Scan for a `@pytest.mark` line immediately preceding `@pytest.fixture` | Remove the mark from the fixture; gate inside the consuming test/fixture body. Silent no-op pre-9, hard error 9+ | low / trivial | 4, 6 |

## C. Collection, plugins, capability errors (goals 1, 6)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H14 | Collection aborts: "Marks cannot be applied to fixtures" | `pytest --collect-only -q 2>&1 \| tail -5` | Move the mark's condition into the fixture body via `pytest.skip()`; never stack `@pytest.mark.*` above `@pytest.fixture` | low / trivial | 6 |
| H22 | Collection/import-bound (`--co` itself slow) | `time pytest --co -q` is a large fraction of total | Do **not** xdist (each worker re-collects). Disable unused autoload plugins (`-p no:` / `PYTEST_DISABLE_PLUGIN_AUTOLOAD`), narrow `testpaths`, reduce parametrize explosion, defer heavy top-level imports | low / medium | 1, 6 |
| H44 | Third-party `pytest11` plugin error blocks an unrelated suite | Traceback names `site-packages/<pkg>/pytest_plugin.py` during `load_setuptools_entrypoints` | Temporarily `-p no:<entrypoint_name>` to keep measuring; report the upstream plugin as the real blocker | low / trivial | 6, 7 |

## D. Safety gates and parallelism (goal 6)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H17 | **GATE:** prove order-independence before parallel/reorder | `uvx pytest-randomly` over ≥ 3 seeds; reproduce with `--randomly-seed=last`; run the suspect nodeid in isolation | Block xdist/reorder until green across seeds **and** in isolation; fix coupling via fixture teardown that resets globals | low / medium | 6 |
| H18 | **GATE:** collection must be deterministic for xdist | `pytest --co -q \| sort > a`; repeat `> b`; `diff a b` must be empty | List-ify parametrize values (no `set`/unordered dict); remove time/random/env-conditional collection | low / small | 6 |
| H19 | Suite slow, tests independent, runtime-bound | `time pytest --co -q` fast **and** H17/H18 pass | Enable `-n auto` (cap `--maxprocesses` if I/O-bound on one shared resource) | medium / small | 6 |
| H20 | Green serially but flakes under `-n auto` | Run `-n auto` 5–10×; failures move between workers | `--dist=loadscope`/`loadfile` to co-locate module/class state, and/or `@pytest.mark.xdist_group`; refactor only if grouping is insufficient | low / small | 6 |
| H21 | Session fixture assumed once but runs once per xdist worker | Add a counter/log to the fixture; run `-n2`; it fires per worker | Use `tmp_path_factory.getbasetemp().parent` + `FileLock` single-exec, or `testrun_uid` for per-run-unique resources | medium / medium | 5, 6 |
| H16 | Session/module-scoped mutable resource mutated across modules | `rg 'scope="session"\|scope="module"'` conftest; then `rg 'create_all\|metadata\|\.add\(\|writestr\|bootstrap'` across consumers | Keep the shared resource read-only and isolate writes behind a function-scoped transaction-rollback fixture, or drop to function scope | medium / medium | 5, 6 |

## E. Caching and recomputation (goals 6, 11)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H24 | Expensive computation recomputed every run (build/schema/dataset) | `--durations` shows the same costly setup each invocation | Memoize cross-run via `config.cache.set/get` under a namespaced key + invalidation token (input hash/mtime); guard writes with `if not hasattr(config, "workerinput")` | medium / medium | 6, 11 |
| H35 | Per-test `tmp_path` rebuilds an identical file tree | `rg 'tmp_path /'` tests/; same files written across many tests | Build the tree once with a module/session `tmp_path_factory` fixture; share read-only | low / small | 5, 6 |
| H34 | Expensive object built in body/function fixture and reused unchanged | `pytest --durations=25` + `rg` repeated construction of the same heavy type | Hoist construction to a session/module fixture + a cheap function-scoped reset (`.clear()`/`.reset()`); or content-hash a build cache | medium / medium | 5, 6 |

## F. External I/O, timing, markers (goals 6, 7)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H15 | Autouse/default-path fixture does real network I/O, unguarded | `rg 'autouse=True'` then follow to `urlretrieve`/`requests`/`urlopen`/`.download`; check for a network/slow marker | Make the heavy fixture opt-in behind a registered marker or env var with `pytest.skip`; split unit vs integration paths | medium / medium | 6 |
| H33 | Tests call real `time.sleep`/`asyncio.sleep` for non-trivial durations | `rg 'time\.sleep\(\|asyncio\.sleep\('` tests/, then `pytest --durations=25` | Route production timing through an indirection and monkeypatch a `FakeClock` fixture (advance a counter); or cap with `pytest-timeout` | low / small | 6 |
| H37 | Slow/networked/subprocess tests run by default (no marker/gate) | `rg 'requests\.\|httpx\.\|subprocess\.\|socket\.\|docker\|\.connect\('` tests/; check markers/addopts | Register a marker (slow/integration/network), apply it (hand or folder-based auto-mark in `pytest_collection_modifyitems`), deselect by default via `addopts '-m "not integration"'` or a `--runslow` flag | low / small | 6 |
| H39 | Optional/heavy dependency imported at module top | `rg '^import \|^from '` tests/ for heavy/optional libs; `pytest --collect-only` | Replace the top-level import with `pytest.importorskip('pkg', minversion=...)` so the module skips cleanly when absent | low / trivial | 6 |
| H40 | No per-test timeout / warnings ignored / unregistered markers | Check pyproject for `timeout`, `filterwarnings`, `strict-markers`, `markers`; run `pytest -W error` locally | Add `pytest-timeout` (`--timeout-method=thread` for async), `filterwarnings=['error']`, `--strict-markers`, and register every custom marker | low / trivial | 6, 7 |

## G. Consolidation and packaging (goals 3, 11)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H25 | Duplicate tracks: in-body data loop, or duplicated helpers | `rg` duplicated helper defs in sibling conftests; tests looping a data list inside the body instead of parametrize | Consolidate into one `NamedTuple` + `test_id` parametrized track; hoist shared helpers into one support module/`pytest11` plugin | medium / small | 3, 10 |
| H36 | Repeated near-identical object construction across tests/params | `rg 'SomeType\('` tests/; duplicated builder boilerplate | Introduce a factory (callable) fixture that yields a closure, tracks instances, tears down in reverse order | low / small | 5, 6 |
| H38 | Shared expensive fixtures copy-pasted across conftests/repos | Diff conftest fixtures across packages; `rg 'pytest_plugins'` | Package fixtures as an installable `pytest11` plugin (`entry-points.pytest11`) or `pytest_plugins = ('pkg.module',)`; register markers via `addinivalue_line` | low / medium | 3, 11 |

## H. Typing and parametrize convention (goals 9, 10)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H26 | Legacy `tmpdir`/`tmpdir_factory` (often mis-typed as `pathlib.Path`) | `rg '\btmpdir\b\|tmpdir_factory'` tests/ conftest.py | Replace with `tmp_path`/`tmp_path_factory` (true `pathlib.Path`); fix annotations | low / trivial | 9 |
| H27 | Untyped test/fixture (missing return type or unannotated params) | Run the project strict checker over tests/, or grep `def test_` lacking `-> None` | Annotate every param and return; type pytest builtins (`monkeypatch: pytest.MonkeyPatch`, `tmp_path: pathlib.Path`, `request: pytest.FixtureRequest`, `capsys: pytest.CaptureFixture[str]`, `pytester: pytest.Pytester`) | low / medium | 9 |
| H28 | `parametrize` with comma-joined argname string + bare tuples (3+ fields) | `rg 'parametrize\(\s*["\x27][^"\x27]*,[^"\x27]*["\x27]'` (first arg is a quoted multi-name string) | Introduce `class NameFixture(t.NamedTuple)` with `test_id: str` first + a module-level fixtures list; wire Style A (`Fixture._fields`, `ids=[f.test_id for f in ...]`) or Style B | low / small | 10 |
| H29 | `parametrize` without `ids=` (auto `param0`/`param1`) | `pytest --collect-only -q` showing `test_x[0]`; or grep parametrize bodies lacking `ids=` | Add a stable `test_id` and `ids=[f.test_id for f in FIXTURES]` (or `ids=lambda c: c.test_id`) so failures name the scenario | low / trivial | 10 |
| H30 | NamedTuple/dataclass case struct lacking a `test_id` field | `rg 'class \w+(Fixture\|Case)\(.*NamedTuple'` then inspect for `test_id: str` | Add `test_id: str` as the first field (Style A) and derive ids from it | low / small | 10 |
| H31 | Test module missing `from __future__ import annotations` or using `Tuple`/`List` | `rg --files-without-match 'from __future__ import annotations'` over the test glob (exclude `__init__.py`) | Add the future import; prefer builtin generics (`list[FooFixture]`) and namespace typing (`import typing as t`, `t.NamedTuple`) | low / trivial | 9, 10 |
| H32 | Class-based test groupings (`class TestFoo`) | `rg '^class Test[A-Z]'` over the test glob | Flatten into module-level `def test_*` functions with descriptive names (functional-tests convention) | medium / medium | 3, 9 |

## I. Developer loop (goals 6, 7)

| ID | Signal | Detect | Action | Risk / Effort | Goals |
|----|--------|--------|--------|---------------|-------|
| H23 | Slow inner loop while iterating on one test | Many passing tests run before the one under iteration | Recommend `--lf`/`--sw`/`--ff`/`--nf` for the **dev loop only**; never the gating CI run (`--ff` reordering can repeat fixture setup) | low / trivial | 6, 7 |
