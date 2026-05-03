from __future__ import annotations

from pathlib import Path

from tests.helpers.source_coverage_fixture_assertions import (
    assert_source_coverage_needs_review,
    assert_source_coverage_negative,
    assert_source_coverage_success,
)
from veracrawl.cli.source_coverage import run_fixture
from veracrawl.contracts.enums import SourceCoverageFailureType


def test_source_coverage_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "source-coverage-adapter-success",
        profile="target",
        out=tmp_path / "source-coverage-adapter-success",
    )
    assert_source_coverage_success(report)


def test_source_coverage_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "source-coverage-adapter-runtime-unavailable",
        profile="target",
        out=tmp_path / "source-coverage-adapter-runtime-unavailable",
    )
    assert_source_coverage_needs_review(report)


def test_source_coverage_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "source-coverage-adapter-native-state-canonical": (
            SourceCoverageFailureType.ADAPTER_NATIVE_STATE_CANONICAL.value,
            "adapter_native_state_canonical_refs",
        ),
        "source-coverage-adapter-raw-secret-leak": (
            SourceCoverageFailureType.RAW_SECRET_LEAK.value,
            "raw_secret_leak_refs",
        ),
        "source-coverage-adapter-missing-browser-refs": (
            SourceCoverageFailureType.MISSING_BROWSER_REFS.value,
            "browser_interaction_refs",
        ),
        "source-coverage-adapter-missing-credential-audit": (
            SourceCoverageFailureType.MISSING_CREDENTIAL_AUDIT.value,
            "credential_audit_refs",
        ),
        "source-coverage-adapter-missing-document-artifact": (
            SourceCoverageFailureType.MISSING_DOCUMENT_ARTIFACT.value,
            "document_artifact_refs",
        ),
        "source-coverage-adapter-missing-api-payload": (
            SourceCoverageFailureType.MISSING_API_PAYLOAD.value,
            "api_payload_refs",
        ),
        "source-coverage-adapter-missing-replay": (
            SourceCoverageFailureType.MISSING_REPLAY_REFS.value,
            "replay_bundle_ref",
        ),
        "source-coverage-adapter-unsafe-browser-side-effect": (
            SourceCoverageFailureType.UNSAFE_BROWSER_SIDE_EFFECT.value,
            "unsafe_browser_side_effect_refs",
        ),
        "source-coverage-adapter-unsupported-adapter": (
            SourceCoverageFailureType.UNSUPPORTED_ADAPTER.value,
            "unsupported_adapter_refs",
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, missing_field) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_source_coverage_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
