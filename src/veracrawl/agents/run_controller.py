"""Phase 5 step 5.3 — agent run controller (integrator).

Composes the building blocks from Phase 4 + Phase 5 into a
single ``run_url`` call that drives one URL through the
extraction + recovery pipeline:

1. ``cost_gate.check(...)`` — refuses early if any composed
   cap is breached.
2. ``schema_runtime.extract(...)`` — Phase 4 step 4.6.
3. On typed failure: ``recovery.decide(...)`` (Phase 5 step
   5.1).
4. Apply the recovery decision:
   * ``ABANDON`` / ``REQUEST_REVIEW`` — halt this URL.
   * ``DIFFERENT_URL`` — recurse with the suggested URL,
     bounded by ``max_recovery_iterations``.
   * ``ESCALATE_ADAPTER`` — surface the escalation target to
     the caller (this controller doesn't own the adapter
     chain — Phase 3 step 3.2 ``PolicyDrivenEscalator``
     does; we surface and stop).
5. Return ``UrlRunOutcome`` with the candidate (when
   extraction succeeded) or the terminating decision.

This step does NOT produce a full Phase 0 ``AgentRunResult``
— that requires ``AgentActionTrace`` plumbing scoped to the
multi-agent orchestration layer (out of Phase 5 building-
block scope). It produces the smallest useful integration
surface: per-URL extraction with bounded recovery.

The repeated-failure-signature counter inside the cost gate
catches infinite-recovery-loop bugs; ``max_recovery_iterations``
is the hard upper bound per URL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from veracrawl.contracts.agent import (
    LLMExtractionCandidate,
    LLMFieldCitation,
    LLMFieldConfidence,
    RecoveryDecision,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import RecoveryDecisionKind
from veracrawl.contracts.errors import (
    FatalError,
    PolicyViolation,
    RetryableError,
)
from veracrawl.contracts.llm_input import Anchor
from veracrawl.ports.cost_gate import CostGatePort
from veracrawl.ports.recovery import RecoveryPort

_DEFAULT_MAX_RECOVERY_ITERATIONS = 3


@dataclass
class UrlRunOutcome:
    """Result of one URL run through the extraction + recovery loop.

    ``terminal_decision`` is the last ``RecoveryDecision``
    applied; ``ABANDON`` / ``REQUEST_REVIEW`` /
    ``ESCALATE_ADAPTER`` results halt the loop with a
    non-None decision. A successful extraction returns
    ``terminal_decision=None`` and ``candidate`` populated.
    """

    final_url: str
    candidate: LLMExtractionCandidate | None
    citations: list[LLMFieldCitation]
    confidences: list[LLMFieldConfidence]
    recovery_trace: list[RecoveryDecision]
    terminal_decision: RecoveryDecision | None
    iterations: int


@dataclass
class _ExtractionRequest:
    source_url: str
    prompt_ref: str
    prompt_context: dict[str, Any]
    output_class: type[BaseModel]
    anchors: list[Anchor]
    per_field_anchor_refs: dict[str, list[Ref]]
    per_field_excerpts: dict[str, str]
    per_field_raw_scores: dict[str, float]
    model_name: str
    max_output_tokens: int
    schema_ref: Ref
    model_call_trace_ref: Ref
    abstentions: dict[str, str] = field(default_factory=dict)


class AgentRunController:
    """Phase 5 step 5.3 integrator."""

    def __init__(
        self,
        *,
        schema_runtime: Any,  # SchemaExtractionRuntime; Any to avoid import cycle
        recovery: RecoveryPort,
        cost_gate: CostGatePort,
        run_ref: Ref,
        objective_ref: Ref,
        max_recovery_iterations: int = _DEFAULT_MAX_RECOVERY_ITERATIONS,
    ) -> None:
        if not run_ref or not run_ref.strip():
            raise ValueError("run_ref must be non-blank")
        if not objective_ref or not objective_ref.strip():
            raise ValueError("objective_ref must be non-blank")
        if max_recovery_iterations < 0:
            raise ValueError("max_recovery_iterations must be non-negative")
        self._schema_runtime = schema_runtime
        self._recovery = recovery
        self._cost_gate = cost_gate
        self._run_ref = run_ref
        self._objective_ref = objective_ref
        self._max_recovery_iterations = max_recovery_iterations

    def run_url(
        self,
        *,
        extraction_request: _ExtractionRequest,
    ) -> UrlRunOutcome:
        """Drive one URL through the loop. Public entry point."""

        return self._run_with_recovery(
            extraction_request=extraction_request,
            iteration=0,
            recovery_trace=[],
        )

    def _run_with_recovery(
        self,
        *,
        extraction_request: _ExtractionRequest,
        iteration: int,
        recovery_trace: list[RecoveryDecision],
    ) -> UrlRunOutcome:
        url = extraction_request.source_url
        origin = self._origin_for(url)
        # Pre-flight cost-gate check (also bumps repeated-
        # failure counter on the previous decision's signature
        # if any).
        last_signature = (
            recovery_trace[-1].failure_signature if recovery_trace else None
        )
        self._cost_gate.check(
            run_ref=self._run_ref,
            objective_ref=self._objective_ref,
            origin=origin,
            failure_signature=last_signature,
        )
        try:
            candidate, citations, confidences = self._schema_runtime.extract(
                source_url=extraction_request.source_url,
                prompt_ref=extraction_request.prompt_ref,
                prompt_context=extraction_request.prompt_context,
                output_class=extraction_request.output_class,
                anchors=extraction_request.anchors,
                per_field_anchor_refs=extraction_request.per_field_anchor_refs,
                per_field_excerpts=extraction_request.per_field_excerpts,
                per_field_raw_scores=extraction_request.per_field_raw_scores,
                model_name=extraction_request.model_name,
                max_output_tokens=extraction_request.max_output_tokens,
                schema_ref=extraction_request.schema_ref,
                model_call_trace_ref=extraction_request.model_call_trace_ref,
                abstentions=extraction_request.abstentions,
            )
        except (FatalError, RetryableError, PolicyViolation) as failure:
            return self._handle_failure(
                failure=failure,
                extraction_request=extraction_request,
                iteration=iteration,
                recovery_trace=recovery_trace,
            )
        return UrlRunOutcome(
            final_url=url,
            candidate=candidate,
            citations=citations,
            confidences=confidences,
            recovery_trace=recovery_trace,
            terminal_decision=None,
            iterations=iteration,
        )

    def _handle_failure(
        self,
        *,
        failure: BaseException,
        extraction_request: _ExtractionRequest,
        iteration: int,
        recovery_trace: list[RecoveryDecision],
    ) -> UrlRunOutcome:
        if iteration >= self._max_recovery_iterations:
            # Hard upper bound. Synthesize a final ABANDON
            # decision so the trace shows why we halted.
            decision = self._recovery.decide(
                failure=failure,
                attempt_evidence_ref=f"attempt:max-iter:{iteration}",
                run_ref=self._run_ref,
                recovery_iteration=iteration,
            )
            recovery_trace.append(decision)
            return UrlRunOutcome(
                final_url=extraction_request.source_url,
                candidate=None,
                citations=[],
                confidences=[],
                recovery_trace=recovery_trace,
                terminal_decision=decision,
                iterations=iteration,
            )
        decision = self._recovery.decide(
            failure=failure,
            attempt_evidence_ref=f"attempt:iter:{iteration}",
            run_ref=self._run_ref,
            recovery_iteration=iteration,
        )
        recovery_trace.append(decision)
        if decision.kind is RecoveryDecisionKind.DIFFERENT_URL:
            new_request = _ExtractionRequest(
                source_url=decision.alternative_url or "",
                prompt_ref=extraction_request.prompt_ref,
                prompt_context=extraction_request.prompt_context,
                output_class=extraction_request.output_class,
                anchors=extraction_request.anchors,
                per_field_anchor_refs=extraction_request.per_field_anchor_refs,
                per_field_excerpts=extraction_request.per_field_excerpts,
                per_field_raw_scores=extraction_request.per_field_raw_scores,
                model_name=extraction_request.model_name,
                max_output_tokens=extraction_request.max_output_tokens,
                schema_ref=extraction_request.schema_ref,
                model_call_trace_ref=extraction_request.model_call_trace_ref,
                abstentions=extraction_request.abstentions,
            )
            return self._run_with_recovery(
                extraction_request=new_request,
                iteration=iteration + 1,
                recovery_trace=recovery_trace,
            )
        # ABANDON / REQUEST_REVIEW / ESCALATE_ADAPTER halt the
        # per-URL loop. ESCALATE_ADAPTER surfaces the target
        # to the caller (which owns the adapter chain).
        return UrlRunOutcome(
            final_url=extraction_request.source_url,
            candidate=None,
            citations=[],
            confidences=[],
            recovery_trace=recovery_trace,
            terminal_decision=decision,
            iterations=iteration,
        )

    @staticmethod
    def _origin_for(url: str) -> str:
        """Sanitized origin for cost-gate keying.

        Strips path / query / fragment / userinfo. The cost
        gate only needs the scheme + netloc to track per-host
        spend — keeping richer URL parts would key the same
        host's spend across many distinct entries.
        """

        from urllib.parse import urlparse

        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.hostname or ''}"


__all__ = ["AgentRunController", "UrlRunOutcome", "_ExtractionRequest"]
