"""``SchemaExtractionLoop`` — s10 propose → extract → detect → repair runtime.

Pipes a corpus of ``NormalizedDocumentReadModel`` through the three
ports introduced by s7/s8/s9:

1. ``strategy.propose(documents[0])`` → ``SchemaProposal``.
2. For each document: apply the proposal's xpaths (very simple
   regex-based scan over the resolved text) and record per-field
   hit/miss into an ``ExtractionOutcome``.
3. ``drift_detector.detect(proposal, outcomes)`` → ``DriftReport``.
4. If drifted fields exist: ``repairer.repair(drift, documents)`` →
   ``RepairProposal``; re-extract drifted fields using the proposed
   xpaths.

The loop is **pure** given its ports + ``resolve_text``. No clock,
no RNG. The integration tests rely on this purity for byte-equal
report comparison across runs.

R1 reservation note: this slice is named ``SchemaExtractionLoop`` to
avoid a name clash with the existing
``contracts.processing.SchemaExtractionRuntimeReport`` and
``extract.schema_runtime.SchemaExtractionRuntimeResult``.

See ``docs/plans/general-purpose-crawler-agentification/
s10-schema-extraction-runtime.md``.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.extraction_outcome import ExtractionOutcome
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.repair_proposal import RepairProposal
from veracrawl.contracts.schema_proposal import ProposedField, SchemaProposal
from veracrawl.ports.drift_detection import DriftDetectionPort
from veracrawl.ports.extraction_strategy import ExtractionStrategyPort
from veracrawl.ports.repair import RepairPort


@dataclass(frozen=True, slots=True)
class SchemaExtractionLoopReport:
    """Compact in-memory result; integration tests assert per-page values.

    Includes only s10-scoped data so the loop stays decoupled from the
    larger ``contracts.processing.SchemaExtractionRuntimeReport``
    (which carries many phase-2 fields not relevant here). The runner
    integration slice (post-s10) is responsible for projecting this
    into the canonical report.
    """

    proposal_ref: Ref
    drift_ref: Ref
    repair_ref: Ref | None
    extraction_outcomes: list[ExtractionOutcome]
    extracted_values: list[dict[str, str | None]]
    replay_refs: list[Ref]


def _xpath_to_label(xpath: str) -> str | None:
    """Best-effort extraction of the literal label used inside an xpath.

    The fixture adapters emit xpaths like
    ``//dl/dt[contains(., 'Color')]/...`` or
    ``//*[normalize-space()='Price']/...``. This pulls the quoted
    label out so we can scan the document for surrounding values.
    """

    match = re.search(r"['\"]([^'\"]+)['\"]", xpath)
    return match.group(1) if match else None


def _extract_value(text: str, label: str) -> str | None:
    # Match ``<dt>Label</dt><dd>VALUE</dd>`` and
    # ``<th>Label</th><td>VALUE</td>`` patterns.
    label_escaped = re.escape(label)
    dl_match = re.search(
        rf"<dt[^>]*>\s*{label_escaped}\s*</dt>\s*<dd[^>]*>(.*?)</dd>",
        text, re.IGNORECASE | re.DOTALL,
    )
    if dl_match:
        return _strip_tags(dl_match.group(1)).strip() or None
    tr_match = re.search(
        rf"<th[^>]*>\s*{label_escaped}\s*</th>\s*<td[^>]*>(.*?)</td>",
        text, re.IGNORECASE | re.DOTALL,
    )
    if tr_match:
        return _strip_tags(tr_match.group(1)).strip() or None
    # Fallback: heading-style ``<h*>Label</h*>...<p>VALUE</p>``.
    h_match = re.search(
        rf"<h[1-6][^>]*>\s*{label_escaped}\s*</h[1-6]>\s*"
        r"<(?:p|span|div)[^>]*>(.*?)</(?:p|span|div)>",
        text, re.IGNORECASE | re.DOTALL,
    )
    if h_match:
        return _strip_tags(h_match.group(1)).strip() or None
    return None


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def _extract_fields(
    *,
    doc: NormalizedDocumentReadModel,
    fields: list[ProposedField],
    resolve_text: Callable[[Ref], str],
) -> dict[str, str | None]:
    text = " ".join(resolve_text(ref) for ref in doc.text_sample_refs)
    values: dict[str, str | None] = {}
    for field in fields:
        label = _xpath_to_label(field.xpath) or field.name
        values[field.name] = _extract_value(text, label)
    return values


class SchemaExtractionLoop:
    def __init__(
        self,
        *,
        strategy: ExtractionStrategyPort,
        drift_detector: DriftDetectionPort,
        repairer: RepairPort,
        resolve_text: Callable[[Ref], str],
        quality_threshold: float = 0.70,
    ) -> None:
        if not 0.0 < quality_threshold <= 1.0:
            raise ValueError("quality_threshold must be in (0.0, 1.0]")
        self._strategy = strategy
        self._drift_detector = drift_detector
        self._repairer = repairer
        self._resolve_text = resolve_text
        self._quality_threshold = quality_threshold

    def extract_corpus(
        self,
        *,
        documents: list[NormalizedDocumentReadModel],
        run_ref: Ref,
    ) -> SchemaExtractionLoopReport:
        if not documents:
            raise ValueError("documents must be non-empty")
        proposal = self._strategy.propose(
            document=documents[0], run_ref=run_ref,
        )
        active_fields = list(proposal.proposed_fields)
        extracted, outcomes = self._run_extraction(
            documents=documents, fields=active_fields, run_ref=run_ref,
        )
        drift = self._drift_detector.detect(
            proposal=proposal, extraction_outcomes=outcomes, run_ref=run_ref,
        )
        repair: RepairProposal | None = None
        if drift.drifted_fields and self._should_repair(outcomes, drift):
            repair = self._repairer.repair(
                drift_report=drift,
                document_samples=documents,
                resolve_text=self._resolve_text,
                run_ref=run_ref,
            )
            active_fields = self._apply_repair(active_fields, repair)
            extracted, outcomes = self._run_extraction(
                documents=documents, fields=active_fields, run_ref=run_ref,
            )
        return SchemaExtractionLoopReport(
            proposal_ref=proposal.proposal_ref,
            drift_ref=drift.id,
            repair_ref=repair.id if repair is not None else None,
            extraction_outcomes=outcomes,
            extracted_values=extracted,
            replay_refs=self._build_replay_refs(
                run_ref=run_ref, proposal=proposal, drift=drift, repair=repair,
            ),
        )

    def _run_extraction(
        self,
        *,
        documents: list[NormalizedDocumentReadModel],
        fields: list[ProposedField],
        run_ref: Ref,
    ) -> tuple[list[dict[str, str | None]], list[ExtractionOutcome]]:
        extracted: list[dict[str, str | None]] = []
        outcomes: list[ExtractionOutcome] = []
        for index, doc in enumerate(documents):
            values = _extract_fields(
                doc=doc, fields=fields, resolve_text=self._resolve_text,
            )
            extracted.append(values)
            outcomes.append(ExtractionOutcome(
                id=f"outcome:{run_ref}:{doc.id}:{index}",
                run_ref=run_ref,
                page_canonical_url=doc.normalized_document_ref,
                field_outcomes={
                    name: value is not None for name, value in values.items()
                },
                replay_refs=[run_ref, doc.normalized_document_ref],
            ))
        return extracted, outcomes

    def _should_repair(
        self,
        outcomes: list[ExtractionOutcome],
        drift: DriftReport,
    ) -> bool:
        if not outcomes:
            return False
        # Repair fires when ANY drifted field's success rate sits below
        # the quality threshold (mirrors drift_threshold gate logic).
        for name in drift.drifted_fields:
            success = sum(
                1 for o in outcomes
                if o.field_outcomes.get(name, False)
            )
            rate = success / len(outcomes)
            if rate < self._quality_threshold:
                return True
        return False

    def _apply_repair(
        self,
        fields: list[ProposedField],
        repair: RepairProposal,
    ) -> list[ProposedField]:
        repair_index = {fr.field_name: fr for fr in repair.field_repairs}
        updated: list[ProposedField] = []
        for field in fields:
            if field.name in repair_index:
                updated.append(field.model_copy(update={
                    "xpath": repair_index[field.name].proposed_xpath,
                }))
            else:
                updated.append(field)
        return updated

    def _build_replay_refs(
        self,
        *,
        run_ref: Ref,
        proposal: SchemaProposal,
        drift: DriftReport,
        repair: RepairProposal | None,
    ) -> list[Ref]:
        refs = [run_ref, proposal.proposal_ref, drift.id]
        if repair is not None:
            refs.append(repair.id)
        return refs


__all__ = ["SchemaExtractionLoop", "SchemaExtractionLoopReport"]
