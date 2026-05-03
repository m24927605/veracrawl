from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_graph_memory_production_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_graph_memory_runtime_uses_only_core_modules() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "graph_memory" / "runtime.py")
    forbidden = {
        "veracrawl.adapters",
        "openai",
        "agents",
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "boto3",
        "redis",
        "psycopg",
    }
    assert not imports.intersection(forbidden)
