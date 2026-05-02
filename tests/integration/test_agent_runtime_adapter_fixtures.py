from __future__ import annotations

from pathlib import Path

from tests.helpers.agent_runtime_adapter_fixture_assertions import (
    assert_agent_adapter_needs_review,
    assert_agent_adapter_negative,
    assert_agent_adapter_success,
)
from veracrawl.cli.agent_adapters import run_fixture
from veracrawl.contracts.enums import AgentAdapterFailureType


def test_agent_runtime_adapter_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "agent-runtime-adapter-success",
        profile="target",
        out=tmp_path / "agent-runtime-adapter-success",
    )
    assert_agent_adapter_success(report)


def test_agent_runtime_adapter_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "agent-runtime-adapter-runtime-unavailable",
        profile="target",
        out=tmp_path / "agent-runtime-adapter-runtime-unavailable",
    )
    assert_agent_adapter_needs_review(report)


def test_agent_runtime_adapter_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "agent-runtime-adapter-raw-prompt-leak": (
            AgentAdapterFailureType.RAW_PROMPT_LEAK.value,
            "raw_prompt_leak_refs",
        ),
        "agent-runtime-adapter-framework-state-canonical": (
            AgentAdapterFailureType.FRAMEWORK_STATE_CANONICAL.value,
            "framework_state_canonical_refs",
        ),
        "agent-runtime-adapter-missing-model-trace": (
            AgentAdapterFailureType.MISSING_MODEL_TRACE.value,
            "model_call_trace_refs",
        ),
        "agent-runtime-adapter-missing-tool-trace": (
            AgentAdapterFailureType.MISSING_TOOL_TRACE.value,
            "tool_call_trace_refs",
        ),
        "agent-runtime-adapter-missing-replay": (
            AgentAdapterFailureType.MISSING_REPLAY_REFS.value,
            "replay_bundle_ref",
        ),
        "agent-runtime-adapter-missing-security-privacy": (
            AgentAdapterFailureType.MISSING_SECURITY_PRIVACY_REFS.value,
            "security_privacy_report_refs",
        ),
        "agent-runtime-adapter-unsupported-framework": (
            AgentAdapterFailureType.UNSUPPORTED_FRAMEWORK.value,
            "unsupported_framework_refs",
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, (operator_status, missing_field) in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_agent_adapter_negative(
            report,
            operator_status=operator_status,
            missing_field=missing_field,
        )
