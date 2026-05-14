"""Integration test 17 — runner + observer + replan against a local HTTP stub.

Spins up a localhost HTTP server that serves one 301 redirect plus a
destination page with two outbound links. Verifies the s6 wiring
end-to-end:

- observer records ≥ 1 redirect event + ≥ 3 url events + ≥ 1 page-
  structure event.
- the replan path fires (`run_report["replan_invoked"] is True`).
- `decision_2.frontier_priority_hints` contains a `HOST_GLOB` hint for
  the redirected host (the planner factory closure produces it from
  the feedback).

The stub uses ``http.server`` + a background thread — no external
dependencies, deterministic, runs offline.
"""

from __future__ import annotations

import http.server
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

from veracrawl.adapters.graph.in_memory_graph_observer import InMemoryGraphObserver
from veracrawl.adapters.object_stores.local_fs_crawl_artifact_store import (
    LocalFsCrawlArtifactStore,
)
from veracrawl.adapters.planning.deterministic_crawl_planner_v2 import (
    DeterministicCrawlPlannerV2,
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
from veracrawl.contracts.crawl_planner import (
    AdapterPrior,
    PlanDecision,
    PlannedSeed,
    PlanRequest,
)
from veracrawl.contracts.enums import AdapterType, FrontierMatchKind
from veracrawl.contracts.planner_observation_feedback import PlannerObservationFeedback
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.ports.crawl_http_fetcher import FetchOutcome, RedirectHop


class _StubHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/start":
            self.send_response(301)
            self.send_header("Location", "/target")
            self.end_headers()
            return
        if self.path == "/target":
            body = (
                b'<html><body>'
                b'<a href="/leaf-a">a</a>'
                b'<a href="/leaf-b">b</a>'
                b'</body></html>'
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in ("/leaf-a", "/leaf-b"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args: Any) -> None:  # noqa: ARG002
        pass


@pytest.fixture
def stub_server() -> Any:
    server = http.server.HTTPServer(("127.0.0.1", 0), _StubHandler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=1.0)


class _HttpxLikeFetcher:
    """Tiny fetcher that drives the stub through urllib (no httpx dep)."""

    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome:  # noqa: ARG002
        import urllib.request

        history: list[RedirectHop] = []

        class _RedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(
                self, req: Any, fp: Any, code: int,
                msg: Any, headers: Any, newurl: str,
            ) -> Any:
                history.append(RedirectHop(
                    from_url=req.full_url, to_url=newurl, status_code=code,
                ))
                return super().redirect_request(req, fp, code, msg, headers, newurl)

        opener = urllib.request.build_opener(_RedirectHandler())
        with opener.open(url) as resp:
            body = resp.read()
            content_type = resp.headers.get("Content-Type", "text/html")
            final_url = resp.geturl()
        return FetchOutcome(
            requested_url=url, final_url=final_url, status_code=200,
            headers={}, body=body, content_type=content_type,
            redirect_chain=[h.to_url for h in history],
            redirect_history=history,
        )


def test_local_stub_redirect_produces_host_glob_hint(
    tmp_path: Path, stub_server: str,
) -> None:
    host = urlsplit(stub_server).hostname or "127.0.0.1"
    start = f"{stub_server}/start"

    spec = CrawlJobSpec(
        id="spec:s6:integ:1", project_id="project:s6-integ",
        objective="s6 stub test",
        seed_urls=[start],
        allowed_domains=[host], denied_domains=[],
        max_depth=2, max_pages=10, max_runtime_seconds=10,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=600, crawl_delay_seconds=0.0),
        source_adapters=[AdapterType.HTTP], robots_policy=RobotsPolicy.WARN,
        private_network_policy=PrivateNetworkPolicy.ALLOW_LOOPBACK_ONLY,
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

    def builder(s: CrawlJobSpec, _r: Path) -> PlanRequest:
        return PlanRequest(
            id="plan-req:integ:1", run_ref="run:s6-integ:1",
            objective_ref="objective:1",
            seed_urls=[start], budget_ref="budget:1",
            policy_snapshot_ref="policy-snap:1",
            policy_decision_refs=["policy-decision:1"],
            replay_config_ref="replay-config:1",
        )

    class _SeedPlanner:
        def plan(self, request: PlanRequest) -> PlanDecision:
            return PlanDecision(
                id="plan-decision:integ:1", request_ref=request.id,
                planner_adapter_ref="adapter:integ:v1",
                planned_seeds=[PlannedSeed(
                    canonical_url=start, priority_score=1.0,
                    adapter_hint=AdapterType.HTTP,
                    rationale_ref="rationale:integ:seed",
                )],
                adapter_priors=[AdapterPrior(
                    adapter_type=AdapterType.HTTP, weight=1.0,
                    rationale_ref="rationale:integ:http",
                )],
                replay_refs=[request.id, "adapter:integ:v1"],
                policy_decision_refs=["policy-decision:1"],
            )

    def factory(fb: PlannerObservationFeedback) -> Any:
        return DeterministicCrawlPlannerV2(feedback=fb)

    base = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)
    idx = [0]

    def utc_clock() -> datetime:
        from datetime import timedelta as _td
        t = base + _td(seconds=idx[0])
        idx[0] += 1
        return t

    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s6-integ")
    observer = InMemoryGraphObserver(run_ref="run:s6-integ:1")
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root,
        fetcher=_HttpxLikeFetcher(),
        planner=_SeedPlanner(), plan_request_builder=builder,
        utc_clock=utc_clock, utc_clock_ref="utc-clock:integ:1",
        graph_observer=observer,
        feedback_aware_planner_factory=factory,
    )
    runner.run()

    report = json.loads(
        (tmp_path / "run-s6-integ" / "reports" / "run_report.json").read_text(),
    )

    assert report["replan_invoked"] is True

    # Observer event-count assertions per plan §Integration test:
    # - >= 1 redirect event (the /start -> /target hop)
    # - >= 3 url events (seed admission + 2 child discoveries)
    # - 1 page-structure event (the /target page parse)
    snap = observer.snapshot(id="snap:integ:check", snapshot_at=base)
    assert len(snap.redirect_observed_events) >= 1, (
        f"expected >=1 redirect event; got {len(snap.redirect_observed_events)}"
    )
    assert len(snap.url_observed_events) >= 3, (
        f"expected >=3 url events; got {len(snap.url_observed_events)}"
    )
    assert len(snap.page_structure_observed_events) >= 1, (
        f"expected >=1 page-structure event; "
        f"got {len(snap.page_structure_observed_events)}"
    )

    # The deterministic v2 planner emits a HOST_GLOB hint per redirect
    # neighbour. The stub fetcher records a redirect from /start →
    # /target, so the feedback's redirect_neighbours contains the
    # /target URL, whose hostname is the stub host.
    hints = report["plan_decision_2_frontier_priority_hints"]
    assert hints is not None
    host_glob_hints = [
        h for h in hints if h["match_kind"] == FrontierMatchKind.HOST_GLOB.value
    ]
    assert len(host_glob_hints) >= 1
    assert any(h["match_value"] == host for h in host_glob_hints)
