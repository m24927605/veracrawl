"""Import-boundary test for s16 worker-lease adapter."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_ADAPTER = _ROOT / "adapters" / "work_queue" / "in_memory_worker_lease.py"
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


def test_adapter_imports_allowlist() -> None:
    for module in _imports(_ADAPTER.read_text()):
        if module.startswith("."):
            pytest.fail(f"{_ADAPTER.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        if module.startswith("veracrawl.ports.worker_lease"):
            continue
        pytest.fail(f"{_ADAPTER.name} imports forbidden module: {module!r}")
