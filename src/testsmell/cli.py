from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table as RichTable

from .reporters import display_path, sorted_findings, to_github, to_html, to_json
from .rules import REGISTRY, SEVERITY_ORDER, Severity
from .scan import ScanResult, scan

app = typer.Typer(help="Find test smells in Python test suites.", no_args_is_help=True)
console = Console()
err_console = Console(stderr=True)


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    GITHUB = "github"


_RENDERERS = {
    OutputFormat.JSON: to_json,
    OutputFormat.HTML: to_html,
    OutputFormat.GITHUB: to_github,
}


def _print_text(result: ScanResult) -> None:
    summary = f"{len(result.modules)} file(s), {result.test_count} test(s)"
    if not result.findings:
        console.print(f"[green]No test smells found[/] in {summary}.")
        return
    out = RichTable("Rule", "Severity", "Location", "Message")
    for f in sorted_findings(result.findings):
        out.add_row(f.rule_id, f.severity.value, f"{display_path(f.path)}:{f.line}", f.message)
    console.print(out)
    console.print(f"{len(result.findings)} finding(s) in {summary}.")


@app.command()
def check(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(exists=True, help="Files or folders to scan (default: current folder)"),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option("--exclude", "-e", help="Glob of paths to skip, e.g. 'tests/fixtures/*'"),
    ] = None,
    fail_on: Annotated[
        Severity, typer.Option(help="Exit non-zero at this severity")
    ] = Severity.WARNING,
    output_format: Annotated[
        OutputFormat, typer.Option("--format", "-f", help="Output format")
    ] = OutputFormat.TEXT,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write the report to a file instead of stdout"),
    ] = None,
) -> None:
    """Scan test files (test_*.py, *_test.py) for test smells."""
    result = scan(paths or [Path(".")], exclude or [])

    if output_format is OutputFormat.TEXT:
        _print_text(result)
    else:
        report = _RENDERERS[output_format](result)
        if output is None and output_format is OutputFormat.HTML:
            output = Path("testsmell-report.html")
        if output is None:
            typer.echo(report)
        else:
            output.write_text(report, encoding="utf-8")
            err_console.print(f"Wrote {len(result.findings)} finding(s) to [bold]{output}[/]")

    threshold = SEVERITY_ORDER.index(fail_on)
    if any(SEVERITY_ORDER.index(f.severity) >= threshold for f in result.findings):
        raise typer.Exit(1)


@app.command("rules")
def list_rules() -> None:
    """List available rules."""
    out = RichTable("ID", "Severity", "Title")
    for r in sorted(REGISTRY.values(), key=lambda r: r.id):
        out.add_row(r.id, r.severity.value, r.title)
    console.print(out)


def main() -> None:
    # Click expands * wildcards itself on Windows, which would turn `--exclude "tests/*"`
    # into a list of folders. Patterns are matched by testsmell, so keep them as typed.
    app(windows_expand_args=False)


if __name__ == "__main__":
    main()
