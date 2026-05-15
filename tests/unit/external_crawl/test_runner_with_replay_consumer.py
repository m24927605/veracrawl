"""Unit tests for s12 runner ↔ ReplayConsumerPort wiring."""

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
from veracrawl.contracts.errors import ReplayExhaustedError
from veracrawl.contracts.replay_bundle import ReplayBundle
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.ports.crawl_http_fetcher import FetchError


def _spec() -> CrawlJobSpec:
    return CrawlJobSpec(
        id="spec:s12:1", project_id="project:s12", objective="s12 test",
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


def _bundle(*clock_iso: str) -> ReplayBundle:
    return ReplayBundle(
        id="bundle:s12:1", run_ref="run:s12:1",
        recorded_at=datetime(2026, 5, 15, 12, 0, tzinfo=UTC),
        clock_trace=list(clock_iso) or ["2026-05-15T12:00:00+00:00"],
        model_response_refs={},
        seed_refs={},
        fetch_outcome_refs={},
    )


def _read_report(tmp_path: Path, run_id: str) -> dict[str, Any]:
    return json.loads(
        (tmp_path / run_id / "reports" / "run_report.json").read_text(),
    )


def test_runner_no_replay_consumer_uses_wall_clock(tmp_path: Path) -> None:
    spec = _spec()
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s12-no-replay")
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
    )
    runner.run()
    rep = _read_report(tmp_path, "run-s12-no-replay")
    assert rep["replay_consumer_ref"] is None
    assert rep["replay_invocation_count"] is None


def test_runner_with_replay_consumer_records_keyed_fields(
    tmp_path: Path,
) -> None:
    """In legacy mode (no s6 wiring) the consumer is plumbed through but
    the runner reads wall-clock timestamps directly. s13 will land the
    full clock-trace consumption via s6. This test pins the keyed-
    always run-report shape: ``replay_consumer_ref`` flips from None
    → "replay-consumer:active" when a consumer is wired.
    """

    bundle = _bundle(
        *[f"2026-05-15T12:00:{i:02d}+00:00" for i in range(60)],
    )
    consumer = InMemoryReplayConsumer(bundle=bundle)
    spec = _spec()
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s12-replay")
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
        replay_consumer=consumer,
    )
    runner.run()
    rep = _read_report(tmp_path, "run-s12-replay")
    assert rep["replay_consumer_ref"] == "replay-consumer:active"
    assert isinstance(rep["replay_invocation_count"], int)


def test_runner_replay_consumer_recorded_in_run_report(
    tmp_path: Path,
) -> None:
    """Confirms the run-report keyed-always shape under replay mode."""

    bundle = _bundle(*[f"2026-05-15T12:00:{i:02d}+00:00" for i in range(60)])
    consumer = InMemoryReplayConsumer(bundle=bundle)
    spec = _spec()
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s12-override")
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
        replay_consumer=consumer,
    )
    runner.run()
    rep = _read_report(tmp_path, "run-s12-override")
    assert rep["replay_invocation_count"] is not None


def test_replay_consumer_exhausted_propagation(tmp_path: Path) -> None:
    """The runner's clock override delegates to consumer.next_utc; when
    the consumer is exhausted the error propagates. Exercised directly
    against the override closure (the runner only consumes the clock
    in s6 mode, deferred to s13).
    """

    del tmp_path  # unused: error path tested directly on the consumer
    bundle = _bundle("2026-05-15T12:00:00+00:00")
    consumer = InMemoryReplayConsumer(bundle=bundle)
    consumer.next_utc()  # exhaust the single-entry trace
    with pytest.raises(ReplayExhaustedError):
        consumer.next_utc()


def test_two_replay_runs_with_same_bundle_produce_byte_equal_keyed_fields(
    tmp_path: Path,
) -> None:
    """Replay invariant smoke test: same bundle → same keyed fields."""

    def _run(run_id: str) -> dict[str, Any]:
        bundle = _bundle(
            *[f"2026-05-15T12:00:{i:02d}+00:00" for i in range(60)],
        )
        consumer = InMemoryReplayConsumer(bundle=bundle)
        spec = _spec()
        fetcher = _FailingFetcher()
        store = LocalFsCrawlArtifactStore(root=tmp_path, run_id=run_id)
        runner = ExternalCrawlRunner(
            spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
            replay_consumer=consumer,
        )
        runner.run()
        return _read_report(tmp_path, run_id)

    a = _run("run-s12-replay-a")
    b = _run("run-s12-replay-b")
    assert a["replay_consumer_ref"] == b["replay_consumer_ref"]
    assert a["replay_invocation_count"] == b["replay_invocation_count"]
