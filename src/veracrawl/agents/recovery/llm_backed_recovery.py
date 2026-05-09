"""Phase 5 step 5.1 — LLM-backed recovery adapter.

``LLMBackedRecovery`` consults the cheap classifier first;
short-circuits ``DEAD_HOST`` and ``PERMANENT_BLOCK`` to
``ABANDON`` without an LLM call. Other verdicts route to
the LLM via a recovery-prompt template.

This attempt ships a deterministic fixture-mode-friendly
LLM dispatcher: callers inject a callable that maps a
recovery context to a ``RecoveryDecisionKind``. Phase 6
step 6.1 wires the real ``ModelProviderPortV2`` call (using
``SchemaExtractionRuntime`` with a ``recovery_decision`` JSON
schema) — the contract surface here lets that swap drop in
without changing the recovery layer's public shape.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable

from veracrawl.contracts.agent import RecoveryDecision
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    RecoveryDecisionKind,
    RecoveryDecisionSource,
)
from veracrawl.ports.recovery import (
    CheapClassifierPort,
    CheapClassifierVerdict,
)


def _failure_signature(failure: BaseException) -> str:
    """Deterministic signature ``sha256(class + status)[:16]``.

    Per phase-5-design.md: signature is used by the cost gate
    to detect repeated-same-failure loops. Origin is excluded
    here because it isn't always available on the failure
    object — the cost gate composes signature + origin
    upstream when needed.
    """

    class_name = type(failure).__name__
    status = getattr(failure, "status_code", "")
    payload = f"{class_name}|{status}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


class LLMBackedRecovery:
    """Recovery adapter with cheap-classifier-before-LLM ordering."""

    def __init__(
        self,
        *,
        cheap_classifier: CheapClassifierPort,
        llm_decision_fn: Callable[[BaseException, int], RecoveryDecisionKind],
    ) -> None:
        self._cheap_classifier = cheap_classifier
        self._llm_decision_fn = llm_decision_fn

    def decide(
        self,
        *,
        failure: BaseException,
        attempt_evidence_ref: Ref,
        run_ref: Ref,
        recovery_iteration: int,
    ) -> RecoveryDecision:
        if not run_ref or not run_ref.strip():
            raise ValueError("run_ref must be non-blank")
        if not attempt_evidence_ref or not attempt_evidence_ref.strip():
            raise ValueError("attempt_evidence_ref must be non-blank")
        if recovery_iteration < 0:
            raise ValueError("recovery_iteration must be non-negative")
        signature = _failure_signature(failure)
        verdict = self._cheap_classifier.classify(
            failure=failure, attempt_evidence_ref=attempt_evidence_ref
        )
        # Cheap-classifier short-circuits.
        if verdict is CheapClassifierVerdict.DEAD_HOST:
            return RecoveryDecision(
                id=f"recovery-decision:{uuid.uuid4().hex}",
                kind=RecoveryDecisionKind.ABANDON,
                reason=f"cheap_classifier:{verdict.value}",
                failure_signature=signature,
                source=RecoveryDecisionSource.CHEAP_CLASSIFIER,
                cost_usd=0.0,
            )
        if verdict is CheapClassifierVerdict.PERMANENT_BLOCK:
            return RecoveryDecision(
                id=f"recovery-decision:{uuid.uuid4().hex}",
                kind=RecoveryDecisionKind.ABANDON,
                reason=f"cheap_classifier:{verdict.value}",
                failure_signature=signature,
                source=RecoveryDecisionSource.CHEAP_CLASSIFIER,
                cost_usd=0.0,
            )
        # LLM-routed verdicts.
        kind = self._llm_decision_fn(failure, recovery_iteration)
        if kind is RecoveryDecisionKind.DIFFERENT_URL:
            # Fixture-mode: callers wanting a different URL
            # must supply it via the dispatcher; this default
            # adapter doesn't produce alternatives. Treat
            # bare DIFFERENT_URL without a target as ABANDON
            # to keep the contract honest — the validator
            # would refuse a DIFFERENT_URL without
            # alternative_url anyway.
            kind = RecoveryDecisionKind.ABANDON
        if kind is RecoveryDecisionKind.ESCALATE_ADAPTER:
            kind = RecoveryDecisionKind.ABANDON  # same reasoning
        return RecoveryDecision(
            id=f"recovery-decision:{uuid.uuid4().hex}",
            kind=kind,
            reason=f"llm_recovery:{verdict.value}",
            failure_signature=signature,
            source=RecoveryDecisionSource.LLM_RECOVERY,
            cost_usd=0.0,
        )


__all__ = ["LLMBackedRecovery", "_failure_signature"]
