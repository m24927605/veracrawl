from __future__ import annotations

from pathlib import Path


def test_browser_quality_core_does_not_import_browser_engines() -> None:
    forbidden = ("playwright", "selenium", "pyppeteer")
    for path in [
        Path("src/veracrawl/benchmarks/browser_quality.py"),
        Path("src/veracrawl/contracts/browser_quality.py"),
        Path("src/veracrawl/review_replay/browser_quality.py"),
    ]:
        text = path.read_text(encoding="utf-8")
        for name in forbidden:
            assert name not in text


def test_playwright_dependency_is_adapter_owned() -> None:
    text = Path("src/veracrawl/adapters/browser/playwright.py").read_text(
        encoding="utf-8"
    )
    assert "playwright.sync_api" in text
