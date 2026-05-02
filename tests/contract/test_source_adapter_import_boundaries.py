from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports


def test_source_core_has_no_concrete_dependency_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_source_core_has_no_site_specific_scraper_modules() -> None:
    root = Path(__file__).parents[2] / "src" / "veracrawl"
    forbidden = {"amazon", "shopify", "linkedin", "facebook", "single_site", "scraper"}
    found = {
        path
        for path in root.rglob("*.py")
        if "adapters" not in path.relative_to(root).parts
        and any(token in path.name.lower() for token in forbidden)
    }
    assert found == set()
