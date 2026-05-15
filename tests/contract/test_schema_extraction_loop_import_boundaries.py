"""Import-boundary tests for s10 ``SchemaExtractionLoop``."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_LOOP = _ROOT / "agents" / "schema_extraction_loop.py"
_RUNNER = _ROOT / "external_crawl" / "runner.py"
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


def test_runtime_imports_allowlist() -> None:
    allowed_prefixes = (
        "veracrawl.contracts.",
        "veracrawl.ports.extraction_strategy",
        "veracrawl.ports.drift_detection",
        "veracrawl.ports.repair",
    )
    for module in _imports(_LOOP.read_text()):
        if module.startswith("."):
            pytest.fail(f"{_LOOP.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if any(module.startswith(p) for p in allowed_prefixes):
            continue
        pytest.fail(f"{_LOOP.name} imports forbidden module: {module!r}")


def test_external_crawl_runner_does_not_import_schema_extraction_loop() -> None:
    for module in _imports(_RUNNER.read_text()):
        assert "schema_extraction_loop" not in module, (
            f"runner must not import s10 SchemaExtractionLoop; "
            f"found {module!r}"
        )
