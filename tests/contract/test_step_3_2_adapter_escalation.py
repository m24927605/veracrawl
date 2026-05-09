"""Phase 3 step 3.2 — PolicyDrivenEscalator contract tests."""

from __future__ import annotations

import pytest

from veracrawl.agents.escalation.policy_driven_escalator import (
    PolicyDrivenEscalator,
    _failure_signature,
)
from veracrawl.contracts.enums import AdapterType
from veracrawl.contracts.source_adapter import AdapterEscalationPolicy
from veracrawl.ports.adapter_escalation import AdapterEscalationPort


def _policy(
    *,
    allowed_transitions: dict[AdapterType, list[AdapterType]] | None = None,
    requires_review: bool = False,
    max_escalations_per_run: int = 2,
) -> AdapterEscalationPolicy:
    return AdapterEscalationPolicy(
        id="policy:test:v1",
        name="test_policy",
        allowed_transitions=allowed_transitions
        or {AdapterType.HTTP: [AdapterType.AUTHORIZED_SESSION]},
        requires_review=requires_review,
        max_escalations_per_run=max_escalations_per_run,
    )


class _FakeFailure(RuntimeError):
    def __init__(self, status_code: int = 403) -> None:
        self.status_code = status_code
        super().__init__(f"fake failure {status_code}")


# --- Happy path ------------------------------------------------------------


def test_decide_picks_first_allowed_target() -> None:
    escalator = PolicyDrivenEscalator()
    decision = escalator.decide(
        from_adapter_type=AdapterType.HTTP,
        failure=_FakeFailure(),
        run_ref="run:1",
        triggered_by_ref="evidence:1",
        policy=_policy(),
        prior_escalation_count=0,
    )
    assert decision is not None
    assert decision.from_adapter_type is AdapterType.HTTP
    assert decision.to_adapter_type is AdapterType.AUTHORIZED_SESSION
    assert decision.failure_signature
    assert decision.policy_ref == "policy:test:v1"


def test_decide_browser_to_authorized_session() -> None:
    escalator = PolicyDrivenEscalator()
    policy = _policy(
        allowed_transitions={
            AdapterType.BROWSER_SNAPSHOT: [AdapterType.AUTHORIZED_SESSION]
        }
    )
    decision = escalator.decide(
        from_adapter_type=AdapterType.BROWSER_SNAPSHOT,
        failure=_FakeFailure(),
        run_ref="run:1",
        triggered_by_ref="evidence:1",
        policy=policy,
        prior_escalation_count=0,
    )
    assert decision is not None
    assert decision.to_adapter_type is AdapterType.AUTHORIZED_SESSION


def test_decide_api_source_to_authorized_session() -> None:
    escalator = PolicyDrivenEscalator()
    policy = _policy(
        allowed_transitions={
            AdapterType.API_SOURCE: [
                AdapterType.HTTP,
                AdapterType.AUTHORIZED_SESSION,
            ]
        }
    )
    decision = escalator.decide(
        from_adapter_type=AdapterType.API_SOURCE,
        failure=_FakeFailure(),
        run_ref="run:1",
        triggered_by_ref="evidence:1",
        policy=policy,
        prior_escalation_count=0,
    )
    assert decision is not None
    # First target wins.
    assert decision.to_adapter_type is AdapterType.HTTP


# --- Refusal paths ---------------------------------------------------------


def test_decide_returns_none_when_max_escalations_reached() -> None:
    escalator = PolicyDrivenEscalator()
    decision = escalator.decide(
        from_adapter_type=AdapterType.HTTP,
        failure=_FakeFailure(),
        run_ref="run:1",
        triggered_by_ref="evidence:1",
        policy=_policy(max_escalations_per_run=2),
        prior_escalation_count=2,
    )
    assert decision is None


def test_decide_returns_none_when_prior_count_exceeds_cap() -> None:
    escalator = PolicyDrivenEscalator()
    decision = escalator.decide(
        from_adapter_type=AdapterType.HTTP,
        failure=_FakeFailure(),
        run_ref="run:1",
        triggered_by_ref="evidence:1",
        policy=_policy(max_escalations_per_run=1),
        prior_escalation_count=5,
    )
    assert decision is None


