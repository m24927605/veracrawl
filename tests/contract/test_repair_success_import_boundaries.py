from __future__ import annotations

from pathlib import Path


def test_repair_success_core_avoids_crawler_and_framework_imports() -> None:
    checked = [
        Path("src/veracrawl/contracts/repair_success.py"),
        Path("src/veracrawl/benchmarks/repair_success.py"),
        Path("src/veracrawl/review_replay/repair_success.py"),
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
