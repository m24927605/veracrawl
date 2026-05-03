from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_dynamic_source_runtime_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_dynamic_source_runtime_gate_has_no_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "fetch" / "dynamic_source_runtime.py")
    assert not {
        name
        for name in imports
        if name == "veracrawl.adapters" or name.startswith("veracrawl.adapters.")
    }


def test_dynamic_source_runtime_cli_uses_dynamic_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "cli" / "source_runtime.py")
    forbidden = {
        "veracrawl.adapters.sources.dynamic_runtime",
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
