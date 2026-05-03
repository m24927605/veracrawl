"""Deterministic processing/evidence materialization for target runtime fixtures."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.target_runtime import (
    TargetAdapterBackedSourceRecord,
    TargetProcessingEvidenceEntry,
    TargetProcessingEvidenceManifest,
    TargetProcessingEvidenceRecord,
)


def build_processing_evidence_records(
    *,
    processing_manifest: TargetProcessingEvidenceManifest,
    adapter_records: list[TargetAdapterBackedSourceRecord],
) -> list[TargetProcessingEvidenceRecord]:
    adapter_by_entry = {record.corpus_entry_ref: record for record in adapter_records}
    return [
        _record_from_entry(
            entry=entry,
            adapter_record=adapter_by_entry[entry.corpus_entry_ref],
        )
        for entry in processing_manifest.entries
        if entry.corpus_entry_ref in adapter_by_entry
    ]


def _record_from_entry(
    *,
    entry: TargetProcessingEvidenceEntry,
    adapter_record: TargetAdapterBackedSourceRecord,
) -> TargetProcessingEvidenceRecord:
    suffix = entry.id.replace(":", "-")
    missing_normalization_refs = (
        [f"missing-normalization:{suffix}"] if entry.simulate_missing_normalization else []
    )
    missing_candidate_anchor_refs = (
        [f"missing-candidate-anchor:{suffix}"]
        if entry.simulate_missing_candidate_anchor
        else []
    )
    missing_evidence_packet_refs = (
        [f"missing-evidence-packet:{suffix}"]
        if entry.simulate_missing_evidence_packet
        else []
    )
    graph_only_evidence_refs = (
        [f"graph-only-evidence:{suffix}"] if entry.simulate_graph_only_evidence else []
    )
    publication_bypass_refs = (
        [f"publication-bypass:{suffix}"] if entry.simulate_publication_bypass else []
    )
    diagnostics = (
        missing_normalization_refs
        + missing_candidate_anchor_refs
        + missing_evidence_packet_refs
        + graph_only_evidence_refs
        + publication_bypass_refs
    )
    normalized_document_ref = None if missing_normalization_refs else f"normalized:{suffix}"
    extraction_candidate_ref = f"candidate:{suffix}" if normalized_document_ref else None
    candidate_anchor_refs = (
        []
        if missing_candidate_anchor_refs
        else [f"candidate-anchor:{suffix}:{field}" for field in entry.required_field_refs]
    )
    evidence_packet_ref = None if missing_evidence_packet_refs else f"evidence-packet:{suffix}"
    evidence_anchor_refs = (
        []
        if missing_evidence_packet_refs or missing_candidate_anchor_refs
        else [f"evidence-anchor:{suffix}:{field}" for field in entry.required_field_refs]
    )
    publication_report_ref = None if publication_bypass_refs else f"publication-report:{suffix}"
    return TargetProcessingEvidenceRecord(
        id=f"processing-evidence:{entry.id}",
        run_ref=adapter_record.run_ref,
        corpus_entry_ref=entry.corpus_entry_ref,
        adapter_backed_source_ref=entry.adapter_backed_source_ref,
        source_observation_ref=adapter_record.source_observation_ref,
        adapter_output_refs=adapter_record.adapter_output_refs,
        normalized_document_ref=normalized_document_ref,
        extraction_candidate_ref=extraction_candidate_ref,
        candidate_anchor_refs=candidate_anchor_refs,
        evidence_packet_ref=evidence_packet_ref,
        evidence_anchor_refs=evidence_anchor_refs,
        publication_report_ref=publication_report_ref,
        policy_decision_refs=[entry.policy_decision_ref],
        replay_refs=[f"replay:{suffix}:processing-evidence"],
        graph_only_evidence_refs=graph_only_evidence_refs,
        missing_normalization_refs=missing_normalization_refs,
        missing_candidate_anchor_refs=missing_candidate_anchor_refs,
        missing_evidence_packet_refs=missing_evidence_packet_refs,
        publication_bypass_refs=publication_bypass_refs,
        result=CompletenessResult.FAIL if diagnostics else CompletenessResult.PASS,
    )
