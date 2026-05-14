"""s6 import-boundary tests (tests 18, 19, 22)."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_RUNNER = _REPO / "src/veracrawl/external_crawl/runner.py"
_CLOCK = _REPO / "src/veracrawl/adapters/clocks/replaying_utc_clock.py"


_CLOCK_STDLIB_ALLOWLIST = {"__future__", "typing", "datetime", "collections.abc"}


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


# Test 18
def test_runner_imports_no_veracrawl_adapters() -> None:
    tree = _parse(_RUNNER)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"relative import not allowed: {ast.dump(node)}"
            module = node.module or ""
            assert module != "veracrawl.adapters", (
                f"runner ImportFrom rejects bare veracrawl.adapters: {ast.dump(node)}"
            )
            assert not module.startswith("veracrawl.adapters."), (
                f"runner ImportFrom rejects veracrawl.adapters.*: {module}"
            )
            if module == "veracrawl":
                for alias in node.names:
                    assert alias.name != "adapters", (
                        f"runner rejects 'from veracrawl import adapters': {ast.dump(node)}"
                    )
                raise AssertionError(
                    f"runner must not do bare `from veracrawl import …`: {ast.dump(node)}",
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "veracrawl.adapters", (
                    f"runner rejects `import veracrawl.adapters`: {alias.name}"
                )
                assert not alias.name.startswith("veracrawl.adapters."), (
                    f"runner rejects `import veracrawl.adapters.*`: {alias.name}"
                )


# Test 19
def test_runner_imports_graph_observation_port_and_feedback_contract() -> None:
    tree = _parse(_RUNNER)
    imports_seen: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imports_seen.add(f"{node.module}.{alias.name}")
    assert "veracrawl.ports.graph_observation.GraphObservationPort" in imports_seen, (
        "runner must import GraphObservationPort from veracrawl.ports.graph_observation"
    )
    feedback_imports = {
        i for i in imports_seen
        if i.startswith("veracrawl.contracts.planner_observation_feedback.")
    }
    assert feedback_imports, (
        "runner must import at least one symbol from "
        "veracrawl.contracts.planner_observation_feedback"
    )


# Test 22 — the clock adapter must be stdlib-only.
def test_replaying_utc_clock_import_boundaries() -> None:
    tree = _parse(_CLOCK)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"relative import not allowed: {ast.dump(node)}"
            module = node.module or ""
            assert not module.startswith("veracrawl"), (
                f"replaying_utc_clock must not import veracrawl.*: {module}"
            )
            assert module in _CLOCK_STDLIB_ALLOWLIST, (
                f"replaying_utc_clock ImportFrom not in stdlib allowlist: {module}"
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("veracrawl"), (
                    f"replaying_utc_clock must not import veracrawl.*: {alias.name}"
                )
                assert alias.name in _CLOCK_STDLIB_ALLOWLIST, (
                    f"replaying_utc_clock Import not in stdlib allowlist: {alias.name}"
                )
