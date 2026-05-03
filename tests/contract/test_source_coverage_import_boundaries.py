from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_source_coverage_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_source_coverage_cli_uses_dynamic_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "cli" / "source_coverage.py")
    forbidden = {
        "veracrawl.adapters.source_coverage.contract",
        "playwright",
        "selenium",
        "requests",
        "httpx",
        "aiohttp",
        "bs4",
        "lxml",
        "pypdf",
        "boto3",
        "redis",
        "openai",
    }
    assert "importlib" in imports
    assert not imports.intersection(forbidden)
