from __future__ import annotations

from pathlib import Path


def test_quality_release_core_avoids_crawler_and_framework_imports() -> None:
    checked = [
        Path("src/veracrawl/contracts/quality_release.py"),
        Path("src/veracrawl/benchmarks/quality_release.py"),
        Path("src/veracrawl/review_replay/quality_release.py"),
    ]
    forbidden = [
        "playwright",
        "selenium",
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "openai",
        "requests",
        "scrapy",
        "quotes.toscrape",
    ]
    for path in checked:
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in text, (path, token)
