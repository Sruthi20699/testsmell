from pathlib import Path

from conftest import FIXTURES

from testsmell.discovery import ParseError, find_test_files, is_test_file, parse_file


def test_is_test_file():
    assert is_test_file(Path("test_api.py"))
    assert is_test_file(Path("api_test.py"))
    assert not is_test_file(Path("api.py"))
    assert not is_test_file(Path("conftest.py"))


def test_find_skips_virtualenvs_and_honours_exclude(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "test_a.py").write_text("")
    (tmp_path / "pkg" / "helpers.py").write_text("")
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "test_vendored.py").write_text("")
    (tmp_path / "skip").mkdir()
    (tmp_path / "skip" / "test_b.py").write_text("")

    found = list(find_test_files([tmp_path], exclude=["*/skip/*"]))
    assert [p.name for p in found] == ["test_a.py"]


def test_explicit_file_is_always_scanned(tmp_path):
    path = tmp_path / "checks.py"
    path.write_text("")
    assert list(find_test_files([path])) == [path]


def test_collects_module_and_class_tests():
    module = parse_file(FIXTURES / "clean" / "test_clean.py")
    assert [t.qualname for t in module.tests] == [
        "test_add",
        "test_add_rejects_strings",
        "test_mock_called",
        "TestAdd.test_negative",
        "TestAdd.test_is_none_check",
    ]


def test_syntax_error_is_reported_not_raised(tmp_path):
    path = tmp_path / "test_broken.py"
    path.write_text("def test_x(:\n    pass\n")
    result = parse_file(path)
    assert isinstance(result, ParseError)
    assert result.line == 1
