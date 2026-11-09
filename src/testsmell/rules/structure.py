from __future__ import annotations

import ast
from collections.abc import Iterable

from ..astutil import dotted_name
from ..discovery import FunctionNode, TestModule
from .base import Severity, rule

_SLEEP_CALLS = {"time.sleep", "sleep"}
_BROAD_EXCEPTIONS = {"Exception", "BaseException", "AssertionError"}


@rule("TS003", "Test sleeps", Severity.WARNING)
def sleep_in_test(module: TestModule):
    for test in module.tests:
        for node in ast.walk(test.node):
            if isinstance(node, ast.Call) and dotted_name(node.func) in _SLEEP_CALLS:
                yield (
                    node.lineno,
                    (
                        f"Test '{test.qualname}' calls {dotted_name(node.func)}(), which makes the "
                        "suite slow and flaky. Poll for the condition with a timeout, or mock time."
                    ),
                )


def _duplicates(body: Iterable[ast.stmt], owner: str):
    first_seen: dict[str, int] = {}
    for node in body:
        if isinstance(node, FunctionNode) and node.name.startswith("test"):
            if node.name in first_seen:
                yield (
                    node.lineno,
                    (
                        f"Test '{owner}{node.name}' is defined again (first on line "
                        f"{first_seen[node.name]}); the earlier test is silently replaced and "
                        "never runs. Rename one of them."
                    ),
                )
            else:
                first_seen[node.name] = node.lineno


@rule("TS004", "Duplicate test name", Severity.ERROR)
def duplicate_test_names(module: TestModule):
    yield from _duplicates(module.tree.body, "")
    for node in module.tree.body:
        if isinstance(node, ast.ClassDef):
            yield from _duplicates(node.body, f"{node.name}.")


def _swallows(handler: ast.ExceptHandler) -> bool:
    broad = handler.type is None or dotted_name(handler.type) in _BROAD_EXCEPTIONS
    does_nothing = all(
        isinstance(s, ast.Pass) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
        for s in handler.body
    )
    return broad and does_nothing


@rule("TS005", "Test swallows failures", Severity.WARNING)
def swallowed_failures(module: TestModule):
    for test in module.tests:
        for node in ast.walk(test.node):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if _swallows(handler):
                        caught = dotted_name(handler.type) if handler.type else "everything"
                        yield (
                            handler.lineno,
                            (
                                f"Test '{test.qualname}' catches {caught} and ignores it, which "
                                "also hides failing asserts. Use pytest.raises for expected errors."
                            ),
                        )
