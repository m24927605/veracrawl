"""Import-boundary test for s3.2 ``dispatch.py`` (test 15)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_DISPATCH = _ROOT / "external_crawl" / "dispatch.py"
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


# Test 15 — strict allowlist
def test_dispatch_imports_stdlib_plus_contracts_only() -> None:
    allowed_prefixes = (
        "veracrawl.contracts.crawl_planner",
        "veracrawl.contracts.enums",
        "veracrawl.contracts.common",
        "veracrawl.external_crawl.frontier",
    )
    for module in _imports(_DISPATCH.read_text()):
        if module.startswith("."):
            pytest.fail(
                f"{_DISPATCH.name} forbids relative imports: {module!r}",
            )
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if any(module == p or module.startswith(p + ".") for p in allowed_prefixes):
            continue
        pytest.fail(
            f"{_DISPATCH.name} imports forbidden module: {module!r}",
        )
