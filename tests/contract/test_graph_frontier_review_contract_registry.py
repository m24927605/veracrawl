from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_graph_frontier_review_contracts_are_registered() -> None:
    for name in [
        "GraphSignal",
        "FrontierItem",
        "ReviewItem",
        "GraphFrontierDecisionRecord",
        "GraphReviewRouteDecisionRecord",
        "GraphFrontierReviewRuntimeReport",
        "GraphFrontierReviewFixtureManifest",
        "CommandResult",
        "EventCursorRecord",
        "OutboxRecord",
        "ReplayBundleManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_graph_frontier_review_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_graph_frontier_decision": "graph_frontier_decision_recorded",
        "record_graph_review_route_decision": "graph_review_route_decision_recorded",
        "record_graph_frontier_review_report": "graph_frontier_review_reported",
        "record_graph_frontier_review_fixture_manifest": (
            "graph_frontier_review_fixture_manifest_recorded"
        ),
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "graph-frontier-review-success",
        "graph-frontier-review-runtime-unavailable",
        "graph-frontier-review-signal-as-evidence",
        "graph-frontier-review-missing-source-graph",
        "graph-frontier-review-missing-explanation",
        "graph-frontier-review-unauthorized-frontier-mutation",
        "graph-frontier-review-missing-review-route",
        "graph-frontier-review-missing-replay",
        "graph-frontier-review-unsupported-signal",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_graph_ref


def test_graph_frontier_review_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["graph_frontier_review_runtime_gate"]
    assert area.coverage_status == "materialized"
    assert "GraphFrontierDecisionRecord" in area.materialized_contract_refs
    assert "GraphReviewRouteDecisionRecord" in area.materialized_contract_refs
    assert "GraphFrontierReviewRuntimeReport" in area.materialized_contract_refs
