"""Result publication, Result API, and export runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    ExportAttemptStatus,
    ExportCorrectionStatus,
    ExportDeliveryMode,
    ExportJobStatus,
    ExportPropagationStatus,
    ExportRetryClassification,
    ExportTargetType,
    ExportWithdrawalReason,
    ExportWithdrawalStatus,
    PolicyDecisionValue,
    ResultPublicationExportFailureType,
    VerificationDecisionValue,
)
from veracrawl.contracts.export import (
    ExportAttempt,
    ExportCorrectionRecord,
    ExportDeliveryReceipt,
    ExportJob,
    ExportTargetSpec,
    ExportWithdrawalAttempt,
    ExportWithdrawalJob,
)
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.contracts.publication import (
    OutputManifest,
    PublicationReport,
    PublishedOutput,
    ResultApiSnapshot,
    ResultPublicationExportRuntimeReport,
)
from veracrawl.contracts.verification import ReviewDecision, VerificationDecision
from veracrawl.evidence.coverage import EvidenceBuildResult
from veracrawl.policy.gates import decision_for
from veracrawl.publish.gates import PublicationOutcome, publish_evidence_backed_output


@dataclass(frozen=True)
class ResultPublicationExportRuntimeResult:
    report: ResultPublicationExportRuntimeReport
    publication: PublicationOutcome | None = None
    result_api_snapshot: ResultApiSnapshot | None = None
    export_target: ExportTargetSpec | None = None
    export_jobs: list[ExportJob] | None = None
    export_attempts: list[ExportAttempt] | None = None
    delivery_receipts: list[ExportDeliveryReceipt] | None = None
    withdrawal_jobs: list[ExportWithdrawalJob] | None = None
    withdrawal_attempts: list[ExportWithdrawalAttempt] | None = None
    correction_records: list[ExportCorrectionRecord] | None = None


def run_result_publication_export_runtime(
    *,
    fixture_id: str,
    scenario: str,
    live_evidence_runtime_report_ref: Ref | None,
    candidate: ExtractionCandidate | None,
    evidence: EvidenceBuildResult | None,
    verification: VerificationDecision | None,
    review: ReviewDecision | None,
) -> ResultPublicationExportRuntimeResult:
    if (
        live_evidence_runtime_report_ref is None
        or candidate is None
        or evidence is None
        or verification is None
        or review is None
    ):
        return _failure_result(
            fixture_id=fixture_id,
            failure=ResultPublicationExportFailureType.MISSING_LIVE_EVIDENCE,
            missing_field="live_evidence_runtime_report_ref",
            live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
        )

    if scenario == "result-publication-direct-export-bypass":
        return _failure_result(
            fixture_id=fixture_id,
            failure=ResultPublicationExportFailureType.DIRECT_EXPORT_BYPASS,
            missing_field="published_output_refs",
            live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
            candidate=candidate,
            evidence=evidence,
            verification=verification,
            review=review,
            direct_export_bypass_refs=[f"direct-export:{fixture_id}:candidate-only"],
        )

    if scenario == "result-publication-privacy-missing":
        return _failure_result(
            fixture_id=fixture_id,
            failure=ResultPublicationExportFailureType.PRIVACY_MISSING,
            missing_field="privacy_lifecycle_refs",
            live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
            candidate=candidate,
            evidence=evidence,
            verification=verification,
            review=review,
        )

    if scenario == "result-publication-replay-mismatch":
        return _failure_result(
            fixture_id=fixture_id,
            failure=ResultPublicationExportFailureType.REPLAY_MISMATCH,
            missing_field="replay_bundle_ref",
            live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
            candidate=candidate,
            evidence=evidence,
            verification=verification,
            review=review,
            replay_bundle_ref=None,
        )

    publication_policy = _policy(
        fixture_id=fixture_id,
        decision_type="runtime_publication",
        subject_ref=candidate.id,
        allow=scenario != "result-publication-policy-denied",
    )
    runtime_verification = verification
    if scenario == "result-publication-verification-not-accepted":
        runtime_verification = verification.model_copy(
            update={"decision": VerificationDecisionValue.REVIEW}
        )
    publication = publish_evidence_backed_output(
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        candidate=candidate,
        coverage=evidence.coverage,
        evidence_packet=evidence.packet,
        evidence_manifest=evidence.manifest,
        verification=runtime_verification,
        review=review,
        publication_policy=publication_policy,
        privacy_lifecycle_refs=_privacy_refs(fixture_id),
        replay_bundle_ref=f"replay-bundle:{fixture_id}:result-publication",
        command_record_refs=[f"durable-command:{fixture_id}:publication"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:publication"],
        outbox_refs=[f"outbox:{fixture_id}:publication"],
    )
    if publication.report.completion_result != CompletenessResult.PASS:
        failure = (
            ResultPublicationExportFailureType.PUBLICATION_POLICY_DENIED
            if publication_policy.decision != PolicyDecisionValue.ALLOW
            else ResultPublicationExportFailureType.VERIFICATION_NOT_ACCEPTED
        )
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=failure.value,
            live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
            candidate=candidate,
            evidence=evidence,
            verification=runtime_verification,
            review=review,
            publication_report=publication.report,
            policy_refs=[publication_policy.id],
            diagnostics=publication.report.failure_report_refs,
        )

    if publication.published_output is None or publication.output_manifest is None:
        return _failure_result(
            fixture_id=fixture_id,
            failure=ResultPublicationExportFailureType.MISSING_OUTPUT_MANIFEST,
            missing_field="output_manifest_refs",
            live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
            candidate=candidate,
            evidence=evidence,
            verification=runtime_verification,
            review=review,
            publication_report=publication.report,
            policy_refs=[publication_policy.id],
        )

    if scenario == "result-publication-missing-output-manifest":
        return _failure_result(
            fixture_id=fixture_id,
            failure=ResultPublicationExportFailureType.MISSING_OUTPUT_MANIFEST,
            missing_field="output_manifest_refs",
            live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
            candidate=candidate,
            evidence=evidence,
            verification=runtime_verification,
            review=review,
            publication_report=publication.report,
            published_output=publication.published_output,
            policy_refs=[publication_policy.id],
        )

    result_api = _result_api_snapshot(
        fixture_id=fixture_id,
        published_output=publication.published_output,
        output_manifest=publication.output_manifest,
    )
    target_type = (
        ExportTargetType.API
        if scenario == "result-publication-api-success"
        else ExportTargetType.FILE
    )
    export_policy = _policy(
        fixture_id=fixture_id,
        decision_type="export_dispatch",
        subject_ref=publication.output_manifest.id,
        allow=True,
    )
    export_set = _build_export_set(
        fixture_id=fixture_id,
        target_type=target_type,
        output_ref=publication.published_output.id,
        output_manifest=publication.output_manifest,
        export_policy_ref=export_policy.id,
        include_receipt=scenario != "result-publication-export-missing-receipt",
        include_withdrawal=(
            scenario
            not in {
                "result-publication-export-missing-receipt",
                "result-publication-withdrawal-missing-propagation",
                "result-publication-correction-without-withdrawal",
            }
        ),
        include_correction=scenario != "result-publication-correction-without-withdrawal",
    )
    export_failure = _export_failure_for(scenario)
    if export_failure is not None:
        return _failure_result(
            fixture_id=fixture_id,
            failure=export_failure,
            missing_field=_missing_field_for(export_failure),
            live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
            candidate=candidate,
            evidence=evidence,
            verification=runtime_verification,
            review=review,
            publication_report=publication.report,
            published_output=publication.published_output,
            output_manifest=publication.output_manifest,
            result_api_snapshot=result_api,
            export_set=export_set,
            policy_refs=[publication_policy.id, export_policy.id],
        )

    report = _report(
        fixture_id=fixture_id,
        completion_result=CompletenessResult.PASS,
        operator_status="result_publication_export_completed",
        live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
        candidate=candidate,
        evidence=evidence,
        verification=runtime_verification,
        review=review,
        publication_report=publication.report,
        published_output=publication.published_output,
        output_manifest=publication.output_manifest.model_copy(
            update={
                "export_lifecycle_refs": [
                    *[job.id for job in export_set.export_jobs],
                    *[receipt.id for receipt in export_set.delivery_receipts],
                ]
            }
        ),
        result_api_snapshot=result_api,
        export_set=export_set,
        policy_refs=[publication_policy.id, export_policy.id],
    )
    return ResultPublicationExportRuntimeResult(
        report=report,
        publication=publication,
        result_api_snapshot=result_api,
        export_target=export_set.target,
        export_jobs=export_set.export_jobs,
        export_attempts=export_set.export_attempts,
        delivery_receipts=export_set.delivery_receipts,
        withdrawal_jobs=export_set.withdrawal_jobs,
        withdrawal_attempts=export_set.withdrawal_attempts,
        correction_records=export_set.correction_records,
    )


@dataclass(frozen=True)
class _ExportSet:
    target: ExportTargetSpec
    export_jobs: list[ExportJob]
    export_attempts: list[ExportAttempt]
    delivery_receipts: list[ExportDeliveryReceipt]
    withdrawal_jobs: list[ExportWithdrawalJob]
    withdrawal_attempts: list[ExportWithdrawalAttempt]
    correction_records: list[ExportCorrectionRecord]
    destination_mapping_refs: list[Ref]


def _build_export_set(
    *,
    fixture_id: str,
    target_type: ExportTargetType,
    output_ref: Ref,
    output_manifest: OutputManifest,
    export_policy_ref: Ref,
    include_receipt: bool,
    include_withdrawal: bool,
    include_correction: bool,
) -> _ExportSet:
    target = ExportTargetSpec(
        id=f"export-target:{fixture_id}",
        project_id=f"project:{fixture_id}",
        target_type=target_type,
        destination_ref=f"destination:{fixture_id}:{target_type.value}",
        destination_schema_ref=f"destination-schema:{fixture_id}:v1",
        auth_scope_ref=f"auth-scope:{fixture_id}:redacted",
        delivery_mode=ExportDeliveryMode.BATCH,
        idempotency_key_template="{project_id}:{target_id}:{output_manifest_hash}",
        policy_decision_refs=[export_policy_ref],
    )
    export_attempt = ExportAttempt(
        id=f"export-attempt:{fixture_id}:1",
        export_job_id=f"export-job:{fixture_id}",
        attempt_number=1,
        idempotency_key=stable_hash(
            {"fixture": fixture_id, "manifest": output_manifest.manifest_hash}
        ),
        output_refs=[output_ref],
        external_object_ids=[f"external-object:{fixture_id}:v1"] if include_receipt else [],
        delivery_receipt_ref=f"export-receipt:{fixture_id}" if include_receipt else None,
        status=ExportAttemptStatus.COMPLETED if include_receipt else ExportAttemptStatus.FAILED,
        error={}
        if include_receipt
        else {"error": "delivery receipt missing after dispatch"},
        retry_classification=None
        if include_receipt
        else ExportRetryClassification.PERMANENT,
    )
    receipts: list[ExportDeliveryReceipt] = []
    if include_receipt:
        receipts.append(
            _receipt(
                fixture_id=fixture_id,
                attempt_ref=export_attempt.id,
                destination_ref=target.destination_ref,
                delivered_refs=[output_ref],
                withdrawn_refs=[],
            )
        )
    export_job = ExportJob(
        id=f"export-job:{fixture_id}",
        run_id=f"run:{fixture_id}",
        export_target_spec_id=target.id,
        output_refs=[output_ref],
        destination_schema_version="v1",
        policy_decision_refs=[export_policy_ref],
        attempt_refs=[export_attempt.id],
        delivery_receipt_refs=[receipt.id for receipt in receipts],
        idempotency_key_refs=[f"idempotency-key:{fixture_id}:export"],
        status=ExportJobStatus.COMPLETED if include_receipt else ExportJobStatus.FAILED,
    )
    withdrawal_jobs: list[ExportWithdrawalJob] = []
    withdrawal_attempts: list[ExportWithdrawalAttempt] = []
    if include_withdrawal:
        withdrawal_attempt = ExportWithdrawalAttempt(
            id=f"export-withdrawal-attempt:{fixture_id}:1",
            export_withdrawal_job_id=f"export-withdrawal-job:{fixture_id}",
            attempt_number=1,
            idempotency_key=stable_hash({"withdraw": fixture_id, "output": output_ref}),
            external_object_mappings={output_ref: [f"external-object:{fixture_id}:v1"]},
            propagation_status=ExportPropagationStatus.PROPAGATED,
            delivery_receipt_ref=f"export-receipt:{fixture_id}:withdrawal",
        )
        withdrawal_receipt = _receipt(
            fixture_id=f"{fixture_id}:withdrawal",
            attempt_ref=withdrawal_attempt.id,
            destination_ref=target.destination_ref,
            delivered_refs=[],
            withdrawn_refs=[output_ref],
        )
        receipts.append(withdrawal_receipt)
        withdrawal_attempts.append(withdrawal_attempt)
        withdrawal_jobs.append(
            ExportWithdrawalJob(
                id=f"export-withdrawal-job:{fixture_id}",
                project_id=f"project:{fixture_id}",
                export_target_spec_id=target.id,
                output_version_refs=[output_ref],
                reason=ExportWithdrawalReason.SUPERSEDED,
                policy_decision_refs=[export_policy_ref],
                withdrawal_attempt_refs=[withdrawal_attempt.id],
                status=ExportWithdrawalStatus.COMPLETED,
            )
        )
    correction_records: list[ExportCorrectionRecord] = []
    replacement_ref = f"published-output:{fixture_id}:replacement"
    replacement_job = ExportJob(
        id=f"export-job:{fixture_id}:replacement",
        run_id=f"run:{fixture_id}",
        export_target_spec_id=target.id,
        output_refs=[replacement_ref],
        destination_schema_version="v1",
        policy_decision_refs=[export_policy_ref],
        idempotency_key_refs=[f"idempotency-key:{fixture_id}:replacement"],
        status=ExportJobStatus.QUEUED,
    )
    export_jobs = [export_job, replacement_job]
    if include_correction and include_withdrawal:
        correction_records.append(
            ExportCorrectionRecord(
                id=f"export-correction:{fixture_id}",
                project_id=f"project:{fixture_id}",
                superseded_output_ref=output_ref,
                replacement_output_ref=replacement_ref,
                withdrawal_job_ref=f"export-withdrawal-job:{fixture_id}",
                replacement_export_job_ref=replacement_job.id,
                destination_object_mappings={
                    output_ref: [f"external-object:{fixture_id}:v1"],
                    replacement_ref: [f"external-object:{fixture_id}:replacement"],
                },
                receipt_refs=[receipt.id for receipt in receipts],
                policy_decision_refs=[export_policy_ref],
                status=ExportCorrectionStatus.PROPAGATED,
            )
        )
    return _ExportSet(
        target=target,
        export_jobs=export_jobs,
        export_attempts=[export_attempt],
        delivery_receipts=receipts,
        withdrawal_jobs=withdrawal_jobs,
        withdrawal_attempts=withdrawal_attempts,
        correction_records=correction_records,
        destination_mapping_refs=[f"destination-object-mapping:{fixture_id}"]
        if include_receipt
        else [],
    )


def _receipt(
    *,
    fixture_id: str,
    attempt_ref: Ref,
    destination_ref: Ref,
    delivered_refs: list[Ref],
    withdrawn_refs: list[Ref],
) -> ExportDeliveryReceipt:
    external_ids = [
        f"external-object:{fixture_id}:{index}"
        for index, _ in enumerate(delivered_refs or withdrawn_refs, start=1)
    ]
    payload = {
        "attempt_ref": attempt_ref,
        "destination_ref": destination_ref,
        "external_object_ids": external_ids,
        "delivered_refs": delivered_refs,
        "withdrawn_refs": withdrawn_refs,
    }
    return ExportDeliveryReceipt(
        id=f"export-receipt:{fixture_id}",
        export_attempt_id=attempt_ref,
        destination_ref=destination_ref,
        external_object_ids=external_ids,
        delivered_output_refs=delivered_refs,
        withdrawn_output_refs=withdrawn_refs,
        delete_propagation_refs=[f"delete-propagation:{fixture_id}"]
        if withdrawn_refs
        else [],
        receipt_hash=stable_hash(payload),
    )


def _result_api_snapshot(
    *,
    fixture_id: str,
    published_output: PublishedOutput,
    output_manifest: OutputManifest,
) -> ResultApiSnapshot:
    payload = {
        "published_output_refs": [published_output.id],
        "output_manifest_refs": [output_manifest.id],
        "manifest_hash": output_manifest.manifest_hash,
    }
    return ResultApiSnapshot(
        id=f"result-api-snapshot:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        published_output_refs=[published_output.id],
        output_manifest_refs=[output_manifest.id],
        response_artifact_ref=f"artifact:{fixture_id}:result-api-response",
        response_schema_ref="schema:result-api:v1",
        privacy_lifecycle_refs=_privacy_refs(fixture_id),
        replay_bundle_ref=f"replay-bundle:{fixture_id}:result-publication",
        response_hash=stable_hash(payload),
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: ResultPublicationExportFailureType,
    missing_field: str,
    live_evidence_runtime_report_ref: Ref | None,
    candidate: ExtractionCandidate | None = None,
    evidence: EvidenceBuildResult | None = None,
    verification: VerificationDecision | None = None,
    review: ReviewDecision | None = None,
    publication_report: PublicationReport | None = None,
    published_output: PublishedOutput | None = None,
    output_manifest: OutputManifest | None = None,
    result_api_snapshot: ResultApiSnapshot | None = None,
    export_set: _ExportSet | None = None,
    policy_refs: list[Ref] | None = None,
    direct_export_bypass_refs: list[Ref] | None = None,
    replay_bundle_ref: Ref | None = "",
    diagnostics: list[str] | None = None,
) -> ResultPublicationExportRuntimeResult:
    report = _report(
        fixture_id=fixture_id,
        completion_result=CompletenessResult.FAIL
        if failure
        not in {
            ResultPublicationExportFailureType.VERIFICATION_NOT_ACCEPTED,
            ResultPublicationExportFailureType.WITHDRAWAL_MISSING_PROPAGATION,
        }
        else CompletenessResult.NEEDS_REVIEW,
        operator_status=failure.value,
        live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
        candidate=candidate,
        evidence=evidence,
        verification=verification,
        review=review,
        publication_report=publication_report,
        published_output=published_output,
        output_manifest=output_manifest,
        result_api_snapshot=result_api_snapshot,
        export_set=export_set,
        policy_refs=policy_refs or [],
        failure=failure,
        failure_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_fields=[missing_field],
        direct_export_bypass_refs=direct_export_bypass_refs or [],
        replay_bundle_ref=(
            replay_bundle_ref
            if replay_bundle_ref != ""
            else f"replay-bundle:{fixture_id}:result-publication"
        ),
        diagnostics=diagnostics or [f"result publication/export failed: {failure.value}"],
    )
    return ResultPublicationExportRuntimeResult(
        report=report,
        publication=PublicationOutcome(report=publication_report)
        if publication_report
        else None,
        result_api_snapshot=result_api_snapshot,
        export_target=export_set.target if export_set else None,
        export_jobs=export_set.export_jobs if export_set else None,
        export_attempts=export_set.export_attempts if export_set else None,
        delivery_receipts=export_set.delivery_receipts if export_set else None,
        withdrawal_jobs=export_set.withdrawal_jobs if export_set else None,
        withdrawal_attempts=export_set.withdrawal_attempts if export_set else None,
        correction_records=export_set.correction_records if export_set else None,
    )


def _report(
    *,
    fixture_id: str,
    completion_result: CompletenessResult,
    operator_status: str,
    live_evidence_runtime_report_ref: Ref | None,
    candidate: ExtractionCandidate | None,
    evidence: EvidenceBuildResult | None,
    verification: VerificationDecision | None,
    review: ReviewDecision | None,
    publication_report: PublicationReport | None = None,
    published_output: PublishedOutput | None = None,
    output_manifest: OutputManifest | None = None,
    result_api_snapshot: ResultApiSnapshot | None = None,
    export_set: _ExportSet | None = None,
    policy_refs: list[Ref] | None = None,
    failure: ResultPublicationExportFailureType | None = None,
    failure_refs: list[Ref] | None = None,
    missing_fields: list[str] | None = None,
    direct_export_bypass_refs: list[Ref] | None = None,
    replay_bundle_ref: Ref | None = None,
    diagnostics: list[str] | None = None,
) -> ResultPublicationExportRuntimeReport:
    actual_replay_ref: Ref | None = (
        replay_bundle_ref
        if replay_bundle_ref is not None
        else f"replay-bundle:{fixture_id}:result-publication"
    )
    if failure == ResultPublicationExportFailureType.REPLAY_MISMATCH:
        actual_replay_ref = None
    command_refs = [
        f"durable-command:{fixture_id}:publication",
        f"durable-command:{fixture_id}:export",
    ]
    event_refs = [
        f"event-cursor:{fixture_id}:publication",
        f"event-cursor:{fixture_id}:export",
    ]
    outbox_refs = [f"outbox:{fixture_id}:publication", f"outbox:{fixture_id}:export"]
    if failure == ResultPublicationExportFailureType.REPLAY_MISMATCH:
        command_refs = []
        event_refs = []
        outbox_refs = []
    return ResultPublicationExportRuntimeReport(
        id=f"result-publication-export-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_evidence_runtime_report_ref=live_evidence_runtime_report_ref,
        extraction_candidate_refs=_present([candidate.id]) if candidate else [],
        evidence_coverage_refs=_present([evidence.coverage.id]) if evidence else [],
        evidence_packet_refs=_present([evidence.packet.id]) if evidence else [],
        evidence_manifest_refs=_present([evidence.manifest.id]) if evidence else [],
        verification_decision_refs=_present([verification.id]) if verification else [],
        review_decision_refs=_present([review.id]) if review else [],
        publication_report_refs=_present([publication_report.id]) if publication_report else [],
        published_output_refs=_present([published_output.id]) if published_output else [],
        output_manifest_refs=_present([output_manifest.id]) if output_manifest else [],
        result_api_snapshot_refs=_present([result_api_snapshot.id])
        if result_api_snapshot
        else [],
        export_target_spec_refs=_present([export_set.target.id]) if export_set else [],
        export_job_refs=[job.id for job in export_set.export_jobs] if export_set else [],
        export_attempt_refs=[attempt.id for attempt in export_set.export_attempts]
        if export_set
        else [],
        delivery_receipt_refs=[receipt.id for receipt in export_set.delivery_receipts]
        if export_set
        else [],
        withdrawal_job_refs=[job.id for job in export_set.withdrawal_jobs]
        if export_set
        else [],
        withdrawal_attempt_refs=[attempt.id for attempt in export_set.withdrawal_attempts]
        if export_set
        else [],
        correction_record_refs=[record.id for record in export_set.correction_records]
        if export_set
        else [],
        destination_object_mapping_refs=export_set.destination_mapping_refs
        if export_set
        else [],
        policy_decision_refs=_dedupe(policy_refs or []),
        privacy_lifecycle_refs=(
            []
            if failure == ResultPublicationExportFailureType.PRIVACY_MISSING
            else _privacy_refs(fixture_id)
        ),
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        replay_bundle_ref=actual_replay_ref,
        direct_export_bypass_refs=direct_export_bypass_refs or [],
        failure_report_refs=failure_refs or [],
        missing_ref_fields=missing_fields or [],
        failure_type=failure,
        operator_status=operator_status,
        completion_result=completion_result,
        diagnostics=diagnostics or [],
    )


def _export_failure_for(
    scenario: str,
) -> ResultPublicationExportFailureType | None:
    return {
        "result-publication-export-missing-receipt": (
            ResultPublicationExportFailureType.EXPORT_MISSING_RECEIPT
        ),
        "result-publication-withdrawal-missing-propagation": (
            ResultPublicationExportFailureType.WITHDRAWAL_MISSING_PROPAGATION
        ),
        "result-publication-correction-without-withdrawal": (
            ResultPublicationExportFailureType.CORRECTION_WITHOUT_WITHDRAWAL
        ),
    }.get(scenario)


def _missing_field_for(failure: ResultPublicationExportFailureType) -> str:
    return {
        ResultPublicationExportFailureType.EXPORT_MISSING_RECEIPT: "delivery_receipt_refs",
        ResultPublicationExportFailureType.WITHDRAWAL_MISSING_PROPAGATION: (
            "withdrawal_attempt_refs"
        ),
        ResultPublicationExportFailureType.CORRECTION_WITHOUT_WITHDRAWAL: (
            "correction_record_refs"
        ),
    }.get(failure, failure.value)


def _policy(
    *,
    fixture_id: str,
    decision_type: str,
    subject_ref: str,
    allow: bool,
) -> PolicyDecision:
    return decision_for(
        decision_id=f"policy:{fixture_id}:{decision_type}:{subject_ref}",
        run_id=f"run:{fixture_id}",
        objective_id=f"objective:{fixture_id}",
        decision_type=decision_type,
        subject_ref=subject_ref,
        allow=allow,
        reasons=[f"{decision_type} denied for fixture"],
    )


def _privacy_refs(fixture_id: str) -> list[Ref]:
    return [f"privacy-lifecycle:{fixture_id}:published-output"]


def _present(refs: list[Ref | None]) -> list[Ref]:
    return [ref for ref in refs if ref is not None]


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(refs))
