"""s18 close (engineering-resolvable subset): fetch-through-replay corpus.

Original carry-forward #5 was "three @pytest.mark.live tests against
real external sites with snapshot capture". The "real external sites"
half is external-blocked on legal / robots / availability clearance —
not engineering-resolvable. The engineering-resolvable half is the
**integration path**: ``ReplayingHttpFetcher`` feeding recorded
``FetchOutcome``s into the extraction loop end-to-end. That's what
this file tests.

Pattern when real-site clearance lands: replace
``_CANNED_FETCH_OUTCOMES`` with snapshots captured during a record
run; the rest of the wiring stays unchanged.

Marked ``@pytest.mark.live`` at module level to signal "exercises the
integration path that would be used live", per the s18 plan's intent.
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.drift_detection.anchor_frequency_drift_detector import (
    AnchorFrequencyDriftDetector,
)
from veracrawl.adapters.extraction_strategy.anchor_frequency_strategy import (
    AnchorFrequencyExtractionStrategy,
)
from veracrawl.adapters.network.replaying_http_fetcher import (
    ReplayingHttpFetcher,
)
from veracrawl.adapters.repair.anchor_reselect_repair import AnchorReselectRepair
from veracrawl.agents.schema_extraction_loop import SchemaExtractionLoop
from veracrawl.contracts.common import Ref
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.ports.crawl_http_fetcher import FetchOutcome

pytestmark = pytest.mark.live


_NEWS_HTML = """
<html><body>
    <dl><dt>Title</dt><dd>Apollo Mission</dd></dl>
    <dl><dt>Title</dt><dd>Apollo Mission</dd></dl>
    <dl><dt>Published</dt><dd>2026-03-12</dd></dl>
    <dl><dt>Published</dt><dd>2026-03-12</dd></dl>
</body></html>
"""

_PRODUCT_HTML = """
<html><body>
    <dl><dt>SKU</dt><dd>WIDGET-001</dd></dl>
    <dl><dt>SKU</dt><dd>WIDGET-001</dd></dl>
    <dl><dt>Price</dt><dd>29.99</dd></dl>
    <dl><dt>Price</dt><dd>29.99</dd></dl>
</body></html>
"""


def _outcome(url: str, body: str) -> FetchOutcome:
    return FetchOutcome(
        requested_url=url, final_url=url, status_code=200,
        headers={"content-type": "text/html"},
        body=body.encode("utf-8"),
        content_type="text/html",
    )


def test_replaying_fetcher_into_extraction_loop_news_corpus() -> None:
    """Phase 1 (would-be record): caller captures real-site HTML into
    canned ``FetchOutcome`` map (simulated here via ``_NEWS_HTML``).
    Phase 2 (replay): ``ReplayingHttpFetcher`` serves the snapshot;
    extraction loop runs against the fetched body.
    """

    url = "https://example.com/news/article-1"
    fetcher = ReplayingHttpFetcher(
        outcomes_by_url={url: _outcome(url, _NEWS_HTML)},
    )
    fetched = fetcher.fetch(url, timeout_seconds=5.0)
    assert fetched.status_code == 200

    # Phase 3: feed the fetched bytes into the extraction loop. In a
    # real-site test the runner would do this; here we exercise the
    # loop directly to keep the test self-contained.
    text = fetched.body.decode("utf-8")
    samples = {f"sample:{url}": text}

    def resolver(ref: Ref) -> str:
        return samples[ref]

    loop = SchemaExtractionLoop(
        strategy=AnchorFrequencyExtractionStrategy(resolve_text=resolver),
        drift_detector=AnchorFrequencyDriftDetector(drift_threshold=0.30),
        repairer=AnchorReselectRepair(),
        resolve_text=resolver,
    )
    doc = NormalizedDocumentReadModel(
        id=f"doc:{url}",
        normalized_document_ref=f"normalized:{url}",
        text_sample_refs=[f"sample:{url}"],
    )
    report = loop.extract_corpus(documents=[doc], run_ref="run:s18:news")
    extracted = report.extracted_values[0]
    assert "title" in extracted
    assert "published" in extracted


def test_replaying_fetcher_into_extraction_loop_ecommerce_corpus() -> None:
    """Same shape, e-commerce vertical."""

    url = "https://example.com/products/widget-001"
    fetcher = ReplayingHttpFetcher(
        outcomes_by_url={url: _outcome(url, _PRODUCT_HTML)},
    )
    fetched = fetcher.fetch(url, timeout_seconds=5.0)
    text = fetched.body.decode("utf-8")
    samples = {f"sample:{url}": text}

    def resolver(ref: Ref) -> str:
        return samples[ref]

    loop = SchemaExtractionLoop(
        strategy=AnchorFrequencyExtractionStrategy(resolve_text=resolver),
        drift_detector=AnchorFrequencyDriftDetector(drift_threshold=0.30),
        repairer=AnchorReselectRepair(),
        resolve_text=resolver,
    )
    doc = NormalizedDocumentReadModel(
        id=f"doc:{url}",
        normalized_document_ref=f"normalized:{url}",
        text_sample_refs=[f"sample:{url}"],
    )
    report = loop.extract_corpus(
        documents=[doc], run_ref="run:s18:ecommerce",
    )
    extracted = report.extracted_values[0]
    assert "sku" in extracted
    assert "price" in extracted


def test_two_runs_with_same_snapshot_byte_equal_extraction() -> None:
    """Replay invariant smoke test: two runs against the same
    ``ReplayingHttpFetcher`` snapshot produce byte-equal extraction.
    """

    def _run() -> str:
        url = "https://example.com/article"
        fetcher = ReplayingHttpFetcher(
            outcomes_by_url={url: _outcome(url, _NEWS_HTML)},
        )
        fetched = fetcher.fetch(url, timeout_seconds=5.0)
        text = fetched.body.decode("utf-8")
        samples = {f"sample:{url}": text}

        def resolver(ref: Ref) -> str:
            return samples[ref]

        loop = SchemaExtractionLoop(
            strategy=AnchorFrequencyExtractionStrategy(resolve_text=resolver),
            drift_detector=AnchorFrequencyDriftDetector(drift_threshold=0.30),
            repairer=AnchorReselectRepair(),
            resolve_text=resolver,
        )
        doc = NormalizedDocumentReadModel(
            id=f"doc:{url}",
            normalized_document_ref=f"normalized:{url}",
            text_sample_refs=[f"sample:{url}"],
        )
        report = loop.extract_corpus(documents=[doc], run_ref="run:s18:replay")
        return report.proposal_ref

    a = _run()
    b = _run()
    assert a == b
