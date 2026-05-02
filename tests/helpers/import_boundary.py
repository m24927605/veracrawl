from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_CORE_IMPORTS = {
    "veracrawl.adapters",
    "openai",
    "agents",
    "langchain",
    "langgraph",
    "crewai",
    "autogen",
    "semantic_kernel",
    "playwright",
    "selenium",
    "boto3",
    "botocore",
    "psycopg",
    "sqlalchemy",
    "redis",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def core_python_files(root: Path) -> list[Path]:
    return [
        path
        for path in (root / "src" / "veracrawl").rglob("*.py")
        if "adapters" not in path.relative_to(root / "src" / "veracrawl").parts
    ]


def forbidden_core_imports(root: Path) -> dict[Path, set[str]]:
    violations: dict[Path, set[str]] = {}
    for path in core_python_files(root):
        imports = imported_modules(path)
        bad = {
            name
            for name in imports
            for forbidden in FORBIDDEN_CORE_IMPORTS
            if name == forbidden or name.startswith(f"{forbidden}.")
        }
        if bad:
            violations[path] = bad
    return violations
