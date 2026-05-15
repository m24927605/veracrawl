"""Import-boundary tests for s1 ``CrawlPlannerPort`` (tests 20, 21, 22)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_PORT = _ROOT / "ports" / "crawl_planner.py"
_ADAPTER = _ROOT / "adapters" / "planning" / "deterministic_crawl_planner.py"
_LLM_ADAPTER = _ROOT / "adapters" / "planning" / "llm_crawl_planner.py"
_REPLAYING = _ROOT / "adapters" / "model_providers" / "replaying_model_provider.py"
_RUNNER = _ROOT / "external_crawl" / "runner.py"
_STDLIB = set(sys.stdlib_module_names)


def _imports(source: str) -> list[str]:
    # ``from a.b import c`` yields ``a.b.c`` so the allowlist sees the full name (iter-3 fix).
    out: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            for a in node.names:
                out.append(f"{prefix}.{a.name}" if prefix else a.name)
    return out


def _check_allowlist(path: Path, extra: tuple[str, ...]) -> None:
    for module in _imports(path.read_text()):
        if module.startswith("."):
            pytest.fail(f"{path.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        if any(module == e or module.startswith(e + ".") for e in extra):
            continue
        pytest.fail(f"{path.name} imports forbidden module: {module!r}")


def test_ports_crawl_planner_imports_only_contracts_and_stdlib() -> None:
    _check_allowlist(_PORT, extra=())


@pytest.mark.skipif(not _ADAPTER.exists(), reason="DeterministicCrawlPlanner lands in s1 step 4")
def test_adapters_planning_deterministic_crawl_planner_imports_allowlist() -> None:
    _check_allowlist(_ADAPTER, extra=("veracrawl.ports.crawl_planner",))


@pytest.mark.skipif(not _LLM_ADAPTER.exists(), reason="LlmCrawlPlanner lands in s2 step 4")
def test_adapters_planning_llm_crawl_planner_imports_allowlist() -> None:
    _check_allowlist(_LLM_ADAPTER, extra=(
        "pydantic",
        "veracrawl.ports.crawl_planner",
        "veracrawl.ports.model_provider_v2",
        "veracrawl.ports.prompt_registry",
        "veracrawl.ports.token_budget",
    ))


@pytest.mark.skipif(not _REPLAYING.exists(), reason="ReplayingModelProviderV2 lands in s2 step 3")
def test_adapters_model_providers_replaying_model_provider_imports_allowlist() -> None:
    _check_allowlist(_REPLAYING, extra=(
        "veracrawl.ports.model_provider_v2",
        # s2.1 step 4: replay-via-raw-response-ref reads bytes via
        # ``ArtifactStorePort.read``; legitimate port dependency.
        "veracrawl.ports.stores",
    ))


def test_external_crawl_runner_imports_crawl_planner_only_via_contracts_and_ports() -> None:
    # s3 lifts the s1/s2-era prohibition for two specific paths:
    # ``veracrawl.contracts.crawl_planner`` (typing) and
    # ``veracrawl.ports.crawl_planner`` (the port). Any other
    # ``crawl_planner`` import (e.g.
    # ``veracrawl.external_crawl.crawl_planner``, an adapter module,
    # or a relative form) is forbidden.
    allowed_prefixes = (
        "veracrawl.contracts.crawl_planner",
        "veracrawl.ports.crawl_planner",
    )
    for module in _imports(_RUNNER.read_text()):
        if module.startswith("."):
            pytest.fail(f"runner forbids relative imports: {module!r}")
        if module == "veracrawl.adapters" or module.startswith("veracrawl.adapters."):
            pytest.fail(f"runner must not import any adapter module: {module!r}")
        if "crawl_planner" in module:
            if not any(module == p or module.startswith(p + ".") for p in allowed_prefixes):
                pytest.fail(
                    f"runner must import crawl_planner only via "
                    f"veracrawl.contracts.crawl_planner or "
                    f"veracrawl.ports.crawl_planner; got {module!r}"
                )
