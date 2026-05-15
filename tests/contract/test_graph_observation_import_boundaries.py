"""Import-boundary tests for s4 ``GraphObservationPort`` (tests 18-20)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_PORT = _ROOT / "ports" / "graph_observation.py"
_ADAPTER = _ROOT / "adapters" / "graph" / "in_memory_graph_observer.py"
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


def test_ports_graph_observation_imports_only_contracts_and_stdlib() -> None:
    _check_allowlist(_PORT, extra=())


def test_adapters_graph_in_memory_graph_observer_imports_allowlist() -> None:
    _check_allowlist(_ADAPTER, extra=("veracrawl.ports.graph_observation",))


def test_external_crawl_runner_imports_graph_observation_via_port_and_contracts() -> None:
    """s6 has shipped (the runner wires GraphObservationPort + the
    event contracts). This test inverts the s4-era prohibition:
    instead of refusing graph_observation imports, it now requires
    them — the s6 wiring is the binding state.
    """

    modules = list(_imports(_RUNNER.read_text()))
    has_port_import = any(
        m == "veracrawl.ports.graph_observation"
        or m.startswith("veracrawl.ports.graph_observation.")
        for m in modules
    )
    has_contract_import = any(
        m.startswith("veracrawl.contracts.graph_observation.")
        for m in modules
    )
    assert has_port_import, (
        "runner must import GraphObservationPort from "
        "veracrawl.ports.graph_observation (s6 wiring)"
    )
    assert has_contract_import, (
        "runner must import s6 event contracts from "
        "veracrawl.contracts.graph_observation"
    )
