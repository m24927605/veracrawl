from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_product_acceptance_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_product_acceptance_runtime_and_cli_have_no_forbidden_imports() -> None:
    root = Path(__file__).parents[2]
    forbidden = {
        "aiohttp",
        "boto3",
        "crewai",
        "django",
        "fastapi",
        "flask",
        "httpx",
        "langchain",
        "langgraph",
        "openai",
        "playwright",
        "psycopg",
        "redis",
        "requests",
        "selenium",
        "sqlalchemy",
    }
    runtime_imports = imported_modules(
        root / "src" / "veracrawl" / "product_acceptance" / "gate.py"
    )
    cli_imports = imported_modules(
        root / "src" / "veracrawl" / "cli" / "product_acceptance.py"
    )
    assert not runtime_imports.intersection(forbidden)
    assert not cli_imports.intersection(forbidden)
