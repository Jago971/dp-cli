---
name: testing-conventions
description: Tests - marker taxonomy (unit/integration/contract), naming, factories, CI wiring, test README as a bug log, running pytest. The test-first loop, seams and mocking belong to tdd.
---

# Testing conventions

Test-first practice, seams, anti-patterns and mocking: call the Skill tool with `tdd`. This skill holds the Datumpin conventions around it.

## Three tiers

Every test carries exactly one tier marker, so CI can select it:

- **unit**: pure functions, no DB, no network, fast.
- **integration**: real internal wiring (a router against a real test DB), no external network.
- **contract**: calls a real dependent service. It runs manually or on a schedule, outside CI.

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = --durations=10
markers =
    unit: pure-function tests, no DB or network
    integration: router/CRUD tests against a real test DB
    contract: cross-service tests against a live dependent service
```

`--durations=10` stays on so slow tests surface early. Directories mirror the tiers: `tests/unit/`, `tests/integration/`, `tests/contract/`.

## Naming

`test_<action>_<condition>_<expected_outcome>`, so the name says what broke:

```
test_create_common_addressing_ambiguous_source_returns_409
```

## Fixtures and test data

Test-data builders live in one `factories.py` (`make_customer`, `make_source`, `make_addressing`). Frontend tests mock the API boundary module (see `tdd`, `mocking.md`).

## CI wiring

- CI runs `unit` and `integration`.
- A test that must skip in CI uses `@pytest.mark.skipif(condition)` and documents the reason in the CI/runner doc.
- Non-blocking CI is stated in the workflow README (see `gitea-workflows`).

## Test READMEs are a bug log

A suite's README names the specific real bugs it caught, with root cause and fix, so it reads as an audit trail:

```
`_footer.py::apply_sort` raised TypeError on an unrecognized sort field
instead of the no-op its docstring promised — fixed, with a regression test.
```

## Running tests

- Run `python -m pytest -q` inside the service's container (`docker compose ... exec <service> python -m pytest -q`), so the working directory is on `sys.path` and local and CI runs match.
- Run pytest directly and read its exit code. A pipe through `tail` or `head` returns the last command's status, so a killed run (exit 137) looks like success. Redirect long output to a file and read the file.
- Give a fake process a real integer `pid` and patch the kill call. A mock `pid` coerces to `1`, so `os.killpg`/`os.kill` would signal process group 1, which kills the container's own processes when it runs as root.
- Read the running instance's own configuration (customers, names, ids) in tests, so the suite passes in every instance's container.
- Run the suite after a clean no-cache rebuild, and re-check the count in the test README when the suite changes shape.
- Set up coverage reporting (`pytest-cov`) at the start of a project.

## Done when

- `pytest --markers` lists the three tiers, and every test carries exactly one.
- `python -m pytest -q` exits 0 inside the container, and the test README's count matches.
- The README names at least one real bug (cause and fix) per area.
- CI selects `unit` and `integration` and excludes `contract`.
