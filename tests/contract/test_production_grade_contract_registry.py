from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_production_grade_contracts_registered() -> None:
    for name in {
        "ProductionSourceProfile",
        "CrawlBound",
        "ProductionGradeClosureManifest",
        "CrawlDiscoveryPlan",
        "DiscoveryEntryPoint",
        "CandidateSourceTarget",
        "DiscoveryApprovalDecision",
        "AcquisitionAttemptRecord",
        "AuthorizedSourceAccessRecord",
        "ProductionGateReport",
        "ReleaseBlocker",
        "FalseReadyGuard",
        "ProductionGradeCapabilityMatrix",
        "ReleaseDecision",
        "ProductionGradeReleaseReport",
    }:
        assert name in FOUNDATION_CONTRACTS


def test_production_grade_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_production_grade_closure_manifest": (
            "production_grade_closure_manifest_recorded"
        ),
        "record_crawl_discovery_plan": "crawl_discovery_plan_recorded",
        "record_discovery_entry_point": "discovery_entry_point_recorded",
        "record_candidate_source_target": "candidate_source_target_recorded",
        "record_discovery_approval_decision": (
            "discovery_approval_decision_recorded"
        ),
        "record_acquisition_attempt": "acquisition_attempt_recorded",
        "record_authorized_source_access": "authorized_source_access_recorded",
        "record_production_gate_report": "production_gate_report_recorded",
        "record_production_grade_capability_matrix": (
            "production_grade_capability_matrix_recorded"
        ),
        "record_false_ready_guard": "false_ready_guard_recorded",
        "record_release_blocker": "release_blocker_recorded",
        "record_release_decision": "release_decision_recorded",
        "record_production_grade_release_report": (
            "production_grade_release_report_recorded"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    fixture = FIXTURE_ORACLES["production-grade-release-ready"]
    assert fixture.expected_outputs_ref
    assert fixture.expected_replay_ref
    assert not fixture.negative_case
    assert not FIXTURE_ORACLES[
        "production-acquisition-escalation-live-evidence"
    ].negative_case
    assert not FIXTURE_ORACLES[
        "production-authorized-source-live-official-api"
    ].negative_case
    assert not FIXTURE_ORACLES[
        "production-extraction-quality-live-evidence"
    ].negative_case
    assert FIXTURE_ORACLES["production-grade-release-missing-gate"].negative_case


def test_production_grade_target_area_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["production_grade_web_crawler_release_gate"]
    assert "ProductionGateReport" in area.materialized_contract_refs
    assert "CrawlDiscoveryPlan" in area.materialized_contract_refs
    assert "ProductionGradeReleaseReport" in area.materialized_contract_refs
    assert "FalseReadyGuard" in area.materialized_contract_refs
    assert "ModelCallTrace" in area.materialized_contract_refs
    assert "ReplayBundleManifest" in area.materialized_contract_refs
    assert validate_registry().ok
