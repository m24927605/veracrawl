"""Integration test for s10 ``SchemaExtractionLoop`` against a fixture corpus.

Uses an in-memory 3-page HTML corpus where page-C deliberately drifts
one field's anchor label. The full propose → extract → detect →
repair loop runs with the s7 / s8 deterministic fixture adapters
(no LLM, no network).
"""

from __future__ import annotations

from collections.abc import Callable

from veracrawl.adapters.drift_detection.anchor_frequency_drift_detector import (
    AnchorFrequencyDriftDetector,
)
from veracrawl.adapters.extraction_strategy.anchor_frequency_strategy import (
    AnchorFrequencyExtractionStrategy,
)
from veracrawl.adapters.repair.anchor_reselect_repair import AnchorReselectRepair
from veracrawl.agents.schema_extraction_loop import SchemaExtractionLoop
from veracrawl.contracts.common import Ref
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)

_PAGE_A = """
<html><body>
    <dl><dt>Title</dt><dd>Apollo Mission</dd></dl>
    <dl><dt>Title</dt><dd>Apollo Mission</dd></dl>
    <dl><dt>Price</dt><dd>15</dd></dl>
    <dl><dt>Price</dt><dd>15</dd></dl>
</body></html>
"""

_PAGE_B = """
<html><body>
    <dl><dt>Title</dt><dd>Gemini Brief</dd></dl>
    <dl><dt>Price</dt><dd>22</dd></dl>
</body></html>
"""

# Page-C drifts: the "Price" anchor moves to "Cost".
_PAGE_C = """
<html><body>
    <dl><dt>Title</dt><dd>Mercury Notes</dd></dl>
    <dl><dt>Cost</dt><dd>9</dd></dl>
    <h2>Cost</h2><p>9</p>
    <h2>Cost</h2><p>9</p>
</body></html>
"""


def _resolver() -> Callable[[Ref], str]:
    samples = {
        "sample:page-a": _PAGE_A,
        "sample:page-b": _PAGE_B,
        "sample:page-c": _PAGE_C,
    }
    return lambda ref: samples[ref]


def _doc(slug: str) -> NormalizedDocumentReadModel:
    return NormalizedDocumentReadModel(
        id=f"doc:{slug}",
        normalized_document_ref=f"normalized:{slug}",
        text_sample_refs=[f"sample:{slug}"],
    )


def _loop(*, quality_threshold: float = 0.70) -> SchemaExtractionLoop:
    resolver = _resolver()
    return SchemaExtractionLoop(
        strategy=AnchorFrequencyExtractionStrategy(resolve_text=resolver),
        drift_detector=AnchorFrequencyDriftDetector(drift_threshold=0.30),
        repairer=AnchorReselectRepair(),
        resolve_text=resolver,
        quality_threshold=quality_threshold,
    )


def test_corpus_three_pages_extract_proposal_and_outcomes() -> None:
    loop = _loop()
    report = loop.extract_corpus(
        documents=[_doc("page-a"), _doc("page-b"), _doc("page-c")],
        run_ref="run:s10:corpus:1",
    )
    # Three outcomes, one per page.
    assert len(report.extraction_outcomes) == 3
    # Page-a + page-b have "price"; page-c misses it.
    price_per_page = [
        o.field_outcomes.get("price", False)
        for o in report.extraction_outcomes
    ]
    assert price_per_page == [True, True, False]


def test_corpus_drift_detected_on_page_c() -> None:
    loop = _loop()
    report = loop.extract_corpus(
        documents=[_doc("page-a"), _doc("page-b"), _doc("page-c")],
        run_ref="run:s10:corpus:2",
    )
    # 1 of 3 pages missed price → ~33% missing rate → above default
    # 30% drift threshold → drift flagged.
    assert report.drift_ref.startswith("drift-report:")


def test_corpus_repair_proposes_alternative_xpath_when_quality_low() -> None:
    # With quality_threshold=1.0, ANY miss triggers repair.
    loop = _loop(quality_threshold=1.0)
    report = loop.extract_corpus(
        documents=[_doc("page-a"), _doc("page-b"), _doc("page-c")],
        run_ref="run:s10:corpus:3",
    )
    assert report.repair_ref is not None
    assert report.repair_ref.startswith("repair:")
