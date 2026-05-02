"""Deterministic normalization and page understanding pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    LinkProvenanceStatus,
    PageType,
)
from veracrawl.contracts.processing import (
    AnchorMap,
    LinkProvenance,
    NormalizationManifest,
    NormalizedDocument,
    PageTypeClassification,
    SiteModel,
    TextAnchor,
)


@dataclass(frozen=True)
class NormalizationResult:
    normalized_text: str
    normalized_document: NormalizedDocument
    manifest: NormalizationManifest
    anchors: list[TextAnchor]
    anchor_map: AnchorMap
    link_provenance: list[LinkProvenance]
    page_type: PageTypeClassification
    site_model: SiteModel
    artifact_refs: list[Ref]


@dataclass(frozen=True)
class _TextChunk:
    label: str
    text: str
    href: str | None


class _HTMLProjectionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._tag_stack: list[str] = []
        self._current_href: str | None = None
        self.chunks: list[_TextChunk] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append(tag)
        if tag == "a":
            attrs_dict = dict(attrs)
            self._current_href = attrs_dict.get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self._current_href = None
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        label = self._tag_stack[-1] if self._tag_stack else "text"
        self.chunks.append(_TextChunk(label=label, text=text, href=self._current_href))


def classify_page_type(chunks: list[_TextChunk], link_count: int) -> PageType:
    labels = {chunk.label for chunk in chunks}
    text = " ".join(chunk.text.lower() for chunk in chunks)
    if "article" in labels:
        return PageType.DETAIL
    if link_count > 0:
        return PageType.LISTING
    if "search" in text:
        return PageType.SEARCH
    return PageType.STATIC


def normalize_html_document(
    *,
    fixture_id: str,
    run_ref: Ref,
    source_adapter_result_ref: Ref,
    source_url: str,
    raw_artifact_ref: Ref,
    raw_html: str,
    policy_decision_refs: list[Ref],
) -> NormalizationResult:
    parser = _HTMLProjectionParser()
    parser.feed(raw_html)
    normalized_text = " ".join(chunk.text for chunk in parser.chunks)
    input_digest = stable_hash({"raw": raw_html})
    output_digest = stable_hash({"normalized": normalized_text})
    normalized_artifact_ref = f"artifact:{fixture_id}:normalized:{output_digest[:12]}"
    anchor_map_ref = f"anchor-map:{fixture_id}"
    manifest_ref = f"normalization-manifest:{fixture_id}"
    document = NormalizedDocument(
        id=f"normalized:{fixture_id}",
        run_ref=run_ref,
        source_adapter_result_ref=source_adapter_result_ref,
        raw_artifact_ref=raw_artifact_ref,
        normalized_artifact_ref=normalized_artifact_ref,
        anchor_map_ref=anchor_map_ref,
        normalization_manifest_ref=manifest_ref,
        language_refs=["language:en"],
    )
    anchors: list[TextAnchor] = []
    cursor = 0
    for index, chunk in enumerate(parser.chunks, start=1):
        start = normalized_text.find(chunk.text, cursor)
        if start < 0:
            start = cursor
        end = start + len(chunk.text)
        cursor = end
        anchors.append(
            TextAnchor(
                id=f"text-anchor:{fixture_id}:{index}",
                normalized_document_ref=document.id,
                raw_artifact_ref=raw_artifact_ref,
                label=chunk.label,
                text=chunk.text,
                normalized_start=start,
                normalized_end=end,
                selector_ref=f"selector:{fixture_id}:{chunk.label}:{index}",
            )
        )
    anchor_map = AnchorMap(
        id=anchor_map_ref,
        normalized_document_ref=document.id,
        raw_artifact_ref=raw_artifact_ref,
        anchor_refs=[anchor.id for anchor in anchors],
        content_digest=output_digest,
    )
    manifest = NormalizationManifest(
        id=manifest_ref,
        run_ref=run_ref,
        raw_artifact_ref=raw_artifact_ref,
        normalized_artifact_ref=normalized_artifact_ref,
        anchor_map_ref=anchor_map.id,
        parser_ref="parser:stdlib-htmlparser:v1",
        transformation_version="normalize-html:v1",
        input_digest=input_digest,
        output_digest=output_digest,
        policy_decision_refs=policy_decision_refs,
    )
    links: list[LinkProvenance] = []
    link_chunks = (
        (chunk_index, chunk)
        for chunk_index, chunk in enumerate(parser.chunks)
        if chunk.href
    )
    for index, (chunk_index, chunk) in enumerate(link_chunks, start=1):
        anchor_ref = anchors[chunk_index].id
        links.append(
            LinkProvenance(
                id=f"link-provenance:{fixture_id}:{index}",
                normalized_document_ref=document.id,
                source_url_ref=f"url:{source_url}",
                href=urljoin(source_url, chunk.href or ""),
                anchor_text=chunk.text,
                anchor_ref=anchor_ref,
                policy_decision_refs=policy_decision_refs,
                status=LinkProvenanceStatus.DISCOVERED,
            )
        )
    page_type_value = classify_page_type(parser.chunks, len(links))
    page_type = PageTypeClassification(
        id=f"page-type:{fixture_id}",
        normalized_document_ref=document.id,
        page_type=page_type_value,
        signal_refs=[f"signal:{fixture_id}:links:{len(links)}"],
        confidence_ref=f"confidence:{fixture_id}:page-type",
    )
    site_model = SiteModel(
        id=f"site-model:{fixture_id}",
        run_ref=run_ref,
        page_type_refs=[page_type.id],
        link_provenance_refs=[link.id for link in links],
        canonical_url_refs=[f"canonical:{source_url}"],
        summary_ref=f"summary:{fixture_id}:site-model",
    )
    return NormalizationResult(
        normalized_text=normalized_text,
        normalized_document=document,
        manifest=manifest,
        anchors=anchors,
        anchor_map=anchor_map,
        link_provenance=links,
        page_type=page_type,
        site_model=site_model,
        artifact_refs=[normalized_artifact_ref, anchor_map.id],
    )
