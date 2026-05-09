"""Phase 5 step 5.1 — heuristic cheap classifier.

Deterministic status-based routing decisions that don't need
an LLM. Per phase-5-design.md:

* ``404`` / ``410`` → ``DEAD_HOST`` (skip LLM, ABANDON).
* ``403`` with Cloudflare/DataDome fingerprint or
  ``RobotsBlockedError`` → ``PERMANENT_BLOCK`` (skip LLM,
  ABANDON — charter-respected).
* ``5xx`` with ``Retry-After`` → ``TRANSIENT_UNCLEAR``
  (let the LLM decide whether retry is worth it).
* anything else → ``ESCALATE_TO_LLM``.

The classifier inspects the failure exception's
``status_code`` / ``error_code`` / ``classifier_provider``
fields when present; failures that don't carry those hints
default to ``ESCALATE_TO_LLM`` so the LLM can reason about
them.
"""

from __future__ import annotations

from typing import Any

from veracrawl.contracts.common import Ref
from veracrawl.ports.recovery import CheapClassifierVerdict

_DEAD_HOST_STATUS_CODES: frozenset[int] = frozenset({404, 410})
_TRANSIENT_STATUS_CODES: frozenset[int] = frozenset({500, 502, 503, 504})


def _get(failure: BaseException, name: str) -> Any:
    return getattr(failure, name, None)


class HeuristicCheapClassifier:
    """Default cheap classifier."""

    def classify(
        self,
        *,
        failure: BaseException,
        attempt_evidence_ref: Ref,
    ) -> CheapClassifierVerdict:
        del attempt_evidence_ref  # unused for the heuristic;
        # production classifier may inspect the evidence
        # for body-length / content-type signals.
        status_code = _get(failure, "status_code")
        # RobotsBlockedError → permanent block (charter:
        # surface, never solve).
        failure_class = type(failure).__name__
        if failure_class == "RobotsBlockedError":
            return CheapClassifierVerdict.PERMANENT_BLOCK
        # AccessControlBlocked: charter-respected.
        provider = _get(failure, "classifier_provider")
        if provider is not None:
            return CheapClassifierVerdict.PERMANENT_BLOCK
        if isinstance(status_code, int):
            if status_code in _DEAD_HOST_STATUS_CODES:
                return CheapClassifierVerdict.DEAD_HOST
            if status_code in _TRANSIENT_STATUS_CODES:
                return CheapClassifierVerdict.TRANSIENT_UNCLEAR
            if status_code == 403:
                # Could be Cloudflare or a permission error; the
                # LLM can reason about it given the response
                # body.
                return CheapClassifierVerdict.ESCALATE_TO_LLM
        return CheapClassifierVerdict.ESCALATE_TO_LLM


__all__ = ["HeuristicCheapClassifier"]
