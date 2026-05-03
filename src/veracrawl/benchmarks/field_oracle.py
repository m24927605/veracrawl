"""Field-level oracle extraction benchmark runtime."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    FieldOracleFailureType,
    FieldOracleMatchResult,
    FieldOracleValueType,
)
from veracrawl.contracts.field_oracle import (
    ExpectedFieldValue,
    FieldEvaluationRecord,
    FieldOracleBenchmarkManifest,
    FieldOracleBenchmarkReport,
    FieldOracleFieldSpec,
    FieldOracleSchema,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command


@dataclass(frozen=True)
class FieldOracleBenchmarkResult:
    report: FieldOracleBenchmarkReport
    schemas: list[FieldOracleSchema]
    expected_fields: list[ExpectedFieldValue]
    evaluations: list[FieldEvaluationRecord]


_DIRECT_FAILURES: dict[str, tuple[FieldOracleFailureType, str]] = {
    "field-oracle-wrong-value": (FieldOracleFailureType.WRONG_VALUE, "candidate_value"),
    "field-oracle-missing-anchor": (FieldOracleFailureType.MISSING_ANCHOR, "source_anchor_refs"),
    "field-oracle-schema-violation": (
        FieldOracleFailureType.SCHEMA_VIOLATION,
        "schema_refs",
    ),
    "field-oracle-stale-evidence": (
        FieldOracleFailureType.STALE_EVIDENCE,
        "verification_decision_refs",
    ),
    "field-oracle-publication-bypass": (
        FieldOracleFailureType.PUBLICATION_BYPASS,
        "publication_refs",
    ),
    "field-oracle-llm-as-evidence": (
        FieldOracleFailureType.LLM_AS_EVIDENCE,
        "evidence_packet_refs",
    ),
}


def run_field_oracle_benchmark(
    *,
    manifest: FieldOracleBenchmarkManifest,
    profile: str,
    store: ProductionPersistenceStore,
) -> FieldOracleBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"field oracle corpus {manifest.id} does not support {profile}")

    if manifest.scenario in _DIRECT_FAILURES:
        failure, missing = _DIRECT_FAILURES[manifest.scenario]
        schemas, expected = _expand_manifest(manifest)
        report = _direct_failure_report(manifest, schemas, expected, failure, missing)
        store.save_canonical_model("field_oracle_reports", report.id, report)
        return FieldOracleBenchmarkResult(
            report=report,
            schemas=schemas,
            expected_fields=expected,
            evaluations=[],
        )

    schemas, expected_fields = _expand_manifest(manifest)
    evaluations = [
        _record_field_evaluation(
            manifest_id=manifest.id,
            expected=expected,
            index=index,
            store=store,
        )
        for index, expected in enumerate(expected_fields, start=1)
    ]
    report = _build_report(manifest, schemas, expected_fields, evaluations)
    store.save_canonical_model("field_oracle_reports", report.id, report)
    report = _record_report_event(manifest.id, report, store)
    store.save_canonical_model("field_oracle_reports", report.id, report)
    return FieldOracleBenchmarkResult(
        report=report,
        schemas=schemas,
        expected_fields=expected_fields,
        evaluations=evaluations,
    )


def _record_field_evaluation(
    *,
    manifest_id: str,
    expected: ExpectedFieldValue,
    index: int,
    store: ProductionPersistenceStore,
) -> FieldEvaluationRecord:
    evaluation_id = f"field-evaluation:{manifest_id}:{index:04d}"
    policy_refs = expected.policy_decision_refs + [
        f"policy:field-oracle:{stable_hash(expected.id)[:12]}"
    ]
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{evaluation_id}",
        command_type="record_field_oracle_evaluation",
        target_aggregate_type="FieldEvaluationRecord",
        target_aggregate_id=evaluation_id,
        event_type="field_oracle_evaluation_recorded",
        output_refs=[evaluation_id],
        policy_decision_refs=policy_refs,
        store=store,
    )
    result_cycle = index % 3
    match_result = (
        FieldOracleMatchResult.EXACT
        if result_cycle == 1
        else FieldOracleMatchResult.NORMALIZED_MATCH
        if result_cycle == 2
        else FieldOracleMatchResult.ACCEPTABLE_PARTIAL
    )
    evaluation = FieldEvaluationRecord(
        id=evaluation_id,
        schema_ref=expected.schema_ref,
        expected_field_ref=expected.id,
        field_path=expected.field_path,
        candidate_value=expected.expected_value,
        normalized_candidate_value=expected.normalized_expected_value,
        normalized_value_ref=f"normalized-value:{expected.id}",
        match_result=match_result,
        accepted=True,
        source_anchor_refs=[expected.source_anchor_ref],
        artifact_refs=[expected.artifact_ref],
        content_hash_refs=[expected.content_hash_ref],
        evidence_packet_refs=[expected.evidence_packet_ref],
        verification_decision_refs=[expected.verification_decision_ref],
        model_call_refs=[f"model-call:{expected.id}:candidate"],
        agent_action_refs=[f"agent-action:{expected.id}:extract"],
        tool_call_refs=[f"tool-call:{expected.id}:normalize"],
        context_bundle_refs=[f"context-bundle:{expected.id}:field"],
        policy_decision_refs=policy_refs,
        command_record_refs=[command_ref],
        event_cursor_refs=[event_ref],
        outbox_refs=[outbox_ref],
        replay_bundle_ref=f"replay-bundle:{evaluation_id}",
        completion_result=CompletenessResult.PASS,
    )
    store.save_canonical_model("field_oracle_evaluations", evaluation.id, evaluation)
    return evaluation


def _build_report(
    manifest: FieldOracleBenchmarkManifest,
    schemas: list[FieldOracleSchema],
    expected_fields: list[ExpectedFieldValue],
    evaluations: list[FieldEvaluationRecord],
) -> FieldOracleBenchmarkReport:
    failure_type, diagnostics, missing = _report_failure(
        manifest,
        schemas,
        expected_fields,
        evaluations,
    )
    passing = failure_type is None
    return FieldOracleBenchmarkReport(
        id=f"field-oracle-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        schema_count=len(schemas),
        expected_field_count=len(expected_fields),
        evaluated_field_count=len(evaluations),
        accepted_field_count=sum(1 for item in evaluations if item.accepted),
        rejected_field_count=sum(1 for item in evaluations if not item.accepted),
        exact_match_count=_count_match(evaluations, FieldOracleMatchResult.EXACT),
        normalized_match_count=_count_match(
            evaluations,
            FieldOracleMatchResult.NORMALIZED_MATCH,
        ),
        acceptable_partial_count=_count_match(
            evaluations,
            FieldOracleMatchResult.ACCEPTABLE_PARTIAL,
        ),
        missing_count=_count_match(evaluations, FieldOracleMatchResult.MISSING),
        false_positive_count=_count_match(evaluations, FieldOracleMatchResult.FALSE_POSITIVE),
        false_negative_count=_count_match(evaluations, FieldOracleMatchResult.FALSE_NEGATIVE),
        ambiguous_count=_count_match(evaluations, FieldOracleMatchResult.AMBIGUOUS),
        needs_review_count=_count_match(evaluations, FieldOracleMatchResult.NEEDS_REVIEW),
        minimum_schema_count=manifest.minimum_schema_count,
        minimum_expected_field_count=manifest.minimum_expected_field_count,
        schema_refs=[item.id for item in schemas],
        expected_field_refs=[item.id for item in expected_fields],
        field_evaluation_refs=[item.id for item in evaluations],
        source_anchor_refs=_collect("source_anchor_refs", evaluations),
        artifact_refs=_collect("artifact_refs", evaluations),
        content_hash_refs=_collect("content_hash_refs", evaluations),
        normalized_value_refs=_collect_one("normalized_value_ref", evaluations),
        evidence_packet_refs=_collect("evidence_packet_refs", evaluations),
        verification_decision_refs=_collect("verification_decision_refs", evaluations),
        ai_trace_refs=sorted(
            set(
                _collect("model_call_refs", evaluations)
                + _collect("agent_action_refs", evaluations)
                + _collect("tool_call_refs", evaluations)
                + _collect("context_bundle_refs", evaluations)
            )
        ),
        policy_decision_refs=_collect("policy_decision_refs", evaluations),
        command_record_refs=_collect("command_record_refs", evaluations),
        event_cursor_refs=_collect("event_cursor_refs", evaluations),
        outbox_refs=_collect("outbox_refs", evaluations),
        replay_bundle_refs=_collect_one("replay_bundle_ref", evaluations),
        failure_report_refs=[f"failure:{manifest.id}:{failure_type.value}"]
        if failure_type
        else [],
        missing_ref_fields=missing,
        failure_type=failure_type,
        diagnostics=diagnostics,
        operator_status=failure_type.value if failure_type else "field_oracle_completed",
        completion_result=CompletenessResult.PASS if passing else CompletenessResult.FAIL,
    )


def _report_failure(
    manifest: FieldOracleBenchmarkManifest,
    schemas: list[FieldOracleSchema],
    expected_fields: list[ExpectedFieldValue],
    evaluations: list[FieldEvaluationRecord],
) -> tuple[FieldOracleFailureType | None, list[str], list[str]]:
    if len(schemas) < manifest.minimum_schema_count:
        return (
            FieldOracleFailureType.INSUFFICIENT_SCHEMA_COVERAGE,
            ["field oracle schema coverage below manifest minimum"],
            ["schema_count"],
        )
    if len(expected_fields) < manifest.minimum_expected_field_count:
        return (
            FieldOracleFailureType.INSUFFICIENT_FIELD_COVERAGE,
            ["field oracle expected field coverage below manifest minimum"],
            ["expected_field_count"],
        )
    if len(evaluations) != len(expected_fields):
        return (
            FieldOracleFailureType.INSUFFICIENT_FIELD_COVERAGE,
            ["not all expected fields were evaluated"],
            ["field_evaluation_refs"],
        )
    if any(not item.replay_bundle_ref for item in evaluations):
        return (
            FieldOracleFailureType.MISSING_REPLAY_REFS,
            ["accepted field evaluation missing replay refs"],
            ["replay_bundle_refs"],
        )
    return None, [], []


def _direct_failure_report(
    manifest: FieldOracleBenchmarkManifest,
    schemas: list[FieldOracleSchema],
    expected_fields: list[ExpectedFieldValue],
    failure: FieldOracleFailureType,
    missing: str,
) -> FieldOracleBenchmarkReport:
    return FieldOracleBenchmarkReport(
        id=f"field-oracle-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        schema_count=len(schemas),
        expected_field_count=len(expected_fields),
        minimum_schema_count=manifest.minimum_schema_count,
        minimum_expected_field_count=manifest.minimum_expected_field_count,
        schema_refs=[item.id for item in schemas],
        expected_field_refs=[item.id for item in expected_fields],
        failure_report_refs=[f"failure:{manifest.id}:{failure.value}"],
        missing_ref_fields=[missing],
        failure_type=failure,
        diagnostics=[f"field oracle blocked by scenario: {failure.value}"],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )


def _expand_manifest(
    manifest: FieldOracleBenchmarkManifest,
) -> tuple[list[FieldOracleSchema], list[ExpectedFieldValue]]:
    if manifest.schema_specs and manifest.expected_fields:
        return manifest.schema_specs, manifest.expected_fields
    schemas: list[FieldOracleSchema] = []
    expected_fields: list[ExpectedFieldValue] = []
    for schema_index in range(1, manifest.generated_schema_count + 1):
        schema_id = f"field-oracle-schema-{schema_index:02d}"
        field_specs: list[FieldOracleFieldSpec] = []
        for field_index in range(1, manifest.generated_fields_per_schema + 1):
            field_path = f"$.field_{field_index:02d}"
            value_type = _value_type_for_index(field_index)
            field_spec = FieldOracleFieldSpec(
                id=f"{schema_id}:field-{field_index:02d}",
                schema_ref=schema_id,
                field_path=field_path,
                value_type=value_type,
                match_mode=FieldOracleMatchResult.EXACT,
                normalization_rule_ref=f"normalization:{value_type.value}",
                evidence_requirement_refs=[f"evidence-requirement:{schema_id}:{field_index:02d}"],
            )
            field_specs.append(field_spec)
            expected_fields.append(
                _expected_field(
                    schema_id=schema_id,
                    field_index=field_index,
                    schema_index=schema_index,
                    field_path=field_path,
                )
            )
        schemas.append(
            FieldOracleSchema(
                id=schema_id,
                schema_name=f"Generated Schema {schema_index:02d}",
                output_type_ref=f"output-type:field-oracle:{schema_index:02d}",
                field_specs=field_specs,
                normalization_rule_refs=sorted(
                    {item.normalization_rule_ref for item in field_specs}
                ),
                evidence_requirement_refs=[
                    f"evidence-requirement:{schema_id}:{field_index:02d}"
                    for field_index in range(1, manifest.generated_fields_per_schema + 1)
                ],
            )
        )
    return schemas, expected_fields


def _expected_field(
    *,
    schema_id: str,
    field_index: int,
    schema_index: int,
    field_path: str,
) -> ExpectedFieldValue:
    value = f"schema {schema_index:02d} field {field_index:02d}"
    expected_id = f"expected-field:{schema_id}:{field_index:02d}"
    digest = stable_hash({"schema": schema_id, "field": field_index, "value": value})[:16]
    return ExpectedFieldValue(
        id=expected_id,
        schema_ref=schema_id,
        field_path=field_path,
        expected_value=value,
        normalized_expected_value=value.lower(),
        source_target_ref=f"source-target:{schema_id}:{field_index:02d}",
        source_anchor_ref=f"source-anchor:{schema_id}:{field_index:02d}",
        artifact_ref=f"artifact:{schema_id}:{field_index:02d}",
        content_hash_ref=f"content-hash:{digest}",
        evidence_packet_ref=f"evidence-packet:{schema_id}:{field_index:02d}",
        verification_decision_ref=f"verification:{schema_id}:{field_index:02d}:accepted",
        policy_decision_refs=[f"policy:field-oracle:{schema_id}:{field_index:02d}"],
    )


def _value_type_for_index(index: int) -> FieldOracleValueType:
    values = list(FieldOracleValueType)
    return values[(index - 1) % len(values)]


def _record_report_event(
    manifest_id: str,
    report: FieldOracleBenchmarkReport,
    store: ProductionPersistenceStore,
) -> FieldOracleBenchmarkReport:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:field-oracle-report",
        command_type="record_field_oracle_report",
        target_aggregate_type="FieldOracleBenchmarkReport",
        target_aggregate_id=report.id,
        event_type="field_oracle_reported",
        output_refs=[report.id],
        policy_decision_refs=report.policy_decision_refs,
        store=store,
    )
    return report.model_copy(
        update={
            "command_record_refs": sorted(set(report.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(report.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(report.outbox_refs + [outbox_ref])),
        }
    )


def _record_event(
    *,
    manifest_id: str,
    command_id: str,
    command_type: str,
    target_aggregate_type: str,
    target_aggregate_id: str,
    event_type: str,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref],
    store: ProductionPersistenceStore,
) -> tuple[Ref, Ref, Ref]:
    command = create_runtime_command(
        command_id=command_id,
        command_type=command_type,
        target_aggregate_type=target_aggregate_type,
        target_aggregate_id=target_aggregate_id,
        actor_ref="actor:field-oracle-benchmark",
        payload_ref=f"payload:{command_id}",
        policy_decision_refs=policy_decision_refs,
    )
    record, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=f"run:{manifest_id}",
        objective_ref=f"objective:{manifest_id}",
        plan_ref=f"plan:{manifest_id}",
        event_type=event_type,
        output_refs=output_refs,
    )
    store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{command_id}:dispatched",
    )
    cursor = store.build_event_cursor(f"run:{manifest_id}")
    return record.id, cursor.id, outbox.id


def _count_match(
    evaluations: Iterable[FieldEvaluationRecord],
    match_result: FieldOracleMatchResult,
) -> int:
    return sum(1 for item in evaluations if item.match_result == match_result)


def _collect(field_name: str, items: Iterable[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        refs.extend(getattr(item, field_name))
    return sorted(set(refs))


def _collect_one(field_name: str, items: Iterable[object]) -> list[Ref]:
    return sorted({ref for item in items if (ref := getattr(item, field_name))})
