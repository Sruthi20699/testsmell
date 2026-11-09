import json

import pytest
from conftest import FIXTURES
from typer.testing import CliRunner

from testsmell.cli import app, main
from testsmell.reporters import gh_escape, to_github, to_html, to_json
from testsmell.rules import Finding, Severity
from testsmell.scan import scan

SMELLY = FIXTURES / "smelly"
CLEAN = FIXTURES / "clean"
runner = CliRunner()


def test_smelly_fixture_hits_every_rule():
    data = json.loads(to_json(scan([SMELLY])))
    assert data["summary"] == {
        "files": 1,
        "tests": 8,
        "findings": 7,
        "by_severity": {"info": 1, "warning": 4, "error": 2},
    }
    assert sorted({f["rule_id"] for f in data["findings"]}) == [
        "TS001",
        "TS002",
        "TS003",
        "TS004",
        "TS005",
        "TS006",
    ]
    # errors first, info last
    assert next(f["severity"] for f in data["findings"]) == "error"
    assert [f["severity"] for f in data["findings"]][-1] == "info"


def test_clean_fixture_has_no_findings():
    result = scan([CLEAN])
    assert result.findings == []
    assert result.test_count == 5


def test_parse_errors_become_ts000_findings(tmp_path):
    (tmp_path / "test_broken.py").write_text("def test_x(:\n")
    [finding] = scan([tmp_path]).findings
    assert (finding.rule_id, finding.severity) == ("TS000", Severity.ERROR)


def test_html_escapes_messages():
    result = scan([CLEAN])
    result.findings.append(
        Finding("TS001", Severity.WARNING, "<script>x</script>", CLEAN / "test_clean.py", 1)
    )
    html = to_html(result)
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_github_annotations():
    lines = to_github(scan([SMELLY])).splitlines()
    assert lines[0].startswith("::error file=")
    assert any(line.startswith("::notice ") and "TS006" in line for line in lines)
    assert lines[-1].startswith("testsmell: 7 finding(s) in 1 file(s), 8 test(s)")
    assert gh_escape("C:/a,b", prop=True) == "C%3A/a%2Cb"
    assert gh_escape("50%\nnext") == "50%25%0Anext"


def test_cli_exit_codes():
    assert runner.invoke(app, ["check", str(CLEAN), "--fail-on", "info"]).exit_code == 0
    assert runner.invoke(app, ["check", str(SMELLY)]).exit_code == 1
    assert runner.invoke(app, ["check", str(SMELLY), "--fail-on", "error"]).exit_code == 1


def test_cli_exclude_and_json(tmp_path):
    result = runner.invoke(
        app, ["check", str(FIXTURES), "-e", "*/smelly/*", "-f", "json", "--fail-on", "info"]
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["summary"]["files"] == 1


def test_main_keeps_exclude_patterns_unexpanded(monkeypatch, capsys):
    # Regression: on Windows, Click expanded "*" itself, so the pattern became folder paths.
    monkeypatch.chdir(FIXTURES.parent.parent)
    monkeypatch.setattr(
        "sys.argv", ["testsmell", "check", "tests", "-e", "tests/fixtures/*", "--fail-on", "info"]
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert "No test smells found" in capsys.readouterr().out


def test_cli_html_to_file(tmp_path):
    out = tmp_path / "report.html"
    result = runner.invoke(app, ["check", str(SMELLY), "-f", "html", "-o", str(out)])
    assert result.exit_code == 1
    assert "TS004" in out.read_text(encoding="utf-8")
