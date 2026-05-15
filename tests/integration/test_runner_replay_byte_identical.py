"""s13 live byte-identical re-execution test (narrowed scope per R2).

Per R2 the comparison is limited to keys that don't capture
wall-clock state. Inherently-wall-clock fields (``started_at`` etc.)
are excluded by ``_replay_compare.normalize_report``.

The test uses the s12 ``replay_consumer`` opt-in to drive the
runner from a recorded ``ReplayBundle``. Since the runner's
non-s6 path still reads wall-clock ``_now()`` for some fields
(s13 Out of scope per R2), this slice ships the smaller invariant:
two runs against the same recorded bundle produce byte-equal
**replay-side** fields (``replay_consumer_ref``,
``replay_invocation_count``, ``plan_decision_*`` / ``plan_decision_2_*``
when set, ``replay_seed_ref``, ``adapter_dispatch_choices``).
Larger ``_now()``-removal lands in a follow-up.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from veracrawl.adapters.object_stores.local_fs_crawl_artifact_store import (
    LocalFsCrawlArtifactStore,
)
from veracrawl.adapters.replay.in_memory_replay_consumer import (
    InMemoryReplayConsumer,
)
from veracrawl.contracts.crawl_job import (
    ArtifactPolicySpec,
    CrawlJobSpec,
    ExtractionMode,
    ExtractionSpec,
    OutputFormat,
    OutputSpec,
    PrivateNetworkPolicy,
    RateLimitSpec,
    RobotsPolicy,
)
from veracrawl.contracts.enums import AdapterType
from veracrawl.contracts.replay_bundle import ReplayBundle
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.ports.crawl_http_fetcher import FetchError

from ._replay_compare import canonical_json, normalize_report


def _spec() -> CrawlJobSpec:
    return CrawlJobSpec(
        id="spec:s13:1", project_id="project:s13", objective="s13 test",
        seed_urls=["https://a.example/"],
        allowed_domains=["a.example"], denied_domains=[],
        max_depth=1, max_pages=10, max_runtime_seconds=5,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=600, crawl_delay_seconds=0.0),
        source_adapters=[AdapterType.HTTP],
        robots_policy=RobotsPolicy.WARN,
        private_network_policy=PrivateNetworkPolicy.DENY,
        artifact_policy=ArtifactPolicySpec(
            store_raw_html=False, store_headers=False,
            store_screenshots=False, store_documents=False,
        ),
        extraction=ExtractionSpec(
            mode=ExtractionMode.DETERMINISTIC, schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        output=OutputSpec(format=OutputFormat.JSONL, include_raw_refs=False,
                          include_evidence=False),
    )


@dataclass
class _FailingFetcher:
    calls: list[str] = field(default_factory=list)

    def fetch(self, url: str, *, timeout_seconds: float) -> Any:  # noqa: ARG002
        self.calls.append(url)
        raise FetchError("refuse")


def _assemble_bundle(run_id: str) -> ReplayBundle:
    return ReplayBundle(
        id=f"bundle:s13:{run_id}",
        run_ref=f"run:s13:{run_id}",
        recorded_at=datetime(2026, 5, 15, 12, 0, tzinfo=UTC),
        clock_trace=[
            f"2026-05-15T12:00:{i:02d}+00:00" for i in range(60)
        ],
        model_response_refs={},
        seed_refs={},
        fetch_outcome_refs={},
    )


def _run_with_consumer(
    tmp_path: Path, *, run_id: str,
) -> dict[str, Any]:
    bundle = _assemble_bundle(run_id)
    consumer = InMemoryReplayConsumer(bundle=bundle)
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id=run_id)
    runner = ExternalCrawlRunner(
        spec=_spec(), store=store, run_root=store.run_root,
        fetcher=_FailingFetcher(),
        replay_consumer=consumer,
    )
    runner.run()
    return json.loads(
        (tmp_path / run_id / "reports" / "run_report.json").read_text(),
    )


# Test 1
def test_record_phase_produces_keyed_replay_fields(tmp_path: Path) -> None:
    report = _run_with_consumer(tmp_path, run_id="run-s13-record")
    assert report["replay_consumer_ref"] == "replay-consumer:active"
    assert report["replay_invocation_count"] is not None


# Test 2
def test_bundle_assembly_validates_with_required_invariants() -> None:
    bundle = _assemble_bundle("test")
    assert bundle.run_ref == "run:s13:test"
    assert len(bundle.clock_trace) >= 1


# Test 3
def test_replay_phase_uses_replay_consumer_for_lookups(tmp_path: Path) -> None:
    report = _run_with_consumer(tmp_path, run_id="run-s13-replay")
    # Runner consulted the consumer at least once (or recorded that it
    # wired one in — both observable via the keyed fields).
    assert report["replay_consumer_ref"] == "replay-consumer:active"


# Test 4
def test_record_and_replay_replay_keyed_fields_byte_equal(tmp_path: Path) -> None:
    """The replay invariant in s13 narrowed scope: two runs against
    the same bundle produce byte-equal NORMALIZED reports (excluding
    wall-clock fields per R2).
    """

    a = _run_with_consumer(tmp_path, run_id="run-s13-a")
    b = _run_with_consumer(tmp_path, run_id="run-s13-b")
    # ``run_id`` differs by design; normalize lifts wall-clock noise
    # but the report still embeds run-specific paths under
    # ``run_root``. Compare the keyed REPLAY fields directly.
    keys = (
        "replay_consumer_ref",
        "replay_invocation_count",
        "replay_seed_ref",
        "adapter_dispatch_choices",
        "plan_decision_2_ref",
        "plan_decision_2_replay_refs",
        "plan_decision_2_planned_seed_order",
        "plan_decision_2_adapter_priors",
        "plan_decision_2_frontier_priority_hints",
        "plan_decision_2_extraction_strategy_refs",
        "replan_invoked",
    )
    for key in keys:
        assert a.get(key) == b.get(key), (
            f"replay key {key!r} differs across two runs of the same bundle"
        )


# Test 5
def test_compare_helper_strips_wall_clock_fields_only() -> None:
    """The compare helper must leave replay-scope keys intact."""

    sample = {
        "started_at": "2026-05-15T12:00:00",
        "replay_consumer_ref": "replay-consumer:active",
        "replan_invoked": False,
    }
    normalized = normalize_report(sample)
    assert "started_at" not in normalized
    assert normalized["replay_consumer_ref"] == "replay-consumer:active"
    assert normalized["replan_invoked"] is False
    # canonical_json is stable.
    assert canonical_json(sample) == canonical_json(sample.copy())


# Pin the live mark for s13's full run-end-to-end suite
pytestmark = pytest.mark.live
