"""Live test #2 (Phase 1 step 1.6b) — ``httpbin.org/redirect-to``.

design.md §6 step 6.4 deliverable #2: "``httpbin.org/redirect-to``
— redirect chain hop evidence."

Validates that the production HTTP adapter follows a server-issued
redirect (302 + ``Location`` header) and records the hop in
``NetworkClientResult.redirect_hops`` plus a per-attempt
``NetworkAttemptEvidence`` for both the initial and the redirected
fetch. Runs under ``RuntimeMode.PRODUCTION`` with the production
egress / private-network policy.

Gated by ``@pytest.mark.live``; default invocation excludes via
``-m 'not live'``. Operators run with ``pytest -m live``.

iter1 6-point pre-flight scan applied:

1. **Attacker-controlled inputs**: ``httpbin.org/redirect-to``
   accepts a ``url`` query param the test sets to another
   ``httpbin.org`` path — same-origin redirect, so cross-origin
   credential strip is not exercised here (that lives in the
   fixture-mode tests where the cross-origin contract has
   deterministic control).
2. **Execution timing**: two HTTP round trips. The adapter's
   default 10s timeout per request + the AIMD limiter's
   floor-aware pacing keeps the test bounded.
3. **Concurrency**: single fetch sequence, no concurrency.
4. **Failure modes**: missing Location → ``RedirectDeniedError``;
   redirect loop → ``RedirectDeniedError`` with the
   ``max_redirects`` cap; covered by fixture-mode tests. Live
   target down → flake (operator review per design.md §6
   step 6.5).
5. **PRODUCTION mode**: ``with_runtime_mode(RuntimeMode.PRODUCTION)``
   so production-only gates apply.
6. **API symmetry**: same wiring as live test #1 (real robots
   parser + AIMD limiter + conditional cache + cookie jar +
   egress allowlist + private-network denial).
"""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest

from veracrawl.adapters.network.aimd_rate_limiter import InMemoryAimdLimiter
from veracrawl.adapters.network.in_memory_conditional_cache import (
    InMemoryConditionalCache,
)
from veracrawl.adapters.network.in_memory_cookie_jar import InMemoryCookieJar
from veracrawl.adapters.network.stdlib_http import (
    HttpClientConfig,
    StdlibHttpSourceAdapter,
)
from veracrawl.adapters.network.urllib_robots import (
    UrllibRobotsParser,
    make_httpx_robots_fetcher,
)
from veracrawl.contracts.enums import AdapterType, RouteClass
from veracrawl.contracts.network import NetworkRequest
from veracrawl.contracts.source_adapter import SourceAdapterCommand
from veracrawl.fetch.acquisition import source_adapter_spec
from veracrawl.runtime_support.runtime_mode import RuntimeMode, with_runtime_mode

_HTTPBIN_ALLOWLIST: frozenset[str] = frozenset({"https://httpbin.org"})

# Build the redirect-to URL: httpbin will issue 302 → /headers.
_REDIRECT_TARGET = "https://httpbin.org/headers"
_REDIRECT_FROM = (
    "https://httpbin.org/redirect-to?url=" + quote(_REDIRECT_TARGET, safe="") + "&status_code=302"
)


def _make_request(url: str = _REDIRECT_FROM) -> NetworkRequest:
    return NetworkRequest(
        id="network-request:step-1-6b:httpbin-redirect-to",
        run_ref="run:live:step-1-6b",
        source_ref=url,
        url=url,
        method="GET",
        headers_ref="headers:step-1-6b:request",
        policy_decision_refs=["policy:live:step-1-6b:default"],
        egress_policy_ref="policy:live:step-1-6b:egress",
        private_network_policy_ref="policy:live:step-1-6b:private-network",
        robots_policy_ref="policy:live:step-1-6b:robots",
        rate_budget_ref="rate:live:step-1-6b:default",
        size_budget_bytes=1_000_000,
        timeout_ms=15_000,
        idempotency_key="idem:step-1-6b",
    )


