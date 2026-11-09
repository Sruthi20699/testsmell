from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..discovery import TestModule


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


SEVERITY_ORDER = [Severity.INFO, Severity.WARNING, Severity.ERROR]


@dataclass
class Finding:
    rule_id: str
    severity: Severity
    message: str
    path: Path
    line: int


RuleFn = Callable[[TestModule], Iterable[Finding]]


@dataclass
class Rule:
    id: str
    title: str
    severity: Severity
    check: RuleFn


REGISTRY: dict[str, Rule] = {}


def rule(rule_id: str, title: str, severity: Severity):
    """Register a rule. The decorated function yields messages as (line, text) pairs."""

    def wrap(fn: Callable[[TestModule], Iterable[tuple[int, str]]]) -> RuleFn:
        def check(module: TestModule) -> Iterable[Finding]:
            for line, message in fn(module):
                yield Finding(rule_id, severity, message, module.path, line)

        REGISTRY[rule_id] = Rule(rule_id, title, severity, check)
        return check

    return wrap
