"""Unit tests for ``AnchorReselectRepair`` (s8.b)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from veracrawl.adapters.repair.anchor_reselect_repair import AnchorReselectRepair
from veracrawl.contracts.common import Ref
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.ports.repair import RepairPort


def _resolver(samples: dict[str, str]) -> Callable[[Ref], str]:
    return lambda ref: samples[ref]


def _drift(drifted: list[str]) -> DriftReport:
    return DriftReport(
        id="drift:run-1:1",
        run_ref="run:1",
        proposal_ref="proposal:run-1:hash",
        pages_evaluated=5,
        field_missing_rates={n: 0.6 for n in drifted},
        drifted_fields=drifted,
        drift_threshold=0.30,
        replay_refs=["run:1", "proposal:run-1:hash"],
    )


def _doc(sample_ref: str) -> NormalizedDocumentReadModel:
    return NormalizedDocumentReadModel(
        id=f"doc:{sample_ref}",
        normalized_document_ref=f"normalized:{sample_ref}",
        text_sample_refs=[sample_ref],
    )


def test_repair_implements_repair_port() -> None:
    assert isinstance(AnchorReselectRepair(), RepairPort)


def test_repair_proposes_xpath_per_drifted_field() -> None:
    sample = """
        <h2>Price</h2><p>$42</p>
        <h2>Price</h2><p>$99</p>
    """
    adapter = AnchorReselectRepair()
    proposal = adapter.repair(
        drift_report=_drift(["price"]),
        document_samples=[_doc("s:1")],
        resolve_text=_resolver({"s:1": sample}),
        run_ref="run:1",
    )
    assert len(proposal.field_repairs) == 1
    assert proposal.field_repairs[0].field_name == "price"


def test_repair_falls_back_when_no_matching_anchor() -> None:
    adapter = AnchorReselectRepair()
    proposal = adapter.repair(
        drift_report=_drift(["price"]),
        document_samples=[_doc("s:1")],
        resolve_text=_resolver({"s:1": "<p>nothing relevant</p>"}),
        run_ref="run:1",
    )
    field = proposal.field_repairs[0]
    assert field.confidence < 0.50
    assert field.repair_kind == "anchor_reselect"


def test_repair_rejects_drift_report_with_no_drifted_fields() -> None:
    adapter = AnchorReselectRepair()
    no_drift = DriftReport(
        id="drift:1", run_ref="run:1", proposal_ref="proposal:1",
        pages_evaluated=5, field_missing_rates={"title": 0.1},
        drifted_fields=[], drift_threshold=0.30,
        replay_refs=["run:1"],
    )
    with pytest.raises(ValueError, match="drifted_fields"):
        adapter.repair(
            drift_report=no_drift, document_samples=[_doc("s:1")],
            resolve_text=_resolver({"s:1": "<p>x</p>"}), run_ref="run:1",
        )


def test_repair_rejects_empty_document_samples() -> None:
    adapter = AnchorReselectRepair()
    with pytest.raises(ValueError, match="document_samples"):
        adapter.repair(
            drift_report=_drift(["price"]), document_samples=[],
            resolve_text=lambda _ref: "", run_ref="run:1",
        )


def test_repair_is_pure_function() -> None:
    sample = "<h2>Price</h2><p>$1</p><h2>Price</h2><p>$2</p>"
    adapter = AnchorReselectRepair()
    a = adapter.repair(
        drift_report=_drift(["price"]),
        document_samples=[_doc("s:1")],
        resolve_text=_resolver({"s:1": sample}),
        run_ref="run:1",
    )
    b = adapter.repair(
        drift_report=_drift(["price"]),
        document_samples=[_doc("s:1")],
        resolve_text=_resolver({"s:1": sample}),
        run_ref="run:1",
    )
    assert a.canonical_json() == b.canonical_json()


def test_repair_replay_refs_pin_drift_and_adapter() -> None:
    sample = "<h2>Price</h2><h2>Price</h2>"
    adapter = AnchorReselectRepair()
    proposal = adapter.repair(
        drift_report=_drift(["price"]),
        document_samples=[_doc("s:1")],
        resolve_text=_resolver({"s:1": sample}),
        run_ref="run:1",
    )
    assert "drift:run-1:1" in proposal.replay_refs
    assert "adapter:anchor-reselect-repair:v1" in proposal.replay_refs
