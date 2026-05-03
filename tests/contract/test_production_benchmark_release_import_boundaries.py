from __future__ import annotations

from pathlib import Path


def test_production_benchmark_release_core_imports_stay_adapter_neutral() -> None:
    root = Path(__file__).parents[2]
    paths = [
        root / "src" / "veracrawl" / "release" / "benchmark_gate.py",
        root / "src" / "veracrawl" / "review_replay" / "release_gate.py",
        root / "src" / "veracrawl" / "contracts" / "release.py",
    ]
    forbidden = [
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "openai",
        "playwright",
        "selenium",
        "psycopg",
        "redis",
        "boto3",
        "botocore",
        "prometheus",
        "opentelemetry",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for token in forbidden:
        assert token not in combined
