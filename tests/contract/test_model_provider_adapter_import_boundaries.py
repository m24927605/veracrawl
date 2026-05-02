from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_model_provider_adapter_core_has_no_forbidden_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_model_provider_adapter_cli_uses_dynamic_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "cli" / "model_providers.py")
    forbidden = {
        "veracrawl.adapters.model_providers.contract",
        "openai",
        "anthropic",
        "google.generativeai",
        "google.genai",
        "transformers",
        "llama_cpp",
    }
    assert "importlib" in imports
    assert not imports.intersection(forbidden)
