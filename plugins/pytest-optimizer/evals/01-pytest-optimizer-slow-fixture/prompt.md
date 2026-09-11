---
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
---
My pytest suite takes too long, can you speed it up? Here's what `pytest --durations=0` reported:

```
========================= slowest durations =========================
4.82s setup    tests/test_reports.py::test_export_large
4.81s setup    tests/test_reports.py::test_export_small
4.79s setup    tests/test_reports.py::test_export_empty
0.61s call     tests/test_reports.py::test_export_large
0.02s call     tests/test_reports.py::test_export_small
=========================== 5 tests in 15.13s ==========================
```

conftest.py has one fixture, `db_session`, used by all three tests.
