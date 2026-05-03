from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_graph_frontier_review_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_graph_frontier_review_runtime_has_no_forbidden_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "graph" / "frontier_review.py")
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
    assert not imports.intersection(forbidden)
