"""Import-boundary tests for s5 (tests 20-23)."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_CONTRACT = _REPO / "src/veracrawl/contracts/planner_observation_feedback.py"
_ADAPTER = _REPO / "src/veracrawl/adapters/planning/deterministic_crawl_planner_v2.py"
_RUNNER = _REPO / "src/veracrawl/external_crawl/runner.py"

STDLIB_ALLOWLIST = {
    "__future__", "typing", "collections.abc", "re",
    "hashlib", "urllib.parse",
    "pydantic",
}
SNAPSHOT_AND_EVENT_TYPES = {
    "GraphObservationSnapshot",
    "UrlObservedEvent", "RedirectObservedEvent",
    "CanonicalObservedEvent", "PageStructureObservedEvent",
    "derive_planner_observation_feedback",
}

_CONTRACT_ALLOWED_FROM = STDLIB_ALLOWLIST | {
    "veracrawl.contracts.common",
    "veracrawl.contracts.graph_observation",
}
_ADAPTER_ALLOWED_FROM = STDLIB_ALLOWLIST | {
    "veracrawl.contracts.common",
    "veracrawl.contracts.crawl_planner",
    "veracrawl.contracts.enums",
    "veracrawl.contracts.planner_observation_feedback",
    "veracrawl.ports.crawl_planner",
}
_ADAPTER_COMMON_NAMES = {"Ref", "VeraModel", "stable_hash"}
_ADAPTER_CRAWL_PLANNER_NAMES = {
    "PlanRequest", "PlannedSeed", "AdapterPrior",
    "FrontierPriorityHint", "PlanDecision",
}
_ADAPTER_ENUMS_NAMES = {"AdapterType", "FrontierMatchKind"}
_ADAPTER_FEEDBACK_NAMES = {"PlannerObservationFeedback"}


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def _is_type_checking_block(parents: list[ast.AST]) -> bool:
    for p in reversed(parents):
        if (
            isinstance(p, ast.If) and isinstance(p.test, ast.Name)
            and p.test.id == "TYPE_CHECKING"
        ):
            return True
    return False


def _walk_with_parents(node: ast.AST, parents: list[ast.AST]):  # type: ignore[no-untyped-def]
    yield node, list(parents)
    parents.append(node)
    for child in ast.iter_child_nodes(node):
        yield from _walk_with_parents(child, parents)
    parents.pop()


# Test 20
def test_contracts_planner_observation_feedback_imports_allowlist() -> None:
    tree = _parse(_CONTRACT)
    for node, parents in _walk_with_parents(tree, []):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"relative import not allowed: {ast.dump(node)}"
            module = node.module or ""
            if module == "veracrawl.contracts.graph_observation":
                assert _is_type_checking_block(parents), (
                    "graph_observation must be imported only under TYPE_CHECKING"
                )
            assert module in _CONTRACT_ALLOWED_FROM, (
                f"contract ImportFrom not in allowlist: {module}"
            )
            if module == "veracrawl.contracts.common":
                for alias in node.names:
                    assert alias.name in {"Ref", "VeraModel", "stable_hash"}, (
                        f"contract imports {alias.name} from contracts.common — "
                        "only Ref/VeraModel/stable_hash allowed"
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name in STDLIB_ALLOWLIST, (
                    f"contract Import not in stdlib/pydantic allowlist: {alias.name}"
                )


# Test 21
def test_adapters_planning_deterministic_crawl_planner_v2_imports_allowlist() -> None:
    tree = _parse(_ADAPTER)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"relative import not allowed: {ast.dump(node)}"
            module = node.module or ""
            assert module in _ADAPTER_ALLOWED_FROM, (
                f"adapter ImportFrom not in allowlist: {module}"
            )
            if module == "veracrawl.contracts.common":
                for alias in node.names:
                    assert alias.name in _ADAPTER_COMMON_NAMES, (
                        f"adapter imports {alias.name} from contracts.common — "
                        f"only {_ADAPTER_COMMON_NAMES} allowed"
                    )
            elif module == "veracrawl.contracts.crawl_planner":
                for alias in node.names:
                    assert alias.name in _ADAPTER_CRAWL_PLANNER_NAMES, (
                        f"adapter imports {alias.name} from contracts.crawl_planner"
                    )
            elif module == "veracrawl.contracts.enums":
                for alias in node.names:
                    assert alias.name in _ADAPTER_ENUMS_NAMES, (
                        f"adapter imports {alias.name} from contracts.enums"
                    )
            elif module == "veracrawl.contracts.planner_observation_feedback":
                for alias in node.names:
                    assert alias.name in _ADAPTER_FEEDBACK_NAMES, (
                        f"adapter imports {alias.name} from "
                        f"planner_observation_feedback — only "
                        f"{_ADAPTER_FEEDBACK_NAMES} allowed"
                    )
                    assert alias.name not in SNAPSHOT_AND_EVENT_TYPES, (
                        f"adapter must not import snapshot/event type: {alias.name}"
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("veracrawl"), (
                    f"adapter must not use bare `import veracrawl…`: {alias.name}"
                )
                assert alias.name in STDLIB_ALLOWLIST, (
                    f"adapter Import not in stdlib/pydantic allowlist: {alias.name}"
                )


# Test 22
def test_adapters_planning_v2_never_touches_snapshot_attribute() -> None:
    source = _ADAPTER.read_bytes()
    assert b"snapshot" not in source, (
        "adapter source must not contain the literal 'snapshot' "
        "(belt-and-suspenders against feedback.snapshot / "
        "getattr(_, 'snapshot') / model_dump()['snapshot'] access)"
    )
    tree = _parse(_ADAPTER)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr != "snapshot", (
                f"adapter must not access .snapshot: {ast.dump(node)}"
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
        ):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and arg.value == "snapshot":
                    raise AssertionError(
                        f"adapter must not call getattr(_, 'snapshot'): {ast.dump(node)}",
                    )


# Test 23 — superseded by s6 runner import-boundary tests
# (tests/contract/test_runner_graph_observation_import_boundaries.py).
# The s5 guard `runner does not import planner_observation_feedback`
# was a "no wiring yet" check; s6 explicitly wires the import.
# DeterministicCrawlPlannerV2 must still NOT be imported by the runner
# (the s6 wiring goes through the feedback_aware_planner_factory closure,
# not direct adapter import). Pin only that invariant here.
def test_external_crawl_runner_does_not_import_deterministic_crawl_planner_v2() -> None:
    source = _RUNNER.read_text()
    assert "DeterministicCrawlPlannerV2" not in source, (
        "runner must not import DeterministicCrawlPlannerV2 — wire it via "
        "feedback_aware_planner_factory closure instead"
    )
