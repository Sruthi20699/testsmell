"""Render scan results as JSON, a self-contained HTML report, or GitHub annotations."""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from . import __version__
from .rules import Finding, Severity
from .scan import ScanResult, rule_title

_SEVERITY_RANK = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}


def display_path(path: Path) -> str:
    try:
        return os.path.relpath(path.resolve()).replace(os.sep, "/")
    except ValueError:  # different drive on Windows
        return path.as_posix()


def sorted_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda f: (_SEVERITY_RANK[f.severity], f.rule_id, display_path(f.path), f.line),
    )


def to_dict(result: ScanResult) -> dict:
    counts = Counter(f.severity.value for f in result.findings)
    return {
        "tool": "testsmell",
        "version": __version__,
        "summary": {
            "files": len(result.modules),
            "tests": result.test_count,
            "findings": len(result.findings),
            "by_severity": {s.value: counts.get(s.value, 0) for s in Severity},
        },
        "findings": [
            {
                "rule_id": f.rule_id,
                "title": rule_title(f.rule_id),
                "severity": f.severity.value,
                "file": display_path(f.path),
                "line": f.line,
                "message": f.message,
            }
            for f in sorted_findings(result.findings)
        ],
    }


def to_json(result: ScanResult) -> str:
    return json.dumps(to_dict(result), indent=2)


_GITHUB_LEVEL = {Severity.ERROR: "error", Severity.WARNING: "warning", Severity.INFO: "notice"}


def gh_escape(value: str, *, prop: bool = False) -> str:
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if prop:
        value = value.replace(":", "%3A").replace(",", "%2C")
    return value


def to_github(result: ScanResult) -> str:
    """GitHub Actions workflow commands, shown as inline annotations on pull requests."""
    lines = [
        f"::{_GITHUB_LEVEL[f.severity]} file={gh_escape(display_path(f.path), prop=True)},"
        f"line={f.line},title={gh_escape(f'{f.rule_id} {rule_title(f.rule_id)}', prop=True)}"
        f"::{gh_escape(f.message)}"
        for f in sorted_findings(result.findings)
    ]
    s = to_dict(result)["summary"]
    sev = s["by_severity"]
    lines.append(
        f"testsmell: {s['findings']} finding(s) in {s['files']} file(s), {s['tests']} test(s) "
        f"({sev['error']} error, {sev['warning']} warning, {sev['info']} info)"
    )
    return "\n".join(lines)


_CSS = """
:root { color-scheme: light dark; --bg:#fafafa; --fg:#1f2328; --muted:#656d76; --line:#d0d7de;
  --error:#cf222e; --warning:#9a6700; --info:#0969da; }
@media (prefers-color-scheme: dark) { :root { --bg:#0d1117; --fg:#e6edf3; --muted:#8d96a0;
  --line:#30363d; --error:#ff7b72; --warning:#d29922; --info:#58a6ff; } }
body { margin:0; padding:24px 16px; background:var(--bg); color:var(--fg);
  font:14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:1100px; margin:0 auto; }
h1 { font-size:22px; margin:0 0 4px; }
.meta { color:var(--muted); margin-bottom:20px; }
.stats { display:flex; flex-wrap:wrap; gap:12px; margin-bottom:24px; }
.stat { border:1px solid var(--line); border-radius:8px; padding:10px 16px; min-width:110px; }
.stat b { display:block; font-size:22px; }
.table-wrap { overflow-x:auto; }
table { border-collapse:collapse; width:100%; }
th, td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); vertical-align:top; }
th { color:var(--muted); font-weight:600; }
code { font-family:ui-monospace, Consolas, monospace; }
.sev { font-weight:600; text-transform:uppercase; font-size:12px; }
.sev-error { color:var(--error); } .sev-warning { color:var(--warning); } .sev-info { color:var(--info); }
.ok { padding:16px; border:1px solid var(--line); border-radius:8px; }
"""


def to_html(result: ScanResult) -> str:
    data = to_dict(result)
    summary = data["summary"]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    stats = [
        ("Findings", summary["findings"]),
        *((s.capitalize(), n) for s, n in summary["by_severity"].items()),
        ("Files", summary["files"]),
        ("Tests", summary["tests"]),
    ]
    stats_html = "".join(f'<div class="stat"><b>{n}</b>{escape(label)}</div>' for label, n in stats)

    if data["findings"]:
        rows = "".join(
            "<tr>"
            f"<td><code>{escape(f['rule_id'])}</code><br>{escape(f['title'])}</td>"
            f'<td class="sev sev-{f["severity"]}">{f["severity"]}</td>'
            f"<td><code>{escape(f['file'])}:{f['line']}</code></td>"
            f"<td>{escape(f['message'])}</td>"
            "</tr>"
            for f in data["findings"]
        )
        body = (
            '<div class="table-wrap"><table><thead><tr><th>Rule</th><th>Severity</th>'
            f"<th>Location</th><th>Message</th></tr></thead><tbody>{rows}</tbody></table></div>"
        )
    else:
        body = '<p class="ok">No test smells found.</p>'

    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>testsmell report</title><style>{_CSS}</style></head>"
        "<body><main><h1>testsmell report</h1>"
        f'<div class="meta">testsmell {data["version"]} &middot; {generated}</div>'
        f'<div class="stats">{stats_html}</div>{body}</main></body></html>\n'
    )
