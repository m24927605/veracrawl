from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import RuntimeCompletionGateType, RuntimeGateStatus
from veracrawl.contracts.objective import RuntimeCompletionGate
from veracrawl.control.runtime import evaluate_completion_gate


def test_completion_gate_passes_when_required_refs_are_present() -> None:
    gate = evaluate_completion_gate(
        gate_id="gate:pass",
        run_ref="run:1",
        gate_type=RuntimeCompletionGateType.PUBLICATION,
        required_refs={"output_manifest_ref": "output:1", "replay_manifest_ref": "replay:1"},
    )
    assert gate.status == RuntimeGateStatus.PASS
    assert gate.missing_ref_fields == []


def test_completion_gate_fails_when_required_refs_are_missing() -> None:
    gate = evaluate_completion_gate(
        gate_id="gate:fail",
        run_ref="run:1",
        gate_type=RuntimeCompletionGateType.EVIDENCE,
        required_refs={"evidence_packet_ref": None, "coverage_ref": ""},
    )
    assert gate.status == RuntimeGateStatus.FAIL
    assert set(gate.missing_ref_fields) == {"evidence_packet_ref", "coverage_ref"}


def test_non_pass_gate_requires_reason_or_missing_refs() -> None:
    with pytest.raises(ValidationError):
        RuntimeCompletionGate(
            id="gate:bad",
            run_ref="run:1",
            gate_type=RuntimeCompletionGateType.VERIFICATION,
            status=RuntimeGateStatus.CONFLICT,
        )
