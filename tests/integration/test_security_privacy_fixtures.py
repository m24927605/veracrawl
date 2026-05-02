from __future__ import annotations

from pathlib import Path

from tests.helpers.security_privacy_fixture_assertions import (
    assert_security_privacy_needs_review,
    assert_security_privacy_negative,
    assert_security_privacy_success,
)
from veracrawl.cli.security_privacy import run_fixture
from veracrawl.contracts.enums import SecurityPrivacyFailureType


def test_security_privacy_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "security-privacy-success",
        profile="target",
        out=tmp_path / "security-privacy-success",
    )
    assert_security_privacy_success(report)


def test_security_privacy_policy_only_fixture_needs_review(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "security-privacy-policy-only",
        profile="target",
        out=tmp_path / "security-privacy-policy-only",
    )
    assert_security_privacy_needs_review(
        report,
        operator_status="security_privacy_policy_only",
    )


def test_security_privacy_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "security-privacy-unsafe-network": (
            SecurityPrivacyFailureType.UNSAFE_NETWORK.value,
            "security_policy_check_refs",
        ),
        "security-privacy-prompt-injection": (
            SecurityPrivacyFailureType.PROMPT_INJECTION_TOOL_MISUSE.value,
            "prompt_taint_boundary_refs",
        ),
        "security-privacy-credential-leakage": (
            SecurityPrivacyFailureType.CREDENTIAL_LEAKAGE.value,
            "raw_secret_leak_refs",
        ),
        "security-privacy-missing-lifecycle": (
            SecurityPrivacyFailureType.MISSING_LIFECYCLE_PROPAGATION.value,
            "artifact_lifecycle_action_refs",
        ),
        "security-privacy-legal-hold-delete": (
            SecurityPrivacyFailureType.LEGAL_HOLD_DELETE.value,
            "legal_hold_violation_refs",
        ),
        "security-privacy-missing-projection-cleanup": (
            SecurityPrivacyFailureType.MISSING_PROJECTION_CLEANUP.value,
            "projection_cleanup_refs",
        ),
        "security-privacy-missing-redacted-replay": (
            SecurityPrivacyFailureType.MISSING_REDACTED_REPLAY.value,
            "redacted_replay_refs",
        ),
        "security-privacy-missing-observability": (
            SecurityPrivacyFailureType.MISSING_OBSERVABILITY_REFS.value,
            "observability_report_refs",
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, missing_field) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_security_privacy_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
