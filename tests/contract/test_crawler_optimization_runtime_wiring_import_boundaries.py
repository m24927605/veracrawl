from __future__ import annotations

from pathlib import Path


def test_runtime_wiring_core_avoids_benchmark_and_adapter_imports() -> None:
    checked = [
        Path("src/veracrawl/optimization/runtime.py"),
        Path("src/veracrawl/review_replay/crawler_optimization_runtime.py"),
    ]
    forbidden = [
        "veracrawl.benchmarks",
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
