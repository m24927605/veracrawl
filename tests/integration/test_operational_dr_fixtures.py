from __future__ import annotations

from pathlib import Path

from tests.helpers.dr_fixture_assertions import (
    assert_dr_negative,
    assert_dr_runtime_unavailable,
)
from veracrawl.cli.dr import run_fixture
from veracrawl.contracts.enums import DRRestoreFailureType


def test_operational_dr_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "dr-restore-runtime-unavailable",
        profile="target",
        out=tmp_path / "dr-restore-runtime-unavailable",
    )
    assert_dr_runtime_unavailable(report)


def test_operational_dr_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "dr-restore-missing-metadata": (
            DRRestoreFailureType.MISSING_METADATA_RESTORE_REFS.value,
            "metadata_restore_ref",
        ),
        "dr-restore-missing-artifact-reachability": (
            DRRestoreFailureType.MISSING_ARTIFACT_REACHABILITY_REFS.value,
            "artifact_reachability_report_ref",
        ),
        "dr-restore-missing-event-replay": (
            DRRestoreFailureType.MISSING_EVENT_REPLAY_REFS.value,
            "event_replay_report_ref",
        ),
        "dr-restore-missing-projection-rebuild": (
            DRRestoreFailureType.MISSING_PROJECTION_REBUILD_REFS.value,
            "projection_rebuild_job_refs",
        ),
        "dr-restore-missing-export-reconciliation": (
            DRRestoreFailureType.MISSING_EXPORT_RECONCILIATION_REFS.value,
            "export_reconciliation_refs",
        ),
        "dr-restore-unresolved-refs": (
            DRRestoreFailureType.UNRESOLVED_REFS.value,
            "unresolved_refs",
        ),
        "dr-restore-data-loss": (
            DRRestoreFailureType.DATA_LOSS_DETECTED.value,
            "data_loss_detected",
        ),
        "dr-restore-unsafe-recovery-without-approval": (
            DRRestoreFailureType.UNSAFE_RECOVERY_WITHOUT_APPROVAL.value,
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
        assert_dr_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
