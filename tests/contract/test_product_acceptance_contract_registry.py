from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_product_acceptance_contracts_are_registered() -> None:
    expected = {
        "ProductWorkflowReadinessRecord",
        "ProductAcceptanceGateReport",
        "ProductAcceptanceFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    for contract in expected:
        assert FOUNDATION_CONTRACTS[contract].test_refs


def test_product_acceptance_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_product_workflow_readiness": "product_workflow_readiness_recorded",
        "record_product_acceptance_gate_report": "product_acceptance_gate_reported",
        "record_product_acceptance_fixture_manifest": (
            "product_acceptance_fixture_manifest_recorded"
        ),
    }
    for command, event in expected_commands.items():
        assert command in COMMAND_TYPES
        assert event in COMMAND_TYPES[command].emitted_event_types
        assert event in EVENT_TYPES

    expected_fixtures = {
        "product-acceptance-success",
        "product-acceptance-runtime-unavailable",
        "product-acceptance-missing-workflow",
        "product-acceptance-missing-minimum-gate",
        "product-acceptance-missing-evidence",
        "product-acceptance-missing-replay",
        "product-acceptance-missing-operator-visibility",
        "product-acceptance-missing-policy",
        "product-acceptance-missing-workflow-specific-refs",
        "product-acceptance-scaffold-only",
        "product-acceptance-contract-only",
        "product-acceptance-false-complete-status",
        "product-acceptance-degraded-operational",
        "product-acceptance-missing-export-reconciliation",
    }
    assert expected_fixtures.issubset(FIXTURE_ORACLES)


def test_product_acceptance_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["product_acceptance_gate"]
    assert area.coverage_status == "materialized"
    assert "ProductWorkflowReadinessRecord" in area.materialized_contract_refs
    assert "ProductAcceptanceGateReport" in area.materialized_contract_refs
    assert "ProductAcceptanceFixtureManifest" in area.materialized_contract_refs
    assert "ReplayBundleManifest" in area.materialized_contract_refs
