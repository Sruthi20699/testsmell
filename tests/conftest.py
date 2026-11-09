from pathlib import Path

import pytest

from testsmell.discovery import TestModule, parse_file

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def module_from(tmp_path):
    """Write source to a temporary test file and parse it."""

    def make(source: str) -> TestModule:
        path = tmp_path / "test_sample.py"
        path.write_text(source, encoding="utf-8")
        parsed = parse_file(path)
        assert isinstance(parsed, TestModule)
        return parsed

    return make
