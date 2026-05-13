"""Import-boundary tests for s1 ``CrawlPlannerPort`` (tests 20, 21, 22)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_PORT = _ROOT / "ports" / "crawl_planner.py"
_ADAPTER = _ROOT / "adapters" / "planning" / "deterministic_crawl_planner.py"
_RUNNER = _ROOT / "external_crawl" / "runner.py"
_STDLIB = set(sys.stdlib_module_names)


def _imports(source: str) -> list[str]:
    out: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            out.append("." * node.level + (node.module or ""))
    return out


def _check_allowlist(path: Path, extra: tuple[str, ...]) -> None:
    for module in _imports(path.read_text()):
        if module.startswith("."):
            pytest.fail(f"{path.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.startswith("veracrawl.contracts.") or module in extra:
            continue
        pytest.fail(f"{path.name} imports forbidden module: {module!r}")


def test_ports_crawl_planner_imports_only_contracts_and_stdlib() -> None:
    _check_allowlist(_PORT, extra=())


@pytest.mark.skipif(not _ADAPTER.exists(), reason="DeterministicCrawlPlanner lands in s1 step 4")
def test_adapters_planning_deterministic_crawl_planner_imports_allowlist() -> None:
    _check_allowlist(_ADAPTER, extra=("veracrawl.ports.crawl_planner",))


def test_external_crawl_runner_does_not_import_crawl_planner_port() -> None:
    for module in _imports(_RUNNER.read_text()):
        if module.startswith("veracrawl.ports.crawl_planner"):
            pytest.fail(f"runner must not import port in s1: {module!r}")
        if module.startswith("veracrawl.contracts.crawl_planner"):
            pytest.fail(f"runner must not import planner contracts in s1: {module!r}")
