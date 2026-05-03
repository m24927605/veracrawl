from __future__ import annotations

from pathlib import Path

from tests.helpers.graph_memory_production_fixture_assertions import (
    assert_graph_memory_negative,
    assert_graph_memory_success,
)
from veracrawl.cli.graph_memory_runtime import run_fixture
from veracrawl.contracts.enums import GraphMemoryProductionFailureType


def test_graph_memory_success_fixtures(tmp_path: Path) -> None:
    expectations = {
        "graph-memory-production-success": "graph_memory_production_completed",
        "graph-memory-frontier-priority-success": (
            "graph_memory_frontier_priority_completed"
        ),
        "graph-memory-repair-explanation-success": (
            "graph_memory_repair_explanation_completed"
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_graph_memory_success(report, operator_status=operator_status)


def test_graph_memory_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "graph-memory-missing-live-normalization": (
            GraphMemoryProductionFailureType.MISSING_LIVE_NORMALIZATION
        ),
        "graph-memory-missing-live-evidence": (
            GraphMemoryProductionFailureType.MISSING_LIVE_EVIDENCE
        ),
        "graph-memory-missing-multi-agent": (
            GraphMemoryProductionFailureType.MISSING_MULTI_AGENT_REPAIR
        ),
        "graph-memory-graph-as-evidence": (
            GraphMemoryProductionFailureType.GRAPH_AS_EVIDENCE
        ),
        "graph-memory-memory-as-evidence": (
            GraphMemoryProductionFailureType.MEMORY_AS_EVIDENCE
        ),
        "graph-memory-stale-memory": GraphMemoryProductionFailureType.STALE_MEMORY_USED,
        "graph-memory-missing-invalidation": (
            GraphMemoryProductionFailureType.MISSING_INVALIDATION_REF
        ),
        "graph-memory-missing-frontier-explanation": (
            GraphMemoryProductionFailureType.MISSING_FRONTIER_EXPLANATION
        ),
        "graph-memory-replay-mismatch": GraphMemoryProductionFailureType.REPLAY_MISMATCH,
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, failure in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_graph_memory_negative(
            report,
            operator_status=failure.value,
            failure_type=failure.value,
        )
