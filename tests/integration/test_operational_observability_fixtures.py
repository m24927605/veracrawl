from __future__ import annotations

from pathlib import Path

from tests.helpers.observability_fixture_assertions import (
    assert_observability_needs_review,
    assert_observability_negative,
    assert_observability_success,
)
from veracrawl.cli.observability import run_fixture
from veracrawl.contracts.enums import ObservabilityFailureType


def test_operational_observability_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "observability-success",
        profile="target",
        telemetry_backend_ref="telemetry-backend:test",
        collector_handoff_ref="collector-handoff:test",
        out=tmp_path / "observability-success",
    )
    assert_observability_success(report)


def test_operational_observability_needs_review_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    expectations = {
        "observability-runtime-unavailable": "observability_runtime_unavailable",
        "observability-data-surface-only": "observability_data_surface_only",
    }
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_observability_needs_review(report, operator_status=operator_status)


def test_operational_observability_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "observability-missing-metrics": (
            ObservabilityFailureType.MISSING_METRIC_REFS.value,
            "metric_sample_refs",
        ),
        "observability-missing-traces": (
            ObservabilityFailureType.MISSING_TRACE_REFS.value,
            "trace_span_refs",
        ),
        "observability-missing-alerts": (
            ObservabilityFailureType.MISSING_ALERT_REFS.value,
            "alert_record_refs",
        ),
        "observability-missing-runbook": (
            ObservabilityFailureType.MISSING_RUNBOOK_REFS.value,
            "runbook_action_refs",
        ),
        "observability-stale-dashboard-watermark": (
            ObservabilityFailureType.STALE_DASHBOARD_WATERMARK.value,
            "projection_watermark_refs",
        ),
        "observability-missing-dr-refs": (
            ObservabilityFailureType.MISSING_DR_REFS.value,
            "dr_restore_report_refs",
        ),
        "observability-missing-redaction": (
            ObservabilityFailureType.MISSING_REDACTION_REFS.value,
            "redaction_map_refs",
        ),
        "observability-missing-replay": (
            ObservabilityFailureType.MISSING_REPLAY_REFS.value,
            "replay_bundle_ref",
        ),
        "observability-secret-leak": (
            ObservabilityFailureType.SECRET_LEAK_DETECTED.value,
            "unredacted_sensitive_fields",
        ),
        "observability-unsafe-runbook-without-approval": (
            ObservabilityFailureType.UNSAFE_RUNBOOK_WITHOUT_APPROVAL.value,
            "approval_decision_refs",
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, missing_field) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_observability_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
