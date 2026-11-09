# testsmell

Find **test smells** in Python test suites: tests that pass without really testing anything.

A green test run only means something if the tests can fail. `testsmell` reads your test files
with Python's `ast` module (nothing is imported or executed) and flags patterns that make a test
silently useless, slow, or flaky.

Output on this repo's deliberately smelly fixture (messages shortened):

```text
$ testsmell check tests/fixtures/smelly
 Rule   Severity  Location                                  Message
 TS002  error     tests/fixtures/smelly/test_smelly.py:10   assert on a tuple is always true ...
 TS004  error     tests/fixtures/smelly/test_smelly.py:22   Test 'test_duplicate' is defined again (first on line 18) ...
 TS001  warning   tests/fixtures/smelly/test_smelly.py:4    Test 'test_no_assert' never asserts anything ...
 TS003  warning   tests/fixtures/smelly/test_smelly.py:14   Test 'test_sleeps' calls time.sleep() ...
 TS005  warning   tests/fixtures/smelly/test_smelly.py:29   Test 'test_swallows_failure' catches AssertionError ...
 TS006  info      tests/fixtures/smelly/test_smelly.py:35   assert compares to None/True/False with ==/!= ...
7 finding(s) in 1 file(s), 8 test(s).
```

## Install

```bash
pip install git+https://github.com/Sruthi20699/testsmell
```

## Usage

```bash
testsmell check                       # scan the current folder
testsmell check tests src/app/tests   # scan specific folders or files
testsmell check tests -e "tests/fixtures/*"
testsmell check tests --fail-on error # only fail on errors (default: warning)
testsmell rules

# reports
testsmell check tests -f json > smells.json
testsmell check tests -f html -o report.html
testsmell check tests -f github       # GitHub Actions annotations
```

Test files are `test_*.py` and `*_test.py`; tests are `test*` functions at module level or in classes
(pytest's default collection). `.venv`, `.git`, `node_modules`, `build` and similar folders are skipped.

## Rules

| ID | Severity | Rule | Example |
|----|----------|------|---------|
| TS001 | warning | Test has no assertion | `def test_x(): run()` |
| TS002 | error | Assert is always true | `assert (a == b, "msg")`, `assert "text"` |
| TS003 | warning | Test sleeps | `time.sleep(2)` |
| TS004 | error | Duplicate test name (earlier one never runs) | two `def test_save()` |
| TS005 | warning | Test swallows failures | `except Exception: pass` |
| TS006 | info | Compare to None/True/False with `==` | `assert x == None` |
| TS000 | error | File could not be parsed | syntax errors |

TS001 counts `assert`, `pytest.raises` / `warns` / `fail`, `self.assert*` and `mock.assert_*` as assertions.

## GitHub Action

```yaml
name: Test smells
on: [pull_request]

jobs:
  testsmell:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Sruthi20699/testsmell@main
        with:
          paths: tests
          fail-on: warning
```

| Input | Default | Description |
|-------|---------|-------------|
| `paths` | `.` | Space-separated files or folders to scan |
| `exclude` | | Space-separated globs to skip |
| `fail-on` | `warning` | Fail when a finding has at least this severity |
| `report` | | Also write an HTML report to this path |
| `python-version` | `3.12` | Python used to run testsmell |

## Development

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
testsmell check tests -e "tests/fixtures/*"   # testsmell checks its own tests
```

## License

MIT
