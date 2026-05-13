"""Import-boundary tests for s1 ``CrawlPlannerPort`` (tests 20, 21, 22).

Implements the s1 plan's red list, section
``tests/contract/test_crawl_planner_import_boundaries.py``. Each
test walks a Python source file's AST and either rejects imports
outside an allowlist or asserts the absence of forbidden imports.

The allowlist patterns (test 21) implement the iter-5 post-iter-5
follow-up: any import that isn't stdlib, ``veracrawl.contracts.*``,
or ``veracrawl.ports.crawl_planner`` fails the test. Test 22 is the
"runner has not been wired" guard so a future s3 work cannot
accidentally land in s1.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PORT_PATH = _PROJECT_ROOT / "src" / "veracrawl" / "ports" / "crawl_planner.py"
_ADAPTER_PATH = (
    _PROJECT_ROOT
    / "src"
    / "veracrawl"
    / "adapters"
    / "planning"
    / "deterministic_crawl_planner.py"
)
_RUNNER_PATH = _PROJECT_ROOT / "src" / "veracrawl" / "external_crawl" / "runner.py"

_STDLIB_NAMES = set(sys.stdlib_module_names)


def _imported_modules(source: str) -> list[str]:
    """Return every fully-qualified module each import touches."""

    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None or node.level != 0:
                continue
            modules.append(node.module)
    return modules


def _top_level_name(module: str) -> str:
    return module.split(".", 1)[0]


def _is_stdlib(module: str) -> bool:
    return _top_level_name(module) in _STDLIB_NAMES


# ---------------------------------------------------------------------------
# Test 20 — Port allowlist: stdlib + veracrawl.contracts.*.
# ---------------------------------------------------------------------------


def test_ports_crawl_planner_imports_only_contracts_and_stdlib() -> None:
    source = _PORT_PATH.read_text()
    for module in _imported_modules(source):
        if _is_stdlib(module):
            continue
        if module == "veracrawl.contracts.crawl_planner":
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        pytest.fail(
            f"ports/crawl_planner.py imports forbidden module: {module!r}; "
            "the port may import only stdlib and veracrawl.contracts.*"
        )


# ---------------------------------------------------------------------------
# Test 21 — Adapter allowlist: stdlib + veracrawl.contracts.* +
# veracrawl.ports.crawl_planner. (Iter-5 post-iter-5 follow-up.)
#
# The adapter lands in s1 step 4; this test skips until then so the
# step-3 (port) commit can land green with the test reserved.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _ADAPTER_PATH.exists(),
    reason="DeterministicCrawlPlanner lands in s1 step 4 — see "
    "docs/plans/general-purpose-crawler-agentification/"
    "s1-crawl-planner-port-contract.md Module map",
)
def test_adapters_planning_deterministic_crawl_planner_imports_allowlist() -> None:
    source = _ADAPTER_PATH.read_text()
    allowed_prefix = "veracrawl.contracts."
    allowed_port = "veracrawl.ports.crawl_planner"
    for module in _imported_modules(source):
        if _is_stdlib(module):
            continue
        if module == allowed_port:
            continue
        if module.startswith(allowed_prefix):
            continue
        pytest.fail(
            "adapters/planning/deterministic_crawl_planner.py imports "
            f"forbidden module: {module!r}; allowed set is stdlib + "
            "veracrawl.contracts.* + veracrawl.ports.crawl_planner only"
        )


# ---------------------------------------------------------------------------
# Test 22 — Runner must not import the planner port in s1.
# ---------------------------------------------------------------------------


def test_external_crawl_runner_does_not_import_crawl_planner_port() -> None:
    source = _RUNNER_PATH.read_text()
    for module in _imported_modules(source):
        if module.startswith("veracrawl.ports.crawl_planner"):
            pytest.fail(
                "external_crawl/runner.py must not import "
                "veracrawl.ports.crawl_planner in s1 (runner wiring is s3); "
                f"found import: {module!r}"
            )
        if module.startswith("veracrawl.contracts.crawl_planner"):
            pytest.fail(
                "external_crawl/runner.py must not import "
                "veracrawl.contracts.crawl_planner in s1 (runner wiring is s3); "
                f"found import: {module!r}"
            )
