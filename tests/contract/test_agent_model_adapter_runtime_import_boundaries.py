from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_real_agent_model_adapter_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_real_agent_model_adapter_cli_uses_dynamic_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "cli" / "agent_model_runtime.py")
    forbidden = {
        "veracrawl.adapters.model_providers.local_runtime",
        "veracrawl.adapters.model_providers.external_runtime",
        "veracrawl.adapters.agent_frameworks.native_runtime",
        "veracrawl.adapters.agent_frameworks.external_runtime",
        "openai",
        "agents",
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "anthropic",
        "google.generativeai",
        "google.genai",
    }
    assert "importlib" in imports
    assert not imports.intersection(forbidden)
