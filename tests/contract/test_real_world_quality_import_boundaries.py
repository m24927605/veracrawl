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


def test_real_world_quality_core_has_no_concrete_adapter_or_framework_imports() -> None:
    root = Path(__file__).parents[2]
    imports = _imports(root / "src" / "veracrawl" / "benchmarks" / "real_world_quality.py")
    forbidden = {
        "openai",
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "playwright",
        "selenium",
        "urllib",
    }
    assert imports.isdisjoint(forbidden)
