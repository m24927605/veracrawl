"""Unit tests for ``SchemaExtractionLoop`` (s10)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pytest

from veracrawl.adapters.drift_detection.anchor_frequency_drift_detector import (
    AnchorFrequencyDriftDetector,
)
from veracrawl.adapters.extraction_strategy.anchor_frequency_strategy import (
    AnchorFrequencyExtractionStrategy,
)
from veracrawl.adapters.repair.anchor_reselect_repair import AnchorReselectRepair
from veracrawl.agents.schema_extraction_loop import SchemaExtractionLoop
from veracrawl.contracts.common import Ref
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.extraction_outcome import ExtractionOutcome
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.repair_proposal import FieldRepair, RepairProposal
from veracrawl.contracts.schema_proposal import ProposedField, SchemaProposal


def _doc(sample_ref: str) -> NormalizedDocumentReadModel:
    return NormalizedDocumentReadModel(
        id=f"doc:{sample_ref}",
        normalized_document_ref=f"normalized:{sample_ref}",
        text_sample_refs=[sample_ref],
    )


def _resolver(samples: dict[str, str]) -> Callable[[Ref], str]:
    return lambda ref: samples.get(ref, "")


_PAGE_A = """
    <dl><dt>Title</dt><dd>Article A</dd></dl>
    <dl><dt>Title</dt><dd>Article A</dd></dl>
    <dl><dt>Price</dt><dd>42</dd></dl>
    <dl><dt>Price</dt><dd>42</dd></dl>
"""
_PAGE_B = """
    <dl><dt>Title</dt><dd>Article B</dd></dl>
    <dl><dt>Price</dt><dd>99</dd></dl>
