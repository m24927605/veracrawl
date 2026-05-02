from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_network_browser_core_has_no_concrete_dependency_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_network_browser_core_has_no_concrete_http_or_browser_client_imports() -> None:
    root = Path(__file__).parents[2]
    forbidden = {
        "requests",
        "httpx",
        "aiohttp",
        "playwright",
        "selenium",
        "pyppeteer",
    }
    violations: dict[Path, set[str]] = {}
    for path in (root / "src" / "veracrawl").rglob("*.py"):
        relative_parts = path.relative_to(root / "src" / "veracrawl").parts
        if "adapters" in relative_parts:
            continue
        bad = imported_modules(path) & forbidden
        if bad:
            violations[path] = bad
    assert violations == {}
