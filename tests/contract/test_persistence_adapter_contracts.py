from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    PersistenceAdapterConformanceFailureType,
    PersistenceAdapterKind,
    PersistenceMigrationStatus,
)
from veracrawl.contracts.persistence import (
    PersistenceAdapterConformanceReport,
    PersistenceAdapterFixtureManifest,
    PersistenceMigrationRecord,
)


def test_applied_migration_requires_validation_refs() -> None:
    with pytest.raises(ValidationError):
        PersistenceMigrationRecord(
            id="persistence-migration:bad",
            adapter_ref="persistence-adapter:sqlite",
            migration_name="001_bad",
            from_version="0",
            to_version="1",
            status=PersistenceMigrationStatus.APPLIED,
        )


def test_failed_migration_requires_failure_refs() -> None:
    with pytest.raises(ValidationError):
        PersistenceMigrationRecord(
            id="persistence-migration:bad-failure",
            adapter_ref="persistence-adapter:sqlite",
            migration_name="001_bad",
            from_version="0",
            to_version="1",
            status=PersistenceMigrationStatus.FAILED,
        )


def test_pass_conformance_report_requires_operational_refs() -> None:
    with pytest.raises(ValidationError):
        PersistenceAdapterConformanceReport(
            id="persistence-adapter-conformance-report:bad",
            adapter_ref="persistence-adapter:sqlite",
            adapter_kind=PersistenceAdapterKind.SQLITE,
            operator_status="sqlite_adapter_conformance_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_postgres_contract_report_cannot_claim_operational_pass() -> None:
    report = PersistenceAdapterConformanceReport(
        id="persistence-adapter-conformance-report:postgres",
        adapter_ref="persistence-adapter:postgres-contract",
        adapter_kind=PersistenceAdapterKind.POSTGRES_CONTRACT,
        contract_only_refs=["contract:postgres:ports"],
        operator_status="postgres_contract_declared",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    with pytest.raises(ValidationError):
        PersistenceAdapterConformanceReport(
            id="persistence-adapter-conformance-report:postgres-bad",
            adapter_ref="persistence-adapter:postgres-contract",
            adapter_kind=PersistenceAdapterKind.POSTGRES_CONTRACT,
            operator_status="postgres_contract_declared",
            completion_result=CompletenessResult.NEEDS_REVIEW,
        )


def test_negative_adapter_fixture_requires_failure_type() -> None:
    with pytest.raises(ValidationError):
        PersistenceAdapterFixtureManifest(
            id="sqlite-idempotency-gap",
            scenario="sqlite-idempotency-gap",
            profile_refs=["target"],
            expected_completion_result="fail",
            expected_operator_status="sqlite_idempotency_gap",
            negative_case=True,
        )
    manifest = PersistenceAdapterFixtureManifest(
        id="sqlite-idempotency-gap",
        scenario="sqlite-idempotency-gap",
        profile_refs=["target"],
        expected_completion_result="fail",
        expected_operator_status="sqlite_idempotency_gap",
        expected_failure_type=PersistenceAdapterConformanceFailureType.SQLITE_IDEMPOTENCY_GAP,
        negative_case=True,
    )
    assert manifest.expected_failure_type == (
        PersistenceAdapterConformanceFailureType.SQLITE_IDEMPOTENCY_GAP
    )
