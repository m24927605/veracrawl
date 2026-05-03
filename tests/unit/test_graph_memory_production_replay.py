from __future__ import annotations

from veracrawl.graph_memory.runtime import run_graph_memory_production_runtime
from veracrawl.review_replay.graph_memory import (
    graph_memory_replay_passes,
    missing_graph_memory_replay_refs,
)


def test_graph_memory_replay_passes_for_complete_report() -> None:
    result = run_graph_memory_production_runtime(
        fixture_id="unit-replay",
        scenario="graph-memory-production-success",
    )
    assert graph_memory_replay_passes(result.report)
    assert not missing_graph_memory_replay_refs(result.report)


def test_graph_memory_replay_reports_missing_replay() -> None:
    result = run_graph_memory_production_runtime(
        fixture_id="unit-replay-missing",
        scenario="graph-memory-replay-mismatch",
    )
    assert not graph_memory_replay_passes(result.report)
    assert "replay_bundle_ref" in missing_graph_memory_replay_refs(result.report)


def test_graph_memory_replay_rejects_graph_or_memory_boundary_violations() -> None:
    graph = run_graph_memory_production_runtime(
        fixture_id="unit-replay-graph",
        scenario="graph-memory-graph-as-evidence",
    ).report
    memory = run_graph_memory_production_runtime(
        fixture_id="unit-replay-memory",
        scenario="graph-memory-memory-as-evidence",
    ).report
    assert not graph_memory_replay_passes(graph)
    assert not graph_memory_replay_passes(memory)