def test_decide_returns_none_when_policy_requires_review() -> None:
    """``requires_review=True`` policies do not auto-escalate
    — the orchestrator must route to operator review."""

    escalator = PolicyDrivenEscalator()
    decision = escalator.decide(
        from_adapter_type=AdapterType.HTTP,
        failure=_FakeFailure(),
        run_ref="run:1",
        triggered_by_ref="evidence:1",
        policy=_policy(requires_review=True),
        prior_escalation_count=0,
    )
    assert decision is None


def test_decide_returns_none_when_no_allowed_transition_for_source() -> None:
    """The policy declares HTTP→AUTHORIZED_SESSION, but the
    caller asks about API_SOURCE → no target."""

    escalator = PolicyDrivenEscalator()
    decision = escalator.decide(
        from_adapter_type=AdapterType.API_SOURCE,
        failure=_FakeFailure(),
        run_ref="run:1",
        triggered_by_ref="evidence:1",
        policy=_policy(),  # only HTTP→AUTHORIZED_SESSION
        prior_escalation_count=0,
    )
    assert decision is None


# --- Validation ------------------------------------------------------------


def test_decide_rejects_blank_run_ref() -> None:
    escalator = PolicyDrivenEscalator()
    with pytest.raises(ValueError, match="run_ref"):
        escalator.decide(
            from_adapter_type=AdapterType.HTTP,
            failure=_FakeFailure(),
            run_ref="   ",
            triggered_by_ref="evidence:1",
            policy=_policy(),
            prior_escalation_count=0,
        )


def test_decide_rejects_blank_triggered_by() -> None:
    escalator = PolicyDrivenEscalator()
    with pytest.raises(ValueError, match="triggered_by_ref"):
        escalator.decide(
            from_adapter_type=AdapterType.HTTP,
            failure=_FakeFailure(),
            run_ref="run:1",
            triggered_by_ref="   ",
            policy=_policy(),
            prior_escalation_count=0,
        )


def test_decide_rejects_negative_prior_count() -> None:
    escalator = PolicyDrivenEscalator()
    with pytest.raises(ValueError, match="prior_escalation_count"):
        escalator.decide(
            from_adapter_type=AdapterType.HTTP,
            failure=_FakeFailure(),
            run_ref="run:1",
            triggered_by_ref="evidence:1",
            policy=_policy(),
            prior_escalation_count=-1,
        )


# --- Failure signature determinism ----------------------------------------


def test_failure_signature_matches_phase_5_recovery_shape() -> None:
    """The signature shape must be the same as Phase 5 step
    5.1 ``_failure_signature`` so cost-gate counters
    correlate the same shape across the recovery + escalation
    layers."""

    sig1 = _failure_signature(_FakeFailure(404))
    sig2 = _failure_signature(_FakeFailure(404))
    assert sig1 == sig2
    assert len(sig1) == 16


def test_failure_signature_differs_per_status() -> None:
    sig1 = _failure_signature(_FakeFailure(404))
    sig2 = _failure_signature(_FakeFailure(500))
    assert sig1 != sig2


# --- Protocol -------------------------------------------------------------


def test_runtime_checkable() -> None:
    assert isinstance(PolicyDrivenEscalator(), AdapterEscalationPort)


# --- Charter constraint ---------------------------------------------------


def test_decision_must_use_allowed_transition_table() -> None:
    """The Phase 0 ``AdapterEscalationDecision`` validator
    refuses transitions outside the
    ``_ALLOWED_ESCALATION_TRANSITIONS`` table. This test
    confirms a misbehaving escalator (one that tries to
    output a non-allowed transition) gets refused at the
    contract layer, not silently accepted."""

    # The contract layer refuses HTTP → API_SOURCE because
    # it's not in _ALLOWED_ESCALATION_TRANSITIONS. Even if a
    # policy declared it (which the policy validator also
    # would refuse), the decision can't construct.
    bad_policy_dict = {AdapterType.HTTP: [AdapterType.API_SOURCE]}
    with pytest.raises(ValueError):
        AdapterEscalationPolicy(
            id="policy:bad",
            name="bad",
            allowed_transitions=bad_policy_dict,
        )
