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


def test_real_world_benchmark_core_has_no_agent_framework_or_browser_imports() -> None:
    root = Path(__file__).parents[2]
    imports = _imports(root / "src" / "veracrawl" / "benchmarks" / "real_world.py")
    forbidden = {
        "openai",
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "playwright",
        "selenium",
    }
    assert imports.isdisjoint(forbidden)


def test_real_world_benchmark_cli_keeps_concrete_adapter_out_of_core() -> None:
    root = Path(__file__).parents[2]
    core_imports = _imports(root / "src" / "veracrawl" / "benchmarks" / "real_world.py")
    cli_imports = _imports(root / "src" / "veracrawl" / "cli" / "real_benchmark.py")
    assert "veracrawl.adapters.network.stdlib_http" not in core_imports
    assert "veracrawl.adapters.network.stdlib_http" not in cli_imports
    assert "importlib" in cli_imports
    assert "urllib" in cli_imports
