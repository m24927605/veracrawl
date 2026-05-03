from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_website_pattern_coverage_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_website_pattern_runtime_and_cli_have_no_forbidden_imports() -> None:
    root = Path(__file__).parents[2]
    forbidden = {
        "boto3",
        "redis",
        "sqlalchemy",
        "psycopg",
        "langchain",
        "langgraph",
        "openai",
        "playwright",
        "selenium",
        "requests",
        "httpx",
        "aiohttp",
    }
    runtime_imports = imported_modules(root / "src" / "veracrawl" / "patterns" / "coverage.py")
    cli_imports = imported_modules(root / "src" / "veracrawl" / "cli" / "website_patterns.py")
    assert not runtime_imports.intersection(forbidden)
    assert not cli_imports.intersection(forbidden)
