from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports


def test_runtime_core_has_no_concrete_framework_or_storage_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_core_does_not_contain_site_specific_scraper_modules() -> None:
    root = Path(__file__).parents[2] / "src" / "veracrawl"
    forbidden_names = {"amazon", "shopify", "linkedin", "facebook", "twitter", "single_site"}
    found = {
        path
        for path in root.rglob("*.py")
        if any(part.lower() in forbidden_names for part in path.relative_to(root).parts)
    }
    assert found == set()
