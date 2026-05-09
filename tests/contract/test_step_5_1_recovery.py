"""Phase 5 step 5.1 — recovery + cheap-classifier contract tests."""

from __future__ import annotations

import pytest

from veracrawl.agents.recovery.cheap_classifier import HeuristicCheapClassifier
from veracrawl.agents.recovery.llm_backed_recovery import (
    LLMBackedRecovery,
    _failure_signature,
)
from veracrawl.contracts.enums import (
    RecoveryDecisionKind,
    RecoveryDecisionSource,
)
from veracrawl.ports.recovery import (
    CheapClassifierPort,
    CheapClassifierVerdict,
    RecoveryPort,
)

# --- Stub failures ---------------------------------------------------------


class _FakeStatusFailure(RuntimeError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"fake failure status={status_code}")


class _FakeRobotsBlockedError(RuntimeError):
    pass


_FakeRobotsBlockedError.__name__ = "RobotsBlockedError"


class _FakeAccessControlBlocked(RuntimeError):
    def __init__(self) -> None:
        self.classifier_provider = "cloudflare"
        super().__init__("blocked")


# --- HeuristicCheapClassifier ----------------------------------------------


def test_cheap_classifier_protocol_runtime_checkable() -> None:
    classifier = HeuristicCheapClassifier()
    assert isinstance(classifier, CheapClassifierPort)


@pytest.mark.parametrize("status", [404, 410])
def test_cheap_classifier_dead_host_for_404_410(status: int) -> None:
    classifier = HeuristicCheapClassifier()
    verdict = classifier.classify(
        failure=_FakeStatusFailure(status),
        attempt_evidence_ref="attempt:1",
    )
    assert verdict is CheapClassifierVerdict.DEAD_HOST


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_cheap_classifier_transient_unclear_for_5xx(status: int) -> None:
    classifier = HeuristicCheapClassifier()
    verdict = classifier.classify(
        failure=_FakeStatusFailure(status),
        attempt_evidence_ref="attempt:1",
    )
    assert verdict is CheapClassifierVerdict.TRANSIENT_UNCLEAR


def test_cheap_classifier_permanent_block_on_robots_error() -> None:
    classifier = HeuristicCheapClassifier()
    verdict = classifier.classify(
        failure=_FakeRobotsBlockedError("blocked"),
        attempt_evidence_ref="attempt:1",
    )
    assert verdict is CheapClassifierVerdict.PERMANENT_BLOCK


def test_cheap_classifier_permanent_block_on_access_control_blocked() -> None:
    classifier = HeuristicCheapClassifier()
    verdict = classifier.classify(
        failure=_FakeAccessControlBlocked(),
        attempt_evidence_ref="attempt:1",
    )
    assert verdict is CheapClassifierVerdict.PERMANENT_BLOCK


def test_cheap_classifier_escalate_for_403() -> None:
    classifier = HeuristicCheapClassifier()
    verdict = classifier.classify(
        failure=_FakeStatusFailure(403),
        attempt_evidence_ref="attempt:1",
    )
    assert verdict is CheapClassifierVerdict.ESCALATE_TO_LLM


def test_cheap_classifier_escalate_for_unknown_failure() -> None:
    classifier = HeuristicCheapClassifier()
    verdict = classifier.classify(
        failure=RuntimeError("mystery"),
        attempt_evidence_ref="attempt:1",
    )
    assert verdict is CheapClassifierVerdict.ESCALATE_TO_LLM


# --- _failure_signature ----------------------------------------------------


def test_failure_signature_is_deterministic_for_same_class_and_status() -> None:
    sig1 = _failure_signature(_FakeStatusFailure(404))
    sig2 = _failure_signature(_FakeStatusFailure(404))
    assert sig1 == sig2
    assert len(sig1) == 16


def test_failure_signature_differs_across_status() -> None:
    sig1 = _failure_signature(_FakeStatusFailure(404))
    sig2 = _failure_signature(_FakeStatusFailure(500))
    assert sig1 != sig2


def test_failure_signature_differs_across_class() -> None:
    sig1 = _failure_signature(_FakeStatusFailure(404))
    sig2 = _failure_signature(_FakeRobotsBlockedError("blocked"))
    assert sig1 != sig2


# --- LLMBackedRecovery -----------------------------------------------------


def _stub_llm_decide(
    failure: BaseException, recovery_iteration: int
) -> RecoveryDecisionKind:
    del failure, recovery_iteration
    return RecoveryDecisionKind.ABANDON


def test_recovery_protocol_runtime_checkable() -> None:
    classifier = HeuristicCheapClassifier()
    recovery = LLMBackedRecovery(
        cheap_classifier=classifier,
        llm_decision_fn=_stub_llm_decide,
    )
    assert isinstance(recovery, RecoveryPort)


