from __future__ import annotations

from pathlib import Path


def test_crawler_optimization_core_avoids_framework_and_site_imports() -> None:
    checked = [
        Path("src/veracrawl/contracts/crawler_optimization.py"),
        Path("src/veracrawl/benchmarks/crawler_optimization.py"),
        Path("src/veracrawl/review_replay/crawler_optimization.py"),
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
    ]
    for path in checked:
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in text, (path, token)
