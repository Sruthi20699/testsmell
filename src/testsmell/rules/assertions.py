from __future__ import annotations

import ast

from ..astutil import call_name, is_constant
from ..discovery import TestModule
from .base import Severity, rule

# Calls that count as checking something, besides a plain `assert`.
_ASSERTING_CALLS = {"raises", "warns", "deprecated_call", "fail"}


def _has_assertion(fn: ast.AST) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            name = call_name(node)
            # self.assertEqual, mock.assert_called_once_with, pytest.raises, ...
            if name.startswith("assert") or name in _ASSERTING_CALLS:
                return True
    return False


@rule("TS001", "Test has no assertion", Severity.WARNING)
def no_assertion(module: TestModule):
    for test in module.tests:
        if not _has_assertion(test.node):
            yield (
                test.node.lineno,
                (
                    f"Test '{test.qualname}' never asserts anything, so it passes as long as "
                    "nothing raises. Add an assert on the result (or pytest.raises for errors)."
                ),
            )


@rule("TS002", "Assert is always true", Severity.ERROR)
def always_true_assert(module: TestModule):
    for node in ast.walk(module.tree):
        if not isinstance(node, ast.Assert):
            continue
        test = node.test
        if isinstance(test, ast.Tuple) and test.elts:
            yield (
                node.lineno,
                (
                    "assert on a tuple is always true: `assert (cond, 'msg')` checks a non-empty "
                    "tuple. Write `assert cond, 'msg'` without the parentheses."
                ),
            )
        elif isinstance(test, ast.Constant) and test.value and not isinstance(test.value, bool):
            yield (
                node.lineno,
                (
                    f"assert {test.value!r} is always true and checks nothing. "
                    "Assert on a real condition instead."
                ),
            )
        elif is_constant(test, True):
            yield (
                node.lineno,
                "`assert True` checks nothing. Assert on the behaviour under test, or remove it.",
            )


@rule("TS006", "Compare to None/True/False with ==", Severity.INFO)
def equality_with_singleton(module: TestModule):
    for node in ast.walk(module.tree):
        if not (isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare)):
            continue
        cmp = node.test
        operands = [cmp.left, *cmp.comparators]
        if any(isinstance(op, ast.Eq | ast.NotEq) for op in cmp.ops) and any(
            is_constant(o, None, True, False) for o in operands
        ):
            yield (
                node.lineno,
                (
                    "assert compares to None/True/False with ==/!=. Use `is None` / `is not None`, "
                    "or assert the value directly; == can be overridden and hides type mistakes."
                ),
            )
