# Fixture analysis

Recipes for goals 2, 4, and 5: slowest fixtures, unused fixtures, and proper
scope. Backs heuristics `H03`, `H08`–`H13`, `H41`–`H43`.

## Scope and caching model

A fixture's `scope` decides how often its setup runs and how long its value is
cached:

| Scope | Setup runs | Value cached for |
|-------|-----------|------------------|
| `function` (default) | once per test that requests it | one test |
| `class` | once per test class | the class |
| `module` | once per test module | the module |
| `package` | once per package | the package |
| `session` | once per test run | the whole run |

pytest caches a fixture's result and reuses it within its scope (`cached_result`).
The core mis-scope smell: an **expensive `function`-scoped fixture whose value is
shared and not mutated** re-runs N times when one setup would do. Widening the
scope is often the single highest-impact, lowest-risk speedup — *if* the value is
read-only across tests (otherwise see "shared mutable state" below).

## Slowest fixtures and root cause (goal 2)

The `--durations` table cannot name the costly fixture (a `setup` row is the whole
chain). Two complementary tools:

`--setup-show` runs the suite and prints each fixture as it is set up/torn down,
with a scope letter (`F`/`C`/`M`/`P`/`S`):

```bash
pytest --setup-show -q
```

`--setup-plan` shows the same plan **without running tests** — fast, and ideal for
counting setups:

```bash
pytest --setup-plan
```

For true per-fixture timing, generate the opt-in plugin
(`templates/pytest_optimizer_plugin.py`); it wraps `pytest_fixture_setup` and
records each fixture's own setup seconds, filling the gap pytest core leaves.

## Mis-scoped fixture (goal 5, H10/H13)

```bash
pytest --setup-plan | rg 'SETUP +F '
```

Count `SETUP` rows per `F` (function) fixture. A count > 1 on a fixture whose body
does real work (network/db/docker/subprocess/sleep/build) is a scope candidate:

1. Confirm the value is **not mutated** by tests (read the body and consumers).
2. Raise `scope` to `module`/`session` (or `class`/`package`).
3. Verify the `SETUP` count drops with `--setup-plan` again.
4. Run the order-independence gate (`safety-gates.md`) before trusting it.

For indirect/parametrized fixtures that pay setup once per param per test (H13),
move the param to a higher-scoped fixture or cache the per-param resource at
module/session scope and select from it.

## Unused fixtures (goal 4, H08/H09/H41)

Diff **defined** fixtures against **used** fixtures:

```bash
pytest --fixtures -v 2>/dev/null | rg -v 'site-packages|_pytest'
```

```bash
pytest -o addopts='' --fixtures-per-test 2>/dev/null
```

The first command lists project-defined fixtures; the second lists what each test
actually requests. **Gotcha:** if the project's `addopts` enables
`--doctest-modules`, `--fixtures-per-test` raises `INTERNALERROR` (a `DoctestItem`
has no `.function`) and `2>/dev/null` does not hide it — so override addopts with
`-o addopts=''` as above. Fixture introspection does not run the suite, so
clearing addopts here is safe.

A fixture in the first set but not the second, and **not** `autouse`, is a
candidate. Cross-check with the dedicated tool when available:

```bash
uvx --with pytest-deadfixtures --from pytest pytest --dead-fixtures
```

**Mandatory guard (H09).** Static analysis cannot see dynamic requests. Before
deleting, confirm the fixture is not reached via:

```bash
rg "getfixturevalue\([\"']<name>" ; rg "\b<name>\b" tests/
```

A `getfixturevalue('name')` call or a string-based mark reference keeps the
fixture alive even though no signature names it. When any dynamic reference
exists, **keep the fixture** and have a human confirm — this is the one detection
that cannot be fully automated.

Related: a test/fixture that lists a parameter it never uses in its body (H41) is
either a dead dependency (drop it) or an intended side-effect fixture (make it
`autouse`/`usefixtures` and document why).

## Duplicate fixtures (goal 3/4, H11/H42)

```bash
uvx --with pytest-deadfixtures --from pytest pytest --dup-fixtures
```

Or find name collisions across conftests with the built-ins:

```bash
pytest --fixtures -v 2>/dev/null | rg '^\w' | awk '{print $1}' | sort | uniq -d
```

Consolidate duplicates into one fixture in the nearest shared conftest; document
any **intentional** override (a child conftest deliberately shadowing a parent
fixture is legitimate). An empty conftest (no fixtures, no hooks) is dead weight —
delete it (H42).

## Autouse audit (goal 4/5, H12/H15/H43)

```bash
rg 'autouse\s*=\s*True'
```

For each autouse fixture, count its setups:

```bash
pytest --setup-plan | rg '<name>' | rg -c SETUP
```

When the count ≈ total tests **and** the body is expensive or side-effecting, drop
`autouse` and opt the real consumers in via `@pytest.mark.usefixtures`. Keep
autouse only for genuinely universal, cheap setup (env reset, time freezing,
global state reset). If an autouse fixture does unguarded network I/O (H15), gate
it behind a registered marker or env var with `pytest.skip` and split the unit and
integration paths.

A `@pytest.mark.*` decorator stacked directly on a `@pytest.fixture` (H43) is a
silent no-op before pytest 9 and a hard collection error from 9 on — remove it and
move the condition into the body (`pytest.skip()` / `request.getfixturevalue`).

## Shared mutable state (H16/H21)

Before widening scope or parallelizing, check whether the shared resource is
**mutated**:

```bash
rg 'scope="session"|scope="module"' ; rg 'create_all|metadata|\.add\(|writestr|bootstrap'
```

If a session/module-scoped resource is written in more than one module, keep it
read-only and isolate writes behind a function-scoped transaction-rollback
fixture, or drop it to function scope. Under xdist a session fixture runs **once
per worker**, not once per run (H21) — for a single shared resource (DB, port,
file) use the `tmp_path_factory.getbasetemp().parent` + `FileLock` single-exec
pattern, or a `testrun_uid`-keyed per-run resource.
