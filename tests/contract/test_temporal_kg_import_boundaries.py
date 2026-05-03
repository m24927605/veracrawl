from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_temporal_kg_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_temporal_kg_runtime_and_cli_have_no_forbidden_imports() -> None:
    root = Path(__file__).parents[2]
    forbidden = {
        "networkx",
        "neo4j",
        "gremlin_python",
        "langchain",
        "langgraph",
        "openai",
        "playwright",
        "selenium",
        "requests",
        "httpx",
        "aiohttp",
        "boto3",
        "redis",
        "sqlalchemy",
    }
    runtime_imports = imported_modules(root / "src" / "veracrawl" / "graph" / "temporal_kg.py")
    cli_imports = imported_modules(root / "src" / "veracrawl" / "cli" / "temporal_kg.py")
    assert not runtime_imports.intersection(forbidden)
    assert not cli_imports.intersection(forbidden)
