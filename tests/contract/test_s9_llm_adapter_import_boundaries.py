"""Import-boundary tests for s9 LLM adapters."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_STDLIB = set(sys.stdlib_module_names)

_BASE = _ROOT / "adapters" / "_llm_adapter_base.py"
_EXTRACTION = _ROOT / "adapters" / "extraction_strategy" / "llm_extraction_strategy.py"
_DRIFT = _ROOT / "adapters" / "drift" / "llm_drift_detector.py"
_REPAIR = _ROOT / "adapters" / "repair" / "llm_repairer.py"


def _imports(source: str) -> list[str]:
    out: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            for a in node.names:
                out.append(f"{prefix}.{a.name}" if prefix else a.name)
    return out


def _allowlist(path: Path) -> None:
    allowed_prefixes = (
        "veracrawl.contracts.",
        "veracrawl.ports.extraction_strategy",
        "veracrawl.ports.drift_detection",
        "veracrawl.ports.repair",
        "veracrawl.ports.model_provider_v2",
        "veracrawl.ports.prompt_registry",
        "veracrawl.ports.token_budget",
        "veracrawl.adapters._llm_adapter_base",
    )
    for module in _imports(path.read_text()):
        if module.startswith("."):
            pytest.fail(f"{path.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.split(".", 1)[0] in {"pydantic"}:
            continue
        if any(module.startswith(p) for p in allowed_prefixes):
            continue
        pytest.fail(f"{path.name} imports forbidden module: {module!r}")


def test_llm_adapter_base_imports_allowlist() -> None:
    _allowlist(_BASE)


def test_llm_extraction_strategy_imports_allowlist() -> None:
    _allowlist(_EXTRACTION)


def test_llm_drift_detector_imports_allowlist() -> None:
    _allowlist(_DRIFT)


def test_llm_repairer_imports_allowlist() -> None:
    _allowlist(_REPAIR)
