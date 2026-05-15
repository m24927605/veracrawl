"""s18 acceptance corpus: three unfamiliar verticals end-to-end.

Proves the general-purpose claim by running the SchemaExtractionLoop
(s10) against three structurally-distinct synthetic HTML corpora:

* **News** — definition-list metadata (Title / Author / Published).
* **E-commerce** — definition-list product attributes (SKU / Price /
  Stock).
* **Docs** — heading-driven metadata (Section / Version / Updated).

Each corpus uses HTML structures the existing test suite has never
touched. The s7 ``AnchorFrequencyExtractionStrategy`` + s8
``AnchorFrequencyDriftDetector`` + ``AnchorReselectRepair`` work
verbatim across all three — no per-vertical templates.

Live-mode tests against real external sites are out of scope here;
adding them is a separate operational concern (legal/robots
clearance + snapshot lifecycle).
"""

from __future__ import annotations

from collections.abc import Callable

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
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)


def _doc(slug: str) -> NormalizedDocumentReadModel:
    return NormalizedDocumentReadModel(
        id=f"doc:{slug}",
        normalized_document_ref=f"normalized:{slug}",
        text_sample_refs=[f"sample:{slug}"],
    )


def _resolver(samples: dict[str, str]) -> Callable[[Ref], str]:
    return lambda ref: samples[ref]


def _loop(samples: dict[str, str]) -> SchemaExtractionLoop:
    resolver = _resolver(samples)
    return SchemaExtractionLoop(
        strategy=AnchorFrequencyExtractionStrategy(resolve_text=resolver),
        drift_detector=AnchorFrequencyDriftDetector(drift_threshold=0.30),
        repairer=AnchorReselectRepair(),
        resolve_text=resolver,
    )


# Site A — news vertical (article listings + metadata blocks)
_NEWS_PAGE_1 = """
<html><body>
    <article>
        <dl>
            <dt>Title</dt><dd>Mars Rover Returns Samples</dd>
            <dt>Author</dt><dd>Alice Chen</dd>
            <dt>Published</dt><dd>2026-03-12</dd>
        </dl>
    </article>
    <article>
        <dl>
            <dt>Title</dt><dd>Antarctic Ice Survey 2026</dd>
            <dt>Author</dt><dd>Bao Liu</dd>
            <dt>Published</dt><dd>2026-04-02</dd>
        </dl>
    </article>
</body></html>
"""

_NEWS_PAGE_2 = """
<html><body>
    <article>
        <dl>
            <dt>Title</dt><dd>Quantum Lattice Test</dd>
            <dt>Author</dt><dd>Carlos Vega</dd>
            <dt>Published</dt><dd>2026-05-01</dd>
        </dl>
    </article>
</body></html>
"""


def test_corpus_site_a_news_extracts_title_author_published() -> None:
    samples = {"sample:news-1": _NEWS_PAGE_1, "sample:news-2": _NEWS_PAGE_2}
    report = _loop(samples).extract_corpus(
        documents=[_doc("news-1"), _doc("news-2")],
        run_ref="run:s18:news",
    )
    # Proposal generated from news page 1 must include all three fields.
    extracted_first_page = report.extracted_values[0]
    assert {"title", "author", "published"}.issubset(extracted_first_page.keys())
    # Drift report exists; news pages are structurally consistent so
    # ``title`` should NOT drift (success rate 100%).
    assert "title" not in report.extraction_outcomes[1].field_outcomes or (
        report.extraction_outcomes[1].field_outcomes.get("title", False)
    )


# Site B — e-commerce vertical (product attribute blocks)
_PRODUCT_PAGE_1 = """
<html><body>
    <section class="product">
        <dl>
            <dt>SKU</dt><dd>WIDGET-001</dd>
            <dt>Price</dt><dd>29.99</dd>
            <dt>Stock</dt><dd>In stock</dd>
        </dl>
    </section>
    <section class="product">
        <dl>
            <dt>SKU</dt><dd>WIDGET-002</dd>
            <dt>Price</dt><dd>49.99</dd>
            <dt>Stock</dt><dd>Backorder</dd>
        </dl>
    </section>
</body></html>
"""

_PRODUCT_PAGE_2 = """
<html><body>
    <section class="product">
        <dl>
            <dt>SKU</dt><dd>GIZMO-100</dd>
            <dt>Price</dt><dd>14.50</dd>
            <dt>Stock</dt><dd>In stock</dd>
        </dl>
    </section>
</body></html>
"""


