"""Phase 5 step 5.1 — recovery + cheap-classifier ports.

The recovery layer dispatches typed failures from Phase 1
(transport) / Phase 2 (auth) / Phase 3 (access control) /
Phase 4 (LLM) into one of four outcomes:

* ``DIFFERENT_URL`` — the recovery layer suggests a
  different URL within the same adapter (e.g., a model
  hint that the canonical product URL is one path level
  up).
* ``ESCALATE_ADAPTER`` — the recovery layer suggests
  trying the next adapter in the Phase 3 escalation chain
  (e.g., HTTP failed → try BROWSER_SNAPSHOT).
* ``REQUEST_REVIEW`` — the failure shape is unfamiliar;
  surface to operator review (Phase 6 ships the actual
  channel).
* ``ABANDON`` — terminal failure; halt this URL.

The cheap classifier is the always-runs-first filter that
short-circuits obvious failures (404 / 410 / Cloudflare
fingerprints / robots-blocked) without burning LLM tokens.
``LLMBackedRecovery`` consults it before any provider call.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from veracrawl.contracts.agent import RecoveryDecision
from veracrawl.contracts.common import Ref


class CheapClassifierVerdict(StrEnum):
    """Outcome of the deterministic cheap-classifier pass.

    Two terminal verdicts (``DEAD_HOST`` / ``PERMANENT_BLOCK``)
    skip the LLM call entirely and produce a
    ``RecoveryDecision`` directly. The other two route to
    the LLM (``LLMBackedRecovery._llm_decide``).
    """

    DEAD_HOST = "dead_host"
    PERMANENT_BLOCK = "permanent_block"
    TRANSIENT_UNCLEAR = "transient_unclear"
    ESCALATE_TO_LLM = "escalate_to_llm"


@runtime_checkable
class CheapClassifierPort(Protocol):
    """Cheap deterministic failure classifier.

    Runs before any LLM call. Adapters that recognise a
    failure shape definitively (``DEAD_HOST`` /
    ``PERMANENT_BLOCK``) save an LLM call; otherwise they
    return ``TRANSIENT_UNCLEAR`` / ``ESCALATE_TO_LLM`` and
    let the recovery layer dispatch to the model.
    """

    def classify(
        self,
        *,
        failure: BaseException,
        attempt_evidence_ref: Ref,
    ) -> CheapClassifierVerdict:
        ...


@runtime_checkable
class RecoveryPort(Protocol):
    """Decide what to do about a typed failure."""

    def decide(
        self,
        *,
        failure: BaseException,
        attempt_evidence_ref: Ref,
        run_ref: Ref,
        recovery_iteration: int,
    ) -> RecoveryDecision:
        ...


__all__ = [
    "CheapClassifierPort",
    "CheapClassifierVerdict",
    "RecoveryPort",
]
