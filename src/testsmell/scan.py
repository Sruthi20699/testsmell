"""Run every registered rule over a set of paths."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from .discovery import ParseError, TestModule, find_test_files, parse_file
from .rules import REGISTRY, Finding, Severity

PARSE_ERROR_ID = "TS000"


@dataclass
class ScanResult:
    modules: list[TestModule] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def test_count(self) -> int:
        return sum(len(m.tests) for m in self.modules)


def scan(paths: Iterable[Path], exclude: Iterable[str] = ()) -> ScanResult:
    result = ScanResult()
    for path in find_test_files(paths, exclude):
        parsed = parse_file(path)
        if isinstance(parsed, ParseError):
            result.findings.append(
                Finding(PARSE_ERROR_ID, Severity.ERROR, parsed.message, parsed.path, parsed.line)
            )
            continue
        result.modules.append(parsed)
        for r in REGISTRY.values():
            result.findings.extend(r.check(parsed))
    return result


def rule_title(rule_id: str) -> str:
    return REGISTRY[rule_id].title if rule_id in REGISTRY else "File could not be parsed"
