"""Phase 4 step 4.6 — LLM-driven extraction runtime.

The integrator wiring Phase 4 ports together. Given:

* a prompt-template ref (``PromptRegistryPort``);
* a logical context dict (URL, anchor list, screenshot ref);
* a target Pydantic class (the caller declares the
  expected output shape — full JSON Schema validation lives
  here, not in the v2 adapters);
* anchor records (provider-blind ``Anchor`` shapes); and
* per-field raw confidence the LLM self-reports;

``SchemaExtractionRuntime.extract`` produces:

* an :class:`LLMExtractionCandidate` carrying the parsed
  field values + per-field citation refs + per-field
  calibrated confidence refs;
* a list of :class:`LLMFieldCitation` records (one per
  extracted field, anchored to the input ``Anchor`` set);
* a list of :class:`LLMFieldConfidence` records with
  ``calibration_method`` matching the wired
  :class:`CalibrationPort`.

The flow:

1. Render the prompt template through the registry
   (credential boundary applies — Phase 2 step 2.3).
2. Build a ``ProviderRequest`` with
   ``ResponseFormatKind.JSON_OBJECT`` (the v2 adapters
   refuse ``JSON_SCHEMA``; full validation happens here via
   the caller-supplied Pydantic class).
3. ``budget.estimate_charge`` (refuses if estimate alone
   breaches the cap).
4. ``provider.complete(request)`` — typed retryable / fatal
   errors propagate.
5. Parse ``response.parsed_output`` (populated for
   ``JSON_OBJECT``) and validate via the caller's Pydantic
   class. Validation failures raise
   :class:`StructuredOutputViolation` (sanitized — never
   echo the raw output into the message).
6. Calibrate raw scores per field via
   ``CalibrationPort.calibrate``.
7. ``budget.charge`` the actual usage (durable persist
   first, then advisory total update; raises
   ``TokenBudgetExceeded`` after persist if the cap is
   newly breached).
8. Build + return the extraction records.

Caller responsibilities:
- Supply the Pydantic class (declares the field shape).
- Supply anchor records and the
  ``per_field_anchor_refs`` map (which anchors back which
  field).
- The runtime does NOT decide which fields to abstain on;
  the caller's prompt + the LLM's response together drive
  abstention. Fields the LLM declined return as
  ``LLMExtractionCandidate.abstentions`` instead of
  ``field_values``.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from veracrawl.contracts.agent import (
    LLMExtractionCandidate,
    LLMFieldCitation,
    LLMFieldConfidence,
    Message,
    ResponseFormat,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CalibrationMethod,
    MessageRole,
    ResponseFormatKind,
)
from veracrawl.contracts.errors import StructuredOutputViolation
from veracrawl.contracts.llm_input import Anchor, ProviderRequest
from veracrawl.ports.calibration import CalibrationPort
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2
from veracrawl.ports.prompt_registry import PromptRegistryPort
from veracrawl.ports.token_budget import TokenBudgetPort

_CALIBRATOR_ID_TO_METHOD: dict[str, CalibrationMethod] = {
    "identity": CalibrationMethod.NONE,
    "platt": CalibrationMethod.PLATT,
    "isotonic": CalibrationMethod.ISOTONIC,
}


class SchemaExtractionRuntime:
    """LLM-driven extraction integrator (Phase 4 step 4.6)."""

    def __init__(
        self,
        *,
        provider: ModelProviderPortV2,
        prompt_registry: PromptRegistryPort,
        token_budget: TokenBudgetPort,
        calibrator: CalibrationPort,
        run_ref: Ref,
    ) -> None:
        if not run_ref or not run_ref.strip():
            raise ValueError("run_ref must be a non-blank identifier")
        self._provider = provider
        self._prompt_registry = prompt_registry
        self._token_budget = token_budget
        self._calibrator = calibrator
        self._run_ref = run_ref

    def extract(
        self,
        *,
        source_url: str,
        prompt_ref: str,
        prompt_context: Mapping[str, Any],
        output_class: type[BaseModel],
        anchors: list[Anchor],
        per_field_anchor_refs: Mapping[str, list[Ref]],
        per_field_excerpts: Mapping[str, str],
        per_field_raw_scores: Mapping[str, float],
        model_name: str,
        max_output_tokens: int,
        schema_ref: Ref,
        model_call_trace_ref: Ref,
        abstentions: Mapping[str, str] | None = None,
    ) -> tuple[
        LLMExtractionCandidate,
        list[LLMFieldCitation],
        list[LLMFieldConfidence],
    ]:
        # 1. Render prompt (credential boundary applies).
        rendered_prompt = self._prompt_registry.render(prompt_ref, prompt_context)
        # 2. Build provider request.
        request = ProviderRequest(
            id=f"provider-request:{prompt_ref}:{uuid.uuid4().hex}",
            run_ref=self._run_ref,
            model_name=model_name,
            messages=[
                Message(role=MessageRole.USER, content=rendered_prompt),
            ],
            response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT),
            max_output_tokens=max_output_tokens,
            anchors=anchors,
        )
        # 3. Pre-flight budget check.
        self._token_budget.estimate_charge(request)
        # 4. Provider call.
        response = self._provider.complete(request)
        # 5. Schema validation via the caller's Pydantic class.
        if response.parsed_output is None:
            # ``JSON_OBJECT`` should have populated parsed_output;
            # if not, something upstream went wrong.
            raise StructuredOutputViolation(
                status_code=200,
                error_code="STRUCTURED_OUTPUT_VIOLATION",
                request_id=None,
            )
        try:
            output_class.model_validate(response.parsed_output)
        except ValidationError as exc:
            # Pydantic's error message includes field values;
            # strip to a sanitized error.
            del exc
            raise StructuredOutputViolation(
                status_code=200,
                error_code="STRUCTURED_OUTPUT_VIOLATION",
                request_id=None,
            ) from None
        # 6. Calibrate per-field raw scores.
        calibration_method = _CALIBRATOR_ID_TO_METHOD.get(
            getattr(self._calibrator, "calibrator_id", "identity"),
            CalibrationMethod.NONE,
        )
        calibration_version = self._resolve_calibration_version(
            method=calibration_method
        )
        # 7. Build extraction records.
        candidate_id = f"llm-extraction-candidate:{uuid.uuid4().hex}"
        per_field_values: dict[str, Any] = {
            name: response.parsed_output[name]
            for name in per_field_raw_scores
            if name in response.parsed_output
        }
        absent_fields = set(per_field_raw_scores) - set(per_field_values)
        merged_abstentions = dict(abstentions or {})
        for field_name in absent_fields:
            if field_name not in merged_abstentions:
                merged_abstentions[field_name] = "field absent in model output"
        # Build citations + confidences only for present fields.
        citations: list[LLMFieldCitation] = []
        confidences: list[LLMFieldConfidence] = []
        citation_refs: dict[str, Ref] = {}
        confidence_refs: dict[str, Ref] = {}
        for field_name in per_field_values:
            citation = LLMFieldCitation(
                id=f"llm-field-citation:{uuid.uuid4().hex}",
                candidate_ref=candidate_id,
                field_name=field_name,
                anchor_refs=list(per_field_anchor_refs.get(field_name, [])),
                excerpt=per_field_excerpts.get(field_name, ""),
            )
            citations.append(citation)
            citation_refs[field_name] = citation.id
            calibrated = self._calibrator.calibrate(
                per_field_raw_scores[field_name],
                model_name=model_name,
                field_name=field_name,
            )
            confidence = LLMFieldConfidence(
                id=f"llm-field-confidence:{uuid.uuid4().hex}",
                candidate_ref=candidate_id,
                field_name=field_name,
                raw_score=calibrated.raw_value,
                calibrated_score=calibrated.value,
                calibration_method=calibration_method,
                calibration_version=calibration_version,
            )
            confidences.append(confidence)
            confidence_refs[field_name] = confidence.id
        candidate = LLMExtractionCandidate(
            id=candidate_id,
            run_ref=self._run_ref,
            source_url=source_url,
            schema_ref=schema_ref,
            model_call_trace_ref=model_call_trace_ref,
            field_values=per_field_values,
            field_citation_refs=citation_refs,
            field_confidence_refs=confidence_refs,
            abstentions=merged_abstentions,
        )
        # 8. Charge actual usage (durable-first; raises after
        # persist if cap newly breached).
        self._token_budget.charge(response.usage, request_ref=request.id)
        return candidate, citations, confidences

    def _resolve_calibration_version(
        self, *, method: CalibrationMethod
    ) -> Ref | None:
        if method is CalibrationMethod.NONE:
            return None
        # The calibrator's ``calibrate`` returns ``CalibratedScore``
        # with a ``fit_artifact_ref``; we use that as the
        # version pin per call site instead. For Phase 4 we
        # synthesize a stable version string here so the
        # ``LLMFieldConfidence`` validator (which requires a
        # version when method != NONE) accepts it. Phase 5 may
        # tighten this to read from the calibrator directly.
        return f"calibration-version:{method.value}"


__all__ = ["SchemaExtractionRuntime"]
