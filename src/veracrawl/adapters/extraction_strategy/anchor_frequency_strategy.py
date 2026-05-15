"""``AnchorFrequencyExtractionStrategy`` — deterministic s7 fixture adapter.

Walks the text yielded by ``resolve_text(ref)`` for each
``text_sample_ref`` in a ``NormalizedDocumentReadModel`` and proposes
one :class:`ProposedField` per structural pattern observed ≥ 2 times.

Patterns supported in this slice:

* ``<dl><dt>NAME</dt><dd>VALUE</dd></dl>`` — definition-list pairs.
* ``<table><tr><th>NAME</th><td>VALUE</td></tr></table>`` — table
  rows whose first cell labels the row.

Type inference walks the *first* observed value sample for each
pattern through ordered regex tests (date → url → number → string).

No LLM, no clock, no RNG — pure function of the input. ``s9`` later
swaps in an LLM-driven adapter that consumes the same port.

See ``docs/plans/general-purpose-crawler-agentification/
s7-extraction-strategy-port.md``.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.schema_proposal import ProposedField, SchemaProposal

_RE_DL = re.compile(
    r"<dt[^>]*>(?P<key>.*?)</dt>\s*<dd[^>]*>(?P<value>.*?)</dd>",
    re.IGNORECASE | re.DOTALL,
)
_RE_TR = re.compile(
    r"<tr[^>]*>\s*<th[^>]*>(?P<key>.*?)</th>\s*<td[^>]*>(?P<value>.*?)</td>",
    re.IGNORECASE | re.DOTALL,
)

_RE_TAG = re.compile(r"<[^>]+>")
_RE_DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$")
_RE_URL = re.compile(r"^https?://[^\s<>\"']+$")
_RE_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")


def _strip_html(value: str) -> str:
    return _RE_TAG.sub("", value).strip()


def _infer_type(value: str) -> str:
    cleaned = _strip_html(value)
    if _RE_DATE_ISO.match(cleaned):
        return "date"
    if _RE_URL.match(cleaned):
        return "url"
    if _RE_NUMBER.match(cleaned):
        return "number"
    return "string"


def _normalize_key(key: str) -> str:
    cleaned = _strip_html(key).lower()
    return re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")


class _AnchorBucket:
    __slots__ = ("name", "first_value", "count", "first_seen_order", "xpath")

    def __init__(self, *, name: str, first_value: str, first_seen_order: int, xpath: str) -> None:
        self.name = name
        self.first_value = first_value
        self.count = 1
        self.first_seen_order = first_seen_order
        self.xpath = xpath


class AnchorFrequencyExtractionStrategy:
    """Pure ``ExtractionStrategyPort`` adapter — no LLM, no I/O."""

    def __init__(self, *, resolve_text: Callable[[Ref], str]) -> None:
        self._resolve_text = resolve_text

    def propose(
        self,
        *,
        document: NormalizedDocumentReadModel,
        run_ref: Ref,
    ) -> SchemaProposal:
        buckets: dict[str, _AnchorBucket] = {}
        order = 0
        for sample_ref in document.text_sample_refs:
            text = self._resolve_text(sample_ref)
            for match in _RE_DL.finditer(text):
                order = self._record(
                    buckets, match, order,
                    xpath_template="//dl/dt[contains(., {label!r})]/following-sibling::dd[1]",
                )
            for match in _RE_TR.finditer(text):
                order = self._record(
                    buckets, match, order,
                    xpath_template=(
                        "//table//tr/th[contains(., {label!r})]"
                        "/following-sibling::td[1]"
                    ),
                )
        repeated = sorted(
            (b for b in buckets.values() if b.count >= 2),
            key=lambda b: b.first_seen_order,
        )
        fields = [self._field_from_bucket(b, order=order) for b in repeated]
        if not fields:
            fields = [self._fallback_field(document)]
        return SchemaProposal(
            id=f"schema-proposal:{run_ref}:{document.id}",
            proposal_ref=f"proposal:{run_ref}:{stable_hash(document.model_dump(mode='json'))}",
            source_document_ref=document.normalized_document_ref,
            proposed_fields=fields,
            proposal_rationale_refs=[f"rationale:anchor-frequency:{document.id}"],
            replay_refs=[
                run_ref,
                document.normalized_document_ref,
                "adapter:anchor-frequency-extraction:v1",
            ],
        )

    def _record(
        self,
        buckets: dict[str, _AnchorBucket],
        match: re.Match[str],
        order: int,
        *,
        xpath_template: str,
    ) -> int:
        key_raw = match.group("key")
        value_raw = match.group("value")
        name = _normalize_key(key_raw)
        if not name:
            return order
        if name in buckets:
            buckets[name].count += 1
            return order
        label = _strip_html(key_raw)
        buckets[name] = _AnchorBucket(
            name=name,
            first_value=value_raw,
            first_seen_order=order,
            xpath=xpath_template.format(label=label),
        )
        return order + 1

    def _field_from_bucket(self, bucket: _AnchorBucket, *, order: int) -> ProposedField:
        del order  # unused; bucket ordering already enforced by sort
        confidence = min(1.0, 0.5 + 0.1 * (bucket.count - 2))
        return ProposedField(
            name=bucket.name,
            xpath=bucket.xpath,
            confidence=confidence,
            evidence_anchor_count=bucket.count,
            proposed_type=_infer_type(bucket.first_value),
        )

    def _fallback_field(self, document: NormalizedDocumentReadModel) -> ProposedField:
        # SchemaProposal validator requires ≥ 1 proposed_field; emit a
        # single low-confidence placeholder pinned to the document so
        # the contract still validates for empty / non-anchor docs.
        return ProposedField(
            name="document",
            xpath="//body",
            confidence=0.1,
            evidence_anchor_count=1,
            proposed_type="string",
        )


__all__ = ["AnchorFrequencyExtractionStrategy"]
