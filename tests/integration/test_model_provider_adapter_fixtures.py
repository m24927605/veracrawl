from __future__ import annotations

from pathlib import Path

from tests.helpers.model_provider_adapter_fixture_assertions import (
    assert_model_provider_adapter_needs_review,
    assert_model_provider_adapter_negative,
    assert_model_provider_adapter_success,
)
from veracrawl.cli.model_providers import run_fixture
from veracrawl.contracts.enums import ModelProviderAdapterFailureType


def test_model_provider_adapter_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "model-provider-adapter-success",
        profile="target",
        out=tmp_path / "model-provider-adapter-success",
    )
    assert_model_provider_adapter_success(report)


def test_model_provider_adapter_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "model-provider-adapter-runtime-unavailable",
        profile="target",
        out=tmp_path / "model-provider-adapter-runtime-unavailable",
    )
    assert_model_provider_adapter_needs_review(report)


def test_model_provider_adapter_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "model-provider-adapter-raw-prompt-leak": (
            ModelProviderAdapterFailureType.RAW_PROMPT_LEAK.value,
            "raw_prompt_leak_refs",
        ),
        "model-provider-adapter-raw-response-leak": (
            ModelProviderAdapterFailureType.RAW_RESPONSE_LEAK.value,
            "raw_response_leak_refs",
        ),
        "model-provider-adapter-provider-state-canonical": (
            ModelProviderAdapterFailureType.PROVIDER_TRANSCRIPT_CANONICAL.value,
            "provider_transcript_canonical_refs",
        ),
        "model-provider-adapter-missing-context-trace": (
            ModelProviderAdapterFailureType.MISSING_CONTEXT_TRACE.value,
            "context_bundle_trace_refs",
        ),
        "model-provider-adapter-missing-replay": (
            ModelProviderAdapterFailureType.MISSING_REPLAY_REFS.value,
            "replay_bundle_ref",
        ),
        "model-provider-adapter-missing-security-privacy": (
            ModelProviderAdapterFailureType.MISSING_SECURITY_PRIVACY_REFS.value,
            "security_privacy_report_refs",
        ),
        "model-provider-adapter-unsafe-tool-suggestion": (
            ModelProviderAdapterFailureType.UNSAFE_TOOL_SUGGESTION.value,
            "unsafe_tool_suggestion_refs",
        ),
        "model-provider-adapter-unsupported-provider": (
            ModelProviderAdapterFailureType.UNSUPPORTED_PROVIDER.value,
            "unsupported_provider_refs",
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, missing_field) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_model_provider_adapter_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
