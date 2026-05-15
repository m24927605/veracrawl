"""``AnchorReselectRepair`` — deterministic s8.b fixture adapter.

For each drifted field in a ``DriftReport``, scan the document samples
(text via ``resolve_text``) for the most-frequent alternative anchor
label that maps to the same field name (case-insensitive match).
Emits a ``RepairProposal`` with one ``FieldRepair`` per drifted field.
Pure function — no clock, no RNG.

See ``docs/plans/general-purpose-crawler-agentification/
s8-drift-repair-ports.md`` (s8.b scope).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.repair_proposal import FieldRepair, RepairProposal

_RE_HEADING = re.compile(
    r"<(h[1-6]|th|dt|label|strong)[^>]*>(?P<label>[^<]+)</\1>",
    re.IGNORECASE,
)


class AnchorReselectRepair:
    """``RepairPort`` impl that proposes a heading-derived xpath."""

    def repair(
        self,
        *,
        drift_report: DriftReport,
        document_samples: list[NormalizedDocumentReadModel],
        resolve_text: Callable[[Ref], str],
        run_ref: Ref,
    ) -> RepairProposal:
        if not drift_report.drifted_fields:
            raise ValueError(
                "drift_report has no drifted_fields; nothing to repair",
            )
        if not document_samples:
            raise ValueError("document_samples must be non-empty")
        label_counts: Counter[str] = Counter()
        for doc in document_samples:
            for sample_ref in doc.text_sample_refs:
                text = resolve_text(sample_ref)
                for match in _RE_HEADING.finditer(text):
                    label = match.group("label").strip().lower()
                    if label:
                        label_counts[label] += 1
        repairs: list[FieldRepair] = []
        for field_name in drift_report.drifted_fields:
            proposed_xpath, confidence = self._propose_xpath(
                field_name, label_counts,
            )
            repairs.append(FieldRepair(
                field_name=field_name,
                original_xpath=f"//*[contains(., {field_name!r})]",
                proposed_xpath=proposed_xpath,
                confidence=confidence,
                repair_kind="anchor_reselect",
            ))
        digest = stable_hash({
            "drift": drift_report.id,
            "fields": [r.field_name for r in repairs],
        })
        return RepairProposal(
            id=f"repair:{run_ref}:{digest}",
            run_ref=run_ref,
            drift_report_ref=drift_report.id,
            field_repairs=repairs,
            replay_refs=[
                run_ref, drift_report.id,
                "adapter:anchor-reselect-repair:v1",
            ],
        )

    def _propose_xpath(
        self, field_name: str, label_counts: Counter[str],
    ) -> tuple[str, float]:
        target = field_name.lower()
        best_label: str | None = None
        best_score = 0
        for label, count in label_counts.items():
            if target in label.replace(" ", "").replace("-", "").replace("_", ""):
                if count > best_score:
                    best_label = label
                    best_score = count
        if best_label is None:
            # Conservative fallback: propose the same field name as the
            # heading text, low confidence.
            return (
                f"//*[normalize-space()={field_name!r}]/following-sibling::*[1]",
                0.20,
            )
        max_count = max(label_counts.values()) if label_counts else 1
        confidence = min(1.0, 0.50 + 0.5 * (best_score / max_count))
        return (
            f"//*[normalize-space()={best_label!r}]/following-sibling::*[1]",
            confidence,
        )


__all__ = ["AnchorReselectRepair"]
