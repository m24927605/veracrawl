from __future__ import annotations

from pathlib import Path


def test_deep_crawl_core_avoids_concrete_framework_and_site_imports() -> None:
    checked = [
        Path("src/veracrawl/contracts/deep_crawl.py"),
        Path("src/veracrawl/benchmarks/deep_crawl.py"),
        Path("src/veracrawl/review_replay/deep_crawl.py"),
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
        "bs4",
        "scrapy",
        "quotes.toscrape",
    ]
    for path in checked:
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in text, (path, token)
