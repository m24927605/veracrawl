from __future__ import annotations

from veracrawl.contracts.enums import PageType
from veracrawl.normalize.pipeline import normalize_html_document


def test_normalize_html_builds_anchors_links_and_site_model() -> None:
    result = normalize_html_document(
        fixture_id="unit-process",
        run_ref="run:unit-process",
        source_adapter_result_ref="source-result:unit",
        source_url="http://example.test/static/basic",
        raw_artifact_ref="artifact:raw",
        raw_html=(
            "<html><title>Title</title><body><h1>Hello</h1>"
            "<a href='/detail'>Detail</a></body></html>"
        ),
        policy_decision_refs=["policy:process"],
    )
    assert "Hello" in result.normalized_text
    assert result.anchors
    assert result.link_provenance
    assert result.link_provenance[0].href == "http://example.test/detail"
    assert result.page_type.page_type == PageType.LISTING
    assert result.site_model.link_provenance_refs


def test_link_provenance_uses_matching_anchor_when_text_repeats() -> None:
    result = normalize_html_document(
        fixture_id="unit-repeat-link",
        run_ref="run:unit-repeat-link",
        source_adapter_result_ref="source-result:unit",
        source_url="http://example.test/static/basic",
        raw_artifact_ref="artifact:raw",
        raw_html=(
            "<html><body><p>Detail</p>"
            "<a href='/detail'>Detail</a></body></html>"
        ),
        policy_decision_refs=["policy:process"],
    )
    assert result.link_provenance
    assert result.link_provenance[0].anchor_ref == result.anchors[1].id
