"""Find test files, parse them with `ast`, and collect the test functions in each."""

from __future__ import annotations

import ast
import fnmatch
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".tox", "build", "dist"}

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass
class TestFunction:
    name: str
    node: FunctionNode
    class_name: str | None = None

    @property
    def qualname(self) -> str:
        return f"{self.class_name}.{self.name}" if self.class_name else self.name


@dataclass
class TestModule:
    path: Path
    tree: ast.Module
    tests: list[TestFunction] = field(default_factory=list)


@dataclass
class ParseError:
    path: Path
    line: int
    message: str


def is_test_file(path: Path) -> bool:
    name = path.name
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def find_test_files(paths: Iterable[Path], exclude: Iterable[str] = ()) -> Iterator[Path]:
    """Yield test files under `paths`. Explicit file arguments are always included."""
    patterns = list(exclude)
    seen: set[Path] = set()
    for root in paths:
        if root.is_file():
            candidates = [root]
        else:
            candidates = sorted(
                p
                for p in root.rglob("*.py")
                if not SKIP_DIRS.intersection(p.parts) and is_test_file(p)
            )
        for path in candidates:
            if path in seen or any(fnmatch.fnmatch(path.as_posix(), pat) for pat in patterns):
                continue
            seen.add(path)
            yield path


def collect_tests(tree: ast.Module) -> list[TestFunction]:
    """pytest-style collection: test* functions at module level or inside classes."""
    tests: list[TestFunction] = []
    for node in tree.body:
        if isinstance(node, FunctionNode) and node.name.startswith("test"):
            tests.append(TestFunction(node.name, node))
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, FunctionNode) and item.name.startswith("test"):
                    tests.append(TestFunction(item.name, item, node.name))
    return tests


def parse_file(path: Path) -> TestModule | ParseError:
    try:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return ParseError(path, exc.lineno or 1, f"Syntax error: {exc.msg}")
    except UnicodeDecodeError as exc:
        return ParseError(path, 1, f"Could not decode file: {exc.reason}")
    return TestModule(path, tree, collect_tests(tree))
