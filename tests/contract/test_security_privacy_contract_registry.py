from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_security_privacy_contracts_are_registered() -> None:
    for name in [
        "SecurityPolicyCheck",
        "CredentialUseAudit",
        "PromptTaintBoundary",
        "ArtifactLifecycleAction",
        "ProjectionCleanupRecord",
        "SecurityPrivacyReport",
        "SecurityPrivacyFixtureManifest",
        "FailureRecord",
        "RecoveryAction",
        "ObservabilityReport",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_security_privacy_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_security_policy_check": "security_policy_check_recorded",
        "record_credential_use_audit": "credential_use_audited",
        "record_prompt_taint_boundary": "prompt_taint_boundary_recorded",
        "record_artifact_lifecycle_action": "artifact_lifecycle_action_recorded",
        "record_projection_cleanup": "projection_cleanup_recorded",
        "record_security_privacy_report": "security_privacy_reported",
        "record_security_privacy_fixture_manifest": (
            "security_privacy_fixture_manifest_recorded"
        ),
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "security-privacy-success",
        "security-privacy-policy-only",
        "security-privacy-unsafe-network",
        "security-privacy-prompt-injection",
        "security-privacy-credential-leakage",
        "security-privacy-missing-lifecycle",
        "security-privacy-legal-hold-delete",
        "security-privacy-missing-projection-cleanup",
        "security-privacy-missing-redacted-replay",
        "security-privacy-missing-observability",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_security_privacy_ref


def test_security_privacy_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["security_privacy_lifecycle_gate"]
    assert area.owner_service == OwnerService.POLICY
    assert area.coverage_status == "materialized"
    assert "SecurityPrivacyReport" in area.materialized_contract_refs
    assert "ObservabilityReport" in area.materialized_contract_refs
    assert not area.placeholder_contract_refs
