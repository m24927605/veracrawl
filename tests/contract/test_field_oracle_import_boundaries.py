from __future__ import annotations

from pathlib import Path


def test_field_oracle_core_avoids_concrete_framework_and_site_imports() -> None:
    checked = [
        Path("src/veracrawl/contracts/field_oracle.py"),
        Path("src/veracrawl/benchmarks/field_oracle.py"),
        Path("src/veracrawl/review_replay/field_oracle.py"),
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