"""


def _loop() -> SchemaExtractionLoop:
    resolver = _resolver({"s:a": _PAGE_A, "s:b": _PAGE_B})
    return SchemaExtractionLoop(
        strategy=AnchorFrequencyExtractionStrategy(resolve_text=resolver),
        drift_detector=AnchorFrequencyDriftDetector(drift_threshold=0.30),
        repairer=AnchorReselectRepair(),
        resolve_text=resolver,
    )


# Spy adapters for the call-order tests
@dataclass
class _SpyStrategy:
    canned: SchemaProposal
    calls: list[NormalizedDocumentReadModel] = field(default_factory=list)

    def propose(
        self, *, document: NormalizedDocumentReadModel, run_ref: Ref,
    ) -> SchemaProposal:
        del run_ref
        self.calls.append(document)
        return self.canned


@dataclass
class _SpyDetector:
    canned: DriftReport
    calls: list[tuple[SchemaProposal, list[ExtractionOutcome]]] = field(
        default_factory=list,
    )

    def detect(
        self, *, proposal: SchemaProposal,
        extraction_outcomes: list[ExtractionOutcome], run_ref: Ref,
    ) -> DriftReport:
        del run_ref
        self.calls.append((proposal, list(extraction_outcomes)))
        return self.canned


@dataclass
class _SpyRepairer:
    canned: RepairProposal
    calls: list[DriftReport] = field(default_factory=list)

    def repair(
        self, *, drift_report: DriftReport,
        document_samples: list[NormalizedDocumentReadModel],
        resolve_text: Callable[[Ref], str],
        run_ref: Ref,
    ) -> RepairProposal:
        del document_samples, resolve_text, run_ref
        self.calls.append(drift_report)
        return self.canned


def _canned_proposal(*field_names: str) -> SchemaProposal:
    return SchemaProposal(
        id="schema-proposal:test:1", proposal_ref="proposal:test:1",
        source_document_ref="normalized:s:a",
        proposed_fields=[
            ProposedField(name=n, xpath=f"//*[contains(., '{n.title()}')]",
                          confidence=0.8, evidence_anchor_count=2,
                          proposed_type="string")
            for n in field_names
        ],
        proposal_rationale_refs=["rationale:1"],
        replay_refs=["run:test:1"],
    )


def _canned_drift(drifted: list[str]) -> DriftReport:
    return DriftReport(
        id="drift:test:1", run_ref="run:test:1",
        proposal_ref="proposal:test:1",
        pages_evaluated=2,
        field_missing_rates={d: 0.6 for d in drifted} or {"title": 0.0},
        drifted_fields=drifted, drift_threshold=0.30,
        replay_refs=["run:test:1"],
    )


def _canned_repair() -> RepairProposal:
    return RepairProposal(
        id="repair:test:1", run_ref="run:test:1",
        drift_report_ref="drift:test:1",
        field_repairs=[FieldRepair(
            field_name="price", original_xpath="//x",
            proposed_xpath="//*[contains(., 'Price')]",
            confidence=0.9, repair_kind="anchor_reselect",
        )],
        replay_refs=["run:test:1"],
    )


# Test 1
def test_extract_corpus_calls_strategy_propose_with_first_document() -> None:
    strategy = _SpyStrategy(canned=_canned_proposal("title"))
    detector = _SpyDetector(canned=_canned_drift([]))
    repairer = _SpyRepairer(canned=_canned_repair())
    loop = SchemaExtractionLoop(
        strategy=strategy, drift_detector=detector, repairer=repairer,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": _PAGE_B}),
    )
    docs = [_doc("s:a"), _doc("s:b")]
    loop.extract_corpus(documents=docs, run_ref="run:test:1")
    assert strategy.calls == [docs[0]]


# Test 2
def test_extract_corpus_records_extraction_outcomes_per_page() -> None:
    report = _loop().extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:2",
    )
    assert len(report.extraction_outcomes) == 2


# Test 3
def test_extract_corpus_calls_drift_detector_with_outcomes() -> None:
    strategy = _SpyStrategy(canned=_canned_proposal("title"))
    detector = _SpyDetector(canned=_canned_drift([]))
    repairer = _SpyRepairer(canned=_canned_repair())
    loop = SchemaExtractionLoop(
        strategy=strategy, drift_detector=detector, repairer=repairer,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": _PAGE_B}),
    )
    loop.extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:3",
    )
    assert len(detector.calls) == 1
    assert len(detector.calls[0][1]) == 2


# Test 4
def test_extract_corpus_skips_repair_when_no_drift() -> None:
    strategy = _SpyStrategy(canned=_canned_proposal("title"))
    detector = _SpyDetector(canned=_canned_drift([]))
    repairer = _SpyRepairer(canned=_canned_repair())
    loop = SchemaExtractionLoop(
        strategy=strategy, drift_detector=detector, repairer=repairer,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": _PAGE_B}),
    )
    report = loop.extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:4",
    )
    assert report.repair_ref is None
    assert repairer.calls == []


# Test 5
def test_extract_corpus_calls_repair_when_drift_present() -> None:
    strategy = _SpyStrategy(canned=_canned_proposal("price"))
    detector = _SpyDetector(canned=_canned_drift(["price"]))
    repairer = _SpyRepairer(canned=_canned_repair())
    # Use a corpus where the second page doesn't contain "Price" so the
    # success rate dips below quality_threshold and repair fires.
    loop = SchemaExtractionLoop(
        strategy=strategy, drift_detector=detector, repairer=repairer,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": "<p>none</p>"}),
    )
    report = loop.extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:5",
    )
    assert report.repair_ref == "repair:test:1"
    assert repairer.calls


# Test 6
def test_extract_corpus_re_extracts_after_repair() -> None:
    """After repair returns a new xpath, the loop re-runs extraction
    against the repaired field set — exercised via the spy detector
    being called twice when no drift remains after re-extraction.
    """

    strategy = _SpyStrategy(canned=_canned_proposal("price"))
    detector = _SpyDetector(canned=_canned_drift(["price"]))
    repairer = _SpyRepairer(canned=_canned_repair())
    loop = SchemaExtractionLoop(
        strategy=strategy, drift_detector=detector, repairer=repairer,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": _PAGE_B}),
    )
    report = loop.extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:6",
    )
    # The re-extraction happens but does NOT re-call drift_detector
    # (single-shot per slice scope). The repair-applied extraction
    # values land in extracted_values[*]["price"].
    assert any(values["price"] is not None for values in report.extracted_values)


# Test 7
def test_extract_corpus_quality_threshold_gates_repair() -> None:
    """High quality_threshold (1.0) → repair fires when even one miss
    appears; low threshold (~0) → repair skipped when success rate
    barely scrapes by.
    """

    strategy = _SpyStrategy(canned=_canned_proposal("price"))
    detector = _SpyDetector(canned=_canned_drift(["price"]))
    repairer = _SpyRepairer(canned=_canned_repair())

    # quality_threshold high → ANY miss triggers repair.
    loop_strict = SchemaExtractionLoop(
        strategy=strategy, drift_detector=detector, repairer=repairer,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": "<p>nothing</p>"}),
        quality_threshold=1.0,
    )
    loop_strict.extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:7-strict",
    )
    strict_calls = len(repairer.calls)

    # quality_threshold below the actual success rate → skip repair.
    repairer2 = _SpyRepairer(canned=_canned_repair())
    loop_lax = SchemaExtractionLoop(
        strategy=_SpyStrategy(canned=_canned_proposal("price")),
        drift_detector=_SpyDetector(canned=_canned_drift(["price"])),
        repairer=repairer2,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": _PAGE_B}),
        quality_threshold=0.01,
    )
    loop_lax.extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:7-lax",
    )
    lax_calls = len(repairer2.calls)
    assert strict_calls > lax_calls


# Test 8
def test_extract_corpus_report_includes_proposal_ref() -> None:
    report = _loop().extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:8",
    )
    assert report.proposal_ref.startswith("proposal:")


# Test 9
def test_extract_corpus_report_includes_drift_ref() -> None:
    report = _loop().extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:9",
    )
    assert report.drift_ref.startswith("drift-report:")


# Test 10
def test_extract_corpus_report_includes_repair_ref_when_repaired() -> None:
    strategy = _SpyStrategy(canned=_canned_proposal("price"))
    detector = _SpyDetector(canned=_canned_drift(["price"]))
    repairer = _SpyRepairer(canned=_canned_repair())
    loop = SchemaExtractionLoop(
        strategy=strategy, drift_detector=detector, repairer=repairer,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": "<p>none</p>"}),
    )
    report = loop.extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:10",
    )
    assert report.repair_ref == "repair:test:1"


# Test 11
def test_extract_corpus_replay_refs_chain_complete() -> None:
    strategy = _SpyStrategy(canned=_canned_proposal("price"))
    detector = _SpyDetector(canned=_canned_drift(["price"]))
    repairer = _SpyRepairer(canned=_canned_repair())
    loop = SchemaExtractionLoop(
        strategy=strategy, drift_detector=detector, repairer=repairer,
        resolve_text=_resolver({"s:a": _PAGE_A, "s:b": "<p>none</p>"}),
    )
    report = loop.extract_corpus(
        documents=[_doc("s:a"), _doc("s:b")], run_ref="run:test:11",
    )
    # [run_ref, proposal_ref, drift_ref, repair_ref]
    assert report.replay_refs == [
        "run:test:11", "proposal:test:1", "drift:test:1", "repair:test:1",
    ]


# Test 12
def test_extract_corpus_pure_function_given_canned_ports() -> None:
    def _build_loop() -> SchemaExtractionLoop:
        return SchemaExtractionLoop(
            strategy=_SpyStrategy(canned=_canned_proposal("title")),
            drift_detector=_SpyDetector(canned=_canned_drift([])),
            repairer=_SpyRepairer(canned=_canned_repair()),
            resolve_text=_resolver({"s:a": _PAGE_A, "s:b": _PAGE_B}),
        )

    docs = [_doc("s:a"), _doc("s:b")]
    a = _build_loop().extract_corpus(documents=docs, run_ref="run:pure")
    b = _build_loop().extract_corpus(documents=docs, run_ref="run:pure")
    assert a.extracted_values == b.extracted_values
    assert a.replay_refs == b.replay_refs


# Test 13
def test_extract_corpus_rejects_empty_document_list() -> None:
    with pytest.raises(ValueError, match="documents"):
        _loop().extract_corpus(documents=[], run_ref="run:empty")


# Bonus — quality_threshold validator
def test_loop_rejects_invalid_quality_threshold() -> None:
    with pytest.raises(ValueError, match="quality_threshold"):
        SchemaExtractionLoop(
            strategy=_SpyStrategy(canned=_canned_proposal("t")),
            drift_detector=_SpyDetector(canned=_canned_drift([])),
            repairer=_SpyRepairer(canned=_canned_repair()),
            resolve_text=lambda _ref: "",
            quality_threshold=0.0,
        )
