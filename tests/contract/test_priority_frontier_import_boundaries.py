"""Import-boundary tests for s3.1 priority-queue frontier (test 22)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_PRIORITY = _ROOT / "external_crawl" / "priority_frontier.py"
_PROTOCOL = _ROOT / "external_crawl" / "frontier_protocol.py"
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


# Test 22
def test_priority_frontier_imports_stdlib_and_contracts_only() -> None:
    """``priority_frontier.py`` may only import stdlib + veracrawl.contracts
    + the existing frontier module (shared types).
    """

    for module in _imports(_PRIORITY.read_text()):
        if module.startswith("."):
            pytest.fail(
                f"{_PRIORITY.name} forbids relative imports: {module!r}",
            )
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        if module.startswith("veracrawl.external_crawl.frontier") or \
                module.startswith("veracrawl.external_crawl.url"):
            continue
        pytest.fail(
            f"{_PRIORITY.name} imports forbidden module: {module!r}",
        )


def test_frontier_protocol_is_protocol_only() -> None:
    """``frontier_protocol.py`` is structural only — no adapter coupling."""

    for module in _imports(_PROTOCOL.read_text()):
        if module.startswith("."):
            pytest.fail(
                f"{_PROTOCOL.name} forbids relative imports: {module!r}",
            )
        if module.split(".", 1)[0] in _STDLIB:
            continue
        # Protocol re-exports types from the frontier module.
        if module.startswith("veracrawl.external_crawl.frontier"):
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        pytest.fail(
            f"{_PROTOCOL.name} imports forbidden module: {module!r}",
        )


def test_runner_does_not_import_priority_frontier_directly() -> None:
    """Runner must not couple to the priority adapter; injection only."""

    forbidden = "veracrawl.external_crawl.priority_frontier"
    for module in _imports(_RUNNER.read_text()):
        if module.startswith(forbidden):
            pytest.fail(
                f"{_RUNNER.name} must inject PriorityCrawlFrontier "
                f"via ctor, not import it directly; found {module!r}",
            )
