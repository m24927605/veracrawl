from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.agent_model_runtime import run_fixture
from veracrawl.contracts.enums import CompletenessResult

FIXTURES = [
    ("agent-model-adapter-local-runtime-success", CompletenessResult.PASS),
    ("agent-model-adapter-runtime-unavailable", CompletenessResult.NEEDS_REVIEW),
    ("agent-model-adapter-missing-run-control", CompletenessResult.FAIL),
    ("agent-model-adapter-missing-live-normalization", CompletenessResult.FAIL),
    ("agent-model-adapter-missing-schema-extraction", CompletenessResult.FAIL),
    ("agent-model-adapter-unsupported-provider", CompletenessResult.FAIL),
    ("agent-model-adapter-unsupported-framework", CompletenessResult.FAIL),
    ("agent-model-adapter-raw-prompt-leak", CompletenessResult.FAIL),
    ("agent-model-adapter-raw-response-leak", CompletenessResult.FAIL),
    ("agent-model-adapter-raw-credential-leak", CompletenessResult.FAIL),
    ("agent-model-adapter-framework-state-canonical", CompletenessResult.FAIL),
    ("agent-model-adapter-provider-transcript-canonical", CompletenessResult.FAIL),
    ("agent-model-adapter-missing-model-trace", CompletenessResult.FAIL),
    ("agent-model-adapter-missing-tool-trace", CompletenessResult.FAIL),
    ("agent-model-adapter-missing-replay", CompletenessResult.FAIL),
    ("agent-model-adapter-core-import-boundary", CompletenessResult.FAIL),
]


@pytest.mark.parametrize(("fixture_id", "expected"), FIXTURES)
def test_agent_model_adapter_runtime_fixture(
    fixture_id: str,
    expected: CompletenessResult,
    tmp_path: Path,
) -> None:
    result = run_fixture(
        Path("tests/fixtures") / fixture_id,
        profile="target",
        out=tmp_path / fixture_id,
    )
    assert result.report.completion_result == expected
    assert (tmp_path / fixture_id / "run_report.json").exists()
    if expected == CompletenessResult.PASS:
        assert result.report.model_call_trace_refs
        assert result.report.tool_call_trace_refs
        assert result.report.replay_bundle_ref
