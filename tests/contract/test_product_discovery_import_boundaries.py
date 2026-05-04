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


def test_product_discovery_core_has_no_framework_or_sdk_imports() -> None:
    root = Path(__file__).parents[2]
    imports = _imports(root / "src" / "veracrawl" / "benchmarks" / "product_discovery.py")
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


def test_product_discovery_cli_loads_adapters_dynamically() -> None:
    root = Path(__file__).parents[2]
    cli_imports = _imports(root / "src" / "veracrawl" / "cli" / "product_discovery.py")
    assert "importlib" in cli_imports
    assert "openai" not in cli_imports
    assert "langchain" not in cli_imports
