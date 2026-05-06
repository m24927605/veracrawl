from __future__ import annotations

from pathlib import Path


def test_objective_gate_core_avoids_benchmark_adapter_and_framework_imports() -> None:
    checked = [
        Path("src/veracrawl/optimization/objective_gate.py"),
        Path("src/veracrawl/review_replay/crawler_optimization_objective_gate.py"),
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