def test_recovery_short_circuits_dead_host_to_abandon() -> None:
    classifier = HeuristicCheapClassifier()
    llm_called = False

    def llm(_failure: BaseException, _iter: int) -> RecoveryDecisionKind:
        nonlocal llm_called
        llm_called = True
        return RecoveryDecisionKind.ABANDON

    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=llm
    )
    decision = recovery.decide(
        failure=_FakeStatusFailure(404),
        attempt_evidence_ref="attempt:1",
        run_ref="run:1",
        recovery_iteration=0,
    )
    assert decision.kind is RecoveryDecisionKind.ABANDON
    assert decision.source is RecoveryDecisionSource.CHEAP_CLASSIFIER
    assert decision.cost_usd == 0.0
    assert llm_called is False  # cheap classifier short-circuited


def test_recovery_short_circuits_permanent_block_to_abandon() -> None:
    classifier = HeuristicCheapClassifier()
    llm_called = False

    def llm(_failure: BaseException, _iter: int) -> RecoveryDecisionKind:
        nonlocal llm_called
        llm_called = True
        return RecoveryDecisionKind.ABANDON

    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=llm
    )
    decision = recovery.decide(
        failure=_FakeRobotsBlockedError("blocked"),
        attempt_evidence_ref="attempt:1",
        run_ref="run:1",
        recovery_iteration=0,
    )
    assert decision.kind is RecoveryDecisionKind.ABANDON
    assert decision.source is RecoveryDecisionSource.CHEAP_CLASSIFIER
    assert llm_called is False


def test_recovery_routes_transient_unclear_to_llm() -> None:
    classifier = HeuristicCheapClassifier()

    def llm(_failure: BaseException, _iter: int) -> RecoveryDecisionKind:
        return RecoveryDecisionKind.REQUEST_REVIEW

    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=llm
    )
    decision = recovery.decide(
        failure=_FakeStatusFailure(503),
        attempt_evidence_ref="attempt:1",
        run_ref="run:1",
        recovery_iteration=0,
    )
    assert decision.kind is RecoveryDecisionKind.REQUEST_REVIEW
    assert decision.source is RecoveryDecisionSource.LLM_RECOVERY


def test_recovery_routes_escalate_to_llm() -> None:
    classifier = HeuristicCheapClassifier()

    def llm(_failure: BaseException, _iter: int) -> RecoveryDecisionKind:
        return RecoveryDecisionKind.ABANDON

    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=llm
    )
    decision = recovery.decide(
        failure=RuntimeError("unknown"),
        attempt_evidence_ref="attempt:1",
        run_ref="run:1",
        recovery_iteration=0,
    )
    assert decision.source is RecoveryDecisionSource.LLM_RECOVERY


def test_recovery_failure_signature_is_pinned_on_decision() -> None:
    classifier = HeuristicCheapClassifier()
    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=_stub_llm_decide
    )
    decision1 = recovery.decide(
        failure=_FakeStatusFailure(404),
        attempt_evidence_ref="attempt:1",
        run_ref="run:1",
        recovery_iteration=0,
    )
    decision2 = recovery.decide(
        failure=_FakeStatusFailure(404),
        attempt_evidence_ref="attempt:2",
        run_ref="run:1",
        recovery_iteration=1,
    )
    assert decision1.failure_signature == decision2.failure_signature


def test_recovery_rejects_blank_run_ref() -> None:
    classifier = HeuristicCheapClassifier()
    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=_stub_llm_decide
    )
    with pytest.raises(ValueError, match="run_ref"):
        recovery.decide(
            failure=_FakeStatusFailure(404),
            attempt_evidence_ref="attempt:1",
            run_ref="   ",
            recovery_iteration=0,
        )


def test_recovery_rejects_blank_attempt_evidence_ref() -> None:
    classifier = HeuristicCheapClassifier()
    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=_stub_llm_decide
    )
    with pytest.raises(ValueError, match="attempt_evidence_ref"):
        recovery.decide(
            failure=_FakeStatusFailure(404),
            attempt_evidence_ref="   ",
            run_ref="run:1",
            recovery_iteration=0,
        )


def test_recovery_rejects_negative_iteration() -> None:
    classifier = HeuristicCheapClassifier()
    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=_stub_llm_decide
    )
    with pytest.raises(ValueError, match="recovery_iteration"):
        recovery.decide(
            failure=_FakeStatusFailure(404),
            attempt_evidence_ref="attempt:1",
            run_ref="run:1",
            recovery_iteration=-1,
        )


def test_recovery_different_url_without_target_falls_back_to_abandon() -> None:
    """The fixture-mode dispatcher returns DIFFERENT_URL but
    doesn't supply an alternative — the validator would
    refuse the resulting decision. The adapter falls back
    to ABANDON to keep the contract honest."""

    classifier = HeuristicCheapClassifier()

    def llm(_failure: BaseException, _iter: int) -> RecoveryDecisionKind:
        return RecoveryDecisionKind.DIFFERENT_URL

    recovery = LLMBackedRecovery(
        cheap_classifier=classifier, llm_decision_fn=llm
    )
    decision = recovery.decide(
        failure=RuntimeError("unknown"),
        attempt_evidence_ref="attempt:1",
        run_ref="run:1",
        recovery_iteration=0,
    )
    assert decision.kind is RecoveryDecisionKind.ABANDON
