"""Schema-bound extraction candidate runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    ExtractionCandidateStatus,
    SchemaExtractionFailureType,
)
from veracrawl.contracts.processing import (
    ExtractionCandidate,
    ExtractionStrategy,
    SchemaExtractionRuntimeReport,
)
from veracrawl.extract.candidates import build_extraction_strategy, create_anchored_candidate
from veracrawl.normalize.pipeline import NormalizationResult


@dataclass(frozen=True)
class SchemaExtractionRuntimeResult:
    report: SchemaExtractionRuntimeReport
    strategy: ExtractionStrategy | None = None
    candidate: ExtractionCandidate | None = None


_DIRECT_FAILURES: dict[str, tuple[SchemaExtractionFailureType, str]] = {
    "schema-extraction-missing-normalization": (
        SchemaExtractionFailureType.MISSING_LIVE_NORMALIZATION,
        "live_normalization_runtime_report_ref",
    ),
    "schema-extraction-schema-validation-failed": (
        SchemaExtractionFailureType.SCHEMA_VALIDATION_FAILED,
        "schema_validation_refs",
    ),
    "schema-extraction-missing-model-tool-trace": (
        SchemaExtractionFailureType.MISSING_MODEL_TOOL_TRACE,
        "model_trace_refs",
    ),
    "schema-extraction-candidate-direct-publication": (
        SchemaExtractionFailureType.CANDIDATE_DIRECT_PUBLICATION,
        "publication_refs",
    ),
    "schema-extraction-replay-mismatch": (
        SchemaExtractionFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_schema_extraction_runtime(
    *,
    fixture_id: str,
    scenario: str,
    live_normalization_runtime_report_ref: Ref | None,
    normalization: NormalizationResult | None,
    schema_ref: Ref,
    approved_exploratory_schema: bool = False,
    model_trace_refs: list[Ref] | None = None,
    tool_trace_refs: list[Ref] | None = None,
    publication_refs: list[Ref] | None = None,
) -> SchemaExtractionRuntimeResult:
    policy_refs = [f"policy:{fixture_id}:schema-extraction"]
    if live_normalization_runtime_report_ref is None or normalization is None:
        return _failure_result(
            fixture_id=fixture_id,
            failure=SchemaExtractionFailureType.MISSING_LIVE_NORMALIZATION,
            missing_field="live_normalization_runtime_report_ref",
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        )
    if "exploratory" in schema_ref and not approved_exploratory_schema:
        return _failure_result(
            fixture_id=fixture_id,
            failure=SchemaExtractionFailureType.SCHEMA_VALIDATION_FAILED,
            missing_field="approved_exploratory_schema_refs",
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            normalization=normalization,
            diagnostics=["exploratory schema was not explicitly approved"],
        )

    if scenario == "schema-extraction-missing-field-anchor":
        return _missing_anchor_result(
            fixture_id=fixture_id,
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            normalization=normalization,
        )

    if scenario == "schema-extraction-drift-repair-required":
        return _drift_needs_review_result(
            fixture_id=fixture_id,
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            normalization=normalization,
            approved_exploratory_schema=approved_exploratory_schema,
        )

    if scenario in _DIRECT_FAILURES:
        failure, missing_field = _DIRECT_FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            normalization=normalization,
            publication_refs=publication_refs
            or (
                [f"published-output:{fixture_id}:forbidden"]
                if failure == SchemaExtractionFailureType.CANDIDATE_DIRECT_PUBLICATION
                else []
            ),
        )

    traces = _trace_refs(fixture_id, model_trace_refs, tool_trace_refs)
    if not traces[0] or not traces[1]:
        return _failure_result(
            fixture_id=fixture_id,
            failure=SchemaExtractionFailureType.MISSING_MODEL_TOOL_TRACE,
            missing_field="model_trace_refs",
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            normalization=normalization,
        )

    try:
        strategy, candidate = _strategy_and_candidate(
            fixture_id=fixture_id,
            normalization=normalization,
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            model_trace_refs=traces[0],
            tool_trace_refs=traces[1],
        )
    except (ValueError, ValidationError) as exc:
        return _failure_result(
            fixture_id=fixture_id,
            failure=SchemaExtractionFailureType.EXTRACTION_FAILED,
            missing_field="extraction_candidate_refs",
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            normalization=normalization,
            diagnostics=[str(exc)],
        )

    approved_refs = (
        [f"schema-approval:{fixture_id}:exploratory"]
        if approved_exploratory_schema
        else []
    )
    report = _report(
        fixture_id=fixture_id,
        completion_result=CompletenessResult.PASS,
        operator_status="schema_extraction_completed",
        schema_ref=schema_ref,
        policy_refs=policy_refs,
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        normalization=normalization,
        strategy=strategy,
        candidate=candidate,
        approved_exploratory_schema_refs=approved_refs,
    )
    return SchemaExtractionRuntimeResult(report=report, strategy=strategy, candidate=candidate)


def _strategy_and_candidate(
    *,
    fixture_id: str,
    normalization: NormalizationResult,
    schema_ref: Ref,
    policy_refs: list[Ref],
    model_trace_refs: list[Ref],
    tool_trace_refs: list[Ref],
    omit_anchor_for: str | None = None,
    status: ExtractionCandidateStatus = ExtractionCandidateStatus.CANDIDATE,
    rejection_refs: list[Ref] | None = None,
) -> tuple[ExtractionStrategy, ExtractionCandidate]:
    strategy = build_extraction_strategy(
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        normalized_document=normalization.normalized_document,
        policy_decision_refs=policy_refs,
    ).model_copy(update={"schema_ref": schema_ref})
    candidate = create_anchored_candidate(
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        normalized_document=normalization.normalized_document,
        anchors=normalization.anchors,
        strategy=strategy,
        link_count=len(normalization.link_provenance),
        omit_anchor_for=omit_anchor_for,
    ).model_copy(
        update={
            "schema_validation_refs": [f"schema-validation:{fixture_id}:pass"],
            "model_trace_refs": model_trace_refs,
            "tool_trace_refs": tool_trace_refs,
            "rejection_refs": rejection_refs or [],
            "replay_refs": [f"replay:{fixture_id}:schema-extraction:candidate"],
            "status": status,
        }
    )
    _validate_schema_fields(strategy, candidate)
    return strategy, candidate


def _validate_schema_fields(
    strategy: ExtractionStrategy,
    candidate: ExtractionCandidate,
) -> None:
    missing = sorted(set(strategy.field_names) - set(candidate.field_values))
    unanchored = sorted(set(candidate.field_values) - set(candidate.field_anchor_refs))
    if missing:
        raise ValueError(f"candidate missing schema fields: {missing}")
    if unanchored:
        raise ValueError(f"candidate fields missing anchors: {unanchored}")


def _missing_anchor_result(
    *,
    fixture_id: str,
    schema_ref: Ref,
    policy_refs: list[Ref],
    live_normalization_runtime_report_ref: Ref,
    normalization: NormalizationResult,
) -> SchemaExtractionRuntimeResult:
    try:
        _strategy_and_candidate(
            fixture_id=fixture_id,
            normalization=normalization,
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            model_trace_refs=[f"model-trace:{fixture_id}:schema-extraction"],
            tool_trace_refs=[f"tool-trace:{fixture_id}:extract-fields"],
            omit_anchor_for="summary",
        )
    except (ValueError, ValidationError) as exc:
        return _failure_result(
            fixture_id=fixture_id,
            failure=SchemaExtractionFailureType.MISSING_FIELD_ANCHOR,
            missing_field="candidate_field_anchor_refs",
            schema_ref=schema_ref,
            policy_refs=policy_refs,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            normalization=normalization,
            diagnostics=[str(exc)],
        )
    return _failure_result(
        fixture_id=fixture_id,
        failure=SchemaExtractionFailureType.MISSING_FIELD_ANCHOR,
        missing_field="candidate_field_anchor_refs",
        schema_ref=schema_ref,
        policy_refs=policy_refs,
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        normalization=normalization,
    )


def _drift_needs_review_result(
    *,
    fixture_id: str,
    schema_ref: Ref,
    policy_refs: list[Ref],
    live_normalization_runtime_report_ref: Ref,
    normalization: NormalizationResult,
    approved_exploratory_schema: bool,
) -> SchemaExtractionRuntimeResult:
    rejection_refs = [f"candidate-rejection:{fixture_id}:schema-drift"]
    strategy, candidate = _strategy_and_candidate(
        fixture_id=fixture_id,
        normalization=normalization,
        schema_ref=schema_ref,
        policy_refs=policy_refs,
        model_trace_refs=[f"model-trace:{fixture_id}:schema-extraction"],
        tool_trace_refs=[f"tool-trace:{fixture_id}:extract-fields"],
        status=ExtractionCandidateStatus.REJECTED,
        rejection_refs=rejection_refs,
    )
    report = _report(
        fixture_id=fixture_id,
        completion_result=CompletenessResult.NEEDS_REVIEW,
        operator_status=SchemaExtractionFailureType.DRIFT_REPAIR_REQUIRED.value,
        schema_ref=schema_ref,
        policy_refs=policy_refs,
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        normalization=normalization,
        strategy=strategy,
        candidate=candidate,
        approved_exploratory_schema_refs=(
            [f"schema-approval:{fixture_id}:exploratory"]
            if approved_exploratory_schema
            else []
        ),
        failure=SchemaExtractionFailureType.DRIFT_REPAIR_REQUIRED,
        failure_refs=[f"failure:{fixture_id}:schema-drift"],
        candidate_rejection_refs=rejection_refs,
        drift_signal_refs=[f"drift-signal:{fixture_id}:schema-fields"],
        repair_recommendation_refs=[f"repair-recommendation:{fixture_id}:schema-refresh"],
        diagnostics=["schema drift requires review before candidate acceptance"],
    )
    return SchemaExtractionRuntimeResult(report=report, strategy=strategy, candidate=candidate)


def _failure_result(
    *,
    fixture_id: str,
    failure: SchemaExtractionFailureType,
    missing_field: str,
    schema_ref: Ref,
    policy_refs: list[Ref],
    live_normalization_runtime_report_ref: Ref | None,
    normalization: NormalizationResult | None = None,
    publication_refs: list[Ref] | None = None,
    diagnostics: list[str] | None = None,
) -> SchemaExtractionRuntimeResult:
    report = _report(
        fixture_id=fixture_id,
        completion_result=CompletenessResult.FAIL,
        operator_status=failure.value,
        schema_ref=schema_ref,
        policy_refs=policy_refs,
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        normalization=normalization,
        publication_refs=publication_refs or [],
        failure=failure,
        failure_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_fields=[missing_field],
        diagnostics=diagnostics or [f"schema extraction runtime failed: {failure.value}"],
    )
    return SchemaExtractionRuntimeResult(report=report)


def _report(
    *,
    fixture_id: str,
    completion_result: CompletenessResult,
    operator_status: str,
    schema_ref: Ref,
    policy_refs: list[Ref],
    live_normalization_runtime_report_ref: Ref | None,
    normalization: NormalizationResult | None = None,
    strategy: ExtractionStrategy | None = None,
    candidate: ExtractionCandidate | None = None,
    approved_exploratory_schema_refs: list[Ref] | None = None,
    publication_refs: list[Ref] | None = None,
    failure: SchemaExtractionFailureType | None = None,
    failure_refs: list[Ref] | None = None,
    missing_fields: list[str] | None = None,
    candidate_rejection_refs: list[Ref] | None = None,
    drift_signal_refs: list[Ref] | None = None,
    repair_recommendation_refs: list[Ref] | None = None,
    diagnostics: list[str] | None = None,
) -> SchemaExtractionRuntimeReport:
    return SchemaExtractionRuntimeReport(
        id=f"schema-extraction-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        normalized_document_refs=_present([normalization.normalized_document.id])
        if normalization
        else [],
        source_anchor_refs=[anchor.id for anchor in normalization.anchors]
        if normalization
        else [],
        anchor_map_refs=_present([normalization.anchor_map.id]) if normalization else [],
        extraction_strategy_refs=_present([strategy.id]) if strategy else [],
        extraction_candidate_refs=_present([candidate.id]) if candidate else [],
        candidate_field_anchor_refs=(
            _dedupe(list(candidate.field_anchor_refs.values())) if candidate else []
        ),
        schema_refs=[schema_ref],
        schema_validation_refs=candidate.schema_validation_refs if candidate else [],
        approved_exploratory_schema_refs=approved_exploratory_schema_refs or [],
        model_trace_refs=candidate.model_trace_refs if candidate else [],
        tool_trace_refs=candidate.tool_trace_refs if candidate else [],
        confidence_refs=candidate.confidence_refs if candidate else [],
        candidate_rejection_refs=candidate_rejection_refs or [],
        drift_signal_refs=drift_signal_refs or [],
        repair_recommendation_refs=repair_recommendation_refs or [],
        artifact_refs=normalization.artifact_refs if normalization else [],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"durable-command:{fixture_id}:schema-extraction"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:schema-extraction"],
        outbox_refs=[f"outbox:{fixture_id}:schema-extraction"],
        replay_bundle_ref=(
            None
            if failure == SchemaExtractionFailureType.REPLAY_MISMATCH
            else f"replay-bundle:{fixture_id}:schema-extraction"
        ),
        publication_refs=publication_refs or [],
        failure_report_refs=failure_refs or [],
        missing_ref_fields=missing_fields or [],
        failure_type=failure,
        operator_status=operator_status,
        completion_result=completion_result,
        diagnostics=diagnostics or [],
    )


def _trace_refs(
    fixture_id: str,
    model_trace_refs: list[Ref] | None,
    tool_trace_refs: list[Ref] | None,
) -> tuple[list[Ref], list[Ref]]:
    return (
        model_trace_refs
        if model_trace_refs is not None
        else [f"model-trace:{fixture_id}:schema-extraction"],
        tool_trace_refs
        if tool_trace_refs is not None
        else [f"tool-trace:{fixture_id}:extract-fields"],
    )


def _present(refs: list[Ref | None]) -> list[Ref]:
    return [ref for ref in refs if ref is not None]


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(refs))
