# Typed parametrize convention

The target shape for goals 9 (typings) and 10 (typed parametrize). Backs
`H26`–`H32`. A migration is correct when failures name the **scenario**, not
`param0`, and a type checker covers the test as strictly as the source.

The **hard rule**: a `test_id` field is present and `ids=` is derived from it.
First-field placement and the `Fixture` vs `Case` class name are conventions, not
requirements.

## Style A — unpack the NamedTuple into test parameters

Each field becomes a test argument. `test_id` is both the first parameter and the
case id, so adding a field wires it into every test signature automatically.

```python
from __future__ import annotations

import typing as t

import pytest


class CaseFixture(t.NamedTuple):
    test_id: str       # first field: human-readable id AND a test parameter
    given: str
    expected: int


CASES: list[CaseFixture] = [
    CaseFixture(test_id="empty", given="", expected=0),
    CaseFixture(test_id="single-word", given="hi", expected=2),
    CaseFixture(test_id="multibyte", given="漢", expected=1),
]


@pytest.mark.parametrize(
    list(CaseFixture._fields),
    CASES,
    ids=[c.test_id for c in CASES],
)
def test_length(test_id: str, given: str, expected: int) -> None:
    assert measure(given) == expected
```

`list(CaseFixture._fields)` derives the argnames from the type — no
hand-maintained `"test_id,given,expected"` string to drift out of sync.

## Style B — pass one case object

Keep the case as a single typed argument. Tolerates any field order and is handy
when fields are numerous or nested.

```python
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.test_id)
def test_length(case: CaseFixture) -> None:
    assert measure(case.given) == case.expected
```

## Typed fixtures and builtins (goal 9)

- Start every test module with `from __future__ import annotations`.
- Annotate every parameter and every return (`-> None` for tests).
- Type pytest's builtins explicitly:

| Builtin | Annotation |
|---------|------------|
| `tmp_path` | `pathlib.Path` |
| `tmp_path_factory` | `pytest.TempPathFactory` |
| `monkeypatch` | `pytest.MonkeyPatch` |
| `request` | `pytest.FixtureRequest` |
| `capsys` | `pytest.CaptureFixture[str]` |
| `caplog` | `pytest.LogCaptureFixture` |
| `pytester` | `pytest.Pytester` |

- Prefer builtin generics (`list[CaseFixture]`, `dict[str, str]`) and namespace
  typing (`import typing as t`, `t.NamedTuple`).

## Anti-patterns to migrate

| Smell (heuristic) | Migration |
|-------------------|-----------|
| `parametrize("a,b,c", [(1, 2, 3)])` with 3+ bare-tuple fields (H28) | Introduce `class XFixture(t.NamedTuple)` + Style A or B |
| `parametrize` with no `ids=`, producing `test_x[0]` (H29) | Add `test_id` and `ids=[c.test_id for c in CASES]` |
| NamedTuple/dataclass case without a `test_id` (H30) | Add `test_id: str` (first field for Style A) and derive ids |
| Legacy `tmpdir`/`tmpdir_factory` (H26) | Replace with `tmp_path`/`tmp_path_factory` (true `pathlib.Path`) |
| Module missing `from __future__ import annotations` (H31) | Add it; switch `Tuple`/`List` to builtin generics |
| Untyped test/fixture (H27) | Annotate params + return; run the project strict checker over `tests/` |
| `class TestFoo` used only to group (H32) | Flatten into module-level `def test_*` with descriptive names |
| In-body `for case in DATA:` loop covering distinct cases (H25) | Convert the loop into a parametrized track so each case is a reported test |

## Verification

A migration is done when:

- `pytest --collect-only -q` shows readable ids (`test_length[multibyte]`), not
  `test_length[0]`.
- The project's strict type checker (mypy `strict`, or basedpyright) includes the
  test directory and passes.
- Behavior is unchanged: the same set of assertions runs, now individually named.
