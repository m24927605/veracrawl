from __future__ import annotations

import ast
from pathlib import Path


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".", 1)[0])
    return modules


def test_production_grade_core_has_no_framework_or_infra_imports() -> None:
    root = Path(__file__).parents[2]
    imports = _imports(root / "src" / "veracrawl" / "benchmarks" / "production_grade.py")
    forbidden = {
        "openai",
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "playwright",
        "selenium",
        "boto3",
        "redis",
        "psycopg",
    }
    assert imports.isdisjoint(forbidden)


def test_production_grade_cli_has_no_direct_framework_imports() -> None:
    root = Path(__file__).parents[2]
    imports = _imports(root / "src" / "veracrawl" / "cli" / "production_grade.py")
    assert "openai" not in imports
    assert "langchain" not in imports
    assert "langgraph" not in imports