def _make_command(url: str = _REDIRECT_FROM) -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id="cmd:live:step-1-6b",
        adapter_spec=source_adapter_spec(AdapterType.HTTP),
        source_ref=url,
        policy_snapshot_ref="policy:live:step-1-6b:default",
        deterministic_clock_ref="clock:live:step-1-6b",
        randomness_seed_ref="random:live:step-1-6b",
    )


def _real_robots_port() -> UrllibRobotsParser:
    fetcher = make_httpx_robots_fetcher(
        timeout_s=10.0,
        max_redirects=5,
        egress_allowlist=_HTTPBIN_ALLOWLIST,
        allow_private_network=False,
    )
    return UrllibRobotsParser(fetcher=fetcher)


def _production_config() -> HttpClientConfig:
    return HttpClientConfig(
        robots_port=_real_robots_port(),
        rate_limiter=InMemoryAimdLimiter(),
        conditional_cache=InMemoryConditionalCache(),
        cookie_jar=InMemoryCookieJar(),
        route_class=RouteClass.LISTING,
        egress_allowlist=_HTTPBIN_ALLOWLIST,
        allow_private_network=False,
    )


@pytest.mark.live
def test_httpbin_redirect_to_records_redirect_hop_and_final_response() -> None:
    """Acceptance (design.md §6 step 6.4 #2): ``httpbin.org/redirect-to``
    emits a 302 + ``Location`` to ``/headers``; the adapter follows
    the redirect, records the hop in ``redirect_hops``, and returns
    the final 200 ``/headers`` body."""

    config = _production_config()
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = StdlibHttpSourceAdapter(_make_request(), config=config)
        adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    # Final response is from /headers (the redirect target).
    assert result.response.status_code == 200
    assert result.response.final_url == _REDIRECT_TARGET
    # Body is httpbin's headers echo.
    payload = json.loads(result.body_text)
    assert "headers" in payload, f"unexpected httpbin shape: {payload}"
    # Exactly one redirect hop recorded.
    assert len(result.redirect_hops) == 1
    hop = result.redirect_hops[0]
    assert hop.from_url == _REDIRECT_FROM
    assert hop.to_url == _REDIRECT_TARGET
    assert hop.status_code == 302
    assert hop.sequence == 1


@pytest.mark.live
def test_httpbin_redirect_to_per_attempt_evidence_for_both_hops() -> None:
    """Per-attempt ``NetworkAttemptEvidence`` populated for both the
    initial redirect and the redirected target.

    This is the load-bearing replay/audit assertion: a redirect is
    a separate HTTP attempt and must carry its own evidence row."""

    config = _production_config()
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = StdlibHttpSourceAdapter(_make_request(), config=config)
        adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    # One evidence per hop: initial 302 + final 200.
    assert len(result.attempt_evidences) == 2
    initial_ev, final_ev = result.attempt_evidences
    # Initial: 302 redirect to /headers.
    assert initial_ev.request_url == _REDIRECT_FROM
    assert initial_ev.response_status == 302
    assert initial_ev.redirect_hop_count == 0
    # Final: 200 from the redirect target.
    assert final_ev.request_url == _REDIRECT_TARGET
    assert final_ev.response_status == 200
    assert final_ev.redirect_hop_count == 1


@pytest.mark.live
def test_httpbin_redirect_to_records_redirect_hop_refs_on_response() -> None:
    """``NetworkResponse.redirect_hop_refs`` carries the hop IDs so a
    replay record can join the response → hop → attempt-evidence
    chain via stable references."""

    config = _production_config()
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = StdlibHttpSourceAdapter(_make_request(), config=config)
        adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    hop_ids_from_response = list(result.response.redirect_hop_refs)
    hop_ids_in_chain = [hop.id for hop in result.redirect_hops]
    assert hop_ids_from_response == hop_ids_in_chain
    assert len(hop_ids_from_response) == 1
