from __future__ import annotations

from pathlib import Path


def test_owner_integration_core_avoids_benchmark_adapter_and_framework_imports() -> None:
    checked = [
        Path("src/veracrawl/scheduler/optimization_integration.py"),
        Path("src/veracrawl/normalize/optimization_integration.py"),
        Path("src/veracrawl/extract/optimization_integration.py"),
        Path("src/veracrawl/graph/optimization_integration.py"),
        Path("src/veracrawl/publish/optimization_integration.py"),
        Path("src/veracrawl/ops/optimization_integration.py"),
        Path("src/veracrawl/review_replay/crawler_optimization_owner_integration.py"),
    ]
    forbidden = [
        "veracrawl.benchmarks",
        "veracrawl.adapters",
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
