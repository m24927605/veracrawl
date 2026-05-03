from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_IMPORT_ROOTS = {
    "agents",
    "autogen",
    "boto3",
    "crewai",
    "httpx",
    "langchain",
    "langgraph",
    "openai",
    "playwright",
    "psycopg",
    "redis",
    "requests",
    "selenium",
    "semantic_kernel",
}


def _import_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def test_target_runtime_core_has_no_concrete_framework_imports() -> None:
    files = [
        Path("src/veracrawl/contracts/target_runtime.py"),
        *Path("src/veracrawl/target_runtime").glob("*.py"),
    ]
    for path in files:
        imported = _import_roots(path)
        assert not (imported & FORBIDDEN_IMPORT_ROOTS), (path, imported)
