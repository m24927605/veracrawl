from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_runtime_registry_is_complete_and_valid() -> None:
    report = validate_registry()
    assert report.ok, report.errors
    for contract in [
        "CrawlObjective",
        "CrawlPlan",
        "CrawlRun",
        "RunPlanSnapshot",
        "RuntimeCompletionGate",
        "RuntimeArtifactRef",
        "NormalizedDocument",
        "ExtractionCandidate",
        "EvidenceCoverageResult",
        "EvidencePacket",
        "VerificationDecision",
        "OutputManifest",
        "PublishedOutput",
        "AgentRecommendation",
    ]:
        assert contract in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[contract].test_refs


def test_runtime_owner_command_and_event_taxonomy_is_registered() -> None:
    expected_commands = {
        "record_source_adapter_result": "FETCH",
        "record_normalized_document": "NORMALIZE",
        "record_extraction_candidate": "EXTRACT",
        "build_evidence_packet": "EVIDENCE",
        "record_verification_decision": "VERIFY",
        "publish_output_manifest": "PUBLISH",
        "record_replay_bundle": "REVIEW_REPLAY",
        "accept_agent_recommendation": "AGENTS",
    }
    for command_name, owner in expected_commands.items():
        command = COMMAND_TYPES[command_name]
        assert command.owner_service.name == owner
        assert command.payload_schema_ref in FOUNDATION_CONTRACTS
        for event_type in command.emitted_event_types:
            assert event_type in EVENT_TYPES


def test_runtime_fixtures_are_registered_with_replay_oracles() -> None:
    expected = {
        "runtime-record-success": False,
        "runtime-blocked-source": True,
        "runtime-missing-evidence": True,
        "runtime-verification-conflict": True,
        "runtime-adapter-mismatch": True,
        "runtime-replay-gap": True,
        "runtime-boundary-violation": True,
    }
    for fixture_id, negative in expected.items():
        fixture = FIXTURE_ORACLES[fixture_id]
        assert fixture.negative_case is negative
        assert fixture.manifest_ref.endswith("manifest.yaml")
        assert fixture.expected_replay_ref


def test_runtime_materialized_target_areas_are_explicit() -> None:
    for area in ["evidence", "verification", "publication", "artifact_lifecycle"]:
        registration = TARGET_CONTRACT_AREAS[area]
        assert registration.coverage_status == "materialized"
        assert registration.materialized_contract_refs
        assert registration.followup_spec_gate is None
