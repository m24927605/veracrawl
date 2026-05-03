from __future__ import annotations

from pathlib import Path

from tests.helpers.dynamic_source_runtime_fixture_assertions import (
    assert_dynamic_source_runtime_needs_review,
    assert_dynamic_source_runtime_negative,
    assert_dynamic_source_runtime_success,
)
from veracrawl.cli.source_runtime import run_fixture
from veracrawl.contracts.enums import DynamicSourceRuntimeFailureType


def test_dynamic_source_runtime_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "dynamic-source-runtime-success",
        profile="target",
        out=tmp_path / "dynamic-source-runtime-success",
    )
    assert_dynamic_source_runtime_success(report)


def test_dynamic_source_runtime_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "dynamic-source-runtime-runtime-unavailable",
        profile="target",
        out=tmp_path / "dynamic-source-runtime-runtime-unavailable",
    )
    assert_dynamic_source_runtime_needs_review(report)


def test_dynamic_source_runtime_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "dynamic-source-runtime-raw-secret-leak": (
            DynamicSourceRuntimeFailureType.RAW_SECRET_LEAK.value,
            "raw_secret_leak_refs",
        ),
        "dynamic-source-runtime-adapter-state-canonical": (
            DynamicSourceRuntimeFailureType.ADAPTER_NATIVE_STATE_CANONICAL.value,
            "adapter_native_state_canonical_refs",
        ),
        "dynamic-source-runtime-missing-credential-audit": (
            DynamicSourceRuntimeFailureType.MISSING_CREDENTIAL_AUDIT.value,
            "credential_audit_refs",
        ),
        "dynamic-source-runtime-missing-document-artifact": (
            DynamicSourceRuntimeFailureType.MISSING_DOCUMENT_ARTIFACT.value,
            "document_artifact_refs",
        ),
        "dynamic-source-runtime-missing-api-payload": (
            DynamicSourceRuntimeFailureType.MISSING_API_PAYLOAD.value,
            "api_payload_refs",
        ),
        "dynamic-source-runtime-missing-replay": (
            DynamicSourceRuntimeFailureType.MISSING_REPLAY_REFS.value,
            "replay_bundle_ref",
        ),
        "dynamic-source-runtime-unsafe-browser-side-effect": (
            DynamicSourceRuntimeFailureType.UNSAFE_BROWSER_SIDE_EFFECT.value,
            "unsafe_browser_side_effect_refs",
        ),
        "dynamic-source-runtime-unsupported-adapter": (
            DynamicSourceRuntimeFailureType.UNSUPPORTED_ADAPTER.value,
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
        assert_dynamic_source_runtime_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
