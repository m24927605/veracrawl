"""Import-boundary tests for s12 replay wiring."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_RUNNER = _ROOT / "external_crawl" / "runner.py"
_FETCHER = _ROOT / "adapters" / "network" / "replaying_http_fetcher.py"
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


def test_runner_imports_replay_consumer_port_only() -> None:
    """Runner must consume replay via the port, not the in-memory adapter."""

    found_port = False
    for module in _imports(_RUNNER.read_text()):
        if "replay_consumer" in module:
            assert "veracrawl.ports.replay_consumer" in module, (
                f"runner must reference replay via the port; found {module!r}"
            )
            found_port = True
        assert not module.startswith("veracrawl.adapters.replay"), (
            f"runner must not import replay adapter; found {module!r}"
        )
    assert found_port, "runner must import ReplayConsumerPort"


def test_replaying_http_fetcher_imports_allowlist() -> None:
    for module in _imports(_FETCHER.read_text()):
        if module.startswith("."):
            pytest.fail(f"{_FETCHER.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        if module.startswith("veracrawl.ports.crawl_http_fetcher"):
            continue
        pytest.fail(f"{_FETCHER.name} imports forbidden module: {module!r}")
