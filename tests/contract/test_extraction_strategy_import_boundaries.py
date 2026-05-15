"""Import-boundary tests for s7 (tests 12-13)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_PORT = _ROOT / "ports" / "extraction_strategy.py"
_ADAPTER = _ROOT / "adapters" / "extraction_strategy" / "anchor_frequency_strategy.py"
_STDLIB = set(sys.stdlib_module_names)


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


# Test 12
def test_port_imports_stdlib_and_contracts_only() -> None:
    for module in _imports(_PORT.read_text()):
        if module.startswith("."):
            pytest.fail(f"{_PORT.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        pytest.fail(f"{_PORT.name} imports forbidden module: {module!r}")


# Test 13 — adapter strict allowlist with per-name common allowlist (R6)
_COMMON_ALLOWED = {"Ref", "VeraModel", "stable_hash"}


def test_anchor_frequency_strategy_imports_allowlist() -> None:
    for module in _imports(_ADAPTER.read_text()):
        if module.startswith("."):
            pytest.fail(f"{_ADAPTER.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.startswith("veracrawl.contracts.common."):
            name = module.split(".")[-1]
            if name in _COMMON_ALLOWED:
                continue
            pytest.fail(
                f"{_ADAPTER.name} may import only "
                f"{sorted(_COMMON_ALLOWED)} from contracts.common; "
                f"found {name!r}",
            )
        if module.startswith("veracrawl.contracts.normalized_document_read_model."):
            continue
        if module.startswith("veracrawl.contracts.schema_proposal."):
            continue
        if module.startswith("veracrawl.ports.extraction_strategy"):
            continue
        pytest.fail(f"{_ADAPTER.name} imports forbidden module: {module!r}")