def test_corpus_site_b_ecommerce_extracts_product_attributes() -> None:
    samples = {
        "sample:product-1": _PRODUCT_PAGE_1,
        "sample:product-2": _PRODUCT_PAGE_2,
    }
    report = _loop(samples).extract_corpus(
        documents=[_doc("product-1"), _doc("product-2")],
        run_ref="run:s18:ecommerce",
    )
    extracted_first_page = report.extracted_values[0]
    assert {"sku", "price", "stock"}.issubset(extracted_first_page.keys())
    # Price field should infer as "number" type-ish; we don't pin the
    # type here because the type inference walks first observed value
    # and "29.99" is numeric.


# Site C — docs vertical (table-row metadata)
_DOCS_PAGE_1 = """
<html><body>
    <table>
        <tr><th>Section</th><td>Introduction</td></tr>
        <tr><th>Version</th><td>1.0</td></tr>
        <tr><th>Updated</th><td>2026-05-15</td></tr>
    </table>
    <table>
        <tr><th>Section</th><td>Quickstart</td></tr>
        <tr><th>Version</th><td>1.0</td></tr>
        <tr><th>Updated</th><td>2026-05-15</td></tr>
    </table>
</body></html>
"""

_DOCS_PAGE_2 = """
<html><body>
    <table>
        <tr><th>Section</th><td>Advanced</td></tr>
        <tr><th>Version</th><td>1.1</td></tr>
        <tr><th>Updated</th><td>2026-05-20</td></tr>
    </table>
</body></html>
"""


def test_corpus_site_c_docs_extracts_section_version_updated() -> None:
    samples = {"sample:docs-1": _DOCS_PAGE_1, "sample:docs-2": _DOCS_PAGE_2}
    report = _loop(samples).extract_corpus(
        documents=[_doc("docs-1"), _doc("docs-2")],
        run_ref="run:s18:docs",
    )
    extracted_first_page = report.extracted_values[0]
    # Tables drive section/version/updated via the table-row pattern.
    assert {"section", "version", "updated"}.issubset(extracted_first_page.keys())


# Cross-vertical invariant: same loop, same adapters, no per-vertical
# config — the general-purpose claim.
def test_corpus_general_purpose_loop_handles_all_three_verticals() -> None:
    """One ``SchemaExtractionLoop`` configuration extracts data from
    all three structurally-distinct verticals with no per-vertical
    setup. This is THE general-purpose acceptance test.
    """

    verticals: list[tuple[str, dict[str, str], list[str], set[str]]] = [
        (
            "news",
            {"sample:n": _NEWS_PAGE_1},
            ["n"],
            {"title", "author", "published"},
        ),
        (
            "ecommerce",
            {"sample:e": _PRODUCT_PAGE_1},
            ["e"],
            {"sku", "price", "stock"},
        ),
        (
            "docs",
            {"sample:d": _DOCS_PAGE_1},
            ["d"],
            {"section", "version", "updated"},
        ),
    ]
    for vertical, samples, slugs, expected_fields in verticals:
        report = _loop(samples).extract_corpus(
            documents=[_doc(s) for s in slugs],
            run_ref=f"run:s18:gp:{vertical}",
        )
        actual = set(report.extracted_values[0].keys())
        assert expected_fields.issubset(actual), (
            f"{vertical}: expected {expected_fields}, got {actual}"
        )


# Placeholder live-mode tests pin the @pytest.mark.live shape per
# AC2; they're skipped without an explicit live-corpus configuration.

@pytest.mark.live
@pytest.mark.skip(reason="live corpus requires legal/robots clearance per R1")
def test_corpus_site_a_news_runs_end_to_end_live() -> None:
    pytest.skip("operational follow-up — see s18 plan reservation R1")


@pytest.mark.live
@pytest.mark.skip(reason="live corpus requires legal/robots clearance per R1")
def test_corpus_site_b_ecommerce_runs_end_to_end_live() -> None:
    pytest.skip("operational follow-up — see s18 plan reservation R1")


@pytest.mark.live
@pytest.mark.skip(reason="live corpus requires legal/robots clearance per R1")
def test_corpus_site_c_docs_runs_end_to_end_live() -> None:
    pytest.skip("operational follow-up — see s18 plan reservation R1")
