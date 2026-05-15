"""Import-boundary tests for s11 replay-consumer port + adapter."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_PORT = _ROOT / "ports" / "replay_consumer.py"
_ADAPTER = _ROOT / "adapters" / "replay" / "in_memory_replay_consumer.py"
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


def _allowlist(path: Path) -> None:
    for module in _imports(path.read_text()):
        if module.startswith("."):
            pytest.fail(f"{path.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        if module.startswith("veracrawl.ports.replay_consumer"):
            continue
        pytest.fail(f"{path.name} imports forbidden module: {module!r}")


def test_port_imports_allowlist() -> None:
    _allowlist(_PORT)


def test_in_memory_consumer_imports_allowlist() -> None:
    _allowlist(_ADAPTER)
