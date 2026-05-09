"""Phase 3 step 3.3 — source_coverage_gate evaluative-role boundary test.

Per phase-3-design.md acceptance: ``source_coverage_gate``
no longer references the classifier or escalator modules
(mechanical: import-graph check). This test enforces the
boundary so a future refactor can't accidentally fold
classifier / escalator responsibilities into the
source-coverage evaluator.

The source-coverage gate's job is *evaluating* whether a
run met its coverage goal — counting expected vs actual
fetches, recording missed targets — NOT deciding which
adapter to escalate to or which access-control protection
is in front of a URL. Those are Phase 3 step 3.1 / 3.2's
jobs and live in their own modules.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_SOURCE_COVERAGE_GATE = _SRC / "fetch" / "source_coverage_gate.py"

# Modules that source_coverage_gate must NOT import — these
# carry the classifier / escalator responsibility.
_FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "veracrawl.agents.access_control.heuristic_classifier",
    "veracrawl.agents.access_control",
    "veracrawl.agents.escalation.policy_driven_escalator",
    "veracrawl.agents.escalation",
    "veracrawl.ports.access_control_classifier",
    "veracrawl.ports.adapter_escalation",
    # The recovery layer is also off-limits — coverage gate
    # is downstream of recovery, not a peer.
    "veracrawl.agents.recovery",
    "veracrawl.ports.recovery",
)


def test_source_coverage_gate_does_not_import_classifier_or_escalator() -> None:
    if not _SOURCE_COVERAGE_GATE.exists():
        pytest.skip(f"source_coverage_gate module missing: {_SOURCE_COVERAGE_GATE}")
    text = _SOURCE_COVERAGE_GATE.read_text(encoding="utf-8")
    offenders: list[str] = []
    for forbidden in _FORBIDDEN_IMPORTS:
        if forbidden in text:
            offenders.append(forbidden)
    assert not offenders, (
        "Phase 3 step 3.3 boundary: source_coverage_gate must remain "
        f"evaluative-only and must not import: {offenders!r}"
    )


def test_source_coverage_gate_module_exists() -> None:
    assert _SOURCE_COVERAGE_GATE.exists(), (
        "source_coverage_gate.py missing — refactor must update the "
        "Phase 3 step 3.3 boundary test path"
    )


def test_classifier_and_escalator_modules_exist_separately() -> None:
    """The boundary is meaningful only if the classifier +
    escalator are real modules sitting in their own files.
    Phase 3 step 3.1 + 3.2 must have shipped them."""

    classifier = _SRC / "agents" / "access_control" / "heuristic_classifier.py"
    escalator = (
        _SRC / "agents" / "escalation" / "policy_driven_escalator.py"
    )
    assert classifier.exists(), "Phase 3 step 3.1 classifier module missing"
    assert escalator.exists(), "Phase 3 step 3.2 escalator module missing"
