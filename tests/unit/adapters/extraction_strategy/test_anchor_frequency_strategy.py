"""Unit tests for ``AnchorFrequencyExtractionStrategy`` (s7 tests 14-22)."""

from __future__ import annotations

from collections.abc import Callable

from veracrawl.adapters.extraction_strategy.anchor_frequency_strategy import (
    AnchorFrequencyExtractionStrategy,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.ports.extraction_strategy import ExtractionStrategyPort


def _read_model(*sample_refs: str) -> NormalizedDocumentReadModel:
    return NormalizedDocumentReadModel(
        id="doc:test:1",
        normalized_document_ref="normalized-doc:test:1",
        text_sample_refs=list(sample_refs) or ["sample:test:1"],
    )


def _resolver(samples: dict[str, str]) -> Callable[[Ref], str]:
    return lambda ref: samples[ref]


# Test 14
def test_propose_emits_field_per_pattern_seen_twice() -> None:
    sample = """
        <dl><dt>Color</dt><dd>red</dd></dl>
        <dl><dt>Color</dt><dd>blue</dd></dl>
    """
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:14",
    )
    names = [f.name for f in proposal.proposed_fields]
    assert "color" in names


# Test 15
def test_propose_skips_singleton_patterns() -> None:
    sample = "<dl><dt>OnlyOnce</dt><dd>x</dd></dl>"
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:15",
    )
    names = [f.name for f in proposal.proposed_fields]
    assert "onlyonce" not in names


# Test 16
def test_propose_infers_number_type_from_digit_values() -> None:
    sample = """
        <dl><dt>Price</dt><dd>42</dd></dl>
        <dl><dt>Price</dt><dd>99</dd></dl>
    """
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:16",
    )
    price = next(f for f in proposal.proposed_fields if f.name == "price")
    assert price.proposed_type == "number"


# Test 17
def test_propose_infers_url_type_from_https_values() -> None:
    sample = """
        <dl><dt>Link</dt><dd>https://a.example/x</dd></dl>
        <dl><dt>Link</dt><dd>https://b.example/y</dd></dl>
    """
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:17",
    )
    link = next(f for f in proposal.proposed_fields if f.name == "link")
    assert link.proposed_type == "url"


# Test 18
def test_propose_infers_date_type_from_iso8601_values() -> None:
    sample = """
        <dl><dt>Published</dt><dd>2026-01-15</dd></dl>
        <dl><dt>Published</dt><dd>2026-03-20</dd></dl>
    """
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:18",
    )
    pub = next(f for f in proposal.proposed_fields if f.name == "published")
    assert pub.proposed_type == "date"


# Test 19
def test_propose_falls_back_to_string_type() -> None:
    sample = """
        <dl><dt>Title</dt><dd>An Article</dd></dl>
        <dl><dt>Title</dt><dd>Another Article</dd></dl>
    """
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:19",
    )
    title = next(f for f in proposal.proposed_fields if f.name == "title")
    assert title.proposed_type == "string"


# Test 20
def test_propose_emission_order_matches_first_anchor_appearance() -> None:
    sample = """
        <dl><dt>B</dt><dd>1</dd></dl>
        <dl><dt>A</dt><dd>2</dd></dl>
        <dl><dt>B</dt><dd>3</dd></dl>
        <dl><dt>A</dt><dd>4</dd></dl>
    """
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:20",
    )
    names = [f.name for f in proposal.proposed_fields]
    # 'b' first observed before 'a' — must keep that order.
    assert names == ["b", "a"]


# Test 21
def test_propose_is_pure_function() -> None:
    sample = """
        <dl><dt>X</dt><dd>1</dd></dl>
        <dl><dt>X</dt><dd>2</dd></dl>
    """
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    a = adapter.propose(document=_read_model("s:1"), run_ref="run:test:21")
    b = adapter.propose(document=_read_model("s:1"), run_ref="run:test:21")
    assert a.canonical_json() == b.canonical_json()


# Test 22
def test_propose_implements_extraction_strategy_port() -> None:
    adapter = AnchorFrequencyExtractionStrategy(resolve_text=lambda _ref: "")
    assert isinstance(adapter, ExtractionStrategyPort)


# Bonus — replay_refs content (R7)
def test_propose_replay_refs_pin_run_and_document() -> None:
    sample = "<dl><dt>X</dt><dd>1</dd></dl><dl><dt>X</dt><dd>2</dd></dl>"
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:replay",
    )
    assert "run:test:replay" in proposal.replay_refs
    assert proposal.source_document_ref == "normalized-doc:test:1"


# Bonus — table-row pattern coverage
def test_propose_emits_field_from_table_row_pattern() -> None:
    sample = """
        <table><tr><th>SKU</th><td>A-1</td></tr></table>
        <table><tr><th>SKU</th><td>A-2</td></tr></table>
    """
    adapter = AnchorFrequencyExtractionStrategy(
        resolve_text=_resolver({"s:1": sample}),
    )
    proposal = adapter.propose(
        document=_read_model("s:1"), run_ref="run:test:tr",
    )
    names = [f.name for f in proposal.proposed_fields]
    assert "sku" in names
