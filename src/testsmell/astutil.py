"""Small helpers for reading `ast` nodes."""

from __future__ import annotations

import ast


def dotted_name(expr: ast.expr) -> str:
    """`time.sleep` for Attribute(Name('time'), 'sleep'); '' for anything not a plain name chain."""
    parts: list[str] = []
    while isinstance(expr, ast.Attribute):
        parts.append(expr.attr)
        expr = expr.value
    if isinstance(expr, ast.Name):
        parts.append(expr.id)
        return ".".join(reversed(parts))
    return ""


def call_name(call: ast.Call) -> str:
    """Last segment of the called name: `assert_called_once` for `mock.assert_called_once()`."""
    return dotted_name(call.func).rsplit(".", 1)[-1]


def is_constant(node: ast.expr, *values: object) -> bool:
    """True if node is one of the given constants (compared by identity for None/True/False)."""
    return isinstance(node, ast.Constant) and any(node.value is v for v in values)
